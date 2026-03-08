"""
LRTemplate Image Adjustment Engine

Applies Lightroom-style adjustments to images using numpy and PIL.
All operations work on float32 numpy arrays with values in [0, 1].
"""

import numpy as np
from PIL import Image, ImageFilter


def apply_preset(image_np: np.ndarray, settings: dict, strength: float = 1.0) -> np.ndarray:
    """
    Apply a full set of lrtemplate settings to an image.

    Args:
        image_np: Image as float32 numpy array, shape (H, W, 3), values in [0, 1].
        settings: Parsed settings dict from lrtemplate.
        strength: Blend factor 0.0 (original) to 1.0 (full effect).

    Returns:
        Adjusted image as float32 numpy array.
    """
    if strength <= 0.0:
        return image_np.copy()

    original = image_np.copy()
    result = image_np.copy()

    # 1. White Balance (Temperature & Tint)
    temp = settings.get("Temperature", None)
    tint = settings.get("Tint", None)
    if temp is not None or tint is not None:
        result = _apply_white_balance(result, temp, tint)

    # 2. Tone adjustments
    result = _apply_tone(result, settings)

    # 3. Tone Curves
    result = _apply_tone_curves(result, settings)

    # 4. HSL adjustments
    result = _apply_hsl(result, settings)

    # 5. Split Toning
    result = _apply_split_toning(result, settings)

    # 6. Clarity
    clarity = settings.get("Clarity2012", settings.get("Clarity", 0))
    if clarity and clarity != 0:
        result = _apply_clarity(result, clarity)

    # 7. Vibrance & Saturation
    vibrance = settings.get("Vibrance", 0)
    saturation = settings.get("Saturation", 0)
    if vibrance and vibrance != 0:
        result = _apply_vibrance(result, vibrance)
    if saturation and saturation != 0:
        result = _apply_saturation_adjust(result, saturation)

    # 8. Vignette
    vignette_amount = settings.get("PostCropVignetteAmount", 0)
    if vignette_amount and vignette_amount != 0:
        vignette_midpoint = settings.get("PostCropVignetteMidpoint", 50)
        vignette_roundness = settings.get("PostCropVignetteRoundness", 0)
        vignette_feather = settings.get("PostCropVignetteFeather", 50)
        result = _apply_vignette(result, vignette_amount, vignette_midpoint,
                                 vignette_feather, vignette_roundness)

    # 9. Grain
    grain_amount = settings.get("GrainAmount", 0)
    if grain_amount and grain_amount != 0:
        grain_size = settings.get("GrainSize", 25)
        result = _apply_grain(result, grain_amount, grain_size)

    # Clamp
    result = np.clip(result, 0.0, 1.0)

    # Blend with original based on strength
    if strength < 1.0:
        result = original * (1.0 - strength) + result * strength

    return result.astype(np.float32)


# =============================================================================
# White Balance
# =============================================================================

def _apply_white_balance(img: np.ndarray, temperature, tint) -> np.ndarray:
    """
    Apply white balance by shifting the color temperature and tint.
    Temperature > 0 = warmer (more yellow), < 0 = cooler (more blue).
    Tint > 0 = more magenta, < 0 = more green.
    """
    result = img.copy()

    if temperature is not None and temperature != 0:
        # Lightroom temperature range is roughly -100 to 100 for offset from As Shot
        # Map to a subtle RGB shift
        t = float(temperature) / 150.0  # Normalize
        # Warm: boost red, slightly reduce blue
        result[:, :, 0] = result[:, :, 0] * (1.0 + t * 0.1)   # R
        result[:, :, 2] = result[:, :, 2] * (1.0 - t * 0.1)   # B

    if tint is not None and tint != 0:
        t = float(tint) / 150.0
        # Tint: positive = magenta (boost R,B, reduce G)
        result[:, :, 1] = result[:, :, 1] * (1.0 - t * 0.05)  # G
        result[:, :, 0] = result[:, :, 0] * (1.0 + t * 0.025)  # R
        result[:, :, 2] = result[:, :, 2] * (1.0 + t * 0.025)  # B

    return result


