"""OpenPose JSON parsing, keypoint conversion, and rendering helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np
import torch


OPENPOSE_18 = {
    "nose": 0,
    "neck": 1,
    "right_shoulder": 2,
    "right_elbow": 3,
    "right_wrist": 4,
    "left_shoulder": 5,
    "left_elbow": 6,
    "left_wrist": 7,
    "right_hip": 8,
    "right_knee": 9,
    "right_ankle": 10,
    "left_hip": 11,
    "left_knee": 12,
    "left_ankle": 13,
    "right_eye": 14,
    "left_eye": 15,
    "right_ear": 16,
    "left_ear": 17,
}

COCO_17 = {
    "nose": 0,
    "left_eye": 1,
    "right_eye": 2,
    "left_ear": 3,
    "right_ear": 4,
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_elbow": 7,
    "right_elbow": 8,
    "left_wrist": 9,
    "right_wrist": 10,
    "left_hip": 11,
    "right_hip": 12,
    "left_knee": 13,
    "right_knee": 14,
    "left_ankle": 15,
    "right_ankle": 16,
}

CANONICAL_17_NAMES = [
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]

OPENPOSE_18_LIMBS = [
    (1, 2),
    (2, 3),
    (3, 4),
    (1, 5),
    (5, 6),
    (6, 7),
    (1, 8),
    (8, 9),
    (9, 10),
    (1, 11),
    (11, 12),
    (12, 13),
    (1, 0),
    (0, 14),
    (14, 16),
    (0, 15),
    (15, 17),
]

COCO_17_LIMBS = [
    (5, 7),
    (7, 9),
    (6, 8),
    (8, 10),
    (5, 6),
    (5, 11),
    (6, 12),
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (0, 1),
    (1, 3),
    (0, 2),
    (2, 4),
]

OPENPOSE_COLORS = [
    (255, 0, 0),
    (255, 85, 0),
    (255, 170, 0),
    (255, 255, 0),
    (170, 255, 0),
    (85, 255, 0),
    (0, 255, 0),
    (0, 255, 85),
    (0, 255, 170),
    (0, 255, 255),
    (0, 170, 255),
    (0, 85, 255),
    (0, 0, 255),
    (85, 0, 255),
    (170, 0, 255),
    (255, 0, 255),
    (255, 0, 170),
    (255, 0, 85),
]


@dataclass
class PosePerson:
    """Normalized person pose payload."""

    keypoints: List[float]
    metadata: Dict[str, Any]


def normalize_token(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def normalize_attributes(attributes: Any) -> List[str]:
    if attributes is None:
        return []
    if isinstance(attributes, str):
        raw_values = attributes.replace(";", ",").split(",")
    elif isinstance(attributes, Iterable) and not isinstance(attributes, (dict, bytes)):
        raw_values = list(attributes)
    else:
        raw_values = [attributes]

    normalized = []
    seen = set()
    for value in raw_values:
        token = normalize_token(value)
        if token and token not in seen:
            normalized.append(token)
            seen.add(token)
    return normalized


def parse_json_payload(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        return json.loads(text)
    return value


def extract_first_json(text: str) -> str:
    """Return the first JSON object or array embedded in arbitrary text."""
    stripped = text.strip()
    if not stripped:
        raise ValueError("Empty input")
    if stripped[0] in "[{":
        return stripped

    decoder = json.JSONDecoder()
    candidates = [idx for idx, char in enumerate(stripped) if char in "[{"]
    for idx in candidates:
        try:
            _, end = decoder.raw_decode(stripped[idx:])
        except json.JSONDecodeError:
            continue
        return stripped[idx : idx + end]
    raise ValueError("No JSON object or array found in text")


def coerce_keypoints(value: Any) -> Optional[List[float]]:
    """Extract one flat keypoint list from common OpenPose-like payloads."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    if isinstance(value, list):
        if all(isinstance(item, (int, float)) for item in value):
            return [float(item) for item in value]
        if value and isinstance(value[0], dict):
            return coerce_keypoints(value[0])
    if not isinstance(value, dict):
        return None

    for key in ("keypoints", "pose_keypoints_2d"):
        keypoints = value.get(key)
        if isinstance(keypoints, list):
            return [float(item) for item in keypoints if isinstance(item, (int, float))]

    people = value.get("people")
    if isinstance(people, list) and people:
        return coerce_keypoints(people[0])

    return None


def extract_people(payload: Any) -> List[PosePerson]:
    """Extract all people from a PAL, OpenPose, or match-result JSON payload."""
    data = parse_json_payload(payload)
    people: List[PosePerson] = []

    if isinstance(data, dict):
        raw_people = data.get("people")
        if isinstance(raw_people, list):
            for item in raw_people:
                keypoints = coerce_keypoints(item)
                if keypoints:
                    metadata = dict(item) if isinstance(item, dict) else {}
                    metadata.pop("keypoints", None)
                    metadata.pop("pose_keypoints_2d", None)
                    people.append(PosePerson(keypoints=keypoints, metadata=metadata))
            return people

        keypoints = coerce_keypoints(data)
        if keypoints:
            metadata = dict(data)
            metadata.pop("keypoints", None)
            metadata.pop("pose_keypoints_2d", None)
            return [PosePerson(keypoints=keypoints, metadata=metadata)]

    if isinstance(data, list):
        keypoints = coerce_keypoints(data)
        if keypoints and all(isinstance(item, (int, float)) for item in data):
            return [PosePerson(keypoints=keypoints, metadata={})]
        for item in data:
            keypoints = coerce_keypoints(item)
            if keypoints:
                metadata = dict(item) if isinstance(item, dict) else {}
                metadata.pop("keypoints", None)
                metadata.pop("pose_keypoints_2d", None)
                people.append(PosePerson(keypoints=keypoints, metadata=metadata))

    return people


