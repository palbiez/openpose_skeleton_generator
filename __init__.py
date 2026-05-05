import os
import socket
import subprocess
import sys
from pathlib import Path

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


def _is_port_open(host: str, port: int) -> bool:
    test_host = "127.0.0.1" if host == "0.0.0.0" else host
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            return sock.connect_ex((test_host, port)) == 0
    except Exception:
        return False


def _launch_browser_server() -> None:
    host = os.getenv("OPENPOSE_BROWSER_HOST", "0.0.0.0")
    port = int(os.getenv("OPENPOSE_BROWSER_PORT", "8189"))
    if _is_port_open(host, port):
        return

    server_script = Path(__file__).parent / "pose_browser_server.py"
    if not server_script.exists():
        print("[PAL OpenPose Browser] auto-start skipped: server script not found")
        return

    # Set environment variable for the models path
    try:
        import folder_paths
        models_dir = folder_paths.get_models_dir()
        env = os.environ.copy()
        env["OPENPOSE_MODELS_PATH"] = str(Path(models_dir) / "openpose")
    except (ImportError, AttributeError):
        env = os.environ.copy()

    cmd = [sys.executable, str(server_script)]
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    try:
        subprocess.Popen(
            cmd,
            cwd=str(server_script.parent),
            stdout=None,  # Show output for debugging
            stderr=None,  # Show errors for debugging
            stdin=subprocess.DEVNULL,
            env=env,
            creationflags=creationflags,
        )
        print(f"[PAL OpenPose Browser] auto-starting server at http://{host}:{port}")
    except Exception as exc:
        print(f"[PAL OpenPose Browser] auto-start failed: {exc}")


try:
    _launch_browser_server()
except Exception as exc:
    print(f"[PAL OpenPose Browser] auto-start initialization failed: {exc}")

WEB_DIRECTORY = "web"

NODE_DISPLAY_NAME_MAPPINGS = {
    "SkeletonFromJSON": "PAL Skeleton From JSON",
    "PoseMatcherNode": "PAL Pose Matcher",
    "PoseSelectorNode": "PAL Pose Selector",
    "PoseFromStructureNode": "PAL Pose From Structure",
    "PoseStructureByIdNode": "PAL Pose Structure by ID",
    "PoseBrowserLauncherNode": "PAL OpenPose Browser Launcher",
}