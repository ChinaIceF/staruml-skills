"""
StarUML .mdj file parser.

Parses the JSON structure into an in-memory representation with:
- ID-indexed map of all elements
- Resolved $ref references
- Tree traversal helpers
- Type-checking helpers
"""

import json
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union


# ---------------------------------------------------------------------------
# Metamodel registry — built from StarUML's metamodel.json
# ---------------------------------------------------------------------------
# Attribute kind constants
AK_PRIM = "prim"
AK_ENUM = "enum"
AK_REF = "ref"
AK_REFS = "refs"
AK_OBJ = "obj"
AK_OBJS = "objs"
AK_VAR = "var"
AK_CUSTOM = "custom"

# Full metamodel definitions extracted from the source code.
# Each entry: { "super": str|None, "attributes": [{name, kind, type, default?, ...}], "view": str|None }
METAMODEL: Dict[str, dict] = {}


def _build_metamodel():
    """Build the complete metamodel registry from the StarUML metamodel.json definitions."""
    # Base core types
    entries = []

    # === Core types ===
    entries.append(("Element", {
        "super": None,
        "attributes": [
            {"name": "_id", "kind": AK_PRIM, "type": "String", "transient": True, "default": ""},
            {"name": "_parent", "kind": AK_REF, "type": "Element", "transient": True},
        ]
    }))
    entries.append(("Model", {
        "super": "Element",
        "attributes": [
            {"name": "name", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "ownedElements", "kind": AK_OBJS, "type": "Model"},
        ]
    }))
    entries.append(("Project", {
        "super": "Model",
        "attributes": [
            {"name": "documentVersion", "kind": AK_PRIM, "type": "Integer", "default": 0},
        ]
    }))
    entries.append(("Tag", {
        "super": "Model",
        "attributes": [
            {"name": "kind", "kind": AK_PRIM, "type": "String", "default": "string"},
            {"name": "value", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "reference", "kind": AK_REF, "type": "Model"},
            {"name": "checked", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "number", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "options", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "hidden", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("ExtensibleModel", {
        "super": "Model",
        "attributes": [
            {"name": "documentation", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "tags", "kind": AK_OBJS, "type": "Tag"},
        ]
    }))
    entries.append(("Relationship", {"super": "ExtensibleModel", "attributes": []}))
    entries.append(("DirectedRelationship", {
        "super": "Relationship",
        "attributes": [
            {"name": "target", "kind": AK_REF, "type": "Model"},
            {"name": "source", "kind": AK_REF, "type": "Model"},
        ]
    }))
    entries.append(("RelationshipEnd", {
        "super": "ExtensibleModel",
        "attributes": [
            {"name": "reference", "kind": AK_REF, "type": "Model"},
        ]
    }))
    entries.append(("UndirectedRelationship", {
        "super": "Relationship",
        "attributes": [
            {"name": "end1", "kind": AK_OBJ, "type": "RelationshipEnd"},
            {"name": "end2", "kind": AK_OBJ, "type": "RelationshipEnd"},
        ]
    }))
    entries.append(("View", {
        "super": "Element",
        "attributes": [
            {"name": "model", "kind": AK_REF, "type": "Model"},
            {"name": "subViews", "kind": AK_OBJS, "type": "View"},
            {"name": "containerView", "kind": AK_REF, "type": "View"},
            {"name": "containedViews", "kind": AK_OBJS, "type": "View"},
            {"name": "visible", "kind": AK_PRIM, "type": "Boolean", "default": True},
            {"name": "enabled", "kind": AK_PRIM, "type": "Boolean", "default": True},
            {"name": "selected", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "selectable", "kind": AK_PRIM, "type": "Integer", "default": 1},
            {"name": "lineColor", "kind": AK_PRIM, "type": "String", "default": "#000000"},
            {"name": "fillColor", "kind": AK_PRIM, "type": "String", "default": "#ffffff"},
            {"name": "fontColor", "kind": AK_PRIM, "type": "String", "default": "#000000"},
            {"name": "font", "kind": AK_CUSTOM, "type": "Font", "default": "Arial;13;0"},
            {"name": "parentStyle", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "showShadow", "kind": AK_PRIM, "type": "Boolean", "default": True},
            {"name": "containerChangeable", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "containerExtending", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "zIndex", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "selectZIndex", "kind": AK_PRIM, "type": "Integer", "default": 0},
        ]
    }))
    entries.append(("NodeView", {
        "super": "View",
        "attributes": [
            {"name": "left", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "top", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "width", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "height", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "minWidth", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "minHeight", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "sizable", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "movable", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "autoResize", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("EdgeView", {
        "super": "View",
        "attributes": [
            {"name": "tail", "kind": AK_REF, "type": "View"},
            {"name": "head", "kind": AK_REF, "type": "View"},
            {"name": "points", "kind": AK_CUSTOM, "type": "Points"},
            {"name": "lineStyle", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "tailStyle", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "headStyle", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "tailDecorator", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "headDecorator", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "tailLabel", "kind": AK_REF, "type": "LabelView"},
            {"name": "headLabel", "kind": AK_REF, "type": "LabelView"},
            {"name": "lineLabel", "kind": AK_REF, "type": "LabelView"},
        ]
    }))
    entries.append(("LabelView", {
        "super": "NodeView",
        "attributes": [
            {"name": "text", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "horizontalAlignment", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "verticalAlignment", "kind": AK_PRIM, "type": "Integer", "default": 0},
            {"name": "wordWrap", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("Diagram", {
        "super": "Model",
        "attributes": [
            {"name": "ownedViews", "kind": AK_OBJS, "type": "View"},
            {"name": "defaultDiagram", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))

    # === UML types ===
    entries.append(("UMLModelElement", {
        "super": "ExtensibleModel",
        "attributes": [
            {"name": "stereotype", "kind": AK_VAR, "type": "UMLStereotype"},
            {"name": "visibility", "kind": AK_ENUM, "type": "UMLVisibilityKind", "default": "public"},
            {"name": "templateParameters", "kind": AK_OBJS, "type": "UMLTemplateParameter"},
        ]
    }))
    entries.append(("UMLFeature", {
        "super": "UMLModelElement",
        "attributes": [
            {"name": "isStatic", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "isLeaf", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "featureDirection", "kind": AK_ENUM, "type": "UMLFeatureDirectionKind", "default": "provided"},
        ]
    }))
    entries.append(("UMLStructuralFeature", {
        "super": "UMLFeature",
        "attributes": [
            {"name": "type", "kind": AK_VAR, "type": "UMLClassifier"},
            {"name": "multiplicity", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "isReadOnly", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "isOrdered", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "isUnique", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "defaultValue", "kind": AK_PRIM, "type": "String", "default": ""},
        ]
    }))
    entries.append(("UMLParameter", {
        "super": "UMLStructuralFeature",
        "attributes": [
            {"name": "direction", "kind": AK_ENUM, "type": "UMLDirectionKind", "default": "in"},
        ]
    }))
    entries.append(("UMLBehavioralFeature", {
        "super": "UMLFeature",
        "attributes": [
            {"name": "parameters", "kind": AK_OBJS, "type": "UMLParameter"},
            {"name": "raisedExceptions", "kind": AK_REFS, "type": "UMLClassifier"},
            {"name": "concurrency", "kind": AK_ENUM, "type": "UMLCallConcurrencyKind", "default": "sequential"},
        ]
    }))
    entries.append(("UMLAttribute", {
        "super": "UMLStructuralFeature",
        "attributes": [
            {"name": "isDerived", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "aggregation", "kind": AK_ENUM, "type": "UMLAggregationKind", "default": "none"},
            {"name": "isID", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("UMLOperation", {
        "super": "UMLBehavioralFeature",
        "attributes": [
            {"name": "isQuery", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "isAbstract", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "specification", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "preconditions", "kind": AK_OBJS, "type": "UMLConstraint"},
            {"name": "bodyConditions", "kind": AK_OBJS, "type": "UMLConstraint"},
            {"name": "postconditions", "kind": AK_OBJS, "type": "UMLConstraint"},
        ]
    }))
    entries.append(("UMLReception", {
        "super": "UMLBehavioralFeature",
        "attributes": [
            {"name": "signal", "kind": AK_REF, "type": "UMLSignal"},
        ]
    }))
    entries.append(("UMLClassifier", {
        "super": "UMLModelElement",
        "attributes": [
            {"name": "attributes", "kind": AK_OBJS, "type": "UMLAttribute"},
            {"name": "operations", "kind": AK_OBJS, "type": "UMLOperation"},
            {"name": "receptions", "kind": AK_OBJS, "type": "UMLReception"},
            {"name": "behaviors", "kind": AK_OBJS, "type": "UMLBehavior"},
            {"name": "isAbstract", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "isFinalSpecialization", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "isLeaf", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("UMLTemplateParameter", {
        "super": "UMLClassifier",
        "attributes": [
            {"name": "parameterType", "kind": AK_VAR, "type": "UMLModelElement"},
            {"name": "defaultValue", "kind": AK_VAR, "type": "UMLModelElement"},
        ]
    }))
    entries.append(("UMLPackage", {
        "super": "UMLModelElement",
        "attributes": [
            {"name": "importedElements", "kind": AK_REFS, "type": "UMLModelElement"},
        ]
    }))
    entries.append(("UMLModel", {
        "super": "UMLPackage",
        "attributes": [
            {"name": "viewpoint", "kind": AK_PRIM, "type": "String", "default": ""},
        ]
    }))
    entries.append(("UMLClass", {
        "super": "UMLClassifier",
        "attributes": [
            {"name": "isActive", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("UMLInterface", {
        "super": "UMLClassifier",
        "attributes": []
    }))
    entries.append(("UMLSignal", {
        "super": "UMLClassifier",
        "attributes": []
    }))
    entries.append(("UMLDataType", {
        "super": "UMLClassifier",
        "attributes": []
    }))
    entries.append(("UMLPrimitiveType", {
        "super": "UMLDataType",
        "attributes": []
    }))
    entries.append(("UMLEnumerationLiteral", {
        "super": "UMLModelElement",
        "attributes": []
    }))
    entries.append(("UMLEnumeration", {
        "super": "UMLDataType",
        "attributes": [
            {"name": "literals", "kind": AK_OBJS, "type": "UMLEnumerationLiteral"},
        ]
    }))
    entries.append(("UMLDirectedRelationship", {
        "super": "DirectedRelationship",
        "attributes": [
            {"name": "stereotype", "kind": AK_VAR, "type": "UMLStereotype"},
            {"name": "visibility", "kind": AK_ENUM, "type": "UMLVisibilityKind", "default": "public"},
        ]
    }))
    entries.append(("UMLUndirectedRelationship", {
        "super": "UndirectedRelationship",
        "attributes": [
            {"name": "stereotype", "kind": AK_VAR, "type": "UMLStereotype"},
            {"name": "visibility", "kind": AK_ENUM, "type": "UMLVisibilityKind", "default": "public"},
        ]
    }))
    entries.append(("UMLRelationshipEnd", {
        "super": "RelationshipEnd",
        "attributes": [
            {"name": "stereotype", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "visibility", "kind": AK_ENUM, "type": "UMLVisibilityKind", "default": "public"},
            {"name": "navigable", "kind": AK_ENUM, "type": "UMLNavigableKind", "default": "unspecified"},
            {"name": "aggregation", "kind": AK_ENUM, "type": "UMLAggregationKind", "default": "none"},
            {"name": "multiplicity", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "defaultValue", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "isReadOnly", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "isOrdered", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "isUnique", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "isDerived", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "isID", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("UMLAssociationEnd", {
        "super": "UMLRelationshipEnd",
        "attributes": [
            {"name": "qualifiers", "kind": AK_OBJS, "type": "UMLAttribute"},
            {"name": "ownerAttribute", "kind": AK_REF, "type": "UMLAttribute"},
        ]
    }))
    entries.append(("UMLAssociation", {
        "super": "UMLUndirectedRelationship",
        "attributes": [
            {"name": "isDerived", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("UMLDependency", {
        "super": "UMLDirectedRelationship",
        "attributes": [
            {"name": "mapping", "kind": AK_PRIM, "type": "String", "default": ""},
        ]
    }))
    entries.append(("UMLAbstraction", {
        "super": "UMLDependency",
        "attributes": []
    }))
    entries.append(("UMLRealization", {
        "super": "UMLAbstraction",
        "attributes": []
    }))
    entries.append(("UMLGeneralization", {
        "super": "UMLDirectedRelationship",
        "attributes": [
            {"name": "discriminator", "kind": AK_PRIM, "type": "String", "default": ""},
        ]
    }))
    entries.append(("UMLInterfaceRealization", {
        "super": "UMLRealization",
        "attributes": []
    }))
    entries.append(("UMLComponentRealization", {
        "super": "UMLRealization",
        "attributes": []
    }))
    entries.append(("UMLAssociationClassLink", {
        "super": "UMLModelElement",
        "attributes": [
            {"name": "classSide", "kind": AK_REF, "type": "UMLClass"},
            {"name": "associationSide", "kind": AK_REF, "type": "UMLAssociation"},
        ]
    }))
    entries.append(("UMLConstraint", {
        "super": "UMLModelElement",
        "attributes": [
            {"name": "specification", "kind": AK_PRIM, "type": "String", "default": ""},
            {"name": "constrainedElements", "kind": AK_REFS, "type": "UMLModelElement"},
        ]
    }))

    # === UML View types ===
    entries.append(("UMLGeneralNodeView", {
        "super": "NodeView",
        "attributes": [
            {"name": "stereotypeDisplay", "kind": AK_ENUM, "type": "UMLStereotypeDisplayKind", "default": "label"},
            {"name": "showVisibility", "kind": AK_PRIM, "type": "Boolean", "default": True},
            {"name": "showOperationSignature", "kind": AK_PRIM, "type": "Boolean", "default": True},
            {"name": "showProperty", "kind": AK_PRIM, "type": "Boolean", "default": True},
            {"name": "showType", "kind": AK_PRIM, "type": "Boolean", "default": True},
            {"name": "showNamespace", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "showMultiplicity", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("UMLClassView", {
        "super": "UMLGeneralNodeView",
        "attributes": [
            {"name": "nameCompartment", "kind": AK_REF, "type": "UMLNameCompartmentView"},
            {"name": "attributeCompartment", "kind": AK_REF, "type": "UMLAttributeCompartmentView"},
            {"name": "operationCompartment", "kind": AK_REF, "type": "UMLOperationCompartmentView"},
            {"name": "receptionCompartment", "kind": AK_REF, "type": "UMLReceptionCompartmentView"},
            {"name": "templateParameterCompartment", "kind": AK_REF, "type": "UMLTemplateParameterCompartmentView"},
            {"name": "suppressAttributes", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "suppressOperations", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "suppressReceptions", "kind": AK_PRIM, "type": "Boolean", "default": False},
            {"name": "suppressTemplateParameters", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("UMLInterfaceView", {
        "super": "UMLClassView",
        "attributes": []
    }))
    entries.append(("UMLEnumerationView", {
        "super": "UMLClassView",
        "attributes": [
            {"name": "enumerationLiteralCompartment", "kind": AK_REF, "type": "UMLEnumerationLiteralCompartmentView"},
        ]
    }))
    entries.append(("UMLNameCompartmentView", {
        "super": "NodeView",
        "attributes": [
            {"name": "stereotypeLabel", "kind": AK_REF, "type": "LabelView"},
            {"name": "nameLabel", "kind": AK_REF, "type": "LabelView"},
            {"name": "namespaceLabel", "kind": AK_REF, "type": "LabelView"},
            {"name": "propertyLabel", "kind": AK_REF, "type": "LabelView"},
        ]
    }))
    entries.append(("UMLAttributeCompartmentView", {
        "super": "NodeView",
        "attributes": [
            {"name": "suppressAllAttributes", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("UMLOperationCompartmentView", {
        "super": "NodeView",
        "attributes": [
            {"name": "suppressAllOperations", "kind": AK_PRIM, "type": "Boolean", "default": False},
        ]
    }))
    entries.append(("UMLReceptionCompartmentView", {
        "super": "NodeView",
        "attributes": []
    }))
    entries.append(("UMLTemplateParameterCompartmentView", {
        "super": "NodeView",
        "attributes": []
    }))
    entries.append(("UMLEnumerationLiteralCompartmentView", {
        "super": "NodeView",
        "attributes": []
    }))
    entries.append(("UMLAttributeView", {
        "super": "LabelView",
        "attributes": [
            {"name": "aggregation", "kind": AK_ENUM, "type": "UMLAggregationKind", "default": "none"},
        ]
    }))
    entries.append(("UMLOperationView", {
        "super": "LabelView",
        "attributes": []
    }))
    entries.append(("UMLReceptionView", {
        "super": "LabelView",
        "attributes": []
    }))
    entries.append(("UMLEnumerationLiteralView", {
        "super": "LabelView",
        "attributes": []
    }))
    entries.append(("UMLAssociationView", {
        "super": "EdgeView",
        "attributes": [
            {"name": "end1NameLabel", "kind": AK_REF, "type": "LabelView"},
            {"name": "end2NameLabel", "kind": AK_REF, "type": "LabelView"},
            {"name": "end1MultiplicityLabel", "kind": AK_REF, "type": "LabelView"},
            {"name": "end2MultiplicityLabel", "kind": AK_REF, "type": "LabelView"},
        ]
    }))
    entries.append(("UMLGeneralizationView", {
        "super": "EdgeView",
        "attributes": []
    }))
    entries.append(("UMLDependencyView", {
        "super": "EdgeView",
        "attributes": []
    }))
    entries.append(("UMLClassDiagram", {
        "super": "Diagram",
        "attributes": []
    }))

    for name, defn in entries:
        METAMODEL[name] = defn


_build_metamodel()


def _get_all_attributes(type_name: str) -> List[dict]:
    """Return all inherited attributes for a given type name."""
    attrs = []
    seen = set()
    current = type_name
    while current and current in METAMODEL:
        defn = METAMODEL[current]
        for attr in defn.get("attributes", []):
            if attr["name"] not in seen:
                seen.add(attr["name"])
                attrs.append(attr)
        current = defn.get("super")
    return attrs


def get_default_value(type_name: str, attr_name: str) -> Any:
    """Get the default value for an attribute of a given type."""
    attrs = _get_all_attributes(type_name)
    for a in attrs:
        if a["name"] == attr_name:
            return a.get("default")
    return None


def is_default_value(type_name: str, attr_name: str, value: Any) -> bool:
    """Check if a value is the default for the given type and attribute."""
    default = get_default_value(type_name, attr_name)
    if default is None:
        return False
    if isinstance(default, bool) and not isinstance(value, bool):
        return False
    if isinstance(value, str) and value == "" and attr_name == "name":
        return True
    return value == default


def is_kind_of(child_type: str, parent_type: str) -> bool:
    """Type test: check if child_type is a kind of parent_type."""
    current = child_type
    while current in METAMODEL:
        if current == parent_type:
            return True
        current = METAMODEL[current].get("super", "")
    return False


def get_view_type(model_type: str) -> Optional[str]:
    """Get the corresponding view type for a model type."""
    current = model_type
    while current in METAMODEL:
        defn = METAMODEL[current]
        if defn.get("view"):
            return defn["view"]
        current = defn.get("super", "")
    return None


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class MdjParser:
    def __init__(self):
        self._by_id: Dict[str, dict] = {}
        self._root: Optional[dict] = None
        self._model_diagram_id: Optional[str] = None  # the UMLClassDiagram id
        self._model_id: Optional[str] = None  # the UMLModel id

    @property
    def root(self) -> dict:
        return self._root

    @property
    def model(self) -> dict:
        return self._by_id.get(self._model_id) if self._model_id else None

    @property
    def class_diagram(self) -> dict:
        return self._by_id.get(self._model_diagram_id) if self._model_diagram_id else None

    @property
    def project(self) -> dict:
        return self._root

    def by_id(self, id_: str) -> Optional[dict]:
        return self._by_id.get(id_)

    def find_by_type(self, type_name: str) -> List[dict]:
        return [v for v in self._by_id.values() if v["_type"] == type_name]

    def find_by_name(self, name: str) -> List[dict]:
        return [v for v in self._by_id.values() if v.get("name") == name]

    def load(self, filepath: str) -> "MdjParser":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._parse(data)
        return self

    def loads(self, json_str: str) -> "MdjParser":
        data = json.loads(json_str)
        self._parse(data)
        return self

    def _parse(self, data: dict):
        self._by_id.clear()
        self._model_diagram_id = None
        self._model_id = None
        self._root = data

        # First pass: index all elements by ID
        self._index_recursive(data)

        # Second pass: resolve $ref references
        self._resolve_refs_recursive(data)

        # Identify key elements
        for eid, elem in self._by_id.items():
            t = elem.get("_type")
            if t == "UMLClassDiagram" and self._model_diagram_id is None:
                self._model_diagram_id = eid
            elif t == "UMLModel" and self._model_id is None:
                self._model_id = eid

    def _index_recursive(self, obj: Any):
        if isinstance(obj, dict):
            if "_id" in obj and "_type" in obj:
                self._by_id[obj["_id"]] = obj
            for v in obj.values():
                self._index_recursive(v)
        elif isinstance(obj, list):
            for item in obj:
                self._index_recursive(item)

    def _resolve_refs_recursive(self, obj: Any):
        if isinstance(obj, dict):
            keys = list(obj.keys())
            for key in keys:
                val = obj[key]
                if isinstance(val, dict) and "$ref" in val:
                    ref_id = val["$ref"]
                    if ref_id in self._by_id:
                        obj[key] = self._by_id[ref_id]
                else:
                    self._resolve_refs_recursive(val)
        elif isinstance(obj, list):
            for item in obj:
                self._resolve_refs_recursive(item)

    def get_parent(self, elem: dict) -> Optional[dict]:
        parent = elem.get("_parent")
        if isinstance(parent, dict) and "_id" in parent:
            return parent
        return None

    def get_children(self, elem: dict) -> List[dict]:
        """Get direct children of an element (via its collection attributes)."""
        children = []
        attrs = _get_all_attributes(elem.get("_type", ""))
        for attr in attrs:
            if attr["kind"] in (AK_OBJ, AK_REF):
                val = elem.get(attr["name"])
                if val and isinstance(val, dict) and "_id" in val:
                    children.append(val)
            elif attr["kind"] in (AK_OBJS, AK_REFS):
                val = elem.get(attr["name"])
                if isinstance(val, list):
                    children.extend(v for v in val if isinstance(v, dict) and "_id" in v)
        return children

    def get_diagram_classes(self) -> List[dict]:
        """Return all class-like model elements in the diagram's model."""
        if not self._model_id:
            return []
        model = self._by_id[self._model_id]
        result = []
        for elem in model.get("ownedElements", []):
            if isinstance(elem, dict) and elem.get("_type") in (
                "UMLClass", "UMLInterface", "UMLEnumeration", "UMLDataType",
                "UMLPrimitiveType", "UMLSignal",
            ):
                result.append(elem)
        return result

    def get_diagram_views(self) -> List[dict]:
        """Return all top-level views in the diagram."""
        diagram = self.class_diagram
        if not diagram:
            return []
        return [v for v in diagram.get("ownedViews", [])
                if isinstance(v, dict) and "_id" in v]

    def get_view_for_model(self, model_id: str) -> Optional[dict]:
        """Find the view that corresponds to a given model element."""
        for view in self.get_diagram_views():
            if view.get("model") is not None:
                mid = view["model"].get("_id") if isinstance(view["model"], dict) else None
                if mid == model_id:
                    return view
        return None

    def get_relationships(self) -> List[dict]:
        """Return all relationship model elements (associations, generalizations, etc.).

        Searches both model-level ownedElements and class-level ownedElements
        (some StarUML files nest associations inside class ownedElements).
        """
        model = self.model
        if not model:
            return []
        result = []
        rel_types = (
            "UMLAssociation", "UMLGeneralization", "UMLDependency",
            "UMLInterfaceRealization", "UMLRealization", "UMLAbstraction",
            "UMLAssociationClassLink",
        )
        for elem in model.get("ownedElements", []):
            if not isinstance(elem, dict):
                continue
            if elem.get("_type") in rel_types:
                result.append(elem)
            # Also check inside this element's ownedElements (associations may be nested)
            for child in elem.get("ownedElements", []):
                if isinstance(child, dict) and child.get("_type") in rel_types:
                    result.append(child)
        return result

    def get_relationship_view(self, rel_id: str) -> Optional[dict]:
        """Find the view for a relationship."""
        for view in self.get_diagram_views():
            model = view.get("model")
            if model and isinstance(model, dict) and model.get("_id") == rel_id:
                return view
        return None

    def classes_summary(self) -> List[Dict[str, Any]]:
        """Return a summary of all classes with their attributes, operations, and relationships."""
        classes = self.get_diagram_classes()
        relationships = self.get_relationships()
        summary = []
        for c in classes:
            info = {
                "id": c["_id"],
                "name": c.get("name", ""),
                "type": c["_type"],
                "is_abstract": c.get("isAbstract", False),
                "stereotype": _extract_name(c.get("stereotype")),
                "attributes": [],
                "operations": [],
                "relationships": [],
                "view": None,
            }
            for a in c.get("attributes", []):
                if isinstance(a, dict):
                    info["attributes"].append({
                        "id": a["_id"],
                        "name": a.get("name", ""),
                        "type": _extract_name(a.get("type")),
                        "visibility": a.get("visibility", "public"),
                        "is_static": a.get("isStatic", False),
                    })
            for o in c.get("operations", []):
                if isinstance(o, dict):
                    params = []
                    for p in o.get("parameters", []):
                        if isinstance(p, dict):
                            params.append({
                                "name": p.get("name", ""),
                                "type": _extract_name(p.get("type")),
                                "direction": p.get("direction", "in"),
                            })
                    info["operations"].append({
                        "id": o["_id"],
                        "name": o.get("name", ""),
                        "visibility": o.get("visibility", "public"),
                        "is_abstract": o.get("isAbstract", False),
                        "is_static": o.get("isStatic", False),
                        "parameters": params,
                    })
            for r in relationships:
                if isinstance(r, dict):
                    if r["_type"] == "UMLAssociation":
                        e1 = r.get("end1")
                        e2 = r.get("end2")
                        if e1 and e2:
                            ref1 = e1.get("reference") if isinstance(e1, dict) else None
                            ref2 = e2.get("reference") if isinstance(e2, dict) else None
                            id1 = ref1.get("_id") if isinstance(ref1, dict) else None
                            id2 = ref2.get("_id") if isinstance(ref2, dict) else None
                            if id1 == c["_id"] or id2 == c["_id"]:
                                other_id = id2 if id1 == c["_id"] else id1
                                other = self.by_id(other_id)
                                info["relationships"].append({
                                    "type": "association",
                                    "target": other.get("name") if other else "?",
                                    "target_id": other_id,
                                })
                    elif r["_type"] == "UMLGeneralization":
                        src = r.get("source")
                        tgt = r.get("target")
                        sid = src.get("_id") if isinstance(src, dict) else None
                        tid = tgt.get("_id") if isinstance(tgt, dict) else None
                        if sid == c["_id"]:
                            tgt_elem = self.by_id(tid)
                            info["relationships"].append({
                                "type": "generalization",
                                "direction": "child->parent",
                                "target": tgt_elem.get("name") if tgt_elem else "?",
                                "target_id": tid,
                            })
                        elif tid == c["_id"]:
                            src_elem = self.by_id(sid)
                            info["relationships"].append({
                                "type": "generalization",
                                "direction": "parent<-child",
                                "target": src_elem.get("name") if src_elem else "?",
                                "target_id": sid,
                            })
            view = self.get_view_for_model(c["_id"])
            if view:
                info["view"] = {
                    "id": view["_id"],
                    "left": view.get("left", 0),
                    "top": view.get("top", 0),
                    "width": view.get("width", 0),
                    "height": view.get("height", 0),
                }
            summary.append(info)
        return summary


def _extract_name(value) -> str:
    """Extract a name string from a value that could be a string or a ref object."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("name", "")
    return ""
