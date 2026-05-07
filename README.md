# PAL OpenPose Skeleton Generator for ComfyUI

PAL OpenPose Skeleton Generator is a ComfyUI custom node package for selecting, matching, and rendering real OpenPose skeletons from a local pose library.

The intended pipeline is:

```text
User prompt
-> Ollama structure extraction
-> normalized pose intent
-> real pose selection from the OpenPose database
-> OpenPose skeleton render
-> ControlNet / Flux image generation
```

The project avoids freeform keypoint generation. It uses real pose data as the geometric source of truth so multi-person scenes stay more stable.

## Project Layout

```text
core/                 Shared registry, matching, OpenPose parsing, rendering helpers
nodes/                ComfyUI node implementations
scripts/              CLI maintenance tools
web/pose_browser/     Local pose browser UI
docs/                 Architecture, schemas, node reference
tests/smoke/          Lightweight contract tests
```

Root-level modules such as `pose_registry.py` and `build_pose_cache.py` are compatibility wrappers for older imports and commands.

## Installation

1. Place this folder in `ComfyUI/custom_nodes/`.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Put pose files under:

```text
ComfyUI/models/openpose/
```

The scanner supports nested OpenPose folders such as:

```text
openpose/kneeling/F/nsfw/all_fours/all_fours_030_depth.png
openpose/kneeling/F/nsfw/all_fours/all_fours_030_bone_structure.png
openpose/kneeling/F/nsfw/all_fours/all_fours_030_openpose.json
```

Preview images prefer `*_depth.png`. If no depth image exists, `*_bone_structure.png` is used.

## Cache

Build or refresh the registry cache:

```bash
python scripts/build_pose_cache.py
```

The legacy command still works:

```bash
python build_pose_cache.py
```

Clean the cache:

```bash
python scripts/build_pose_cache.py --clean
```

## Pose Attributes

Assign automatic pose attributes from keypoint geometry:

```bash
python scripts/auto_pose_attributes.py --root C:\Users\firew\Documents\ComfyUI\models\openpose --write
```

Attributes are written into OpenPose JSON metadata as `meta.auto_attributes` and `meta.attributes`.

## Pose Browser

The browser starts automatically with ComfyUI and is available at:

```text
http://127.0.0.1:8189
```

Environment variables:

```bash
OPENPOSE_MODELS_PATH=C:\Users\firew\Documents\ComfyUI\models\openpose
OPENPOSE_BROWSER_HOST=0.0.0.0
OPENPOSE_BROWSER_PORT=8189
OPENPOSE_BROWSER_AUTOSTART=1
```

## Main Nodes

- `PAL Ollama Pose Parser`: validates and normalizes Ollama JSON output.
- `PAL Pose From Structure`: selects real database poses from normalized structure JSON.
- `PAL Pose Selector`: manually selects a pose by ID, filters, and attributes.
- `PAL Pose By ID`: loads pose JSON, image paths, and metadata from a browser pose ID.
- `PAL OpenPose Renderer`: renders PAL/OpenPose keypoint JSON to a ComfyUI `IMAGE`.
- `PAL Pose Matcher`: finds similar database poses for incoming keypoints.
- `PAL OpenPose Browser Launcher`: manually starts the browser server.

See [docs/NODE_REFERENCE.md](docs/NODE_REFERENCE.md) for input and output contracts.

## Development Checks

Run lightweight smoke checks:

```bash
python scripts/smoke_check.py
```

Or with pytest:

```bash
python -m pytest tests/smoke
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Ollama Schema](docs/OLLAMA_SCHEMA.md)
- [Node Reference](docs/NODE_REFERENCE.md)