# =============================================================================
# Tone Adjustments (Exposure, Contrast, Highlights, Shadows, Whites, Blacks)
# =============================================================================

def _apply_tone(img: np.ndarray, settings: dict) -> np.ndarray:
    """Apply basic tonal adjustments."""
    result = img.copy()

    # Exposure: multiply by 2^exposure
    exposure = settings.get("Exposure2012", settings.get("Exposure", 0))
    if exposure and exposure != 0:
        factor = 2.0 ** (float(exposure) / 2.0)  # LR uses ~stops, we halve for subtlety
        result = result * factor

    # Contrast: S-curve around midpoint
    contrast = settings.get("Contrast2012", settings.get("Contrast", 0))
    if contrast and contrast != 0:
        c = float(contrast) / 100.0  # Normalize to [-1, 1]
        # Simple contrast: shift midpoint
        factor = 1.0 + c * 0.5
        result = (result - 0.5) * factor + 0.5

    # Highlights: compress/expand bright regions
    highlights = settings.get("Highlights2012", settings.get("Highlights", 0))
    if highlights and highlights != 0:
        h = float(highlights) / 100.0
        mask = np.clip((result - 0.5) * 2.0, 0.0, 1.0)  # Highlight mask
        adjustment = -h * 0.3 * mask
        result = result + adjustment

    # Shadows: lift/lower dark regions
    shadows = settings.get("Shadows2012", settings.get("Shadows", 0))
    if shadows and shadows != 0:
        s = float(shadows) / 100.0
        mask = 1.0 - np.clip(result * 2.0, 0.0, 1.0)  # Shadow mask
        adjustment = s * 0.3 * mask
        result = result + adjustment

    # Whites: adjust white point
    whites = settings.get("Whites2012", settings.get("Whites", 0))
    if whites and whites != 0:
        w = float(whites) / 100.0
        # Shift the upper range
        mask = np.clip((result - 0.7) / 0.3, 0.0, 1.0)
        result = result + w * 0.2 * mask

    # Blacks: adjust black point
    blacks = settings.get("Blacks2012", settings.get("Blacks", 0))
    if blacks and blacks != 0:
        b = float(blacks) / 100.0
        mask = 1.0 - np.clip(result / 0.3, 0.0, 1.0)
        result = result + b * 0.2 * mask

    return result


# =============================================================================
# Tone Curves
# =============================================================================

def _apply_tone_curves(img: np.ndarray, settings: dict) -> np.ndarray:
    """Apply tone curves (composite and per-channel)."""
    result = img.copy()

    # Composite curve
    curve_name = settings.get("ToneCurveName2012", "Linear")
    curve_points = settings.get("ToneCurvePV2012", None)

    if curve_points and isinstance(curve_points, list) and len(curve_points) >= 4:
        lut = _build_curve_lut(curve_points)
        # Apply to all channels (luminance-like)
        for c in range(3):
            result[:, :, c] = _apply_lut(result[:, :, c], lut)

    # Per-channel curves
    for channel_idx, channel_name in enumerate(["Red", "Green", "Blue"]):
        key = f"ToneCurvePV2012{channel_name}"
        points = settings.get(key, None)
        if points and isinstance(points, list) and len(points) >= 4:
            lut = _build_curve_lut(points)
            result[:, :, channel_idx] = _apply_lut(result[:, :, channel_idx], lut)

    return result


