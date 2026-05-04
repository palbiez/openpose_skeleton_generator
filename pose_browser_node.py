"""
Pose Browser Node: Search and select poses by criteria.
Provides outputs with Pose IDs and metadata.
"""

import json
from .pose_registry import get_registry


class PoseBrowserNode:
    """Node to search and browse available poses with dropdown filters."""
    
    def __init__(self):
        self.registry = get_registry()
    
    @classmethod
    def INPUT_TYPES(cls):
        registry = get_registry()
        all_poses = registry.get_all_poses()
        
        # Collect all unique variants and subposes
        all_variants = set()
        all_subposes = set()
        
        for pose in all_poses:
            variants = registry.get_available_variants(pose)
            all_variants.update(variants)
            
            for variant in variants:
                subposes = registry.get_available_subposes(pose, variant)
                all_subposes.update(subposes)
        
        all_variants = sorted(list(all_variants))
        all_subposes = sorted(list(all_subposes))
        
        return {
            "required": {
                "pose": (all_poses, {"default": all_poses[0] if all_poses else "standing"}),
                "variant": (all_variants, {"default": all_variants[0] if all_variants else "base"}),
                "subpose": (all_subposes, {"default": all_subposes[0] if all_subposes else "neutral"}),
                "output_format": (["id_only", "id_with_info", "full_json"], {"default": "id_only"}),
            },
            "optional": {}
        }
    
    RETURN_TYPES = ("INT", "STRING", "STRING")
    RETURN_NAMES = ("pose_id", "info", "full_data")
    FUNCTION = "search"
    CATEGORY = "pose"
    
    def search(self, pose, variant, subpose, output_format):
        """Search for a pose matching the criteria."""
        
        # Find exact match
        matching_ids = self.registry.search(pose=pose, variant=variant, subpose=subpose)
        
        if not matching_ids:
            print(f"[PoseBrowser] No match for {pose}/{variant}/{subpose}")
            return (
                -1,
                f"Not found: {pose}/{variant}/{subpose}",
                "{}"
            )
        
        pose_id = matching_ids[0]  # Return first match
        pose_data = self.registry.get_pose_by_id(pose_id)
        
        if output_format == "id_only":
            info = str(pose_id)
        elif output_format == "id_with_info":
            info = self.registry.get_info_by_id(pose_id)
        else:  # full_json
            info = json.dumps(pose_data, default=str, indent=2)
        
        full_data = json.dumps(pose_data, default=str)
        
        print(f"[PoseBrowser] Selected {info}")
        return (pose_id, info, full_data)


class PoseBrowserAdvancedNode:
    """Advanced pose browser with dropdown filters for Pose, Variant, and Subpose."""
    
    def __init__(self):
        self.registry = get_registry()
    
    @classmethod
    def INPUT_TYPES(cls):
        registry = get_registry()
        all_poses = registry.get_all_poses()
        
        # Collect all unique variants and subposes
        all_variants = set()
        all_subposes = set()
        
        for pose in all_poses:
            variants = registry.get_available_variants(pose)
            all_variants.update(variants)
            
            for variant in variants:
                subposes = registry.get_available_subposes(pose, variant)
                all_subposes.update(subposes)
        
        all_variants = sorted(list(all_variants))
        all_subposes = sorted(list(all_subposes))
        
        return {
            "required": {
                "pose": (all_poses, {"default": all_poses[0] if all_poses else "standing"}),
            },
            "optional": {
                "variant": (all_variants, {"default": "base"}) if all_variants else ("STRING", {"default": ""}),
                "subpose": (all_subposes, {"default": "neutral"}) if all_subposes else ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("available_variants", "available_subposes", "matching_ids", "count")
    FUNCTION = "filter_poses"
    CATEGORY = "pose"
    
    def filter_poses(self, pose, variant=None, subpose=None):
        """Filter poses and return available options."""
        
        # Get available variants for this pose
        variants = self.registry.get_available_variants(pose)
        
        # If variant is specified, use it; otherwise get all
        if variant and variant in variants:
            selected_variant = variant
        elif variants:
            selected_variant = variants[0]
        else:
            selected_variant = None
        
        # Get available subposes
        if selected_variant:
            subposes = self.registry.get_available_subposes(pose, selected_variant)
        else:
            subposes = []
        
        # If subpose is specified, use it; otherwise get all
        if subpose and subpose in subposes:
            selected_subpose = subpose
        elif subposes:
            selected_subpose = subposes[0]
        else:
            selected_subpose = None
        
        # Get matching IDs based on all filters
        if selected_variant and selected_subpose:
            matching_ids = self.registry.search(
                pose=pose, 
                variant=selected_variant, 
                subpose=selected_subpose
            )
        elif selected_variant:
            matching_ids = self.registry.search(
                pose=pose, 
                variant=selected_variant
            )
        else:
            matching_ids = self.registry.search(pose=pose)
        
        variants_json = json.dumps(variants)
        subposes_json = json.dumps(subposes)
        ids_json = json.dumps(matching_ids)
        count = len(matching_ids)
        
        print(f"[PoseBrowserAdvanced] Pose: {pose}")
        if variant:
            print(f"[PoseBrowserAdvanced] Variant: {variant}")
        if subpose:
            print(f"[PoseBrowserAdvanced] Subpose: {subpose}")
        print(f"[PoseBrowserAdvanced] Available variants: {variants}")
        print(f"[PoseBrowserAdvanced] Available subposes: {subposes}")
        print(f"[PoseBrowserAdvanced] Matching IDs: {count} results")
        
        return (variants_json, subposes_json, ids_json, count)


class PoseListerNode:
    """List all available poses."""
    
    def __init__(self):
        self.registry = get_registry()
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {}
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("all_poses",)
    FUNCTION = "list_poses"
    CATEGORY = "pose"
    
    def list_poses(self):
        """Return all available poses as JSON."""
        poses = self.registry.list_all()
        result = json.dumps(poses, indent=2, default=str)
        print(f"[PoseLister] Listed {len(poses)} poses")
        return (result,)
