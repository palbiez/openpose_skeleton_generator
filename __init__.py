from .skeleton_generator import SkeletonFromJSON
from .pose_matcher_node import PoseMatcherNode
from .pose_selector_node import PoseSelectorNode
from .pose_from_structure_node import PoseFromStructureNode
from .pose_browser_node import PoseStructureByIdNode, PoseBrowserLauncherNode

NODE_CLASS_MAPPINGS = {
    "SkeletonFromJSON": SkeletonFromJSON,
    "PoseMatcherNode": PoseMatcherNode,
    "PoseSelectorNode": PoseSelectorNode,
    "PoseFromStructureNode": PoseFromStructureNode,
    "PoseStructureByIdNode": PoseStructureByIdNode,
    "PoseBrowserLauncherNode": PoseBrowserLauncherNode,
}

WEB_DIRECTORY = "web"

NODE_DISPLAY_NAME_MAPPINGS = {
    "SkeletonFromJSON": "PAL Skeleton From JSON",
    "PoseMatcherNode": "PAL Pose Matcher",
    "PoseSelectorNode": "PAL Pose Selector",
    "PoseFromStructureNode": "PAL Pose From Structure",
    "PoseStructureByIdNode": "PAL Pose Structure by ID",
    "PoseBrowserLauncherNode": "PAL OpenPose Browser Launcher",
}