def _build_curve_lut(points: list) -> np.ndarray:
    """
    Build a 256-entry LUT from curve control points.
    Points are [x1, y1, x2, y2, ...] pairs going from 0-255.
    """
    if len(points) < 4:
        return np.arange(256, dtype=np.float32) / 255.0

    # Parse into (x, y) pairs
    xy_pairs = []
    for i in range(0, len(points) - 1, 2):
        x = float(points[i])
        y = float(points[i + 1])
        xy_pairs.append((x, y))

    # Sort by x
    xy_pairs.sort(key=lambda p: p[0])

    # Ensure we have endpoints
    if xy_pairs[0][0] > 0:
        xy_pairs.insert(0, (0.0, 0.0))
    if xy_pairs[-1][0] < 255:
        xy_pairs.append((255.0, 255.0))

    # Interpolate using Monotone Cubic Spline (PCHIP)
    xs = [p[0] for p in xy_pairs]
    ys = [p[1] for p in xy_pairs]

    try:
        from scipy.interpolate import PchipInterpolator
        interpolator = PchipInterpolator(xs, ys)
        lut_vals = interpolator(np.arange(256))
    except ImportError:
        lut_vals = np.interp(np.arange(256), xs, ys)

    # Ensure LUT stays in bounds
    lut = np.clip(lut_vals, 0.0, 255.0) / 255.0
    return lut.astype(np.float32)


