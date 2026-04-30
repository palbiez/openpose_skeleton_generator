import json
from .pose_similarity_matcher import PoseMatcher


class PoseMatcherNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coco_keypoints": ("STRING", {}),
                "top_k": ("INT", {"default": 2})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "pose"

    def __init__(self):
        self.matcher = PoseMatcher()

    def run(self, coco_keypoints, top_k):

        try:
            kp = json.loads(coco_keypoints)
        except:
            return ("[]",)

        result = self.matcher.match(kp, top_k=top_k)

        if not result:
            return ("[]",)

        # Skeleton Generator erwartet LISTE
        return (json.dumps(result),)