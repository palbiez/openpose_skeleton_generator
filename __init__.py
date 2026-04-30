from .skeleton_generator import SkeletonFromJSON
from .pose_matcher_node import PoseMatcherNode
from .pose_selector_node import PoseSelectorNode
from .pose_from_structure_node import PoseFromStructureNode

NODE_CLASS_MAPPINGS = {
    "SkeletonFromJSON": SkeletonFromJSON,
    "PoseMatcherNode": PoseMatcherNode,
    "PoseSelectorNode": PoseSelectorNode,
    "PoseFromStructureNode": PoseFromStructureNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SkeletonFromJSON": "PAL Skeleton From JSON",
    "PoseMatcherNode": "PAL Pose Matcher",
    "PoseSelectorNode": "PAL Pose Selector",
    "PoseFromStructureNode": "PAL Pose From Structure"
}