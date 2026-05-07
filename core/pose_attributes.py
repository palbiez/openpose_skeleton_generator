#!/usr/bin/env python3
"""
Assign pose attributes from OpenPose keypoints.

The script scans *_openpose.json files, computes conservative geometry-based
attributes, and stores them in:

    meta.auto_attributes
    meta.attributes

Use --write to modify files. Without --write it only reports what would change.
"""

import argparse
import json
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_ROOT = Path(r"C:\Users\firew\Documents\ComfyUI\models\openpose")

OPENPOSE_18 = {
    "nose": 0,
    "neck": 1,
    "r_shoulder": 2,
    "r_elbow": 3,
    "r_wrist": 4,
    "l_shoulder": 5,
    "l_elbow": 6,
    "l_wrist": 7,
    "r_hip": 8,
    "r_knee": 9,
    "r_ankle": 10,
    "l_hip": 11,
    "l_knee": 12,
    "l_ankle": 13,
    "r_eye": 14,
    "l_eye": 15,
    "r_ear": 16,
    "l_ear": 17,
}

COCO_17 = {
    "nose": 0,
    "l_eye": 1,
    "r_eye": 2,
    "l_ear": 3,
    "r_ear": 4,
    "l_shoulder": 5,
    "r_shoulder": 6,
    "l_elbow": 7,
    "r_elbow": 8,
    "l_wrist": 9,
    "r_wrist": 10,
    "l_hip": 11,
    "r_hip": 12,
    "l_knee": 13,
    "r_knee": 14,
    "l_ankle": 15,
    "r_ankle": 16,
}

ATTRIBUTE_ORDER = [
    "hands_up",
    "hand_up",
    "left_hand_up",
    "right_hand_up",
    "hand_near_face",
    "left_hand_near_face",
    "right_hand_near_face",
    "thinking",
    "hand_on_hip",
    "left_hand_on_hip",
    "right_hand_on_hip",
    "arms_crossed",
    "arms_out",
    "legs_crossed",
    "legs_open",
    "legs_closed",
    "one_knee_high",
    "both_knees_level",
    "torso_lean",
    "torso_lean_left",
    "torso_lean_right",
    "head_down",
    "head_tilted",
    "salute",
    "waving",
    "squatting",
    "all_fours",
]


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    c: float


def normalize_attribute(value) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def unique_attributes(values: Iterable[str]) -> List[str]:
    seen = set()
    attrs = []
    for value in values:
        attr = normalize_attribute(value)
        if attr and attr not in seen:
            attrs.append(attr)
            seen.add(attr)
    return sorted(attrs, key=lambda item: ATTRIBUTE_ORDER.index(item) if item in ATTRIBUTE_ORDER else 999)


def visible(point: Optional[Point], min_confidence: float) -> bool:
    return point is not None and point.c > min_confidence


def distance(a: Optional[Point], b: Optional[Point]) -> Optional[float]:
    if a is None or b is None:
        return None
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def midpoint(points: Sequence[Optional[Point]], min_confidence: float) -> Optional[Point]:
    valid = [point for point in points if visible(point, min_confidence)]
    if not valid:
        return None
    return Point(
        sum(point.x for point in valid) / len(valid),
        sum(point.y for point in valid) / len(valid),
        min(point.c for point in valid),
    )


def split_keypoints(values) -> List[Point]:
    if not isinstance(values, list):
        return []
    points = []
    for index in range(0, len(values) - 2, 3):
        try:
            points.append(Point(float(values[index]), float(values[index + 1]), float(values[index + 2])))
        except Exception:
            continue
    return points


def choose_layout(point_count: int, requested: str) -> Dict[str, int]:
    if requested == "openpose18":
        return OPENPOSE_18
    if requested == "coco17":
        return COCO_17
    return COCO_17 if point_count == 17 else OPENPOSE_18


def named_points(raw_keypoints, layout_name: str) -> Dict[str, Point]:
    points = split_keypoints(raw_keypoints)
    layout = choose_layout(len(points), layout_name)
    named = {}
    for name, index in layout.items():
        if index < len(points):
            named[name] = points[index]

    if "neck" not in named:
        neck = midpoint([named.get("l_shoulder"), named.get("r_shoulder")], 0.0)
        if neck is not None:
            named["neck"] = neck

    return named


def body_scale(points: Dict[str, Point], min_confidence: float) -> float:
    valid_points = [point for point in points.values() if visible(point, min_confidence)]
    if not valid_points:
        return 1.0
    min_x = min(point.x for point in valid_points)
    max_x = max(point.x for point in valid_points)
    min_y = min(point.y for point in valid_points)
    max_y = max(point.y for point in valid_points)
    shoulder_width = distance(points.get("l_shoulder"), points.get("r_shoulder")) or 0.0
    hip_width = distance(points.get("l_hip"), points.get("r_hip")) or 0.0
    return max(max_x - min_x, max_y - min_y, shoulder_width * 3.0, hip_width * 4.0, 1.0)


