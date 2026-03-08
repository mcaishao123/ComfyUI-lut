# ComfyUI-lut

English | [简体中文](README.md)

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

## The Ultimate Weapon: Extracting Proprietary Presets (HALD CUBE Method)

Due to Adobe's closed-source proprietary color engines (especially concerning "Camera Calibration" and complex local masks), pure Python nodes cannot mathematically replicate 100% of advanced Lightroom presets perfectly. 

For these "stubborn presets", we provide an ultimate extraction weapon: the **`hald_tool.py`** script. It forces any proprietary PS/LR color-grading to be baked into a mathematically perfect, 100% accurate `.cube` file.

**Usage Instructions:**
1. Run `python hald_tool.py` in your terminal. It will generate a colorful grid image named `neutral_lut_64.png`.
2. Open `neutral_lut_64.png` in Photoshop.
3. Select the image layer, go to the top menu: **Filter -> Camera Raw Filter...**
4. Apply your complex LR/XMP preset, and click OK.
5. Save the modified, color-graded image back to the folder exactly as: `modified_lut_64.png`.
6. Run `python hald_tool.py` one more time.
7. Done! A perfectly accurate `my_extracted_color.cube` will be generated. Simply load this file into the `CUBE LUT Apply` node in ComfyUI to achieve the exact Photoshop quality!
