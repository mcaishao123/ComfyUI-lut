# ComfyUI-lut

ComfyUI custom nodes for loading and applying Adobe Lightroom `.lrtemplate` / `.xmp` presets and `.cube` 3D LUTs as image filters.

## Features

This extension provides 8 nodes under the **image/filter** category:

### Lightroom Presets (.lrtemplate / .xmp)
- **LRTemplate Loader** 📷 — Load `.lrtemplate` / `.xmp` preset files from the presets folder
- **LRTemplate Apply** 🎨 — Apply loaded presets to images with strength control
- **LRTemplate Manual** 🎛️ — Apply Lightroom-style adjustments with sliders (no preset file needed)
- **LRTemplate Search Loader** 🔍 — Search for a preset file recursively by name

### 3D LUTs (.cube)
- **CUBE LUT Loader** 🎬 — Load `.cube` LUT files from the presets folder
- **CUBE LUT Apply** 🎞️ — Apply a CUBE LUT to images with strength control (trilinear interpolation)
- **CUBE LUT Search Loader** 🔎 — Search for a `.cube` file recursively by name

### Utilities
- **Preset Catalog Generator** 📊 — Batch apply presets to an image and export an Excel visual catalog (supports `.lrtemplate`, `.xmp`, `.cube`).

## Supported Adjustments (Lightroom)

| Category | Parameters |
|---|---|
| **Tone** | Exposure, Contrast, Highlights, Shadows, Whites, Blacks |
| **Presence** | Clarity, Vibrance, Saturation |
| **White Balance** | Temperature, Tint |
| **Tone Curve** | Composite RGB, Per-channel (R/G/B) |
| **HSL** | Hue, Saturation, Luminance per color (Red, Orange, Yellow, Green, Aqua, Blue, Purple, Magenta) |
| **Split Toning** | Highlight hue/saturation, Shadow hue/saturation |
| **Effects** | Post-crop vignette, Film grain |

## Usage

1. Place your `.lrtemplate`, `.xmp`, or `.cube` files in the `ComfyUI-lut/presets/` folder (or use Search Loaders for any directory).
2. Restart ComfyUI or refresh the browser.
3. Add nodes from **image/filter** category.

### Workflow Example

```text
Load Image → LRTemplate Apply ← LRTemplate Loader
                   ↓
             Preview Image
```

## Preset Catalog Generation

The **Preset Catalog Generator** node allows you to select a large folder of presets and generate an `.xlsx` Excel file containing thumbnails of how each preset affects your input image.

> **Note**: For massive preset folders (e.g., 100,000+ files), the catalog node will automatically save its progress every 50 presets to prevent data loss.

You can also run the catalog generator entirely headless via command line:

```bash
cd custom_nodes\ComfyUI-lut
..\..\python_embeded\python.exe generate_preset_catalog.py "D:\your_image.jpg" "D:\preset_folder" "D:\catalog_output.xlsx"
```
