import json
import random
from .pose_similarity_matcher import PoseMatcher
from .pose_similarity_matcher import map_pose_combination

# Cache for options
_cached_options = None

def get_pose_options():
    global _cached_options
    if _cached_options is not None:
        return _cached_options

    try:
        matcher = PoseMatcher()
        poses = set()
        variants = set()
        subposes = set()

        for item in matcher.meta:
            poses.add(item["pose"])
            variants.add(item["variant"])
            subposes.add(item["subpose"])

        _cached_options = {
            "poses": sorted(list(poses)),
            "variants": sorted(list(variants)),
            "subposes": sorted(list(subposes))
        }
    except Exception:
        _cached_options = {
            "poses": ["standing", "sitting", "kneeling", "lying"],
            "variants": ["base", "nsfw"],
            "subposes": ["neutral", "one_knee", "crossed_arms"]
        }

    return _cached_options

class PoseSelectorNode:
    @classmethod
    def INPUT_TYPES(cls):
        options = get_pose_options()
        return {
            "required": {
                "pose": (options["poses"], {"default": "standing"}),
                "variant": (options["variants"], {"default": "base"}),
                "subpose": (options["subposes"], {"default": "neutral"}),
                "seed_control": (["randomize", "fixed", "incremental"], {"default": "randomize"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "select"
    CATEGORY = "pose"

    def __init__(self):
        self.matcher = PoseMatcher()
        self.last_seed = 0

def select(self, pose, variant, subpose, seed_control, seed):
        # Handle seed control like KSampler
        if seed_control == "randomize":
            final_seed = random.randint(0, 0xffffffffffffffff)
        elif seed_control == "fixed":
            final_seed = seed
        elif seed_control == "incremental":
            final_seed = self.last_seed + 1
        else:
            final_seed = random.randint(0, 0xffffffffffffffff)
        
        self.last_seed = final_seed
        random.seed(final_seed)

        # Apply pose mapping for invalid combinations
        mapped_pose, mapped_subpose = map_pose_combination(pose, subpose)
        if mapped_pose != pose or mapped_subpose != subpose:
            pose, subpose = mapped_pose, mapped_subpose

        exact = []
        pose_variant = []
        pose_only = []

        for item in self.matcher.meta:
            if item["pose"] != pose:
                continue

            if item["variant"] == variant and item["subpose"] == subpose:
                exact.append(item)
            if item["variant"] == variant:
                pose_variant.append(item)
            pose_only.append(item)

        if exact:
            candidates = exact
        else:
            print(f"[PoseSelector] No exact match for {pose}/{variant}/{subpose}")
            candidates = []

        if not candidates:
            print(f"[PoseSelector] The selected pose/subpose combination is not available. Please choose a supported subpose for '{pose}'.")
            return ("[]",)

        # Select only one person
        selected = random.choice(candidates)

        result = {
            "score": 0.0,
            "pose": selected["pose"],
            "variant": selected["variant"],
            "subpose": selected["subpose"],
            "attributes": selected.get("attributes", []),
            "keypoints": selected["keypoints"]
        }

        return (json.dumps(result),)
