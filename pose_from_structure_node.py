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
                "seed_control": (["randomize", "fixed", "incremental"], {"default": "randomize"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "convert"
    CATEGORY = "pose"

    def __init__(self):
        self.matcher = PoseMatcher()
        self.last_seed = 0

    @staticmethod
    def normalize_token(value):
        if value is None:
            return ""
        if not isinstance(value, str):
            value = str(value)
        return value.strip().lower().replace(" ", "_").replace("-", "_")

    @staticmethod
    def normalize_attributes(attributes):
        if attributes is None:
            return []
        if isinstance(attributes, str):
            return [attr.strip().lower().replace(" ", "_").replace("-", "_") for attr in attributes.split(",") if attr.strip()]
        if isinstance(attributes, list):
            return [str(attr).strip().lower().replace(" ", "_").replace("-", "_") for attr in attributes if str(attr).strip()]
        return [str(attributes).strip().lower().replace(" ", "_").replace("-", "_")]

    def find_candidates(self, pose, subpose, variant, attributes):
        exact = []
        pose_variant = []
        pose_subpose = []
        pose_only = []

        for item in self.matcher.meta:
            if item["pose"] != pose:
                continue

            item_attributes = [str(attr).strip().lower().replace(" ", "_").replace("-", "_") for attr in item.get("attributes", [])]
            variant_match = not variant or item["variant"] == variant
            subpose_match = not subpose or item["subpose"] == subpose
            attributes_match = all(attr in item_attributes for attr in attributes)

            if variant_match and subpose_match and attributes_match:
                exact.append(item)
            if variant_match and item["subpose"] == subpose and attributes_match:
                pose_subpose.append(item)
            if subpose_match and item["variant"] == variant and attributes_match:
                pose_variant.append(item)
            pose_only.append(item)

        if variant and subpose:
            return exact
        if variant:
            return exact or pose_variant
        if subpose:
            return exact or pose_subpose
        return exact or pose_only

    @staticmethod
    def parse_structure(structure_json):
        data = json.loads(structure_json)
        if isinstance(data, dict) and "people" in data:
            return data["people"]
        if isinstance(data, list):
            return data
        raise ValueError("Input must be a JSON object with a 'people' list or a list of person specs.")

    def convert(self, structure_json, num_people, seed_control, seed):
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

        try:
            people_specs = self.parse_structure(structure_json)
        except Exception as exc:
            print(f"[PoseFromStructure] Invalid structure JSON: {exc}")
            return ("[]",)

        if not isinstance(people_specs, list):
            print("[PoseFromStructure] 'people' should be a list of person specs")
            return ("[]",)

        result = []
        for spec in people_specs[:num_people]:
            if not isinstance(spec, dict):
                print(f"[PoseFromStructure] Skipping invalid person spec: {spec}")
                continue

            pose = self.normalize_token(spec.get("pose", ""))
            subpose = self.normalize_token(spec.get("subpose", ""))
            variant = self.normalize_token(spec.get("variant", ""))
            attributes = self.normalize_attributes(spec.get("attributes", []))

            if not pose:
                print("[PoseFromStructure] Skipping person spec without 'pose'")
                continue

            candidates = self.find_candidates(pose, subpose, variant, attributes)
            if not candidates:
                print(f"[PoseFromStructure] No match found for pose='{pose}', subpose='{subpose}', variant='{variant}', attributes={attributes}")
                continue

            selected = random.choice(candidates)
            result.append({
                "score": 0.0,
                "pose": selected["pose"],
                "variant": selected["variant"],
                "subpose": selected["subpose"],
                "attributes": selected.get("attributes", []),
                "keypoints": selected["keypoints"]
            })

        if not result:
            return ("[]",)

        return (json.dumps(result),)
