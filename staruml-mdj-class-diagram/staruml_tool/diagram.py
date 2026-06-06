"""
High-level API for manipulating UML class diagrams in StarUML .mdj files.

Provides CRUD operations on classes, attributes, operations, and relationships.
"""

import time
import random
import math
from typing import Any, Dict, List, Optional, Tuple

from .parser import MdjParser, _get_all_attributes, get_default_value
from .writer import MdjWriter


# ---------------------------------------------------------------------------
# ID Generator — replicates StarUML's IdGenerator
# ---------------------------------------------------------------------------

ID_TABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

_id_counter = random.randint(0, 65535)


def generate_id() -> str:
    """Generate a StarUML-compatible base64 ID."""
    global _id_counter
    timestamp = int(time.time() * 1000)
    _id_counter = (_id_counter + 1) & 0xFFFF
    rand = random.randint(0, 65535)

    hex_str = f"{timestamp:016x}{_id_counter:04x}{rand:04x}"
    # Convert hex string to base64
    bin_data = bytes.fromhex(hex_str)
    return _bin_to_base64(bin_data)


def _bin_to_base64(data: bytes) -> str:
    """Convert binary data to base64 string (StarUML style)."""
    result = []
    for i in range(0, len(data), 3):
        chunk = data[i:i + 3]
        a = chunk[0]
        b = chunk[1] if len(chunk) > 1 else None
        c = chunk[2] if len(chunk) > 2 else None

        result.append(ID_TABLE[a >> 2])
        if b is not None:
            result.append(ID_TABLE[((a << 4) & 63) | (b >> 4)])
        else:
            result.append(ID_TABLE[((a << 4) & 63)])
            result.append("=")
            continue

        if c is not None:
            result.append(ID_TABLE[((b << 2) & 63) | (c >> 6)])
            result.append(ID_TABLE[c & 63])
        else:
            result.append(ID_TABLE[((b << 2) & 63)])
            result.append("=")
    return "".join(result)


# ---------------------------------------------------------------------------
# Element creation helpers
# ---------------------------------------------------------------------------

def _make_element(type_name: str, **kwargs) -> dict:
    """Create a new element dict with _type, _id, and defaults."""
    elem = {"_type": type_name, "_id": generate_id()}
    # Track which keys are already set (so defaults don't overwrite)
    set_keys = {"_type", "_id"}
    # Apply defaults from metamodel (only for keys not in kwargs or already set)
    attrs = _get_all_attributes(type_name)
    for a in attrs:
        if "default" in a and a["name"] not in set_keys:
            default = a["default"]
            if a["kind"] in ("prim", "enum"):
                if isinstance(default, (str, int, float, bool)):
                    elem[a["name"]] = default
                    set_keys.add(a["name"])
    # Apply overrides
    elem.update(kwargs)
    return elem


# ---------------------------------------------------------------------------
# ClassDiagram — the main API
# ---------------------------------------------------------------------------

