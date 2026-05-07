import json
import subprocess
import sys
from pathlib import Path
from .pose_registry import get_registry


class PoseStructureByIdNode:
    """Resolve a pose ID into structure image paths and metadata."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pose_id": ("INT", {"default": 1, "min": 1}),
                "preferred_image": (["auto", "bone_structure", "bone_structure_full"], {"default": "auto"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("selected_path", "full_path", "pose_info")
    FUNCTION = "resolve"
    CATEGORY = "pose"

    def __init__(self):
        self.registry = get_registry()

    def resolve(self, pose_id, preferred_image):
        pose_data = self.registry.get_pose_by_id(pose_id)
        if not pose_data:
            info = json.dumps({"error": f"Pose ID {pose_id} not found"}, indent=2)
            return ("", "", info)

        bone_structure = pose_data.get("bone_structure_path") or ""
        bone_structure_full = pose_data.get("bone_structure_full_path") or ""
        display_image = pose_data.get("display_image") or pose_data.get("png_path") or ""

        if preferred_image == "bone_structure_full" and bone_structure_full:
            selected = bone_structure_full
        elif preferred_image == "bone_structure" and bone_structure:
            selected = bone_structure
        else:
            selected = bone_structure or bone_structure_full or display_image

        info_payload = {
            "id": pose_data.get("id"),
            "pose": pose_data.get("pose"),
            "variant": pose_data.get("variant"),
            "subpose": pose_data.get("subpose"),
            "attributes": pose_data.get("attributes", []),
            "source_file": pose_data.get("source_file"),
            "display_image": pose_data.get("display_image"),
            "bone_structure": bone_structure,
            "bone_structure_full": bone_structure_full,
        }

        return (str(selected), str(bone_structure_full), json.dumps(info_payload, indent=2, default=str))


class PoseBrowserLauncherNode:
    """Launch the OpenPose browser from inside ComfyUI."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "start_server"
    CATEGORY = "pose"

    def start_server(self):
        server_script = Path(__file__).parent / "pose_browser_server.py"
        if not server_script.exists():
            message = "Pose browser server script not found."
            print(f"[PoseBrowserLauncher] {message}")
            return (message,)

        cmd = [sys.executable, str(server_script)]
        try:
            subprocess.Popen(
                cmd,
                cwd=str(server_script.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
            message = "OpenPose Browser launched on http://127.0.0.1:8189"
            print(f"[PoseBrowserLauncher] {message}")
            return (message,)
        except Exception as e:
            message = f"Failed to launch OpenPose Browser: {e}"
            print(f"[PoseBrowserLauncher] {message}")
            return (message,)
