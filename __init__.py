import os
import socket
import subprocess
import sys
from pathlib import Path

from .nodes.ollama_pose_parser_node import OllamaPoseParserNode
from .nodes.pose_browser_node import PoseBrowserLauncherNode, PoseLoadByIdNode, PoseStructureByIdNode
from .nodes.pose_from_structure_node import PoseFromStructureNode
from .nodes.pose_matcher_node import PoseMatcherNode
from .nodes.pose_renderer_node import PoseOpenPoseRendererNode, SkeletonFromJSON
from .nodes.pose_selector_node import PoseSelectorNode

# Import debug_log from pose_registry
try:
    from .core.pose_registry import debug_log
except ImportError:
    def debug_log(message: str):
        print(message)

NODE_CLASS_MAPPINGS = {
    "OllamaPoseParserNode": OllamaPoseParserNode,
    "PoseOpenPoseRendererNode": PoseOpenPoseRendererNode,
    "SkeletonFromJSON": SkeletonFromJSON,
    "PoseMatcherNode": PoseMatcherNode,
    "PoseSelectorNode": PoseSelectorNode,
    "PoseFromStructureNode": PoseFromStructureNode,
    "PoseLoadByIdNode": PoseLoadByIdNode,
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
    debug_log("[DEBUG] _launch_browser_server: Called")
    host = os.getenv("OPENPOSE_BROWSER_HOST", "0.0.0.0")
    port = int(os.getenv("OPENPOSE_BROWSER_PORT", "8189"))
    debug_log(f"[DEBUG] _launch_browser_server: Checking port {host}:{port}")
    if _is_port_open(host, port):
        debug_log(f"[DEBUG] _launch_browser_server: Port {port} already open, skipping")
        return

    server_script = Path(__file__).parent / "pose_browser_server.py"
    debug_log(f"[DEBUG] _launch_browser_server: Server script path: {server_script}")
    if not server_script.exists():
        debug_log("[DEBUG] _launch_browser_server: Server script not found, skipping")
        return

    # Set environment variable for the models path
    try:
        debug_log("[DEBUG] _launch_browser_server: Trying to import folder_paths")
        import folder_paths
        models_dir = folder_paths.get_models_dir()
        env = os.environ.copy()
        env["OPENPOSE_MODELS_PATH"] = str(Path(models_dir) / "openpose")
        debug_log(f"[DEBUG] _launch_browser_server: Set OPENPOSE_MODELS_PATH to {env['OPENPOSE_MODELS_PATH']}")
    except (ImportError, AttributeError) as e:
        debug_log(f"[DEBUG] _launch_browser_server: folder_paths import failed: {e}")
        env = os.environ.copy()

    cmd = [sys.executable, str(server_script)]
    debug_log(f"[DEBUG] _launch_browser_server: Starting command: {cmd}")
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    try:
        subprocess.Popen(
            cmd,
            cwd=str(server_script.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            env=env,
            creationflags=creationflags,
        )
        debug_log(f"[DEBUG] _launch_browser_server: Server process started at http://{host}:{port}")
    except Exception as exc:
        debug_log(f"[DEBUG] _launch_browser_server: Server start failed: {exc}")


if os.getenv("OPENPOSE_BROWSER_AUTOSTART", "1").lower() not in {"0", "false", "no"}:
    try:
        _launch_browser_server()
    except Exception as exc:
        debug_log(f"[PAL OpenPose Browser] auto-start initialization failed: {exc}")

WEB_DIRECTORY = "web"

NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaPoseParserNode": "PAL Ollama Pose Parser",
    "PoseOpenPoseRendererNode": "PAL OpenPose Renderer",
    "SkeletonFromJSON": "PAL Skeleton From IDs (Legacy)",
    "PoseMatcherNode": "PAL Pose Matcher",
    "PoseSelectorNode": "PAL Pose Selector",
    "PoseFromStructureNode": "PAL Pose From Structure",
    "PoseLoadByIdNode": "PAL Pose By ID",
    "PoseStructureByIdNode": "PAL Pose Structure by ID",
    "PoseBrowserLauncherNode": "PAL OpenPose Browser Launcher",
}