def detect_layout(keypoints: Sequence[float]) -> str:
    point_count = len(keypoints) // 3
    if point_count >= 18:
        return "openpose18"
    if point_count == 17:
        return "coco17"
    return "unknown"


def keypoints_to_canonical17(keypoints: Sequence[float]) -> Optional[List[float]]:
    """Convert OpenPose18 or COCO17 keypoints to a shared 17-point order."""
    layout = detect_layout(keypoints)
    if layout == "coco17":
        return [float(value) for value in keypoints[: 17 * 3]]
    if layout != "openpose18":
        return None

    source = np.array(keypoints[: 18 * 3], dtype=np.float32).reshape(18, 3)
    canonical = np.zeros((17, 3), dtype=np.float32)
    for target_idx, name in enumerate(CANONICAL_17_NAMES):
        source_idx = OPENPOSE_18.get(name)
        if source_idx is not None:
            canonical[target_idx] = source[source_idx]
    return canonical.flatten().astype(float).tolist()


def _valid_bounds(points: np.ndarray, min_confidence: float) -> Optional[Tuple[float, float, float, float]]:
    valid = points[:, 2] > min_confidence
    if valid.sum() < 3:
        return None
    xy = points[valid, :2]
    min_x, min_y = xy.min(axis=0)
    max_x, max_y = xy.max(axis=0)
    if max_x - min_x < 1 or max_y - min_y < 1:
        return None
    return float(min_x), float(min_y), float(max_x), float(max_y)


def fit_people_to_canvas(
    people: Sequence[PosePerson],
    width: int,
    height: int,
    padding: int = 48,
    min_confidence: float = 0.05,
) -> List[PosePerson]:
    """Scale each person into an evenly spaced horizontal slot."""
    if not people:
        return []

    fitted: List[PosePerson] = []
    slot_width = width / len(people)
    usable_padding = max(8, min(padding, int(slot_width * 0.2), int(height * 0.2)))

    for index, person in enumerate(people):
        points = np.array(person.keypoints, dtype=np.float32).reshape(-1, 3)
        bounds = _valid_bounds(points, min_confidence)
        if bounds is None:
            fitted.append(person)
            continue

        min_x, min_y, max_x, max_y = bounds
        source_w = max_x - min_x
        source_h = max_y - min_y
        slot_left = slot_width * index
        slot_right = slot_width * (index + 1)
        target_w = max(1.0, slot_right - slot_left - usable_padding * 2)
        target_h = max(1.0, height - usable_padding * 2)
        scale = min(target_w / source_w, target_h / source_h)

        target_center_x = slot_left + slot_width / 2
        target_center_y = height / 2
        source_center_x = (min_x + max_x) / 2
        source_center_y = (min_y + max_y) / 2

        adjusted = points.copy()
        valid = adjusted[:, 2] > min_confidence
        adjusted[valid, 0] = (adjusted[valid, 0] - source_center_x) * scale + target_center_x
        adjusted[valid, 1] = (adjusted[valid, 1] - source_center_y) * scale + target_center_y
        adjusted[valid, 0] = np.clip(adjusted[valid, 0], 0, width - 1)
        adjusted[valid, 1] = np.clip(adjusted[valid, 1], 0, height - 1)

        fitted.append(PosePerson(keypoints=adjusted.flatten().astype(float).tolist(), metadata=person.metadata))

    return fitted


def draw_people(
    people: Sequence[PosePerson],
    width: int,
    height: int,
    line_width: int = 4,
    point_radius: int = 4,
    style: str = "openpose_color",
    min_confidence: float = 0.05,
) -> np.ndarray:
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    white = (255, 255, 255)

    for person in people:
        points = np.array(person.keypoints, dtype=np.float32).reshape(-1, 3)
        layout = detect_layout(person.keypoints)
        limbs = OPENPOSE_18_LIMBS if layout == "openpose18" else COCO_17_LIMBS

        for limb_index, (a, b) in enumerate(limbs):
            if a >= len(points) or b >= len(points):
                continue
            if points[a, 2] <= min_confidence or points[b, 2] <= min_confidence:
                continue
            color = OPENPOSE_COLORS[limb_index % len(OPENPOSE_COLORS)] if style == "openpose_color" else white
            start = (int(round(points[a, 0])), int(round(points[a, 1])))
            end = (int(round(points[b, 0])), int(round(points[b, 1])))
            cv2.line(canvas, start, end, color, max(1, int(line_width)), lineType=cv2.LINE_AA)

        for point_index, (x, y, confidence) in enumerate(points):
            if confidence <= min_confidence:
                continue
            color = OPENPOSE_COLORS[point_index % len(OPENPOSE_COLORS)] if style == "openpose_color" else white
            cv2.circle(
                canvas,
                (int(round(x)), int(round(y))),
                max(1, int(point_radius)),
                color,
                -1,
                lineType=cv2.LINE_AA,
            )

    return canvas


def image_to_tensor(image: np.ndarray) -> torch.Tensor:
    return torch.from_numpy(image).float().div(255.0).unsqueeze(0)


def make_pose_payload(people: Sequence[Dict[str, Any]], seed: Optional[int] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "schema": "pal_pose_selection/v1",
        "people": list(people),
    }
    if seed is not None:
        payload["seed"] = int(seed)
    return payload

