# ComfyUI-lut

[English](README.md) | 简体中文

ComfyUI 自定义节点，用于加载和应用 Adobe Lightroom 的 `.lrtemplate` / `.xmp` 预设以及 `.cube` 3D LUT 文件作为图像滤镜。

## 功能特性

本插件在 **image/filter** 分类下提供 8 个节点：

### Lightroom 预设 (.lrtemplate / .xmp)
- **LRTemplate Loader** 📷 — 从 presets 文件夹中加载 `.lrtemplate` / `.xmp` 预设文件
- **LRTemplate Apply** 🎨 — 将加载的预设应用到图片上（支持强度调节）
- **LRTemplate Manual** 🎛️ — 提供类似 Lightroom 的手动滑块调节（无需预设文件）
- **LRTemplate Search Loader** 🔍 — 通过文件名在文件夹中递归搜索并加载预设

### 3D LUTs (.cube)
- **CUBE LUT Loader** 🎬 — 从 presets 文件夹中加载 `.cube` LUT 文件
- **CUBE LUT Apply** 🎞️ — 将 CUBE LUT 应用到图片上（支持强度调节和三线性插值）
- **CUBE LUT Search Loader** 🔎 — 通过文件名在文件夹中递归搜索并加载 `.cube` 文件

### 辅助工具
- **Preset Catalog Generator** 📊 — 批量将文件夹内的所有预设应用到一张图片上，并导出生成带有预览效果图的 Excel 表格目录（支持 `.lrtemplate`, `.xmp`, `.cube`）。

## 支持的调整参数 (Lightroom)

| 类别 | 参数项 |
|---|---|
| **色调 (Tone)** | 曝光度、对比度、高光、阴影、白色色阶、黑色色阶 |
| **偏好 (Presence)** | 清晰度、自然饱和度、饱和度 |
| **白平衡 (White Balance)** | 色温、色调 |
| **色调曲线 (Tone Curve)** | RGB 综合曲线、单通道 (R/G/B) 曲线 |
| **HSL** | 各颜色的色相、饱和度、明亮度 (红、橙、黄、绿、浅绿、蓝、紫、洋红) |
| **分离色调 (Split Toning)** | 高光色相/饱和度、阴影色相/饱和度 |
| **效果 (Effects)** | 裁剪后晕影 (暗角)、颗粒 |

## 使用方法

1. 将你的 `.lrtemplate`, `.xmp`, 或 `.cube` 文件放入 `ComfyUI-lut/presets/` 文件夹（或者使用 Search Loader 节点任意指定目录）。
2. 重启 ComfyUI 或刷新浏览器界面。
3. 在 **image/filter** 类别中添加节点。

### 工作流示例

```text
Load Image → LRTemplate Apply ← LRTemplate Loader
                   ↓
             Preview Image
```

## 批量生成预设效果目录 (Excel)

**Preset Catalog Generator** 节点允许你选择一个包含大量预设的文件夹，并生成一个 `.xlsx` Excel 文件，里面会自动贴上每个预设对你输入图片的处理效果缩略图。

> **注意**：对于包含海量预设的文件夹（比如 100,000+ 个文件），该节点会自动每处理 50 个预设保存一次进度，防止意外中断导致数据丢失。

你也可以完全脱离 ComfyUI 界面，通过命令行直接运行生成脚本：

```bash
cd custom_nodes\ComfyUI-lut
..\..\python_embeded\python.exe generate_preset_catalog.py "D:\你的图片.jpg" "D:\预设文件夹路径" "D:\输出的预设目录.xlsx"
```