class ClassDiagram:
    """High-level API for manipulating a UML class diagram."""

    def __init__(self, parser: MdjParser):
        self._parser = parser
        self._model = parser.model
        self._diagram = parser.class_diagram

    @classmethod
    def load(cls, filepath: str) -> "ClassDiagram":
        parser = MdjParser().load(filepath)
        return cls(parser)

    @classmethod
    def create(cls, project_name: str = "UML", model_name: str = "Model",
               diagram_name: str = "Main") -> "ClassDiagram":
        """Create a new empty UML class diagram .mdj structure from scratch.

        Returns a ClassDiagram instance ready for adding classes, relationships, etc.
        Save with .save(filepath) when done.
        """
        project_id = generate_id()
        model_id = generate_id()
        diagram_id = generate_id()

        project = {
            "_type": "Project",
            "_id": project_id,
            "name": project_name,
            "ownedElements": [
                {
                    "_type": "UMLModel",
                    "_id": model_id,
                    "_parent": {"$ref": project_id},
                    "name": model_name,
                    "ownedElements": [
                        {
                            "_type": "UMLClassDiagram",
                            "_id": diagram_id,
                            "_parent": {"$ref": model_id},
                            "name": diagram_name,
                            "defaultDiagram": True,
                            "ownedViews": [],
                        }
                    ],
                }
            ],
            "documentVersion": 1,
        }

        parser = MdjParser()
        parser._parse(project)
        return cls(parser)

    def save(self, filepath: str):
        writer = MdjWriter(self._parser)
        writer.save(filepath)

    def dumps(self) -> str:
        writer = MdjWriter(self._parser)
        return writer.dumps()

    def save_as(self, filepath: str):
        """Save to a new file path."""
        self.save(filepath)

    # -----------------------------------------------------------------------
    # Query
    # -----------------------------------------------------------------------

    def list_classes(self) -> List[Dict[str, Any]]:
        """Return a list of all class-like elements."""
        return self._parser.classes_summary()

    def get_class(self, name: str) -> Optional[dict]:
        """Get a class model element by name."""
        for c in self._parser.get_diagram_classes():
            if c.get("name") == name:
                return c
        return None

    def find_class(self, name_or_id: str) -> Optional[dict]:
        """Find a class by name or ID."""
        by_id = self._parser.by_id(name_or_id)
        if by_id:
            return by_id
        return self.get_class(name_or_id)

    def list_relationships(self) -> List[Dict[str, Any]]:
        """Return all relationships in the model."""
        rels = []
        for r in self._parser.get_relationships():
            rel_type = r["_type"]
            info = {"id": r["_id"], "type": rel_type, "name": r.get("name", "")}
            if rel_type == "UMLAssociation":
                e1 = r.get("end1")
                e2 = r.get("end2")
                ref1 = e1.get("reference") if isinstance(e1, dict) else None
                ref2 = e2.get("reference") if isinstance(e2, dict) else None
                info["end1"] = ref1.get("name") if isinstance(ref1, dict) else str(ref1)
                info["end2"] = ref2.get("name") if isinstance(ref2, dict) else str(ref2)
            elif rel_type in ("UMLGeneralization", "UMLDependency", "UMLInterfaceRealization"):
                src = r.get("source")
                tgt = r.get("target")
                info["source"] = src.get("name") if isinstance(src, dict) else str(src)
                info["target"] = tgt.get("name") if isinstance(tgt, dict) else str(tgt)
            rels.append(info)
        return rels

    # -----------------------------------------------------------------------
    # Add class
    # -----------------------------------------------------------------------

    def add_class(
        self,
        name: str,
        attributes: Optional[List[Dict[str, Any]]] = None,
        operations: Optional[List[Dict[str, Any]]] = None,
        x: float = 320,
        y: float = 240,
        is_abstract: bool = False,
        stereotype: Optional[str] = None,
    ) -> dict:
        """
        Add a new class to the diagram.

        Returns the newly created class model element dict.

        attribute format: {"name": "attrName", "type": "String", "visibility": "private"}
        operation format: {"name": "opName", "visibility": "public", "parameters": [
                            {"name": "param1", "type": "String", "direction": "in"},
                            {"name": "ret", "type": "void", "direction": "return"}
                          ]}
        """
        model_elem = _make_element(
            "UMLClass",
            name=name,
            isAbstract=is_abstract,
            _parent=self._model,
            attributes=[],
            operations=[],
            receptions=[],
            behaviors=[],
            templateParameters=[],
        )
        if stereotype:
            model_elem["stereotype"] = stereotype

        # Add to model
        self._model["ownedElements"].append(model_elem)
        self._parser._by_id[model_elem["_id"]] = model_elem

        # Create attributes
        if attributes:
            for attr_def in attributes:
                self._add_attribute_to_model(model_elem, attr_def)

        # Create operations
        if operations:
            for op_def in operations:
                self._add_operation_to_model(model_elem, op_def)

        # Create view
        self._create_class_view(model_elem, x, y)

        return model_elem

    def _add_attribute_to_model(self, class_elem: dict, attr_def: Dict[str, Any]):
        attr = _make_element(
            "UMLAttribute",
            name=attr_def.get("name", ""),
            type=attr_def.get("type", ""),
            visibility=attr_def.get("visibility", "private"),
            isStatic=attr_def.get("isStatic", False),
            isDerived=attr_def.get("isDerived", False),
            multiplicity=attr_def.get("multiplicity", ""),
            defaultValue=attr_def.get("defaultValue", ""),
            _parent=class_elem,
        )
        class_elem.setdefault("attributes", []).append(attr)
        self._parser._by_id[attr["_id"]] = attr

    def _add_operation_to_model(self, class_elem: dict, op_def: Dict[str, Any]):
        op = _make_element(
            "UMLOperation",
            name=op_def.get("name", ""),
            visibility=op_def.get("visibility", "public"),
            isAbstract=op_def.get("isAbstract", False),
            isStatic=op_def.get("isStatic", False),
            parameters=[],
            _parent=class_elem,
        )
        for param_def in op_def.get("parameters", []):
            param = _make_element(
                "UMLParameter",
                name=param_def.get("name", ""),
                type=param_def.get("type", ""),
                direction=param_def.get("direction", "in"),
                _parent=op,
            )
            op.setdefault("parameters", []).append(param)
            self._parser._by_id[param["_id"]] = param
        class_elem.setdefault("operations", []).append(op)
        self._parser._by_id[op["_id"]] = op

    def _create_class_view(self, model_elem: dict, x: float, y: float):
        """Create a full UMLClassView hierarchy for a class model element."""
        # If model is abstract, adjust position
        prefix = ""
        if model_elem.get("stereotype"):
            prefix = f"«{model_elem['stereotype']}»\n"

        class_name = model_elem["name"]
        has_attributes = len(model_elem.get("attributes", [])) > 0
        has_operations = len(model_elem.get("operations", [])) > 0

        n_attrs = len(model_elem.get("attributes", []))
        n_ops = len(model_elem.get("operations", []))

        font = "Arial;13;0"
        line_height = 13

        # Calculate widths and heights
        name_width = max(200, len(class_name) * 8 + 20) if class_name else 200
        attr_widths = [len(self._format_attribute(a)) * 8 + 20 for a in model_elem.get("attributes", [])]
        op_widths = [len(self._format_operation(o)) * 8 + 20 for o in model_elem.get("operations", [])]
        all_widths = [name_width] + attr_widths + op_widths
        content_width = max(all_widths) if all_widths else 200
        view_width = content_width + 10
        compartment_width = content_width

        name_height = 25
        attr_height = max(5, n_attrs * (line_height + 2) + 5) if n_attrs > 0 else 5
        op_height = max(5, n_ops * (line_height + 2) + 5) if n_ops > 0 else 5
        total_height = name_height + attr_height + op_height

        # Create compartments
        # --- Compartment 1: Name ---
        name_compartment = _make_element(
            "UMLNameCompartmentView",
            _parent=None,
            model=model_elem,
            subViews=[],
            font=font,
            parentStyle=True,
            left=x,
            top=y,
            width=compartment_width,
            height=name_height,
        )

        # Stereotype label
        stereo_text = ""
        if isinstance(model_elem.get("stereotype"), str) and model_elem["stereotype"]:
            stereo_text = f"«{model_elem['stereotype']}»"

        stereo_label = _make_element(
            "LabelView",
            _parent=name_compartment,
            visible=bool(stereo_text),
            font=font,
            parentStyle=True,
            left=x + 5,
            top=y + 2,
            width=compartment_width - 10,
            height=line_height if stereo_text else 0,
            text=stereo_text,
        )
        name_compartment["subViews"].append(stereo_label)
        name_compartment["stereotypeLabel"] = stereo_label

        # Name label
        name_label = _make_element(
            "LabelView",
            _parent=name_compartment,
            font="Arial;13;1",
            parentStyle=True,
            left=x + 5,
            top=y + (line_height + 2) if stereo_text else y + 2,
            width=compartment_width - 10,
            height=line_height,
            text=class_name,
        )
        name_compartment["subViews"].append(name_label)
        name_compartment["nameLabel"] = name_label

        # Namespace label (hidden)
        ns_label = _make_element(
            "LabelView",
            _parent=name_compartment,
            visible=False,
            font=font,
            parentStyle=True,
            left=x + 5,
            top=y,
            width=200,
            height=line_height,
            text=f"(from {self._model.get('name', 'Model')})",
        )
        name_compartment["subViews"].append(ns_label)
        name_compartment["namespaceLabel"] = ns_label

        # Property label (hidden)
        prop_label = _make_element(
            "LabelView",
            _parent=name_compartment,
            visible=False,
            font=font,
            parentStyle=True,
            left=x + 5,
            top=y,
            height=line_height,
            horizontalAlignment=1,
        )
        name_compartment["subViews"].append(prop_label)
        name_compartment["propertyLabel"] = prop_label

        self._parser._by_id[name_compartment["_id"]] = name_compartment
        self._parser._by_id[stereo_label["_id"]] = stereo_label
        self._parser._by_id[name_label["_id"]] = name_label
        self._parser._by_id[ns_label["_id"]] = ns_label
        self._parser._by_id[prop_label["_id"]] = prop_label

        # --- Compartment 2: Attributes ---
        attrs_y = y + name_height
        attr_compartment = _make_element(
            "UMLAttributeCompartmentView",
            _parent=None,
            model=model_elem,
            subViews=[],
            font=font,
            parentStyle=True,
            left=x,
            top=attrs_y,
            width=compartment_width,
            height=attr_height,
        )

        for idx, attr_model in enumerate(model_elem.get("attributes", [])):
            attr_text = self._format_attribute(attr_model)
            attr_view = _make_element(
                "UMLAttributeView",
                _parent=attr_compartment,
                model=attr_model,
                font=font,
                parentStyle=True,
                left=x + 5,
                top=attrs_y + 5 + idx * (line_height + 2),
                width=compartment_width - 10,
                height=line_height,
                text=attr_text,
                horizontalAlignment=0,
            )
            attr_compartment["subViews"].append(attr_view)
            self._parser._by_id[attr_view["_id"]] = attr_view

        self._parser._by_id[attr_compartment["_id"]] = attr_compartment

        # --- Compartment 3: Operations ---
        ops_y = attrs_y + attr_height
        op_compartment = _make_element(
            "UMLOperationCompartmentView",
            _parent=None,
            model=model_elem,
            subViews=[],
            font=font,
            parentStyle=True,
            left=x,
            top=ops_y,
            width=compartment_width,
            height=op_height,
        )

        for idx, op_model in enumerate(model_elem.get("operations", [])):
            op_text = self._format_operation(op_model)
            op_view = _make_element(
                "UMLOperationView",
                _parent=op_compartment,
                model=op_model,
                font=font,
                parentStyle=True,
                left=x + 5,
                top=ops_y + 5 + idx * (line_height + 2),
                width=compartment_width - 10,
                height=line_height,
                text=op_text,
                horizontalAlignment=0,
            )
            op_compartment["subViews"].append(op_view)
            self._parser._by_id[op_view["_id"]] = op_view

        self._parser._by_id[op_compartment["_id"]] = op_compartment

        # --- Hidden compartments ---
        recep_compartment = _make_element(
            "UMLReceptionCompartmentView",
            _parent=None,
            model=model_elem,
            visible=False,
            font=font,
            parentStyle=True,
            left=x,
            top=y,
            width=10,
            height=10,
        )
        self._parser._by_id[recep_compartment["_id"]] = recep_compartment

        template_compartment = _make_element(
            "UMLTemplateParameterCompartmentView",
            _parent=None,
            model=model_elem,
            visible=False,
            font=font,
            parentStyle=True,
            left=x,
            top=y,
            width=10,
            height=10,
        )
        self._parser._by_id[template_compartment["_id"]] = template_compartment

        # --- ClassView ---
        class_view = _make_element(
            "UMLClassView",
            _parent=self._diagram,
            model=model_elem,
            subViews=[
                name_compartment, attr_compartment, op_compartment,
                recep_compartment, template_compartment,
            ],
            font=font,
            parentStyle=False,
            containerChangeable=True,
            left=x,
            top=y,
            width=view_width,
            height=total_height,
            nameCompartment=name_compartment,
            attributeCompartment=attr_compartment,
            operationCompartment=op_compartment,
            receptionCompartment=recep_compartment,
            templateParameterCompartment=template_compartment,
        )

        # Fix _parent back-references for compartments
        name_compartment["_parent"] = class_view
        attr_compartment["_parent"] = class_view
        op_compartment["_parent"] = class_view
        recep_compartment["_parent"] = class_view
        template_compartment["_parent"] = class_view

        self._diagram.setdefault("ownedViews", []).append(class_view)
        self._parser._by_id[class_view["_id"]] = class_view

    @staticmethod
    def _format_attribute(attr: dict) -> str:
        """Format an attribute as UML text line."""
        name = attr.get("name", "")
        vis = attr.get("visibility", "public")
        vis_map = {"public": "+", "protected": "#", "private": "-", "package": "~"}
        vis_str = vis_map.get(vis, "+")
        is_static = attr.get("isStatic", False)
        is_derived = attr.get("isDerived", False)
        prefix = ""
        if is_derived:
            prefix += "/"
        if is_static:
            prefix += "$" if not prefix else ""

        type_info = attr.get("type", "")
        if isinstance(type_info, dict):
            type_info = type_info.get("name", "")
        type_str = f": {type_info}" if type_info else ""

        mult = attr.get("multiplicity", "")
        mult_str = f"[{mult}]" if mult else ""

        default = attr.get("defaultValue", "")
        default_str = f" = {default}" if default else ""

        return f"{vis_str}{prefix}{name}{type_str}{mult_str}{default_str}"

    @staticmethod
    def _format_operation(op: dict) -> str:
        """Format an operation as UML text line."""
        name = op.get("name", "")
        vis = op.get("visibility", "public")
        vis_map = {"public": "+", "protected": "#", "private": "-", "package": "~"}
        vis_str = vis_map.get(vis, "+")
        is_static = op.get("isStatic", False)
        is_abstract = op.get("isAbstract", False)
        prefix = ""
        if is_abstract:
            prefix += "@"
        if is_static:
            prefix += "$" if not prefix else ""

        params = []
        ret_type = ""
        for p in op.get("parameters", []):
            p_name = p.get("name", "")
            p_type = p.get("type", "")
            if isinstance(p_type, dict):
                p_type = p_type.get("name", "")
            p_dir = p.get("direction", "in")
            if p_dir == "return":
                ret_type = p_type
            else:
                param_str = p_name
                if p_type:
                    param_str += f": {p_type}"
                if p.get("defaultValue"):
                    param_str += f" = {p['defaultValue']}"
                if p_dir == "inout":
                    param_str = "inout " + param_str
                elif p_dir == "out":
                    param_str = "out " + param_str
                params.append(param_str)

        params_str = ", ".join(params)
        if any(
            p.get("direction", "in") == "return"
            for p in op.get("parameters", [])
        ):
            ret_str = f": {ret_type}" if ret_type else ""
        else:
            # infer from operation text if no explicit return param
            ret_str = ""

        is_query = op.get("isQuery", False)
        query_str = " {query}" if is_query else ""

        return f"{prefix}{vis_str}{name}({params_str}){ret_str}{query_str}"

    # -----------------------------------------------------------------------
    # Remove class
    # -----------------------------------------------------------------------

    def remove_class(self, name_or_id: str) -> bool:
        """Remove a class and its view from the diagram. Also removes associated relationships."""
        class_elem = self.find_class(name_or_id)
        if not class_elem:
            return False

        cid = class_elem["_id"]

        # Remove relationships involving this class
        rels = self._parser.get_relationships()
        for rel in rels:
            related = False
            if rel["_type"] == "UMLAssociation":
                e1 = rel.get("end1")
                e2 = rel.get("end2")
                ref1 = e1.get("reference") if isinstance(e1, dict) else None
                ref2 = e2.get("reference") if isinstance(e2, dict) else None
                if (isinstance(ref1, dict) and ref1["_id"] == cid) or \
                   (isinstance(ref2, dict) and ref2["_id"] == cid):
                    related = True
            elif rel["_type"] in ("UMLGeneralization", "UMLDependency", "UMLInterfaceRealization"):
                src = rel.get("source")
                tgt = rel.get("target")
                if (isinstance(src, dict) and src["_id"] == cid) or \
                   (isinstance(tgt, dict) and tgt["_id"] == cid):
                    related = True
            if related:
                self._remove_relationship(rel)

        # Remove view
        view = self._parser.get_view_for_model(cid)
        if view:
            self._remove_view_recursive(view)

        # Remove model element
        self._model["ownedElements"].remove(class_elem)
        del self._parser._by_id[cid]
        return True

    def _remove_relationship(self, rel: dict):
        """Remove a relationship and its view."""
        # Remove view
        rel_view = self._parser.get_relationship_view(rel["_id"])
        if rel_view:
            self._remove_view_recursive(rel_view)

        # Remove model
        try:
            self._model["ownedElements"].remove(rel)
        except ValueError:
            pass
        if rel["_id"] in self._parser._by_id:
            del self._parser._by_id[rel["_id"]]

    def _remove_view_recursive(self, view: dict):
        """Remove a view and all its sub-views from the diagram and parser."""
        for sub in view.get("subViews", []):
            if isinstance(sub, dict):
                self._remove_view_recursive(sub)
        try:
            self._diagram["ownedViews"].remove(view)
        except ValueError:
            pass
        if view["_id"] in self._parser._by_id:
            del self._parser._by_id[view["_id"]]

    # -----------------------------------------------------------------------
    # Add attribute to class
    # -----------------------------------------------------------------------

    def add_attribute(self, class_name_or_id: str, attr_def: Dict[str, Any]) -> Optional[dict]:
        """Add an attribute to a class and update its view."""
        class_elem = self.find_class(class_name_or_id)
        if not class_elem:
            return None

        self._add_attribute_to_model(class_elem, attr_def)
        self._rebuild_class_view(class_elem)
        return class_elem["attributes"][-1]

    # -----------------------------------------------------------------------
    # Remove attribute from class
    # -----------------------------------------------------------------------

    def remove_attribute(self, class_name_or_id: str, attr_name: str) -> bool:
        """Remove an attribute from a class by name."""
        class_elem = self.find_class(class_name_or_id)
        if not class_elem:
            return False
        for i, a in enumerate(class_elem.get("attributes", [])):
            if isinstance(a, dict) and a.get("name") == attr_name:
                class_elem["attributes"].pop(i)
                if a["_id"] in self._parser._by_id:
                    del self._parser._by_id[a["_id"]]
                self._rebuild_class_view(class_elem)
                return True
        return False

    # -----------------------------------------------------------------------
    # Add operation to class
    # -----------------------------------------------------------------------

    def add_operation(self, class_name_or_id: str, op_def: Dict[str, Any]) -> Optional[dict]:
        """Add an operation to a class and update its view."""
        class_elem = self.find_class(class_name_or_id)
        if not class_elem:
            return None

        self._add_operation_to_model(class_elem, op_def)
        self._rebuild_class_view(class_elem)
        return class_elem["operations"][-1]

    # -----------------------------------------------------------------------
    # Remove operation from class
    # -----------------------------------------------------------------------

    def remove_operation(self, class_name_or_id: str, op_name: str) -> bool:
        """Remove an operation from a class by name."""
        class_elem = self.find_class(class_name_or_id)
        if not class_elem:
            return False
        for i, o in enumerate(class_elem.get("operations", [])):
            if isinstance(o, dict) and o.get("name") == op_name:
                class_elem["operations"].pop(i)
                if o["_id"] in self._parser._by_id:
                    del self._parser._by_id[o["_id"]]
                self._rebuild_class_view(class_elem)
                return True
        return False

    # -----------------------------------------------------------------------
    # Edit property
    # -----------------------------------------------------------------------

    def edit_property(self, elem_id: str, property_name: str, value: Any) -> bool:
        """Set a property on any element by ID. Returns True on success."""
        elem = self._parser.by_id(elem_id)
        if not elem:
            return False
        elem[property_name] = value
        return True

    def rename_class(self, name_or_id: str, new_name: str) -> bool:
        """Rename a class model and update its view labels."""
        class_elem = self.find_class(name_or_id)
        if not class_elem:
            return False
        class_elem["name"] = new_name
        self._rebuild_class_view(class_elem)
        return True

    # -----------------------------------------------------------------------
    # Add relationships
    # -----------------------------------------------------------------------

    def add_association(
        self,
        class_a_name: str,
        class_b_name: str,
        end1_name: str = "",
        end2_name: str = "",
        end1_multiplicity: str = "",
        end2_multiplicity: str = "",
        end1_aggregation: str = "none",
        end2_aggregation: str = "none",
        end1_navigable: str = "unspecified",
        end2_navigable: str = "unspecified",
    ) -> Optional[dict]:
        """Add an association between two classes."""
        class_a = self.get_class(class_a_name)
        class_b = self.get_class(class_b_name)
        if not class_a or not class_b:
            return None

        rel = _make_element(
            "UMLAssociation",
            _parent=self._model,
            name="",
        )

        end1 = _make_element(
            "UMLAssociationEnd",
            _parent=rel,
            reference=class_a,
            name=end1_name,
            multiplicity=end1_multiplicity,
            aggregation=end1_aggregation,
            navigable=end1_navigable,
        )
        end2 = _make_element(
            "UMLAssociationEnd",
            _parent=rel,
            reference=class_b,
            name=end2_name,
            multiplicity=end2_multiplicity,
            aggregation=end2_aggregation,
            navigable=end2_navigable,
        )
        rel["end1"] = end1
        rel["end2"] = end2

        self._model["ownedElements"].append(rel)
        self._parser._by_id[rel["_id"]] = rel
        self._parser._by_id[end1["_id"]] = end1
        self._parser._by_id[end2["_id"]] = end2

        # Create association view
        view_a = self._parser.get_view_for_model(class_a["_id"])
        view_b = self._parser.get_view_for_model(class_b["_id"])

        if view_a and view_b:
            ax = view_a.get("left", 0) + view_a.get("width", 0) / 2
            ay = view_a.get("top", 0) + view_a.get("height", 0) / 2
            bx = view_b.get("left", 0) + view_b.get("width", 0) / 2
            by = view_b.get("top", 0) + view_b.get("height", 0) / 2

            assoc_view = _make_element(
                "UMLAssociationView",
                _parent=self._diagram,
                model=rel,
                tail=view_a,
                head=view_b,
                font=rel.get("font", "Arial;13;0"),
                parentStyle=True,
                lineStyle=0,
            )
            # points
            assoc_view["points"] = f"{ax},{ay};{bx},{by}"
            self._diagram.setdefault("ownedViews", []).append(assoc_view)
            self._parser._by_id[assoc_view["_id"]] = assoc_view

        return rel

    def add_generalization(
        self,
        child_name: str,
        parent_name: str,
        discriminator: str = "",
    ) -> Optional[dict]:
        """Add a generalization relationship (child inherits from parent)."""
        child = self.get_class(child_name)
        parent = self.get_class(parent_name)
        if not child or not parent:
            return None

        rel = _make_element(
            "UMLGeneralization",
            _parent=self._model,
            source=child,
            target=parent,
            discriminator=discriminator,
            name="",
        )

        self._model["ownedElements"].append(rel)
        self._parser._by_id[rel["_id"]] = rel

        view_child = self._parser.get_view_for_model(child["_id"])
        view_parent = self._parser.get_view_for_model(parent["_id"])

        if view_child and view_parent:
            cx = view_child.get("left", 0) + view_child.get("width", 0) / 2
            cy = view_child.get("top", 0)
            px = view_parent.get("left", 0) + view_parent.get("width", 0) / 2
            py = view_parent.get("top", 0) + view_parent.get("height", 0)

            gen_view = _make_element(
                "UMLGeneralizationView",
                _parent=self._diagram,
                model=rel,
                tail=view_child,
                head=view_parent,
                font="Arial;13;0",
                parentStyle=True,
                lineStyle=0,
            )
            gen_view["points"] = f"{cx},{cy};{px},{py}"
            self._diagram.setdefault("ownedViews", []).append(gen_view)
            self._parser._by_id[gen_view["_id"]] = gen_view

        return rel

    def add_dependency(
        self,
        source_name: str,
        target_name: str,
        stereotype: str = "",
        mapping: str = "",
    ) -> Optional[dict]:
        """Add a dependency relationship (dashed arrow)."""
        src = self.get_class(source_name)
        tgt = self.get_class(target_name)
        if not src or not tgt:
            return None

        rel = _make_element(
            "UMLDependency",
            _parent=self._model,
            source=src,
            target=tgt,
            mapping=mapping,
            name="",
        )
        if stereotype:
            rel["stereotype"] = stereotype

        self._model["ownedElements"].append(rel)
        self._parser._by_id[rel["_id"]] = rel

        view_src = self._parser.get_view_for_model(src["_id"])
        view_tgt = self._parser.get_view_for_model(tgt["_id"])

        if view_src and view_tgt:
            sx = view_src.get("left", 0) + view_src.get("width", 0) / 2
            sy = view_src.get("top", 0) + view_src.get("height", 0) / 2
            tx = view_tgt.get("left", 0) + view_tgt.get("width", 0) / 2
            ty = view_tgt.get("top", 0) + view_tgt.get("height", 0) / 2

            dep_view = _make_element(
                "UMLDependencyView",
                _parent=self._diagram,
                model=rel,
                tail=view_src,
                head=view_tgt,
                font="Arial;13;0",
                parentStyle=True,
                lineStyle=0,
            )
            dep_view["points"] = f"{sx},{sy};{tx},{ty}"
            self._diagram.setdefault("ownedViews", []).append(dep_view)
            self._parser._by_id[dep_view["_id"]] = dep_view

        return rel

    def remove_relationship(self, relationship_id: str) -> bool:
        """Remove a relationship by ID."""
        for rel in self._parser.get_relationships():
            if rel["_id"] == relationship_id:
                self._remove_relationship(rel)
                return True
        return False

    # -----------------------------------------------------------------------
    # View rebuilding
    # -----------------------------------------------------------------------

    def _rebuild_class_view(self, class_elem: dict):
        """Rebuild the view for a class after its attributes/operations change."""
        cid = class_elem["_id"]
        old_view = self._parser.get_view_for_model(cid)
        if old_view:
            old_x = old_view.get("left", 320)
            old_y = old_view.get("top", 240)
            self._remove_view_recursive(old_view)
        else:
            old_x = 320
            old_y = 240
        self._create_class_view(class_elem, old_x, old_y)

    # -----------------------------------------------------------------------
    # Auto-layout
    # -----------------------------------------------------------------------

    def auto_layout(self, start_x: float = 80, start_y: float = 80,
                    layer_spacing: float = 80, node_spacing: float = 80):
        """Auto-layout all class views using relationship-aware layered layout.

        Generalization edges define a hierarchy (parents above children).
        Association edges attract connected classes together within a layer.
        """
        classes = self._parser.get_diagram_classes()
        if not classes:
            return

        class_by_id = {c["_id"]: c for c in classes}
        view_by_id = {}
        for c in classes:
            v = self._parser.get_view_for_model(c["_id"])
            if v:
                view_by_id[c["_id"]] = v

        all_ids = set(class_by_id.keys())

        # --- Build relationship graph ---
        gen_parent_of = {}    # child_id -> parent_id
        gen_children_of = {}  # parent_id -> [child_id]
        assoc_neighbors = {}  # id -> set(neighbor_ids)
        dep_neighbors = {}    # id -> set(neighbor_ids)

        for cid in all_ids:
            gen_children_of.setdefault(cid, [])
            assoc_neighbors.setdefault(cid, set())
            dep_neighbors.setdefault(cid, set())

        for rel in self._parser.get_relationships():
            if rel["_type"] == "UMLGeneralization":
                sid = _ref_id(rel.get("source"))
                tid = _ref_id(rel.get("target"))
                if sid in all_ids and tid in all_ids:
                    gen_parent_of[sid] = tid
                    gen_children_of.setdefault(tid, []).append(sid)
            elif rel["_type"] == "UMLAssociation":
                id1, id2 = _association_end_ids(rel)
                if id1 in all_ids and id2 in all_ids:
                    assoc_neighbors[id1].add(id2)
                    assoc_neighbors[id2].add(id1)
            elif rel["_type"] in ("UMLDependency", "UMLInterfaceRealization",
                                   "UMLRealization", "UMLAbstraction"):
                sid = _ref_id(rel.get("source"))
                tid = _ref_id(rel.get("target"))
                if sid in all_ids and tid in all_ids:
                    dep_neighbors.setdefault(sid, set()).add(tid)
                    dep_neighbors.setdefault(tid, set()).add(sid)

        # --- Layer assignment ---
        # Priority 1: generalizations define the hierarchy.
        # Priority 2: if no generalizations, use BFS on the association graph
        #   to discover natural layers. Root = most-connected node.
        layer = {}  # id -> depth

        if gen_parent_of:
            # Generalization-based layering
            child_ids = set(gen_parent_of.keys())
            roots = all_ids - child_ids
            for cid, pid in list(gen_parent_of.items()):
                if pid not in all_ids:
                    roots.add(cid)
                    del gen_parent_of[cid]
            queue = [(rid, 0) for rid in roots]
            visited = set()
            while queue:
                cid, depth = queue.pop(0)
                if cid in visited:
                    continue
                visited.add(cid)
                layer[cid] = max(layer.get(cid, 0), depth)
                for child in gen_children_of.get(cid, []):
                    queue.append((child, depth + 1))
            for cid in all_ids:
                if cid not in layer:
                    layer[cid] = 0
        else:
            # No generalizations: BFS through association/dependency graph
            # Pick the most-connected node as root
            def _total_degree(cid):
                return len(assoc_neighbors.get(cid, set())) + len(dep_neighbors.get(cid, set()))
            degrees = [(cid, _total_degree(cid)) for cid in all_ids]
            degrees.sort(key=lambda x: -x[1])
            # BFS from all unvisited nodes, starting with highest-degree
            queue = [(cid, 0) for cid, _ in degrees]
            visited = set()
            while queue:
                cid, depth = queue.pop(0)
                if cid in visited:
                    continue
                visited.add(cid)
                layer[cid] = max(layer.get(cid, 0), depth)
                # Expand through both associations and dependencies
                for nb in assoc_neighbors.get(cid, set()):
                    queue.append((nb, depth + 1))
                for nb in dep_neighbors.get(cid, set()):
                    queue.append((nb, depth + 1))

            # If BFS produced too many layers (deep chain), cap at readable depth
            # and use pancake sort to re-layer very deep chains.
            # Also: limit max width per layer to ~800px
            MAX_LAYER_WIDTH = 1200
            # Collapse: if layer 0 has all classes or very wide, split by degree
            max_layer_depth = max(layer.values()) if layer else 0
            if max_layer_depth == 0 and len(all_ids) > 3:
                # All on one row — forcibly split by degree bands
                sorted_ids = [cid for cid, _ in degrees]
                # Use BFS from multiple seeds to create natural layers
                layer.clear()
                remaining = set(sorted_ids)
                current_layer = 0
                while remaining:
                    seed = max(remaining, key=lambda cid: _total_degree(cid))
                    remaining.remove(seed)
                    layer[seed] = current_layer
                    frontier = [seed]
                    found = set()
                    while frontier and len(found) < 6:
                        cur = frontier.pop(0)
                        for nb in assoc_neighbors.get(cur, set()):
                            if nb in remaining and nb not in found:
                                found.add(nb)
                                remaining.remove(nb)
                                layer[nb] = current_layer
                                frontier.append(nb)
                        for nb in dep_neighbors.get(cur, set()):
                            if nb in remaining and nb not in found:
                                found.add(nb)
                                remaining.remove(nb)
                                layer[nb] = current_layer
                                frontier.append(nb)
                    current_layer += 1

        # Group by layer
        max_layer = max(layer.values()) if layer else 0
        layer_ids = {d: [] for d in range(max_layer + 1)}
        for cid, d in layer.items():
            layer_ids[d].append(cid)

        # --- Position assignment ---
        # Strategy: place classes within each layer from left to right,
        # grouping connected classes together.
        pos_by_id = {}  # id -> (x, y)

        current_y = start_y
        for d in range(max_layer + 1):
            ids = layer_ids[d]
            if not ids:
                continue

            # Compute max height in this layer
            max_h = max((view_by_id.get(cid, {}).get("height", 100) for cid in ids), default=100)

            # Order: first place classes with gen children (important nodes),
            # then sort by association connectivity.
            def _order_key(cid):
                has_children = 1 if len(gen_children_of.get(cid, [])) > 0 else 0
                n_assoc = len(assoc_neighbors.get(cid, set()))
                return (-has_children, -n_assoc)

            ordered_ids = sorted(ids, key=_order_key)

            # Build clusters: connected components via associations within this layer
            id_set = set(ordered_ids)
            clusters = []
            unvisited = set(ordered_ids)
            while unvisited:
                seed = unvisited.pop()
                cluster = [seed]
                stack = [seed]
                while stack:
                    cur = stack.pop()
                    for nb in assoc_neighbors.get(cur, set()):
                        if nb in unvisited:
                            unvisited.remove(nb)
                            cluster.append(nb)
                            stack.append(nb)
                clusters.append(cluster)

            # Position clusters left to right
            cur_x = start_x
            final_x = {}  # id -> x
            for cluster in clusters:
                cluster_w = 0
                for cid in cluster:
                    v = view_by_id.get(cid, {})
                    cluster_w += v.get("width", 200)
                cluster_w += (len(cluster) - 1) * node_spacing

                cx = cur_x
                for cid in cluster:
                    v = view_by_id.get(cid, {})
                    w = v.get("width", 200)
                    final_x[cid] = cx
                    cx += w + node_spacing
                cur_x += cluster_w + node_spacing * 2

            for cid in ordered_ids:
                pos_by_id[cid] = (final_x[cid], current_y)

            current_y += max_h + layer_spacing

        # --- Apply new positions ---
        for cid, (new_x, new_y) in pos_by_id.items():
            view = view_by_id.get(cid)
            if not view:
                continue
            old_x = view.get("left") or 0
            old_y = view.get("top") or 0
            dx = new_x - old_x
            dy = new_y - old_y
            self._shift_view(view, dx, dy)

        # Update relationship view endpoints
        self._update_relationship_views(class_by_id, view_by_id)

        # Ensure all attribute/operation views are left-aligned
        self._ensure_left_alignment()

    def _shift_view(self, view: dict, dx: float, dy: float):
        """Recursively shift a view and all sub-views by (dx, dy)."""
        if "left" in view:
            view["left"] = view["left"] + dx
        if "top" in view:
            view["top"] = view["top"] + dy
        for sub in view.get("subViews", []):
            if isinstance(sub, dict):
                self._shift_view(sub, dx, dy)

    def _update_relationship_views(self, class_by_id: dict, view_by_id: dict):
        """Update edge view endpoints after moving classes."""
        for rel in self._parser.get_relationships():
            rv = self._parser.get_relationship_view(rel["_id"])
            if not rv:
                continue

            # Get tail and head class IDs
            tail_id = head_id = None
            if rel["_type"] == "UMLAssociation":
                e1 = rel.get("end1")
                e2 = rel.get("end2")
                ref1 = e1.get("reference") if isinstance(e1, dict) else None
                ref2 = e2.get("reference") if isinstance(e2, dict) else None
                tail_id = ref1.get("_id") if isinstance(ref1, dict) else None
                head_id = ref2.get("_id") if isinstance(ref2, dict) else None
            elif rel["_type"] in ("UMLGeneralization", "UMLDependency", "UMLInterfaceRealization"):
                src = rel.get("source")
                tgt = rel.get("target")
                tail_id = src.get("_id") if isinstance(src, dict) else None
                head_id = tgt.get("_id") if isinstance(tgt, dict) else None

            if not tail_id or not head_id:
                continue
            tv = view_by_id.get(tail_id)
            hv = view_by_id.get(head_id)
            if not tv or not hv:
                continue

            # Update tail/head refs
            rv["tail"] = tv
            rv["head"] = hv
            # Update points to connect centers
            tx = tv.get("left", 0) + tv.get("width", 0) / 2
            ty = tv.get("top", 0) + tv.get("height", 0) / 2
            hx = hv.get("left", 0) + hv.get("width", 0) / 2
            hy = hv.get("top", 0) + hv.get("height", 0) / 2
            rv["points"] = f"{tx},{ty};{hx},{hy}"

            # Shift edge sub-views
            if "subViews" in rv:
                for sub in rv["subViews"]:
                    if isinstance(sub, dict):
                        self._shift_view(sub, 0, 0)  # Keep relative positions

    def _ensure_left_alignment(self):
        """Ensure all attribute and operation view labels have horizontalAlignment=0 (left)."""
        for view in self._parser.get_diagram_views():
            if view.get("_type") in ("UMLClassView", "UMLInterfaceView", "UMLEnumerationView"):
                for sub in view.get("subViews", []):
                    if not isinstance(sub, dict):
                        continue
                    st = sub.get("_type", "")
                    if st in ("UMLAttributeCompartmentView", "UMLOperationCompartmentView",
                              "UMLEnumerationLiteralCompartmentView"):
                        for sv in sub.get("subViews", []):
                            if isinstance(sv, dict):
                                sv["horizontalAlignment"] = 0


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _ref_id(val) -> str:
    """Extract _id from a value that may be a string, a ref dict, or a resolved element."""
    if isinstance(val, dict):
        return val.get("_id", "")
    return val if isinstance(val, str) else ""


def _association_end_ids(rel: dict) -> tuple:
    """Get both end class IDs from an association."""
    e1 = rel.get("end1")
    e2 = rel.get("end2")
    ref1 = e1.get("reference") if isinstance(e1, dict) else None
    ref2 = e2.get("reference") if isinstance(e2, dict) else None
    id1 = ref1.get("_id") if isinstance(ref1, dict) else ""
    id2 = ref2.get("_id") if isinstance(ref2, dict) else ""
    return id1, id2
