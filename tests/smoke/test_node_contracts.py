import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.openpose_io import extract_people
from nodes.ollama_pose_parser_node import OllamaPoseParserNode
from nodes.pose_renderer_node import PoseOpenPoseRendererNode


def test_ollama_parser_contract():
    node = OllamaPoseParserNode()
    structure_json, report_json = node.parse(
        '{"people":[{"role":"subject","pose":"seated","attributes":["crossed_legs"]}]}',
        "base",
        4,
    )
    structure = json.loads(structure_json)
    report = json.loads(report_json)

    assert structure["schema"] == "pal_pose_intent/v1"
    assert structure["people"][0]["pose"] == "sitting"
    assert structure["people"][0]["attributes"] == ["legs_crossed"]
    assert report["output_people"] == 1


def test_renderer_accepts_pal_payload():
    keypoints = []
    for index in range(18):
        keypoints.extend([100 + index * 2, 100 + index * 3, 1.0])

    payload = {
        "schema": "pal_pose_selection/v1",
        "people": [{"id": 1, "pose": "standing", "keypoints": keypoints}],
    }
    people = extract_people(payload)
    assert len(people) == 1

    renderer = PoseOpenPoseRendererNode()
    image, rendered_json = renderer.render(json.dumps(payload), 256, 256, "fit_each_person", "white", 2, 2)
    assert tuple(image.shape) == (1, 256, 256, 3)
    assert json.loads(rendered_json)["people"][0]["id"] == 1

