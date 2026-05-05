# PAL OpenPose Skeleton Generator for ComfyUI

This ComfyUI custom node package provides comprehensive pose selection, matching, and skeleton generation capabilities using OpenPose data. It includes an integrated web browser for pose exploration and selection.

## Installation

1. Install the package dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Place the custom node folder in your ComfyUI `custom_nodes` directory.

3. **Optional but recommended**: Pre-build the pose registry cache for faster startup:
   ```bash
   cd ComfyUI/custom_nodes/PAL_open_skeleton_generator
   python build_pose_cache.py
   ```
   This will scan all your pose files and create a cache file for instant loading.

4. Restart ComfyUI. The pose browser will automatically start on port 8189.

## Cache Management

The pose registry automatically caches scanned poses for faster loading. If you add new pose files:

- The cache updates automatically when ComfyUI starts (if pose files are newer than cache)
- Or manually rebuild the cache: `python build_pose_cache.py`
- To clear the cache: `python build_pose_cache.py --clean`

## OpenPose Data Setup

### Where to Place Pose Files

Place your OpenPose JSON and PNG files in the ComfyUI `models/openpose` directory.

The plugin supports the original nested EasyDiffusion / webui structure and scans recursively through subfolders.

Supported layout examples:

```
ComfyUI/
├── models/
│   └── openpose/
│       └── kneeling/
│           └── F/
│               └── nsfw/
│                   └── all_fours/
│                       └── all_fours_001/
│                           ├── all_fours_001.png
│                           ├── all_fours_001_keypoints.json
│                           ├── all_fours_001_bone_structure.png
│                           └── all_fours_001_bone_structure_full.png
```

or flatter nested examples like:

```
ComfyUI/
├── models/
│   └── openpose/
│       └── kneeling/
│           └── F/
│               └── nsfw/
│                   └── all_fours_001.png
│                   └── all_fours_001_keypoints.json
```

The plugin automatically scans this directory on startup and builds an index of available poses.

If the browser server is started from a separate process and no poses appear, the server may not see ComfyUI's `folder_paths` module. In that case, set:

```bash
export OPENPOSE_MODELS_PATH="C:/Users/firew/Documents/ComfyUI/models/openpose"
```

or point it to your OpenPose root in the Stable Diffusion webui install.

If you change the folder structure or want to force a fresh scan, delete `models/openpose/pose_index.json` and restart ComfyUI.

### File Naming Convention

When nested folders are used, the scanner derives pose metadata from the path segments:

- `{pose}` from the first folder below `openpose`
- `{gender}` from the second folder
- `{variant}` from the third folder
- `{subpose}` from the fourth folder

If your files are not fully nested, the scanner also falls back to tokenized filenames like `{pose}_{gender}_{variant}_{subpose}_{id}.png`.

Examples:
- `kneeling_female_base_one_knee_001.png`
- `kneeling/F/nsfw/all_fours/all_fours_001.png`
- `kneeling/F/nsfw/all_fours/all_fours_001/all_fours_001.png`
- `standing_male_base_neutral_042_keypoints.json`

### Automatic Scanning

The pose registry automatically scans the `models/openpose` directory when ComfyUI loads the custom nodes. No manual scanning is required.

## Using the Pose Browser

The pose browser automatically starts when ComfyUI loads and is accessible at:

- **Local access**: http://localhost:8189
- **Network access**: http://YOUR_COMFYUI_IP:8189 (e.g., http://192.168.130.23:8189)

### Browser Features

- **Browse poses**: Filter by pose type, gender, variant, and subpose
- **Search**: Text search across pose metadata
- **Pagination**: Navigate through large pose collections
- **Image preview**: View pose thumbnails and bone structure images
- **Pose selection**: Click poses to get their ID for use in ComfyUI nodes

### Environment Variables

You can customize the browser host and port:

