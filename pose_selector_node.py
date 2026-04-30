import json
from .pose_similarity_matcher import PoseMatcher

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
    except:
        # Fallback if reference data not available
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
                "num_people": ("INT", {"default": 1, "min": 1, "max": 10}),
                "random_seed": ("INT", {"default": -1})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "select"
    CATEGORY = "pose"

    def __init__(self):
        self.matcher = PoseMatcher()

    def select(self, pose, variant, subpose, num_people, random_seed):
        import random
        if random_seed >= 0:
            random.seed(random_seed)

        # Filter reference data by criteria
        candidates = []
        for item in self.matcher.meta:
            if item["pose"] == pose and item["variant"] == variant and item["subpose"] == subpose:
                candidates.append(item)

        if not candidates:
            print(f"[PoseSelector] No matches found for {pose}/{variant}/{subpose}")
            return ("[]",)

        # Select num_people randomly
        selected = random.sample(candidates, min(num_people, len(candidates)))

        # Format as expected by SkeletonFromJSON
        result = []
        for item in selected:
            result.append({
                "score": 0.0,  # Not applicable for manual selection
                "pose": item["pose"],
                "variant": item["variant"],
                "subpose": item["subpose"],
                "attributes": item["attributes"],
                "keypoints": item["keypoints"]
            })

        return (json.dumps(result),)