import json

import numpy as np

try:
    from ..core.openpose_io import (
        PosePerson,
        draw_people,
        extract_people,
        fit_people_to_canvas,
        image_to_tensor,
        make_pose_payload,
    )
    from ..core.pose_registry import get_registry
except ImportError:
    from core.openpose_io import (
        PosePerson,
        draw_people,
        extract_people,
        fit_people_to_canvas,
        image_to_tensor,
        make_pose_payload,
    )
    from core.pose_registry import get_registry


class PoseOpenPoseRendererNode:
    """Render PAL/OpenPose keypoint JSON into a ComfyUI IMAGE tensor."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pose_json": ("STRING", {"multiline": True, "default": ""}),
                "width": ("INT", {"default": 768, "min": 64, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 768, "min": 64, "max": 4096, "step": 8}),
                "layout": (["fit_each_person", "preserve_coordinates"], {"default": "fit_each_person"}),
                "style": (["openpose_color", "white"], {"default": "openpose_color"}),
                "line_width": ("INT", {"default": 4, "min": 1, "max": 24}),
                "point_radius": ("INT", {"default": 4, "min": 1, "max": 24}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "rendered_pose_json")
    FUNCTION = "render"
    CATEGORY = "pose"

    def render(self, pose_json, width, height, layout, style, line_width, point_radius):
        try:
            people = extract_people(pose_json)
        except Exception as exc:
            print(f"[PoseRenderer] Invalid pose JSON: {exc}")
            people = []

        if layout == "fit_each_person":
            people = fit_people_to_canvas(people, width, height)

        canvas = draw_people(
            people,
            width,
            height,
            line_width=line_width,
            point_radius=point_radius,
            style=style,
        )
        rendered_payload = make_pose_payload(
            [
                {
                    **person.metadata,
                    "keypoints": person.keypoints,
                }
                for person in people
            ]
        )
        return (image_to_tensor(canvas), json.dumps(rendered_payload, ensure_ascii=False))


class SkeletonFromJSON:
    """
    Legacy ID-based renderer kept for existing ComfyUI workflows.

    New workflows should use PAL OpenPose Renderer and feed it pose_json from
    PAL Pose Selector, PAL Pose From Structure, or PAL Pose By ID.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 768, "min": 64, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 768, "min": 64, "max": 4096, "step": 8}),
                "num_people": ("INT", {"default": 1, "min": 1, "max": 10}),
            },
            "optional": {},
            "hidden": {},
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "pose"

    def generate(self, width, height, num_people, update=None, **kwargs):
        registry = get_registry()
        people = []

        for index in range(1, num_people + 1):
            pose_id = kwargs.get(f"pose_{index}_id")
            if not isinstance(pose_id, int):
                continue

            pose_data = registry.get_pose_by_id(pose_id) or {}
            keypoints = registry.get_keypoints_by_id(pose_id)
            if not keypoints:
                print(f"[SkeletonFromJSON] Pose ID {pose_id} has no keypoints")
                continue

            metadata = {
                "id": pose_id,
                "pose": pose_data.get("pose"),
                "variant": pose_data.get("variant"),
                "subpose": pose_data.get("subpose"),
                "attributes": pose_data.get("attributes", []),
            }
            people.append(PosePerson(keypoints=keypoints, metadata=metadata))

        if not people:
            return (image_to_tensor(np.zeros((height, width, 3), dtype=np.uint8)),)

        people = fit_people_to_canvas(people, width, height)
        canvas = draw_people(people, width, height, style="openpose_color")
        return (image_to_tensor(canvas),)
