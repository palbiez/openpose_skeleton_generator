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

    @staticmethod
    def normalize_attributes(attributes):
        if attributes is None:
            return []
        if isinstance(attributes, str):
            return [attr.strip() for attr in attributes.split(",") if attr.strip()]
        if isinstance(attributes, list):
            return [str(attr).strip() for attr in attributes if str(attr).strip()]
        return [str(attributes).strip()]

    def find_candidates(self, pose, subpose, variant, attributes):
        exact = []
        pose_subpose = []
        pose_only = []

        for item in self.matcher.meta:
            if item["pose"] != pose:
                continue

            item_attributes = item.get("attributes", [])
            variant_match = not variant or item["variant"] == variant
            subpose_match = not subpose or item["subpose"] == subpose
            attributes_match = all(attr in item_attributes for attr in attributes)

            if variant_match and subpose_match and attributes_match:
                exact.append(item)
            if variant_match and subpose_match:
                pose_subpose.append(item)
            pose_only.append(item)

        if exact:
            return exact
        if pose_subpose:
            return pose_subpose
        return pose_only

    @staticmethod
    def parse_structure(structure_json):
        data = json.loads(structure_json)
        if isinstance(data, dict) and "people" in data:
            return data["people"]
        if isinstance(data, list):
            return data
        raise ValueError("Input must be a JSON object with a 'people' list or a list of person specs.")

    def convert(self, structure_json, num_people, random_seed):
        if random_seed >= 0:
            random.seed(random_seed)

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

            pose = str(spec.get("pose", "")).strip()
            subpose = str(spec.get("subpose", "")).strip()
            variant = str(spec.get("variant", "")).strip()
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
