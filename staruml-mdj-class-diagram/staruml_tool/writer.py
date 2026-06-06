"""
StarUML .mdj file writer.

Takes the in-memory representation and serializes it back to valid .mdj JSON
with proper $ref cross-references.
"""

import json
from typing import Any, Dict, List, Optional

from .parser import (
    MdjParser,
    _get_all_attributes,
    get_default_value,
    AK_PRIM,
    AK_ENUM,
    AK_REF,
    AK_REFS,
    AK_OBJ,
    AK_OBJS,
    AK_VAR,
    AK_CUSTOM,
)

# Attributes that must always be written to ensure correct rendering
_ALWAYS_SERIALIZE = frozenset({"horizontalAlignment", "visible"})


class MdjWriter:
    def __init__(self, parser: MdjParser):
        self._parser = parser

    def save(self, filepath: str):
        data = self._serialize()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent="\t", ensure_ascii=False)

    def dumps(self) -> str:
        data = self._serialize()
        return json.dumps(data, indent="\t", ensure_ascii=False)

    def _serialize(self) -> dict:
        return self._serialize_element(self._parser.root)

    def _serialize_element(self, elem: Any) -> Any:
        if elem is None:
            return None
        if isinstance(elem, list):
            return [self._serialize_element(v) for v in elem]
        if isinstance(elem, str):
            # Check if this string is actually an id that points to an element
            # We don't treat plain strings as refs — those are actual string values
            return elem
        if not isinstance(elem, dict):
            return elem

        if "_id" in elem and "_type" in elem:
            return self._serialize_typed_element(elem)

        # Plain dict that's not an element — just copy
        result = {}
        for k, v in elem.items():
            result[k] = self._serialize_element(v)
        return result

    def _serialize_typed_element(self, elem: dict) -> dict:
        type_name = elem.get("_type", "")
        result = {}
        result["_type"] = type_name
        result["_id"] = elem["_id"]

        # Serialize _parent as $ref
        parent = elem.get("_parent")
        if parent and isinstance(parent, dict) and "_id" in parent:
            result["_parent"] = {"$ref": parent["_id"]}

        # Build a lookup of metamodel-defined attributes for this type
        meta_attrs = {}
        for a in _get_all_attributes(type_name):
            meta_attrs[a["name"]] = a

        # Serialize ALL attributes on the element (not just metamodel-defined ones)
        for attr_name, val in elem.items():
            if attr_name in ("_type", "_id", "_parent"):
                continue

            if val is None:
                continue
            if isinstance(val, list) and len(val) == 0:
                # Skip empty lists unless they were explicitly set (non-default)
                meta_def = meta_attrs.get(attr_name)
                if meta_def and meta_def.get("default") == []:
                    continue
                if not meta_def:
                    continue

            # Skip known default values (but always write layout-critical attributes)
            if attr_name not in _ALWAYS_SERIALIZE and self._is_default(type_name, attr_name, val):
                continue

            # Determine how to serialize
            meta_def = meta_attrs.get(attr_name)
            if meta_def:
                result[attr_name] = self._serialize_by_kind(val, meta_def)
            else:
                # Attribute not in metamodel — auto-detect serialization
                result[attr_name] = self._serialize_unknown(val)

        return result

    def _serialize_by_kind(self, val: Any, attr_def: dict) -> Any:
        """Serialize a value according to its metamodel-defined kind."""
        kind = attr_def["kind"]
        if kind == AK_PRIM or kind == AK_ENUM:
            return val
        elif kind == AK_REF:
            return self._val_to_ref(val)
        elif kind == AK_REFS:
            return self._val_to_refs(val)
        elif kind == AK_OBJ or kind == AK_OBJS:
            return self._serialize_element(val)
        elif kind == AK_VAR:
            return self._val_to_var(val)
        elif kind == AK_CUSTOM:
            return val
        return val

    def _serialize_unknown(self, val: Any) -> Any:
        """Auto-detect how to serialize a value not in the metamodel.
        Handles refs ($ref), nested typed elements, lists of refs/elements."""
        if val is None:
            return None
        if isinstance(val, dict):
            if "_id" in val:
                # Element reference -> $ref
                return {"$ref": val["_id"]}
            # Plain dict or nested typed element
            return {k: self._serialize_unknown(v) for k, v in val.items()}
        if isinstance(val, list):
            result = []
            for item in val:
                if isinstance(item, dict) and "_id" in item:
                    result.append({"$ref": item["_id"]})
                elif isinstance(item, dict) and "_type" in item:
                    result.append(self._serialize_element(item))
                else:
                    result.append(self._serialize_unknown(item))
            return result if result else None
        return val

    def _is_default(self, type_name: str, attr_name: str, val: Any) -> bool:
        default = get_default_value(type_name, attr_name)
        if default is None:
            return False
        return val == default

    def _val_to_ref(self, val: Any) -> Any:
        """Convert a value to a $ref if it's an element."""
        if isinstance(val, dict) and "_id" in val:
            return {"$ref": val["_id"]}
        return val

    def _val_to_refs(self, val: Any) -> Any:
        """Convert a list to $ref entries."""
        if isinstance(val, list):
            result = []
            for item in val:
                if isinstance(item, dict) and "_id" in item:
                    result.append({"$ref": item["_id"]})
                else:
                    result.append(item)
            return result if result else None
        return val

    def _val_to_var(self, val: Any) -> Any:
        """Convert variant to string or $ref."""
        if isinstance(val, dict) and "_id" in val:
            return {"$ref": val["_id"]}
        return val
