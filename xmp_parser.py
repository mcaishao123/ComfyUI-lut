"""
XMP Preset Parser - Parse Adobe Lightroom/Camera Raw .xmp preset files.

XMP files are XML-based, with Camera Raw settings under the
crs (http://ns.adobe.com/camera-raw-settings/1.0/) namespace.
"""

import os
import re
import xml.etree.ElementTree as ET


# Camera Raw Settings namespace
CRS_NS = "http://ns.adobe.com/camera-raw-settings/1.0/"
CRS_PREFIX = "{" + CRS_NS + "}"

# RDF namespace
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDF_PREFIX = "{" + RDF_NS + "}"


def parse_xmp(filepath: str) -> dict:
    """
    Parse a .xmp preset file and return a settings dict
    compatible with lr_adjust.apply_preset().

    Args:
        filepath: Path to the .xmp file.

    Returns:
        Dictionary with 'name', 'settings', and 'source' keys.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    settings = {}

    # Method 1: Attributes on rdf:Description element
    for desc in root.iter(f"{RDF_PREFIX}Description"):
        for attr_name, attr_value in desc.attrib.items():
            if attr_name.startswith(CRS_PREFIX):
                key = attr_name[len(CRS_PREFIX):]
                settings[key] = _parse_value(attr_value)

    # Method 2: Child elements under rdf:Description with crs: prefix
    for desc in root.iter(f"{RDF_PREFIX}Description"):
        for child in desc:
            tag = child.tag
            if tag.startswith(CRS_PREFIX):
                key = tag[len(CRS_PREFIX):]
                if key not in settings:
                    # Check for rdf:Seq (ordered list, used for ToneCurve etc.)
                    seq = child.find(f"{RDF_PREFIX}Seq")
                    if seq is not None:
                        values = []
                        for li in seq.findall(f"{RDF_PREFIX}li"):
                            if li.text:
                                values.append(_parse_value(li.text.strip()))
                        settings[key] = values
                    elif child.text and child.text.strip():
                        settings[key] = _parse_value(child.text.strip())

    # Extract tone curve from comma-separated format if needed
    # Some XMP files store ToneCurvePV2012 as comma-separated string
    for curve_key in ["ToneCurvePV2012", "ToneCurvePV2012Red",
                      "ToneCurvePV2012Green", "ToneCurvePV2012Blue"]:
        if curve_key in settings and isinstance(settings[curve_key], str):
            # Parse "0, 0, 128, 135, 255, 255" format
            try:
                values = [_parse_value(v.strip())
                          for v in settings[curve_key].split(",")]
                settings[curve_key] = values
            except (ValueError, AttributeError):
                pass
        elif curve_key in settings and isinstance(settings[curve_key], list):
            # May be list of strings like ["0, 0", "128, 135", "255, 255"]
            if settings[curve_key] and isinstance(settings[curve_key][0], str):
                flat = []
                for item in settings[curve_key]:
                    parts = item.split(",")
                    for p in parts:
                        p = p.strip()
                        if p:
                            flat.append(_parse_value(p))
                settings[curve_key] = flat

    # Derive preset name
    name = os.path.splitext(os.path.basename(filepath))[0]
    for desc in root.iter(f"{RDF_PREFIX}Description"):
        # Check for crs:Name attribute
        name_attr = desc.get(f"{CRS_PREFIX}Name")
        if name_attr:
            name = name_attr
            break
        # Check dc:title
        dc_ns = "http://purl.org/dc/elements/1.1/"
        title_el = desc.find(f"{{{dc_ns}}}title")
        if title_el is not None:
            alt = title_el.find(f"{RDF_PREFIX}Alt")
            if alt is not None:
                li = alt.find(f"{RDF_PREFIX}li")
                if li is not None and li.text:
                    name = li.text.strip()
                    break

    return {
        "name": name,
        "settings": settings,
        "source": filepath,
    }


def _parse_value(text: str):
    """Parse a string value into the appropriate Python type."""
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    # Try integer
    try:
        return int(text)
    except ValueError:
        pass
    # Try float
    try:
        return float(text)
    except ValueError:
        pass
    return text


def list_xmp_presets(directory: str) -> list:
    """List all .xmp files in a directory."""
    presets = []
    if not os.path.isdir(directory):
        return presets
    for fname in sorted(os.listdir(directory)):
        if fname.lower().endswith(".xmp"):
            presets.append((fname, os.path.join(directory, fname)))
    return presets
