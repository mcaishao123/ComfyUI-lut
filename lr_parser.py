"""
LRTemplate Parser - Parse Adobe Lightroom .lrtemplate preset files.

The .lrtemplate format is a Lua-like serialization containing develop settings
such as exposure, contrast, tone curves, HSL adjustments, etc.
"""

import re
import os


def parse_lrtemplate(filepath: str) -> dict:
    """
    Parse a .lrtemplate file and return a Python dict of settings.

    Args:
        filepath: Path to the .lrtemplate file.

    Returns:
        Dictionary with parsed preset data including 'settings' key.
    """
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Remove Lua-style comments
    content = re.sub(r"--\[\[.*?\]\]", "", content, flags=re.DOTALL)
    content = re.sub(r"--[^\n]*", "", content)

    # Parse the top-level table
    result = _parse_lua_table(content)

    # The root is usually s = { ... }, extract the inner dict
    if "s" in result:
        result = result["s"]

    return result


def _parse_lua_table(text: str) -> dict:
    """
    Recursively parse a Lua table from text into a Python dict.
    """
    result = {}

    # Find all top-level assignments: key = value
    # We need to handle nested braces carefully
    pos = 0
    text = text.strip()

    # If the text starts with '{' and ends with '}', it's a table body
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1].strip()
        # Remove trailing comma if present
        if text.endswith(","):
            text = text[:-1].strip()

    while pos < len(text):
        # Skip whitespace and commas
        while pos < len(text) and text[pos] in " \t\n\r,":
            pos += 1

        if pos >= len(text):
            break

        # Try to parse: key = value
        match = re.match(r'(\w+)\s*=\s*', text[pos:])
        if match:
            key = match.group(1)
            pos += match.end()

            value, pos = _parse_value(text, pos)
            result[key] = value
        else:
            # Skip to next comma or end
            next_comma = text.find(",", pos)
            if next_comma == -1:
                break
            pos = next_comma + 1

    return result


def _parse_value(text: str, pos: int):
    """
    Parse a value starting at position pos in text.
    Returns (value, new_pos).
    """
    # Skip whitespace
    while pos < len(text) and text[pos] in " \t\n\r":
        pos += 1

    if pos >= len(text):
        return None, pos

    ch = text[pos]

    # String value: "..."
    if ch == '"':
        return _parse_string(text, pos)

    # Table value: { ... }
    if ch == '{':
        return _parse_table_value(text, pos)

    # Boolean or keyword
    if text[pos:pos + 4] == "true":
        return True, pos + 4

    if text[pos:pos + 5] == "false":
        return False, pos + 5

    # Number (including negative and decimal)
    num_match = re.match(r'-?\d+\.?\d*', text[pos:])
    if num_match:
        num_str = num_match.group(0)
        new_pos = pos + len(num_str)
        if '.' in num_str:
            return float(num_str), new_pos
        else:
            return int(num_str), new_pos

    # Unquoted string (until comma or closing brace)
    end = pos
    while end < len(text) and text[end] not in ",}\n\r":
        end += 1
    val = text[pos:end].strip()
    return val, end


def _parse_string(text: str, pos: int):
    """Parse a quoted string starting at pos."""
    assert text[pos] == '"'
    pos += 1
    result = []
    while pos < len(text):
        ch = text[pos]
        if ch == '\\' and pos + 1 < len(text):
            result.append(text[pos + 1])
            pos += 2
        elif ch == '"':
            pos += 1
            return ''.join(result), pos
        else:
            result.append(ch)
            pos += 1
    return ''.join(result), pos


def _parse_table_value(text: str, pos: int):
    """
    Parse a Lua table starting at pos (which should be '{').
    Returns either a dict (if it has key=value pairs) or a list (if it's an array).
    """
    assert text[pos] == '{'
    # Find the matching closing brace
    depth = 0
    start = pos
    while pos < len(text):
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
            if depth == 0:
                pos += 1
                break
        elif text[pos] == '"':
            # Skip through strings
            pos += 1
            while pos < len(text) and text[pos] != '"':
                if text[pos] == '\\':
                    pos += 1
                pos += 1
        pos += 1

    table_text = text[start + 1:pos - 1].strip()

    # Determine if this is a dict (has key=value) or list (just values)
    # Check if there's any key = pattern
    if re.search(r'\w+\s*=', table_text):
        # It's a dict-like table
        return _parse_lua_table("{" + table_text + "}"), pos
    else:
        # It's an array-like table
        return _parse_array(table_text), pos


def _parse_array(text: str) -> list:
    """Parse a comma-separated list of values."""
    result = []
    pos = 0
    text = text.strip()

    while pos < len(text):
        while pos < len(text) and text[pos] in " \t\n\r,":
            pos += 1

        if pos >= len(text):
            break

        value, pos = _parse_value(text, pos)
        if value is not None:
            result.append(value)

    return result


def get_preset_name(preset_data: dict) -> str:
    """Extract the human-readable name from parsed preset data."""
    return preset_data.get("title", preset_data.get("internalName", "Unknown Preset"))


def get_settings(preset_data: dict) -> dict:
    """Extract the settings dict from parsed preset data."""
    value = preset_data.get("value", {})
    if isinstance(value, dict):
        return value.get("settings", {})
    return {}


def list_presets(directory: str) -> list:
    """
    List all .lrtemplate files in a directory.

    Returns:
        List of (filename, filepath) tuples.
    """
    presets = []
    if not os.path.isdir(directory):
        return presets

    for fname in sorted(os.listdir(directory)):
        if fname.lower().endswith(".lrtemplate"):
            presets.append((fname, os.path.join(directory, fname)))

    return presets
