"""
Pose Registry: Central database for all poses with unique IDs.
Loads all poses from PNG-based database and provides search API.
"""

import importlib
import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image

# DEBUG logging setup
DEBUG_LOG_FILE = Path(__file__).parent / "debug_log.txt"

def debug_log(message: str):
    """Write debug message to log file and console."""
    timestamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    try:
        with open(DEBUG_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(full_message + '\n')
    except Exception as e:
        print(f"[DEBUG] Failed to write to log file: {e}")

# Clear log file on import
try:
    DEBUG_LOG_FILE.unlink(missing_ok=True)
    debug_log("=== DEBUG LOG STARTED ===")
except:
    pass


class PoseRegistry:
    """Singleton registry for all available poses."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            debug_log("[DEBUG] PoseRegistry.__init__: Already initialized, skipping")
            return
        
        debug_log("[DEBUG] PoseRegistry.__init__: Starting initialization")
        self._initialized = True
        self.poses: List[Dict] = []
        self.poses_by_id: Dict[int, Dict] = {}
        self.index_by_filter: Dict[Tuple, List[int]] = {}
        
        # Try to load from cache first
        debug_log("[DEBUG] PoseRegistry.__init__: Attempting to load from cache")
        if self._load_from_cache():
            debug_log(f"[DEBUG] PoseRegistry.__init__: Successfully loaded {len(self.poses)} poses from cache")
        else:
            debug_log("[DEBUG] PoseRegistry.__init__: Cache load failed, loading poses from disk")
            self._load_poses()
            self._save_to_cache()
        
        debug_log(f"[DEBUG] PoseRegistry.__init__: Building index for {len(self.poses)} poses")
        self._build_index()
        debug_log(f"[DEBUG] PoseRegistry.__init__: Initialization complete. Total poses: {len(self.poses)}")
    
    def _load_from_cache(self) -> bool:
        """Try to load poses from cache file. Returns True if successful."""
        cache_file = Path(__file__).parent / "pose_registry_cache.json"
        debug_log(f"[DEBUG] _load_from_cache: Checking cache file: {cache_file}")
        if not cache_file.exists():
            debug_log("[DEBUG] _load_from_cache: Cache file does not exist")
            return False
        
        debug_log(f"[DEBUG] _load_from_cache: Cache file exists, size: {cache_file.stat().st_size} bytes")
        
        try:
            debug_log("[DEBUG] _load_from_cache: Reading cache file")
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            debug_log(f"[DEBUG] _load_from_cache: Cache data loaded, keys: {list(cache_data.keys())}")
            
            # Check if cache is still valid by comparing file modification times
            openpose_dir = self._get_openpose_dir()
            debug_log(f"[DEBUG] _load_from_cache: OpenPose directory: {openpose_dir}")
            if openpose_dir.exists():
                cache_mtime = cache_file.stat().st_mtime
                newest_png = 0
                png_count = 0
                for png_path in openpose_dir.rglob("*.png"):
                    png_mtime = png_path.stat().st_mtime
                    newest_png = max(newest_png, png_mtime)
                    png_count += 1
                
                debug_log(f"[DEBUG] _load_from_cache: Found {png_count} PNG files, newest mtime: {newest_png}, cache mtime: {cache_mtime}")
                
                if newest_png > cache_mtime:
                    debug_log("[DEBUG] _load_from_cache: Cache is outdated, rescanning...")
                    return False
            
            # Load from cache
            debug_log("[DEBUG] _load_from_cache: Loading poses from cache data")
            self.poses = cache_data["poses"]
            self.poses_by_id = {}
            for key, value in cache_data.get("poses_by_id", {}).items():
                try:
                    key_int = int(key)
                except Exception:
                    key_int = key
                self.poses_by_id[key_int] = value
            
            # Convert string keys back to tuples for index_by_filter
            if self.index_by_filter:
                self.index_by_filter = {tuple(k) if isinstance(k, list) else k: v 
                                      for k, v in self.index_by_filter.items()}
            
            # If cache contains no poses but OpenPose data exists, force a rescan.
            if len(self.poses) == 0 and openpose_dir.exists():
                has_png = any(openpose_dir.rglob("*.png"))
                if has_png:
                    debug_log("[DEBUG] _load_from_cache: WARNING: cache is empty but OpenPose PNGs are present; rescanning...")
                    return False
            
            debug_log("[DEBUG] _load_from_cache: Cache load successful")
            return True
            
        except Exception as e:
            debug_log(f"[DEBUG] _load_from_cache: Error loading cache: {e}")
            return False
    
    def _save_to_cache(self):
        """Save current poses to cache file."""
        try:
            cache_file = Path(__file__).parent / "pose_registry_cache.json"
            
            # Convert poses to serializable format
            serializable_poses = []
            for pose in self.poses:
                pose_copy = pose.copy()
                serializable_poses.append(pose_copy)
            
            # Convert tuple keys to lists for JSON serialization
            serializable_index = {list(k) if isinstance(k, tuple) else k: v 
                                for k, v in self.index_by_filter.items()}
            
            cache_data = {
                "poses": serializable_poses,
                "poses_by_id": self.poses_by_id,
                "index_by_filter": serializable_index,
                "total_poses": len(self.poses)
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"[PoseRegistry] Saved cache with {len(self.poses)} poses")
            
        except Exception as e:
            print(f"[PoseRegistry] Error saving cache: {e}")
    
    def _get_openpose_dir(self) -> Path:
        """Get OpenPose directory from ComfyUI models folder."""
        env_path = os.getenv("OPENPOSE_MODELS_PATH")
        if env_path:
            candidate = Path(env_path)
            if candidate.exists():
                return candidate
            print(f"[PoseRegistry] WARNING: OPENPOSE_MODELS_PATH is set but does not exist: {candidate}")

        models_dir = self._resolve_models_dir()
        if models_dir is None:
            print("[PoseRegistry] ERROR: could not resolve ComfyUI models directory from folder_paths or package location")
            return Path("")

        openpose_dir = models_dir / "openpose"
        if openpose_dir.exists():
            return openpose_dir

        print(f"[PoseRegistry] WARNING: expected openpose directory not found: {openpose_dir}")
        return Path("")

    def _resolve_models_dir(self) -> Optional[Path]:
        models_dir = None
        try:
            folder_paths = importlib.import_module("folder_paths")
        except (ImportError, ModuleNotFoundError) as exc:
            print(f"[PoseRegistry] ERROR: folder_paths module unavailable: {exc}")
            folder_paths = None

        if folder_paths is not None:
            for attr_name in ["get_models_dir", "get_models_directory", "get_models_path", "get_model_dir"]:
                if hasattr(folder_paths, attr_name):
                    try:
                        candidate = Path(getattr(folder_paths, attr_name)())
                        if candidate.exists():
                            models_dir = candidate
                            break
                    except Exception:
                        continue

            if models_dir is None and hasattr(folder_paths, "get_input_directory"):
                try:
                    input_dir = Path(folder_paths.get_input_directory())
                    candidate = input_dir.parent / "models"
                    if candidate.exists():
                        models_dir = candidate
                    else:
                        candidate = (input_dir / ".." / "models").resolve()
                        if candidate.exists():
                            models_dir = candidate
                except Exception:
                    pass

        if models_dir is None:
            models_dir = self._find_models_dir_by_search()
            if models_dir is not None:
                print(f"[PoseRegistry] INFO: Found ComfyUI models directory by search: {models_dir}")

        return models_dir

    @staticmethod
    def _find_models_dir_by_search() -> Optional[Path]:
        search_roots = [Path(__file__).resolve().parent, Path.cwd()]
        for root in search_roots:
            for parent in [root] + list(root.parents):
                candidate = parent / "models"
                if candidate.exists() and (candidate / "openpose").exists():
                    return candidate
                candidate = parent / "ComfyUI" / "models"
                if candidate.exists() and (candidate / "openpose").exists():
                    return candidate
        return None

    @staticmethod
    def _normalize_token(value: str) -> str:
        return str(value).strip().lower().replace(" ", "_").replace("-", "_")

    def _derive_pose_metadata(self, png_path: Path, openpose_dir: Path):
        relative = png_path.relative_to(openpose_dir)
        parts = [self._normalize_token(p) for p in relative.with_suffix("").parts if p]

        pose = "unknown"
        gender = "unknown"
        variant = "base"
        subpose = "default"

        if len(parts) >= 4:
            pose, gender, variant, subpose = parts[:4]
        elif len(parts) == 3:
            pose, variant, subpose = parts
            gender = "unknown"
        elif len(parts) == 2:
            pose, variant = parts
            subpose = "default"
            gender = "unknown"
        elif parts:
            filename = parts[-1]
            tokens = filename.split("_")
            if len(tokens) >= 3:
                pose, variant, subpose = tokens[:3]
            elif len(tokens) == 2:
                pose, variant = tokens
                subpose = "default"
            else:
                pose = tokens[0]

        return pose, gender, variant, subpose

    @staticmethod
    def _choose_best_preview(images):
        priority = [
            "_canny.png",
            "_line_art.png",
            "_openposefull.png",
            "_openpose.png",
            "_bone_structure_full.png",
            "_bone_structure.png",
        ]
        lower_names = {image.name.lower(): image for image in images}
        for suffix in priority:
            for name, image in lower_names.items():
                if suffix in name:
                    return image
        return images[0] if images else None

    def _find_associated_images(self, png_path: Path):
        parent = png_path.parent
        siblings = [p for p in parent.glob("*.png") if p.is_file()]
        display = None
        bone_structure = None
        bone_structure_full = None

        # Prefer exact file if it already matches display candidates.
        candidate = self._choose_best_preview(siblings + [png_path])
        if candidate is not None:
            display = candidate

        for candidate in siblings:
            name = candidate.name.lower()
            if "_bone_structure_full" in name and bone_structure_full is None:
                bone_structure_full = candidate
            elif "_bone_structure.png" in name and bone_structure is None:
                bone_structure = candidate

        if bone_structure is None and bone_structure_full is not None:
            bone_structure = bone_structure_full

        if display is None:
            display = png_path

        return display, bone_structure, bone_structure_full

    def _scan_openpose_folder(self, openpose_dir: Path, pose_attributes):
        # Create one pose per PNG file instead of grouping
        pose_id = 1
        
        for png_path in openpose_dir.rglob("*.png"):
            name = png_path.name.lower()
            if name.startswith("cover") or name.startswith("example") or name.startswith("thumb"):
                continue
            if "pose_thumbnails" in str(png_path.parts).lower():
                continue

            pose, gender, variant, subpose = self._derive_pose_metadata(png_path, openpose_dir)
            
            # Use filename as pose name if metadata extraction failed
            if pose == "unknown":
                pose = self._normalize_token(Path(name).stem)
            
            display_image, bone_structure, bone_structure_full = self._find_associated_images(png_path)
            keypoints = self._extract_keypoints_from_png(png_path) or []
            attributes = pose_attributes.get((pose, variant, subpose), [])
            
            pose_data = {
                "id": pose_id,
                "pose": pose,
                "gender": gender,
                "variant": variant,
                "subpose": subpose,
                "attributes": attributes,
                "keypoints": keypoints,
                "png_path": str(png_path),
                "display_image": str(display_image) if display_image else str(png_path),
                "bone_structure_path": str(bone_structure) if bone_structure else "",
                "bone_structure_full_path": str(bone_structure_full) if bone_structure_full else "",
                "source_file": png_path.name,
            }

            self.poses.append(pose_data)
            self.poses_by_id[pose_id] = pose_data
            pose_id += 1

        print(f"[PoseRegistry] Scanned {len(self.poses)} PNG files")

    def _extract_keypoints_from_png(self, png_path: Path) -> Optional[List[float]]:
        """Extract keypoints from PNG file EXIF or info."""
        try:
            # Try PIL first
            with Image.open(png_path) as img:
                for key, value in img.info.items():
                    if isinstance(value, str):
                        text = value.strip()
                        if text.startswith("{") or text.startswith("["):
                            try:
                                data = json.loads(text)
                                if isinstance(data, dict) and "keypoints" in data:
                                    return data["keypoints"]
                                elif isinstance(data, list):
                                    return data
                            except json.JSONDecodeError:
                                continue

            # Fallback: try exiftool if available
            try:
                exiftool_path = r"C:\EasyDiffusion\exiftool\exiftool.exe"
                if os.path.exists(exiftool_path):
                    result = subprocess.run(
                        [exiftool_path, "-j", str(png_path)],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="ignore"
                    )

                    if result.returncode == 0 and result.stdout:
                        data = json.loads(result.stdout)[0]
                        for key, value in data.items():
                            if isinstance(value, str):
                                text = value.strip()
                                if text.startswith("{") or text.startswith("["):
                                    try:
                                        parsed = json.loads(text)
                                        if isinstance(parsed, dict) and "keypoints" in parsed:
                                            return parsed["keypoints"]
                                        elif isinstance(parsed, list):
                                            return parsed
                                    except json.JSONDecodeError:
                                        continue
            except Exception:
                pass

        except Exception as e:
            print(f"[PoseRegistry] Error extracting keypoints from {png_path}: {e}")

        return None

    def _find_alternate_png_path(self, png_path: Path) -> Optional[Path]:
        """Find a best-fit PNG alternative when the exact file is missing."""
        if png_path.exists():
            return png_path

        parent = png_path.parent
        if not parent.exists():
            return None

        candidates = [
            p for p in parent.glob("*.png")
            if p.name.lower() not in {"cover.png", "example.png"}
        ]
        if not candidates:
            return None

        subpose_name = parent.name.lower()

        def score(candidate: Path) -> int:
            name = candidate.name.lower()
            score = 0
            if subpose_name and subpose_name in name:
                score += 50
            if "_bone_structure_full" in name:
                score += 40
            elif "_bone_structure.png" in name:
                score += 30
            elif "_openposehand" in name:
                score += 25
            elif "_canny" in name:
                score += 20
            elif "_depth" in name:
                score += 15
            elif "_normalhand" in name:
                score += 10
            elif "openposefull" in name:
                score += 5
            if name == png_path.name.lower():
                score += 100
            return score

        candidates.sort(key=score, reverse=True)
        best = candidates[0]
        if score(best) > 0:
            return best
        return None

    def _load_poses(self):
        """Load all poses from PNG database."""
        openpose_dir = self._get_openpose_dir()
        print(f"[PoseRegistry] Loading from: {openpose_dir}")

        if not openpose_dir.exists():
            print(f"[PoseRegistry] WARNING: Directory does not exist: {openpose_dir}")
            return

        # Load pose mapping for attributes
        pose_mapping_path = openpose_dir / "pose_mapping.json"
        pose_attributes = {}
        if pose_mapping_path.exists():
            try:
                with open(pose_mapping_path, "r", encoding="utf-8-sig") as f:
                    pose_mapping = json.load(f)
                    for pose_name, variants in pose_mapping.items():
                        for variant_name, subposes in variants.items():
                            for subpose_name, data in subposes.items():
                                key = (pose_name, variant_name, subpose_name)
                                pose_attributes[key] = data.get("attributes", [])
            except Exception as e:
                print(f"[PoseRegistry] Error loading pose_mapping.json: {e}")

        pose_index_path = openpose_dir / "pose_index.json"
        if pose_index_path.exists():
            try:
                with open(pose_index_path, "r", encoding="utf-8-sig") as f:
                    pose_index = json.load(f)
            except Exception as e:
                print(f"[PoseRegistry] Error loading pose_index.json: {e}")
                return

            pose_id = 1
            for pose_name, genders in pose_index.items():
                for gender_name, variants in genders.items():
                    for variant_name, subposes in variants.items():
                        for subpose_name, png_files in subposes.items():
                            for png_file in png_files:
                                file_path = str(png_file).replace("\\", "/").replace("\r", "").replace("\n", "").strip()
                                png_path = openpose_dir / Path(file_path)

                                if not png_path.exists():
                                    alternate_path = self._find_alternate_png_path(png_path)
                                    if alternate_path is not None and alternate_path.exists():
                                        print(f"[PoseRegistry] Resolved missing file {png_path.relative_to(openpose_dir)} -> {alternate_path.relative_to(openpose_dir)}")
                                        png_path = alternate_path

                                if png_path.exists():
                                    keypoints = self._extract_keypoints_from_png(png_path) or []
                                    display_image, bone_structure, bone_structure_full = self._find_associated_images(png_path)
                                    attr_key = (pose_name, variant_name, subpose_name)
                                    attributes = pose_attributes.get(attr_key, [])

                                    pose_data = {
                                        "id": pose_id,
                                        "pose": pose_name,
                                        "gender": gender_name,
                                        "variant": variant_name,
                                        "subpose": subpose_name,
                                        "attributes": attributes,
                                        "keypoints": keypoints,
                                        "png_path": str(png_path),
                                        "display_image": str(display_image) if display_image else str(png_path),
                                        "bone_structure_path": str(bone_structure) if bone_structure else "",
                                        "bone_structure_full_path": str(bone_structure_full) if bone_structure_full else "",
                                        "source_file": png_path.name,
                                    }

                                    self.poses.append(pose_data)
                                    self.poses_by_id[pose_id] = pose_data
                                    pose_id += 1
                                else:
                                    print(f"[PoseRegistry] PNG file not found: {png_path}")
            print(f"[PoseRegistry] Loaded {len(self.poses)} poses")
            return

        self._scan_openpose_folder(openpose_dir, pose_attributes)
    
    def _build_index(self):
        """Build index for faster searches."""
        for pose_data in self.poses:
            pose = pose_data["pose"]
            variant = pose_data["variant"]
            subpose = pose_data["subpose"]
            
            # Index by (pose, variant, subpose)
            key = (pose, variant, subpose)
            if key not in self.index_by_filter:
                self.index_by_filter[key] = []
            self.index_by_filter[key].append(pose_data["id"])
    
    def get_pose_by_id(self, pose_id: int) -> Optional[Dict]:
        """Get a pose by its ID."""
        return self.poses_by_id.get(pose_id)
    
    def get_keypoints_by_id(self, pose_id: int) -> Optional[List[float]]:
        """Get keypoints for a pose ID."""
        pose = self.get_pose_by_id(pose_id)
        return pose["keypoints"] if pose else None
    
    def search(self, pose: Optional[str] = None, variant: Optional[str] = None, 
               subpose: Optional[str] = None) -> List[int]:
        """
        Search for pose IDs matching criteria.
        
        Args:
            pose: Pose name (e.g., "standing", "lying", "kneeling")
            variant: Variant (e.g., "base", "nsfw")
            subpose: Subpose (e.g., "neutral", "prone", "supine")
        
        Returns:
            List of matching pose IDs
        """
        debug_log(f"[DEBUG] search: Called with pose={pose}, variant={variant}, subpose={subpose}")
        debug_log(f"[DEBUG] search: Registry has {len(self.poses)} total poses")
        
        if pose is None:
            # Return all poses
            debug_log(f"[DEBUG] search: No pose filter, returning all {len(self.poses)} pose IDs")
            return [p["id"] for p in self.poses]
        
        # Get all poses matching the given criteria
        results = []
        for pose_data in self.poses:
            if pose is not None and pose_data["pose"] != pose:
                continue
            if variant is not None and pose_data["variant"] != variant:
                continue
            if subpose is not None and pose_data["subpose"] != subpose:
                continue
            results.append(pose_data["id"])
        
        debug_log(f"[DEBUG] search: Found {len(results)} matching poses")
        return results
    
    def get_available_variants(self, pose: str) -> List[str]:
        """Get available variants for a pose."""
        variants = set()
        for pose_data in self.poses:
            if pose_data["pose"] == pose:
                variants.add(pose_data["variant"])
        return sorted(list(variants))
    
    def get_available_subposes(self, pose: str, variant: str) -> List[str]:
        """Get available subposes for a pose/variant combination."""
        subposes = set()
        for pose_data in self.poses:
            if pose_data["pose"] == pose and pose_data["variant"] == variant:
                subposes.add(pose_data["subpose"])
        return sorted(list(subposes))
    
    def get_all_poses(self) -> List[str]:
        """Get list of all unique pose names."""
        poses = set()
        for pose_data in self.poses:
            poses.add(pose_data["pose"])
        return sorted(list(poses))
    
    def get_info_by_id(self, pose_id: int) -> str:
        """Get human-readable info for a pose ID."""
        pose = self.get_pose_by_id(pose_id)
        if not pose:
            return f"ID {pose_id}: NOT FOUND"
        
        return f"ID {pose_id}: {pose['pose']} / {pose['variant']} / {pose['subpose']}"
    
    def list_all(self) -> List[Dict]:
        """Get all poses with their metadata (excluding keypoints)."""
        debug_log(f"[DEBUG] list_all: Called, registry has {len(self.poses)} poses")
        result = [
            {
                "id": p["id"],
                "pose": p["pose"],
                "gender": p.get("gender"),
                "variant": p["variant"],
                "subpose": p["subpose"],
                "attributes": p.get("attributes", []),
                "source_file": p.get("source_file") or Path(p.get("png_path", "")).name,
            }
            for p in self.poses
        ]
        debug_log(f"[DEBUG] list_all: Returning {len(result)} pose summaries")
        return result


# Global singleton instance
registry = None


def get_registry() -> PoseRegistry:
    """Get the global pose registry instance."""
    global registry
    debug_log(f"[DEBUG] get_registry: Called, current registry is {'None' if registry is None else 'initialized'}")
    if registry is None:
        debug_log("[DEBUG] get_registry: Creating new PoseRegistry instance")
        registry = PoseRegistry()
        debug_log(f"[DEBUG] get_registry: Registry created with {len(registry.poses)} poses")
    else:
        debug_log(f"[DEBUG] get_registry: Returning existing registry with {len(registry.poses)} poses")
    return registry
