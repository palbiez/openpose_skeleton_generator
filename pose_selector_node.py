import json
import random
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
        if random_seed >= 0:
            random.seed(random_seed)

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
        elif pose_variant:
            print(f"[PoseSelector] Fallback to pose+variant for {pose}/{variant}/{subpose}")
            candidates = pose_variant
        else:
            if pose_only:
                print(f"[PoseSelector] Fallback to pose only for {pose}/{variant}/{subpose}")
                candidates = pose_only
            else:
                print(f"[PoseSelector] No matches found for {pose}/{variant}/{subpose}")
                return ("[]",)

        if len(candidates) > num_people:
            selected = random.sample(candidates, num_people)
        else:
            selected = list(candidates)

        result = []
        for item in selected:
            result.append({
                "score": 0.0,
                "pose": item["pose"],
                "variant": item["variant"],
                "subpose": item["subpose"],
                "attributes": item.get("attributes", []),
                "keypoints": item["keypoints"]
            })

        return (json.dumps(result),)