def add_hand_attributes(attrs: List[str], points: Dict[str, Point], scale: float, min_confidence: float) -> None:
    shoulders = midpoint([points.get("l_shoulder"), points.get("r_shoulder")], min_confidence)
    neck = points.get("neck")
    nose = points.get("nose")
    face = midpoint(
        [points.get("nose"), points.get("l_eye"), points.get("r_eye"), points.get("l_ear"), points.get("r_ear")],
        min_confidence,
    ) or nose or neck
    hips = midpoint([points.get("l_hip"), points.get("r_hip")], min_confidence)
    torso_vertical_ok = (
        visible(shoulders, min_confidence)
        and visible(hips, min_confidence)
        and abs(shoulders.y - hips.y) > 0.18 * scale
    )

    raised_sides = []
    near_face_sides = []
    on_hip_sides = []

    for side in ("left", "right"):
        prefix = "l" if side == "left" else "r"
        wrist = points.get(f"{prefix}_wrist")
        shoulder = points.get(f"{prefix}_shoulder") or shoulders
        hip = points.get(f"{prefix}_hip") or hips

        if visible(wrist, min_confidence) and visible(shoulder, min_confidence):
            if wrist.y < shoulder.y - 0.12 * scale:
                attrs.append(f"{side}_hand_up")
                raised_sides.append(side)

        if visible(wrist, min_confidence) and visible(face, min_confidence):
            if (distance(wrist, face) or 999999) < 0.18 * scale:
                attrs.append(f"{side}_hand_near_face")
                near_face_sides.append(side)

        if visible(wrist, min_confidence) and visible(hip, min_confidence):
            torso_y_ok = True
            if visible(shoulder, min_confidence):
                top_y = min(shoulder.y, hip.y) - 0.08 * scale
                bottom_y = max(shoulder.y, hip.y) + 0.12 * scale
                torso_y_ok = top_y <= wrist.y <= bottom_y
            if torso_vertical_ok and torso_y_ok and (distance(wrist, hip) or 999999) < 0.17 * scale:
                attrs.append(f"{side}_hand_on_hip")
                on_hip_sides.append(side)

    if len(raised_sides) == 2:
        attrs.append("hands_up")
    elif raised_sides:
        attrs.append("hand_up")

    if near_face_sides:
        attrs.append("hand_near_face")

    if on_hip_sides:
        attrs.append("hand_on_hip")

    left_wrist = points.get("l_wrist")
    right_wrist = points.get("r_wrist")
    left_shoulder = points.get("l_shoulder")
    right_shoulder = points.get("r_shoulder")
    left_elbow = points.get("l_elbow")
    right_elbow = points.get("r_elbow")

    if visible(left_wrist, min_confidence) and visible(right_wrist, min_confidence):
        torso = midpoint([shoulders, hips], min_confidence)
        wrists_near_torso = torso is not None and all(
            (distance(wrist, torso) or 999999) < 0.35 * scale for wrist in (left_wrist, right_wrist)
        )
        shoulder_order = None
        wrist_order = None
        if visible(left_shoulder, min_confidence) and visible(right_shoulder, min_confidence):
            shoulder_order = left_shoulder.x - right_shoulder.x
            wrist_order = left_wrist.x - right_wrist.x
        crossed_order = shoulder_order is not None and shoulder_order * wrist_order < 0
        crossed_targets = (
            visible(right_elbow, min_confidence)
            and (distance(left_wrist, right_elbow) or 999999) < 0.22 * scale
        ) or (
            visible(left_elbow, min_confidence)
            and (distance(right_wrist, left_elbow) or 999999) < 0.22 * scale
        )
        if wrists_near_torso and (crossed_order or crossed_targets):
            attrs.append("arms_crossed")

    for side in ("l", "r"):
        wrist = points.get(f"{side}_wrist")
        shoulder = points.get(f"{side}_shoulder")
        if visible(wrist, min_confidence) and visible(shoulder, min_confidence):
            if abs(wrist.x - shoulder.x) > 0.35 * scale and abs(wrist.y - shoulder.y) < 0.35 * scale:
                attrs.append("arms_out")


