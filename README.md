Comfyui Plugin for Open Pose Skeleton generation

This plugin provides node-based pose selection and structured pose interpretation for ComfyUI.

Required setup:
- Place your OpenPose reference JSON files into the ComfyUI input/openpose folder.
- The matcher loads all `.json` files from that directory.

Included nodes:
- `PAL Pose Selector`: choose `pose`, `variant`, `subpose` and `num_people`, then output ready-to-render skeleton JSON.
- `PAL Pose From Structure`: convert structured LLM/UI pose descriptions into matched real pose keypoints.
- `PAL Skeleton From JSON`: render a skeleton image from pose JSON.

Current supported pose/subpose combinations:
- kneeling: `both_knees`, `one_knee`
- lying: `back`, `prone`, `side`
- sitting: `chair`, `floor`
- standing: `neutral`

Note: the loaded reference dataset currently contains only the `base` variant. If `variant` shows only `base`, das ist korrekt für die aktuellen Daten.

Example `Pose From Structure` input:

{
  "people": [
    {"pose": "kneeling", "subpose": "one_knee", "attributes": ["torso_forward"]},
    {"pose": "standing", "subpose": "neutral", "attributes": ["arms_crossed"]}
  ]
}

Example output format for `PAL Skeleton From JSON`:

[
  {
    "score": 0.0,
    "pose": "kneeling",
    "variant": "base",
    "subpose": "one_knee",
    "attributes": ["torso_forward"],
    "keypoints": [ ... ]
  }
]
