"""
Pose Registry: Central database for all poses with unique IDs.
Loads all poses from reference directory and provides search API.
"""

import json
import numpy as np
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple


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
            return
        
        self._initialized = True
        self.poses: List[Dict] = []
        self.poses_by_id: Dict[int, Dict] = {}
        self.index_by_filter: Dict[Tuple, List[int]] = {}
        
        self._load_poses()
        self._build_index()
    
    def _load_poses(self):
        """Load all poses from reference directory."""
        # Try to get ComfyUI input directory
        try:
            import folder_paths
            ref_dir = Path(folder_paths.get_input_directory()) / "openpose"
        except (ImportError, AttributeError):
            # Fallback path
            ref_dir = Path(os.path.dirname(__file__)) / ".." / ".." / "input" / "openpose"
            ref_dir = ref_dir.resolve()
        
        print(f"[PoseRegistry] Loading from: {ref_dir}")
        
        if not ref_dir.exists():
            print(f"[PoseRegistry] WARNING: Directory does not exist: {ref_dir}")
            return
        
        pose_id = 1
        for json_file in sorted(ref_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for item in data:
                    pose_data = {
                        "id": pose_id,
                        "pose": item.get("pose", "unknown"),
                        "variant": item.get("variant", "base"),
                        "subpose": item.get("subpose", "default"),
                        "attributes": item.get("attributes", []),
                        "keypoints": item.get("keypoints", []),
                        "source_file": json_file.name,
                    }
                    
                    self.poses.append(pose_data)
                    self.poses_by_id[pose_id] = pose_data
                    pose_id += 1
            
            except Exception as e:
                print(f"[PoseRegistry] Error loading {json_file}: {e}")
        
        print(f"[PoseRegistry] Loaded {len(self.poses)} poses")
    
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
        if pose is None:
            # Return all poses
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
        return [
            {
                "id": p["id"],
                "pose": p["pose"],
                "variant": p["variant"],
                "subpose": p["subpose"],
                "attributes": p["attributes"],
                "source_file": p["source_file"],
            }
            for p in self.poses
        ]


# Global singleton instance
registry = PoseRegistry()


def get_registry() -> PoseRegistry:
    """Get the global pose registry instance."""
    return registry
