# ComfyUI-LRTemplate

ComfyUI custom nodes for loading and applying Adobe Lightroom `.lrtemplate` presets as image filters.

## Features

- **LRTemplate Loader** 📷 — Load `.lrtemplate` preset files from the presets folder
- **LRTemplate Apply** 🎨 — Apply loaded presets to images with strength control
- **LRTemplate Manual** 🎛️ — Apply Lightroom-style adjustments with sliders (no preset file needed)

## Supported Adjustments

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

1. Place your `.lrtemplate` files in `ComfyUI-lut/presets/` folder
2. Restart ComfyUI or refresh the browser
3. Add nodes from **image/filter** category:
   - **LRTemplate Loader** → Select preset from dropdown
   - **LRTemplate Apply** → Connect image and preset, adjust strength
4. Connect to a Preview Image or Save Image node

### Workflow Example

```
Load Image → LRTemplate Apply ← LRTemplate Loader
    ↓
Preview Image
```

## Installation

Already installed as a ComfyUI custom node. No additional dependencies required.


批量生成预设效果：

# 先进入脚本目录
cd d:\soft\ComfyUI\ComfyUI\custom_nodes\ComfyUI-lut

# 执行脚本（替换为你的实际路径）
D:\soft\ComfyUI\python_embeded\python.exe generate_preset_catalog.py "你的图片.jpg" "F:\资源\168000全套预设合集" "D:\预设目录.xlsx"
