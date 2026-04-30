import json
import random
from .pose_similarity_matcher import PoseMatcher

class PoseFromStructureNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "structure_json": ("STRING", {}),
                "num_people": ("INT", {"default": 2, "min": 1, "max": 10}),
                "random_seed": ("INT", {"default": -1})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "convert"
    CATEGORY = "pose"

    def __init__(self):
        self.matcher = PoseMatcher()

    def convert(self, structure_json, num_people, random_seed):
        if random_seed >= 0:
            random.seed(random_seed)

        try:
            structure = json.loads(structure_json)
        except:
            print("[PoseFromStructure] Invalid JSON input")
            return ("[]",)

        if "people" not in structure:
            print("[PoseFromStructure] No 'people' key in structure")
            return ("[]",)

        people_specs = structure["people"]
        if not isinstance(people_specs, list):
            print("[PoseFromStructure] 'people' should be a list")
            return ("[]",)

        result = []
        for spec in people_specs[:num_people]:  # Limit to num_people
            pose = spec.get("pose", "")
            subpose = spec.get("subpose", "")
            attributes = spec.get("attributes", [])

            # Find matching poses in reference data
            candidates = []
            for item in self.matcher.meta:
                if item["pose"] == pose and item["subpose"] == subpose:
                    # Check if attributes match (subset check)
                    if all(attr in item["attributes"] for attr in attributes):
                        candidates.append(item)

            if candidates:
                # Select random candidate
                selected = random.choice(candidates)
                result.append({
                    "score": 0.0,
                    "pose": selected["pose"],
                    "variant": selected["variant"],
                    "subpose": selected["subpose"],
                    "attributes": selected["attributes"],
                    "keypoints": selected["keypoints"]
                })
            else:
                print(f"[PoseFromStructure] No match found for pose='{pose}', subpose='{subpose}', attributes={attributes}")

        return (json.dumps(result),)