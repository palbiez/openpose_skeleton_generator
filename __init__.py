from .skeleton_generator import SkeletonFromJSON
from .pose_matcher_node import PoseMatcherNode

NODE_CLASS_MAPPINGS = {
    "SkeletonFromJSON": SkeletonFromJSON,
    "PoseMatcherNode": PoseMatcherNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SkeletonFromJSON": "Skeleton From JSON",
    "PoseMatcherNode": "Pose Matcher"
}