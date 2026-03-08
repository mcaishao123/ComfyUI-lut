"""
CUBE LUT Parser and Applier

Parses .cube (3D LUT / 1D LUT) files and applies them to images.
The CUBE format is a widely-used text-based LUT format for color grading.
"""

import os
import numpy as np


def parse_cube(filepath: str) -> dict:
    """
    Parse a .cube LUT file.

    Args:
        filepath: Path to the .cube file.

    Returns:
        Dictionary with keys:
        - 'title': LUT title
        - 'type': '1D' or '3D'
        - 'size': LUT size (int)
        - 'domain_min': [r, g, b] minimum values
        - 'domain_max': [r, g, b] maximum values
        - 'data': numpy array of LUT data
    """
    title = os.path.splitext(os.path.basename(filepath))[0]
    lut_type = None
    lut_size = None
    domain_min = [0.0, 0.0, 0.0]
    domain_max = [1.0, 1.0, 1.0]
    data_lines = []

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse keywords
            upper = line.upper()

            if upper.startswith("TITLE"):
                # TITLE "name"
                match = line.split('"')
                if len(match) >= 2:
                    title = match[1]
                continue

            if upper.startswith("DOMAIN_MIN"):
                parts = line.split()[1:]
                if len(parts) >= 3:
                    domain_min = [float(x) for x in parts[:3]]
                continue

            if upper.startswith("DOMAIN_MAX"):
                parts = line.split()[1:]
                if len(parts) >= 3:
                    domain_max = [float(x) for x in parts[:3]]
                continue

            if upper.startswith("LUT_1D_SIZE"):
                lut_size = int(line.split()[1])
                lut_type = "1D"
                continue

            if upper.startswith("LUT_3D_SIZE"):
                lut_size = int(line.split()[1])
                lut_type = "3D"
                continue

            # Skip other keywords
            if any(upper.startswith(kw) for kw in ["LUT_", "DOMAIN_"]):
                continue

            # Try to parse as data line (3 floats)
            try:
                values = [float(x) for x in line.split()]
                if len(values) >= 3:
                    data_lines.append(values[:3])
            except ValueError:
                continue

    if lut_type is None or lut_size is None:
        raise ValueError(f"Invalid CUBE file: missing LUT_1D_SIZE or LUT_3D_SIZE in {filepath}")

    data = np.array(data_lines, dtype=np.float32)

    return {
        "title": title,
        "type": lut_type,
        "size": lut_size,
        "domain_min": domain_min,
        "domain_max": domain_max,
        "data": data,
    }


def apply_cube_lut(image_np: np.ndarray, lut_data: dict, strength: float = 1.0) -> np.ndarray:
    """
    Apply a parsed CUBE LUT to an image.

    Args:
        image_np: Image as float32 numpy array (H, W, 3), values in [0, 1].
        lut_data: Parsed LUT dict from parse_cube().
        strength: Blend factor 0.0 (original) to 1.0 (full effect).

    Returns:
        Adjusted image as float32 numpy array.
    """
    if strength <= 0.0:
        return image_np.copy()

    original = image_np.copy()

    if lut_data["type"] == "1D":
        result = _apply_1d_lut(image_np, lut_data)
    elif lut_data["type"] == "3D":
        result = _apply_3d_lut(image_np, lut_data)
    else:
        return image_np.copy()

    result = np.clip(result, 0.0, 1.0)

    if strength < 1.0:
        result = original * (1.0 - strength) + result * strength

    return result.astype(np.float32)


def _apply_1d_lut(image_np: np.ndarray, lut_data: dict) -> np.ndarray:
    """Apply a 1D LUT (independent per-channel curve)."""
    size = lut_data["size"]
    data = lut_data["data"]  # shape: (size, 3)
    d_min = lut_data["domain_min"]
    d_max = lut_data["domain_max"]

    result = image_np.copy()

    for c in range(3):
        # Normalize input to [0, 1] within domain
        channel = result[:, :, c]
        normalized = (channel - d_min[c]) / (d_max[c] - d_min[c] + 1e-10)
        normalized = np.clip(normalized, 0.0, 1.0)

        # Map to LUT indices
        indices = normalized * (size - 1)
        idx_low = np.floor(indices).astype(np.int32)
        idx_high = np.minimum(idx_low + 1, size - 1)
        frac = indices - idx_low

        # Interpolate
        result[:, :, c] = data[idx_low, c] * (1.0 - frac) + data[idx_high, c] * frac

    return result


def _apply_3d_lut(image_np: np.ndarray, lut_data: dict) -> np.ndarray:
    """Apply a 3D LUT using trilinear interpolation."""
    size = lut_data["size"]
    data = lut_data["data"]  # shape: (size^3, 3)
    d_min = lut_data["domain_min"]
    d_max = lut_data["domain_max"]

    # Reshape data to 3D grid: (size, size, size, 3)
    # CUBE format: R varies fastest, then G, then B
    lut_3d = data.reshape(size, size, size, 3)

    h, w, _ = image_np.shape
    result = np.zeros_like(image_np)

    # Normalize input to [0, size-1]
    r = (image_np[:, :, 0] - d_min[0]) / (d_max[0] - d_min[0] + 1e-10) * (size - 1)
    g = (image_np[:, :, 1] - d_min[1]) / (d_max[1] - d_min[1] + 1e-10) * (size - 1)
    b = (image_np[:, :, 2] - d_min[2]) / (d_max[2] - d_min[2] + 1e-10) * (size - 1)

    r = np.clip(r, 0, size - 1 - 1e-6)
    g = np.clip(g, 0, size - 1 - 1e-6)
    b = np.clip(b, 0, size - 1 - 1e-6)

    # Integer and fractional parts
    r0 = np.floor(r).astype(np.int32)
    g0 = np.floor(g).astype(np.int32)
    b0 = np.floor(b).astype(np.int32)
    r1 = np.minimum(r0 + 1, size - 1)
    g1 = np.minimum(g0 + 1, size - 1)
    b1 = np.minimum(b0 + 1, size - 1)

    fr = (r - r0).astype(np.float32)
    fg = (g - g0).astype(np.float32)
    fb = (b - b0).astype(np.float32)

    # Trilinear interpolation
    for c in range(3):
        c000 = lut_3d[b0, g0, r0, c]
        c100 = lut_3d[b0, g0, r1, c]
        c010 = lut_3d[b0, g1, r0, c]
        c110 = lut_3d[b0, g1, r1, c]
        c001 = lut_3d[b1, g0, r0, c]
        c101 = lut_3d[b1, g0, r1, c]
        c011 = lut_3d[b1, g1, r0, c]
        c111 = lut_3d[b1, g1, r1, c]

        c00 = c000 * (1 - fr) + c100 * fr
        c01 = c001 * (1 - fr) + c101 * fr
        c10 = c010 * (1 - fr) + c110 * fr
        c11 = c011 * (1 - fr) + c111 * fr

        c0 = c00 * (1 - fg) + c10 * fg
        c1 = c01 * (1 - fg) + c11 * fg

        result[:, :, c] = c0 * (1 - fb) + c1 * fb

    return result


def list_cube_files(directory: str) -> list:
    """List all .cube files in a directory."""
    files = []
    if not os.path.isdir(directory):
        return files
    for fname in sorted(os.listdir(directory)):
        if fname.lower().endswith(".cube"):
            files.append((fname, os.path.join(directory, fname)))
    return files
