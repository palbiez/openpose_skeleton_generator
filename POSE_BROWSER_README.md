# Pose Browser Setup & Usage

## Overview

The Pose Browser is a web-based interface to browse, filter, and select poses by their unique IDs. It includes:

1. **Thumbnail Renderer** - Generates skeleton previews for all poses
2. **FastAPI Server** - REST API for pose data and filtering
3. **Web UI** - Interactive gallery with filters

## Setup

### Step 1: Install Dependencies

```bash
pip install fastapi uvicorn cv2 numpy
```

Or if using ComfyUI Python:
```bash
# ComfyUI python path
python -m pip install fastapi uvicorn
```

### Step 2: Generate Thumbnails (One-time)

Run this once to render all poses as PNG images:

```bash
python render_all_poses.py
```

This will:
- Load all poses from the registry
- Render each pose as a 256x256 wireframe skeleton
- Save to `web/pose_thumbnails/pose_<id>.png`
- Takes ~1-2 minutes depending on pose count

**Output:**
```
[RenderPoses] ✅ Complete!
[RenderPoses]   Rendered: 1234
[RenderPoses]   Failed: 0
[RenderPoses]   Path: C:\...\web\pose_thumbnails
```

### Step 3: Start the Server

```bash
python pose_browser_server.py
```

**Output:**
```
Starting PAL Pose Browser on http://localhost:8189
Loaded 1234 poses
INFO:     Uvicorn running on http://127.0.0.1:8189 (Press CTRL+C to quit)
```

### Step 4: Access the Web UI

Open your browser and go to:
```
http://localhost:8189
```

## Features

### Filter Options
- **Pose** - Select pose type (standing, lying, kneeling, etc.)
- **Variant** - Filter by variant (base, nsfw, chair, etc.)
- **Subpose** - Filter by subpose (neutral, prone, supine, etc.)
- **Search** - Search by pose ID

### Pose Cards
Each pose displays:
- Skeleton thumbnail (256x256)
- Pose ID (clickable to copy)
- Pose type
- Variant
- Subpose

### Actions
- **Copy ID** - Copy pose ID to clipboard
- **Apply Filters** - Update gallery with selected filters
- **Reset** - Clear all filters

## REST API Endpoints

### Get All Poses
```
GET /api/poses
Response: { "total": 1234, "poses": [...] }
```

### Filter Poses
```
GET /api/filter?pose=standing&variant=base&subpose=neutral
Response: { "count": 5, "poses": [...] }
```

### Get Filter Options
```
GET /api/options?pose=standing
Response: { 
  "poses": ["standing", "lying", ...],
  "variants": ["base", "nsfw", ...],
  "subposes": ["neutral", "prone", ...]
}
```

### Get Pose Details
```
GET /api/pose/{id}
Response: { "id": 42, "pose": "standing", "variant": "base", ... }
```

### Get Thumbnail
```
GET /thumbnails/{id}
Response: PNG image
```

## Integration with ComfyUI

### In ComfyUI Nodes

After selecting a pose from the web browser, use the ID directly:

```python
# In SkeletonFromJSON node
pose_1_id: 42  # Use the ID from the browser
pose_2_id: 15
```

Or use the **PoseBrowserNode** directly in ComfyUI:

```
PoseBrowserNode:
  - Input: pose dropdown, variant dropdown, subpose dropdown
  - Output: pose_id (INT)
  - Connect to SkeletonFromJSON.pose_1_id
```

## File Structure

```
PAL_open_skeleton_generator/
├── render_all_poses.py         # Thumbnail generator
├── pose_browser_server.py      # FastAPI server
├── pose_registry.py            # Central pose database
├── web/
│   ├── pose_browser/
│   │   └── index.html          # Web UI
│   └── pose_thumbnails/        # Generated PNG files (created by render_all_poses.py)
└── ...
```

## Troubleshooting

### "Thumbnails directory not found"
Make sure you ran `render_all_poses.py` first.

### "FastAPI not installed"
```bash
pip install fastapi uvicorn
```

### "Port 8189 already in use"
Edit `pose_browser_server.py` and change:
```python
uvicorn.run(app, host="127.0.0.1", port=8190)  # Change to 8190
```

### "No poses loaded"
Check that your pose data files are in the correct directory that `pose_registry.py` is looking for.

## Performance

- **Thumbnail generation**: ~1-2 minutes for 1000+ poses (depends on hardware)
- **Web UI**: Instant filtering with client-side search
- **Server**: Can handle hundreds of concurrent requests

## Future Enhancements

- [ ] Batch export of selected poses
- [ ] Custom skeleton rendering options
- [ ] Pose comparison view
- [ ] Tags and favorites
- [ ] Pose upload/creation