def add_leg_attributes(
    attrs: List[str],
    points: Dict[str, Point],
    scale: float,
    min_confidence: float,
    include_neutral: bool,
) -> None:
    left_hip = points.get("l_hip")
    right_hip = points.get("r_hip")
    left_knee = points.get("l_knee")
    right_knee = points.get("r_knee")
    left_ankle = points.get("l_ankle")
    right_ankle = points.get("r_ankle")

    hip_width = distance(left_hip, right_hip) or (0.10 * scale)
    knee_dist = distance(left_knee, right_knee)
    ankle_dist = distance(left_ankle, right_ankle)
    leg_width = max(knee_dist or 0.0, ankle_dist or 0.0)

    if leg_width > max(hip_width * 1.75, 0.28 * scale):
        attrs.append("legs_open")
    elif include_neutral and knee_dist is not None and knee_dist < max(hip_width * 1.15, 0.16 * scale):
        attrs.append("legs_closed")

    if (
        visible(left_hip, min_confidence)
        and visible(right_hip, min_confidence)
        and visible(left_ankle, min_confidence)
        and visible(right_ankle, min_confidence)
    ):
        hip_order = left_hip.x - right_hip.x
        ankle_order = left_ankle.x - right_ankle.x
        if hip_order * ankle_order < 0 and (ankle_dist or 999999) < max(hip_width * 1.8, 0.28 * scale):
            attrs.append("legs_crossed")

    if visible(left_knee, min_confidence) and visible(right_knee, min_confidence):
        knee_y_diff = abs(left_knee.y - right_knee.y)
        if knee_y_diff > 0.16 * scale:
            attrs.append("one_knee_high")
        elif include_neutral:
            attrs.append("both_knees_level")


def add_torso_head_attributes(attrs: List[str], points: Dict[str, Point], scale: float, min_confidence: float) -> None:
    shoulders = midpoint([points.get("l_shoulder"), points.get("r_shoulder")], min_confidence)
    hips = midpoint([points.get("l_hip"), points.get("r_hip")], min_confidence)
    neck = points.get("neck") or shoulders
    nose = points.get("nose")

    if visible(shoulders, min_confidence) and visible(hips, min_confidence):
        dx = shoulders.x - hips.x
        if abs(dx) > 0.12 * scale:
            attrs.append("torso_lean")
            attrs.append("torso_lean_right" if dx > 0 else "torso_lean_left")

    if visible(nose, min_confidence) and visible(neck, min_confidence):
        if nose.y > neck.y - 0.08 * scale:
            attrs.append("head_down")
        if abs(nose.x - neck.x) > 0.10 * scale:
            attrs.append("head_tilted")


def name_hint_attributes(json_path: Path) -> List[str]:
    tokens = [json_path.stem.lower()]
    tokens.extend(part.lower() for part in json_path.parent.parts[-4:])
    text = " ".join(tokens).replace("-", "_")

    attrs = []
    if "crossed_legs" in text or "legs_crossed" in text or "cross_legs" in text:
        attrs.append("legs_crossed")
    if "legs_open" in text or "spread_legs" in text or "split_leg" in text or "split_legs" in text:
        attrs.append("legs_open")
    if "thinking" in text or "thinker" in text:
        attrs.extend(["thinking", "hand_near_face"])
    if "hand_on_hip" in text or "hands_on_hip" in text:
        attrs.append("hand_on_hip")
    if "crossed_arms" in text or "arms_crossed" in text:
        attrs.append("arms_crossed")
    if "hand_up" in text or "hands_up" in text:
        attrs.append("hand_up")
    if "salute" in text:
        attrs.extend(["salute", "hand_up"])
    if "waving" in text or "greeting" in text:
        attrs.extend(["waving", "hand_up"])
    if "squatting" in text:
        attrs.append("squatting")
    if "all_fours" in text:
        attrs.append("all_fours")
    return unique_attributes(attrs)


def extract_auto_attributes(
    raw_keypoints,
    layout: str,
    min_confidence: float,
    include_neutral: bool = False,
) -> List[str]:
    points = named_points(raw_keypoints, layout)
    scale = body_scale(points, min_confidence)
    attrs: List[str] = []

    add_hand_attributes(attrs, points, scale, min_confidence)
    add_leg_attributes(attrs, points, scale, min_confidence, include_neutral)
    add_torso_head_attributes(attrs, points, scale, min_confidence)

    return unique_attributes(attrs)