def _apply_lut(channel: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Apply a 256-entry LUT to a single channel."""
    indices = np.clip(channel * 255.0, 0, 255).astype(np.int32)
    return lut[indices]


# =============================================================================
# HSL Adjustments
# =============================================================================

# HSL color ranges used by Lightroom
_LR_COLORS = ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta"]
_LR_HUE_CENTERS = {
    "Red": 0, "Orange": 30, "Yellow": 60, "Green": 120,
    "Aqua": 180, "Blue": 240, "Purple": 270, "Magenta": 330
}


def _rgb_to_hsl(img: np.ndarray) -> tuple:
    """Convert RGB image [0,1] to HSL arrays (H in degrees, S and L in [0,1])."""
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]

    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin

    # Lightness
    l = (cmax + cmin) / 2.0

    # Saturation
    s = np.where(delta == 0, 0.0,
                 np.where(l <= 0.5, delta / (cmax + cmin + 1e-10),
                          delta / (2.0 - cmax - cmin + 1e-10)))

    # Hue
    h = np.zeros_like(r)
    mask_r = (cmax == r) & (delta > 0)
    mask_g = (cmax == g) & (delta > 0)
    mask_b = (cmax == b) & (delta > 0)

    h[mask_r] = (60.0 * ((g[mask_r] - b[mask_r]) / (delta[mask_r] + 1e-10))) % 360
    h[mask_g] = (60.0 * ((b[mask_g] - r[mask_g]) / (delta[mask_g] + 1e-10)) + 120.0) % 360
    h[mask_b] = (60.0 * ((r[mask_b] - g[mask_b]) / (delta[mask_b] + 1e-10)) + 240.0) % 360

    return h, s, l


def _hsl_to_rgb(h: np.ndarray, s: np.ndarray, l: np.ndarray) -> np.ndarray:
    """Convert HSL arrays back to RGB image [0,1]."""
    c = (1.0 - np.abs(2.0 * l - 1.0)) * s
    h_prime = (h / 60.0) % 6
    x = c * (1.0 - np.abs(h_prime % 2 - 1.0))
    m = l - c / 2.0

    r = np.zeros_like(h)
    g = np.zeros_like(h)
    b = np.zeros_like(h)

    for i in range(6):
        mask = (h_prime >= i) & (h_prime < i + 1)
        if i == 0:
            r[mask], g[mask], b[mask] = c[mask], x[mask], 0
        elif i == 1:
            r[mask], g[mask], b[mask] = x[mask], c[mask], 0
        elif i == 2:
            r[mask], g[mask], b[mask] = 0, c[mask], x[mask]
        elif i == 3:
            r[mask], g[mask], b[mask] = 0, x[mask], c[mask]
        elif i == 4:
            r[mask], g[mask], b[mask] = x[mask], 0, c[mask]
        elif i == 5:
            r[mask], g[mask], b[mask] = c[mask], 0, x[mask]

    result = np.stack([r + m, g + m, b + m], axis=-1)
    return np.clip(result, 0.0, 1.0).astype(np.float32)


def _hue_weight(h: np.ndarray, center: float, width: float = 30.0) -> np.ndarray:
    """
    Calculate a weight mask for a hue range.
    Returns values in [0, 1] based on angular distance from center hue.
    """
    # Angular distance
    diff = np.abs(h - center)
    diff = np.minimum(diff, 360.0 - diff)
    weight = np.clip(1.0 - diff / width, 0.0, 1.0)
    return weight


def _apply_hsl(img: np.ndarray, settings: dict) -> np.ndarray:
    """Apply HSL (Hue, Saturation, Luminance) per-color adjustments."""
    # Check if any HSL adjustments exist
    has_hsl = False
    for color in _LR_COLORS:
        if (settings.get(f"HueAdjustment{color}", 0) or
                settings.get(f"SaturationAdjustment{color}", 0) or
                settings.get(f"LuminanceAdjustment{color}", 0)):
            has_hsl = True
            break

    if not has_hsl:
        return img

    h, s, l = _rgb_to_hsl(img)

    for color in _LR_COLORS:
        center = _LR_HUE_CENTERS[color]
        weight = _hue_weight(h, center, width=35.0)

        # Hue shift
        hue_adj = settings.get(f"HueAdjustment{color}", 0)
        if hue_adj and hue_adj != 0:
            h = h + float(hue_adj) * weight
            h = h % 360

        # Saturation
        sat_adj = settings.get(f"SaturationAdjustment{color}", 0)
        if sat_adj and sat_adj != 0:
            factor = 1.0 + float(sat_adj) / 100.0
            s = s * (1.0 + (factor - 1.0) * weight)

        # Luminance
        lum_adj = settings.get(f"LuminanceAdjustment{color}", 0)
        if lum_adj and lum_adj != 0:
            shift = float(lum_adj) / 100.0 * 0.3
            l = l + shift * weight

    s = np.clip(s, 0.0, 1.0)
    l = np.clip(l, 0.0, 1.0)

    return _hsl_to_rgb(h, s, l)


# =============================================================================
# Split Toning
# =============================================================================

def _apply_split_toning(img: np.ndarray, settings: dict) -> np.ndarray:
    """Apply split toning to highlights and shadows."""
    hi_hue = settings.get("SplitToningHighlightHue", 0)
    hi_sat = settings.get("SplitToningHighlightSaturation", 0)
    sh_hue = settings.get("SplitToningShadowHue", 0)
    sh_sat = settings.get("SplitToningShadowSaturation", 0)
    balance = settings.get("SplitToningBalance", 0)

    if (not hi_sat or hi_sat == 0) and (not sh_sat or sh_sat == 0):
        return img

    result = img.copy()
    luminance = np.mean(result, axis=2, keepdims=True)

    # Highlight toning
    if hi_sat and hi_sat > 0:
        hi_color = _hue_to_rgb(float(hi_hue))
        hi_strength = float(hi_sat) / 100.0 * 0.3
        hi_mask = np.clip((luminance - 0.5) * 2.0, 0.0, 1.0)
        for c in range(3):
            result[:, :, c] = result[:, :, c] + (hi_color[c] - 0.5) * hi_strength * hi_mask[:, :, 0]

    # Shadow toning
    if sh_sat and sh_sat > 0:
        sh_color = _hue_to_rgb(float(sh_hue))
        sh_strength = float(sh_sat) / 100.0 * 0.3
        sh_mask = 1.0 - np.clip(luminance * 2.0, 0.0, 1.0)
        for c in range(3):
            result[:, :, c] = result[:, :, c] + (sh_color[c] - 0.5) * sh_strength * sh_mask[:, :, 0]

    return result


def _hue_to_rgb(hue: float) -> tuple:
    """Convert a hue value (0-360) to an RGB tuple in [0,1]."""
    h = (hue % 360) / 60.0
    c = 1.0
    x = 1.0 - abs(h % 2 - 1.0)
    if h < 1:
        return (c, x, 0)
    elif h < 2:
        return (x, c, 0)
    elif h < 3:
        return (0, c, x)
    elif h < 4:
        return (0, x, c)
    elif h < 5:
        return (x, 0, c)
    else:
        return (c, 0, x)


# =============================================================================
# Clarity (Local Contrast)
# =============================================================================

def _apply_clarity(img: np.ndarray, clarity: float) -> np.ndarray:
    """
    Apply clarity (local contrast enhancement) using unsharp masking.
    """
    amount = float(clarity) / 100.0 * 0.5

    # Convert to PIL for Gaussian blur
    h, w, _ = img.shape
    pil_img = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    blurred = pil_img.filter(ImageFilter.GaussianBlur(radius=max(3, min(h, w) // 20)))
    blurred_np = np.array(blurred).astype(np.float32) / 255.0

    # Unsharp mask: original + amount * (original - blurred)
    result = img + amount * (img - blurred_np)
    return result


# =============================================================================
# Vibrance & Saturation
# =============================================================================

def _apply_vibrance(img: np.ndarray, vibrance: float) -> np.ndarray:
    """
    Apply vibrance: saturation boost weighted inversely by existing saturation.
    Less-saturated areas get more boost.
    """
    v = float(vibrance) / 100.0

    h, s, l = _rgb_to_hsl(img)

    # Vibrance: boost saturation more where it's lower
    boost = v * (1.0 - s)  # Higher boost for less saturated
    s = s + boost * 0.5
    s = np.clip(s, 0.0, 1.0)

    return _hsl_to_rgb(h, s, l)


def _apply_saturation_adjust(img: np.ndarray, saturation: float) -> np.ndarray:
    """Apply uniform saturation adjustment."""
    s_val = float(saturation) / 100.0

    h, s, l = _rgb_to_hsl(img)
    s = s * (1.0 + s_val * 0.5)
    s = np.clip(s, 0.0, 1.0)

    return _hsl_to_rgb(h, s, l)


# =============================================================================
# Vignette
# =============================================================================

def _apply_vignette(img: np.ndarray, amount: float, midpoint: float = 50,
                    feather: float = 50, roundness: float = 0) -> np.ndarray:
    """Apply vignette darkening/brightening at the edges."""
    h, w, _ = img.shape
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cy, cx = h / 2.0, w / 2.0

    # Normalize coordinates
    x_norm = (x - cx) / cx
    y_norm = (y - cy) / cy

    # Distance from center
    dist = np.sqrt(x_norm ** 2 + y_norm ** 2)

    # Midpoint and feather
    mp = float(midpoint) / 100.0  # 0 to 1
    ft = max(float(feather) / 100.0, 0.01)  # 0 to 1

    # Create vignette mask
    vignette = np.clip((dist - mp) / ft, 0.0, 1.0)
    vignette = vignette ** 2  # Smooth falloff

    # Amount: negative = darken, positive = brighten
    a = float(amount) / 100.0
    multiplier = 1.0 + a * vignette

    result = img * multiplier[:, :, np.newaxis]
    return result


# =============================================================================
# Grain
# =============================================================================

def _apply_grain(img: np.ndarray, amount: float, size: float = 25) -> np.ndarray:
    """Add film grain to the image."""
    h, w, _ = img.shape
    a = float(amount) / 100.0 * 0.15  # Scale down

    # Generate noise
    s = max(1, int(float(size) / 25.0 * 2))
    if s > 1:
        # Larger grain: generate at lower res and upscale
        small_h, small_w = max(1, h // s), max(1, w // s)
        noise_small = np.random.randn(small_h, small_w).astype(np.float32)
        # Upscale using PIL
        noise_pil = Image.fromarray(((noise_small + 3) / 6 * 255).clip(0, 255).astype(np.uint8))
        noise_pil = noise_pil.resize((w, h), Image.BILINEAR)
        noise = (np.array(noise_pil).astype(np.float32) / 255.0 * 6 - 3)
    else:
        noise = np.random.randn(h, w).astype(np.float32)

    result = img + a * noise[:, :, np.newaxis]
    return result