```bash
export OPENPOSE_BROWSER_HOST=0.0.0.0  # Default: 0.0.0.0 (all interfaces)
export OPENPOSE_BROWSER_PORT=8189     # Default: 8189
```

## ComfyUI Nodes

### PAL Pose Selector

Select poses by category and generate skeleton JSON.

**Inputs:**
- `pose`: Pose type (kneeling, lying, sitting, standing)
- `variant`: Pose variant (base)
- `subpose`: Specific pose variation (both_knees, one_knee, back, prone, side, chair, floor, neutral)
- `num_people`: Number of people in the pose (1-4)

**Outputs:**
- `skeleton_json`: Ready-to-render pose keypoints in JSON format

### PAL Pose Matcher

Match poses based on similarity to reference keypoints.

**Inputs:**
- `reference_keypoints`: JSON string with reference pose keypoints
- `max_results`: Maximum number of matches to return (1-10)

**Outputs:**
- `matched_poses`: JSON array of matched poses with similarity scores

### PAL Pose From Structure

Convert structured pose descriptions into matched keypoints.

**Inputs:**
- `pose_structure`: JSON describing pose requirements
- `max_results`: Maximum matches to return (1-5)

**Outputs:**
- `matched_poses`: Array of matched pose JSON objects

Example input structure:
```json
{
  "people": [
    {"pose": "kneeling", "subpose": "one_knee", "attributes": ["torso_forward"]},
    {"pose": "standing", "subpose": "neutral", "attributes": ["arms_crossed"]}
  ]
}
```

### PAL Pose Structure by ID

Resolve a pose ID from the browser into file paths and metadata.

**Inputs:**
- `pose_id`: Numeric ID from the pose browser
- `preferred_image`: Image type preference (auto, bone_structure, bone_structure_full)

**Outputs:**
- `selected_path`: Path to the selected image file
- `full_path`: Path to bone structure full image
- `pose_info`: JSON metadata about the pose

### PAL Skeleton From JSON

Render skeleton images from pose keypoints.

**Inputs:**
- `skeleton_json`: JSON array of pose keypoints
- `width`: Image width (default: 512)
- `height`: Image height (default: 512)
- `line_width`: Skeleton line thickness (default: 2)

**Outputs:**
- `image`: Rendered skeleton image

### PAL OpenPose Browser Launcher

Manually launch the pose browser (normally starts automatically).

**Outputs:**
- `status`: Launch status message

## Supported Pose Categories

### Kneeling
- `both_knees`: Both knees on ground
- `one_knee`: One knee up

### Lying
- `back`: Lying on back
- `prone`: Lying face down
- `side`: Lying on side

### Sitting
- `chair`: Sitting on chair
- `floor`: Sitting on floor

### Standing
- `neutral`: Standing upright

## Example Workflows

### Basic Pose Selection
1. Use **PAL Pose Selector** to choose pose categories
2. Connect to **PAL Skeleton From JSON** to render the skeleton

### Browser-Based Selection
1. Open the pose browser at http://localhost:8189
2. Browse and find a pose, note its ID
3. Use **PAL Pose Structure by ID** with the ID to get file paths
4. Use the paths in your ComfyUI workflow

### Pose Matching
1. Provide reference keypoints as JSON
2. Use **PAL Pose Matcher** to find similar poses
3. Select from matched results

## Troubleshooting

### Browser Not Accessible
- Check if port 8189 is available: `netstat -an | findstr :8189`
- Verify ComfyUI started without errors
- Check firewall settings for port 8189

### No Poses Found
- Ensure OpenPose files are in `ComfyUI/models/openpose`
- Check file naming follows the convention
- Restart ComfyUI to trigger re-scanning

### Import Errors
- Install dependencies: `pip install -r requirements.txt`
- Ensure you're using Python 3.8+

## Requirements

- Python 3.8+
- ComfyUI
- OpenPose JSON and PNG files in `models/openpose` directory

## License

This project is open source. See individual file headers for licensing information.