def first_person_keypoints(data) -> Optional[List[float]]:
    if not isinstance(data, dict):
        return None
    people = data.get("people")
    if isinstance(people, list) and people and isinstance(people[0], dict):
        value = people[0].get("pose_keypoints_2d") or people[0].get("keypoints")
        if isinstance(value, list):
            return value
    for key in ("pose_keypoints_2d", "keypoints"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return None


def existing_manual_attributes(meta: dict) -> List[str]:
    if "manual_attributes" in meta:
        raw = meta.get("manual_attributes")
    elif "auto_attributes" not in meta:
        raw = meta.get("attributes")
    else:
        raw = []

    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        raw = [raw]
    return unique_attributes(str(item) for item in raw)


def update_json_file(
    json_path: Path,
    layout: str,
    min_confidence: float,
    include_neutral: bool,
    use_name_hints: bool,
    write: bool,
) -> Tuple[bool, List[str], str]:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, [], f"read_error: {exc}"

    keypoints = first_person_keypoints(data)
    if not keypoints:
        return False, [], "no_pose_keypoints"

    auto_attrs = extract_auto_attributes(keypoints, layout, min_confidence, include_neutral)
    if use_name_hints:
        hint_attrs = name_hint_attributes(json_path)
        auto_attrs = unique_attributes(auto_attrs + hint_attrs)
        if "all_fours" in hint_attrs:
            auto_attrs = [
                attr for attr in auto_attrs
                if attr not in {"hand_on_hip", "left_hand_on_hip", "right_hand_on_hip", "legs_crossed"}
            ]
    if not isinstance(data, dict):
        return False, auto_attrs, "unsupported_json_shape"

    meta = data.setdefault("meta", {})
    if not isinstance(meta, dict):
        meta = {}
        data["meta"] = meta

    manual_attrs = existing_manual_attributes(meta)
    merged_attrs = unique_attributes(manual_attrs + auto_attrs)
    changed = meta.get("auto_attributes") != auto_attrs or meta.get("attributes") != merged_attrs

    if write and changed:
        if manual_attrs:
            meta["manual_attributes"] = manual_attrs
        meta["auto_attributes"] = auto_attrs
        meta["attributes"] = merged_attrs
        json_path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")

    return changed, auto_attrs, "ok"


def resolve_roots(values: Optional[List[str]]) -> List[Path]:
    if values:
        return [Path(value) for value in values]
    env_path = os.getenv("OPENPOSE_MODELS_PATH")
    if env_path:
        return [Path(env_path)]
    return [DEFAULT_ROOT]


def scan_root(
    root: Path,
    layout: str,
    min_confidence: float,
    include_neutral: bool,
    use_name_hints: bool,
    write: bool,
) -> dict:
    if not root.exists():
        return {"root": str(root), "error": "root does not exist"}

    summary = {
        "root": str(root),
        "files": 0,
        "changed": 0,
        "skipped": Counter(),
        "attributes": Counter(),
        "examples": [],
    }

    for json_path in sorted(root.rglob("*_openpose.json")):
        summary["files"] += 1
        changed, attributes, status = update_json_file(
            json_path,
            layout,
            min_confidence,
            include_neutral,
            use_name_hints,
            write,
        )
        if status != "ok":
            summary["skipped"][status] += 1
            continue
        if changed:
            summary["changed"] += 1
            if len(summary["examples"]) < 12:
                summary["examples"].append((str(json_path.relative_to(root)), attributes))
        for attribute in attributes:
            summary["attributes"][attribute] += 1

    return summary


def print_summary(summary: dict, write: bool) -> None:
    print(f"\nROOT: {summary['root']}")
    if "error" in summary:
        print(f"ERROR: {summary['error']}")
        return

    mode = "written" if write else "would change"
    print(f"Files scanned: {summary['files']}")
    print(f"Files {mode}: {summary['changed']}")

    if summary["skipped"]:
        print("Skipped:")
        for reason, count in sorted(summary["skipped"].items()):
            print(f"  {reason}: {count}")

    print("Top attributes:")
    for attribute, count in summary["attributes"].most_common(20):
        print(f"  {attribute}: {count}")

    if summary["examples"]:
        print("Examples:")
        for rel_path, attributes in summary["examples"]:
            print(f"  {rel_path}: {', '.join(attributes) if attributes else '-'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Assign OpenPose pose attributes from keypoints.")
    parser.add_argument("--root", action="append", help="OpenPose root directory. Can be passed multiple times.")
    parser.add_argument("--write", action="store_true", help="Write attributes into *_openpose.json files.")
    parser.add_argument(
        "--layout",
        choices=["auto", "openpose18", "coco17"],
        default="auto",
        help="Keypoint layout. Auto uses COCO17 only for 17-point arrays, otherwise OpenPose18.",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.05,
        help="Minimum point confidence for geometry rules.",
    )
    parser.add_argument(
        "--include-neutral",
        action="store_true",
        help="Also write broad neutral labels like legs_closed and both_knees_level.",
    )
    parser.add_argument(
        "--no-name-hints",
        action="store_true",
        help="Disable supplemental attributes inferred from file and folder names.",
    )
    args = parser.parse_args()

    roots = resolve_roots(args.root)
    for root in roots:
        summary = scan_root(
            root,
            args.layout,
            args.min_confidence,
            args.include_neutral,
            not args.no_name_hints,
            args.write,
        )
        print_summary(summary, args.write)

    if not args.write:
        print("\nDry run only. Re-run with --write to update JSON files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
