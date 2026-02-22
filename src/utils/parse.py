from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Any


def parse_mixed_payload(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        return {}
    if stripped[0] in "[{":
        return json.loads(stripped)
    if stripped[0] == "<":
        root = ET.fromstring(stripped)
        return _xml_to_dict(root)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        root = ET.fromstring(stripped)
        return _xml_to_dict(root)


def _xml_to_dict(node: ET.Element) -> dict[str, Any]:
    children = list(node)
    if not children:
        return {node.tag: node.text}
    grouped: dict[str, list[Any]] = {}
    for child in children:
        grouped.setdefault(child.tag, []).append(_xml_to_dict(child)[child.tag])

    result: dict[str, Any] = {}
    for k, v in grouped.items():
        result[k] = v[0] if len(v) == 1 else v
    return {node.tag: result}
