import json
from typing import Any, Dict, List, Optional, Tuple

from staruml_tool.parser import (
    MdjParser,
    METAMODEL,
    AK_PRIM,
    AK_ENUM,
    AK_REF,
    AK_REFS,
    AK_OBJ,
    AK_OBJS,
    AK_VAR,
    AK_CUSTOM,
    _get_all_attributes,
    get_default_value,
    get_view_type,
    is_kind_of,
)


def _register_state_metamodel():
    if "UMLStateMachine" in METAMODEL:
        return

    entries = [
        ("UMLDiagram", {
            "super": "Diagram",
            "attributes": []
        }),
        ("UMLBehavior", {
            "super": "UMLClassifier",
            "attributes": []
        }),
        ("UMLStateMachine", {
            "kind": "class",
            "super": "UMLBehavior",
            "attributes": [
                {"name": "regions", "kind": AK_OBJS, "type": "UMLRegion"}
            ]
        }),
        ("UMLRegion", {
            "kind": "class",
            "super": "UMLModelElement",
            "attributes": [
                {"name": "vertices", "kind": AK_OBJS, "type": "UMLVertex"},
                {"name": "transitions", "kind": AK_OBJS, "type": "UMLTransition"}
            ]
        }),
        ("UMLVertex", {
            "kind": "class",
            "super": "UMLModelElement",
            "attributes": []
        }),
        ("UMLPseudostate", {
            "kind": "class",
            "super": "UMLVertex",
            "attributes": [
                {"name": "kind", "kind": AK_ENUM, "type": "UMLPseudostateKind", "default": "initial"}
            ],
            "view": "UMLPseudostateView"
        }),
        ("UMLConnectionPointReference", {
            "kind": "class",
            "super": "UMLVertex",
            "attributes": [
                {"name": "entry", "kind": AK_REFS, "type": "UMLPseudostate"},
                {"name": "exit", "kind": AK_REFS, "type": "UMLPseudostate"}
            ],
            "view": "UMLConnectionPointReferenceView"
        }),
        ("UMLState", {
            "kind": "class",
            "super": "UMLVertex",
            "attributes": [
                {"name": "regions", "kind": AK_OBJS, "type": "UMLRegion"},
                {"name": "entryActivities", "kind": AK_OBJS, "type": "UMLBehavior"},
                {"name": "doActivities", "kind": AK_OBJS, "type": "UMLBehavior"},
                {"name": "exitActivities", "kind": AK_OBJS, "type": "UMLBehavior"},
                {"name": "submachine", "kind": AK_REF, "type": "UMLStateMachine"},
                {"name": "connections", "kind": AK_OBJS, "type": "UMLConnectionPointReference"}
            ],
            "view": "UMLStateView"
        }),
        ("UMLFinalState", {
            "kind": "class",
            "super": "UMLState",
            "view": "UMLFinalStateView",
            "attributes": []
        }),
        ("UMLTransition", {
            "kind": "class",
            "super": "UMLDirectedRelationship",
            "attributes": [
                {"name": "kind", "kind": AK_ENUM, "type": "UMLTransitionKind", "default": "external"},
                {"name": "guard", "kind": AK_PRIM, "type": "String", "default": ""},
                {"name": "triggers", "kind": AK_OBJS, "type": "UMLEvent"},
                {"name": "effects", "kind": AK_OBJS, "type": "UMLBehavior"}
            ],
            "view": "UMLTransitionView"
        }),
        ("UMLEvent", {
            "kind": "class",
            "super": "UMLModelElement",
            "attributes": [
                {"name": "kind", "kind": AK_ENUM, "type": "UMLEventKind", "default": "anyReceive"},
                {"name": "value", "kind": AK_PRIM, "type": "String", "default": ""}
            ]
        }),
        ("UMLStatechartDiagram", {
            "kind": "class",
            "super": "UMLDiagram",
            "attributes": []
        }),
        ("UMLPseudostateView", {
            "kind": "class",
            "super": "UMLFloatingNodeView",
            "attributes": []
        }),
        ("UMLFloatingNodeView", {
            "kind": "class",
            "super": "NodeView",
            "attributes": [
                {"name": "nameLabel", "kind": AK_REF, "type": "LabelView"},
                {"name": "stereotypeLabel", "kind": AK_REF, "type": "LabelView"},
                {"name": "propertyLabel", "kind": AK_REF, "type": "LabelView"},
            ]
        }),
        ("UMLFinalStateView", {
            "kind": "class",
            "super": "NodeView",
            "attributes": []
        }),
        ("UMLConnectionPointReferenceView", {
            "kind": "class",
            "super": "UMLFloatingNodeView",
            "attributes": []
        }),
        ("NodeLabelView", {
            "kind": "class",
            "super": "LabelView",
            "attributes": [
                {"name": "alpha", "kind": AK_PRIM, "type": "Float", "default": 0},
                {"name": "distance", "kind": AK_PRIM, "type": "Integer", "default": 0},
            ]
        }),
        ("EdgeLabelView", {
            "kind": "class",
            "super": "LabelView",
            "attributes": [
                {"name": "alpha", "kind": AK_PRIM, "type": "Float", "default": 0},
                {"name": "distance", "kind": AK_PRIM, "type": "Integer", "default": 0},
                {"name": "hostEdge", "kind": AK_REF, "type": "EdgeView"},
                {"name": "edgePosition", "kind": AK_PRIM, "type": "Integer", "default": 0},
            ]
        }),
        ("UMLGeneralEdgeView", {
            "kind": "class",
            "super": "EdgeView",
            "attributes": [
                {"name": "nameLabel", "kind": AK_REF, "type": "LabelView"},
                {"name": "stereotypeLabel", "kind": AK_REF, "type": "LabelView"},
                {"name": "propertyLabel", "kind": AK_REF, "type": "LabelView"},
                {"name": "showVisibility", "kind": AK_PRIM, "type": "Boolean", "default": True},
            ]
        }),
        ("UMLTransitionView", {
            "kind": "class",
            "super": "UMLGeneralEdgeView",
            "attributes": []
        }),
        ("UMLInternalActivityCompartmentView", {
            "kind": "class",
            "super": "UMLListCompartmentView",
            "attributes": []
        }),
        ("UMLListCompartmentView", {
            "kind": "class",
            "super": "NodeView",
            "attributes": []
        }),
        ("UMLInternalTransitionCompartmentView", {
            "kind": "class",
            "super": "UMLListCompartmentView",
            "attributes": []
        }),
        ("UMLDecompositionCompartmentView", {
            "kind": "class",
            "super": "UMLListCompartmentView",
            "attributes": []
        }),
        ("UMLStateView", {
            "kind": "class",
            "super": "UMLGeneralNodeView",
            "attributes": [
                {"name": "nameCompartment", "kind": AK_REF, "type": "UMLNameCompartmentView"},
                {"name": "internalActivityCompartment", "kind": AK_REF, "type": "UMLInternalActivityCompartmentView"},
                {"name": "internalTransitionCompartment", "kind": AK_REF, "type": "UMLInternalTransitionCompartmentView"},
                {"name": "decompositionCompartment", "kind": AK_REF, "type": "UMLDecompositionCompartmentView"},
            ]
        }),
    ]

    for name, defn in entries:
        METAMODEL[name] = defn


_register_state_metamodel()


class StateParser(MdjParser):

    def get_state_machines(self) -> List[dict]:
        result = []
        if not self._root:
            return result
        for elem in self._root.get("ownedElements", []):
            if isinstance(elem, dict) and elem.get("_type") == "UMLStateMachine":
                result.append(elem)
        return result

    def get_state_machine(self, name_or_id: str) -> Optional[dict]:
        for sm in self.get_state_machines():
            if sm["_id"] == name_or_id or sm.get("name") == name_or_id:
                return sm
        return None

    def get_states(self, sm_name_or_id: str) -> List[dict]:
        sm = self.get_state_machine(sm_name_or_id)
        if not sm:
            return []
        result = []
        for region in sm.get("regions", []):
            if not isinstance(region, dict):
                continue
            for v in region.get("vertices", []):
                if isinstance(v, dict):
                    result.append(v)
        return result

    def get_state(self, sm_name_or_id: str, state_name_or_id: str) -> Optional[dict]:
        for s in self.get_states(sm_name_or_id):
            if s["_id"] == state_name_or_id or s.get("name") == state_name_or_id:
                return s
        return None

    def get_transitions(self, sm_name_or_id: str) -> List[dict]:
        sm = self.get_state_machine(sm_name_or_id)
        if not sm:
            return []
        result = []
        for region in sm.get("regions", []):
            if not isinstance(region, dict):
                continue
            for t in region.get("transitions", []):
                if isinstance(t, dict):
                    result.append(t)
        return result

    def get_transition(self, sm_name_or_id: str, trans_id: str) -> Optional[dict]:
        for t in self.get_transitions(sm_name_or_id):
            if t["_id"] == trans_id:
                return t
        return None

    def get_region(self, sm_name_or_id: str) -> Optional[dict]:
        sm = self.get_state_machine(sm_name_or_id)
        if not sm:
            return None
        for region in sm.get("regions", []):
            if isinstance(region, dict):
                return region
        return None

    def get_statechart_diagram(self, sm_name_or_id: str) -> Optional[dict]:
        sm = self.get_state_machine(sm_name_or_id)
        if not sm:
            return None
        for elem in sm.get("ownedElements", []):
            if isinstance(elem, dict) and elem.get("_type") == "UMLStatechartDiagram":
                return elem
        return None

    def get_state_view(self, state_model_id: str) -> Optional[dict]:
        for sm in self.get_state_machines():
            diagram = self.get_statechart_diagram(sm["_id"])
            if not diagram:
                continue
            for view in diagram.get("ownedViews", []):
                if not isinstance(view, dict):
                    continue
                model = view.get("model")
                if isinstance(model, dict) and model.get("_id") == state_model_id:
                    return view
        return None

    def get_transition_view(self, trans_model_id: str) -> Optional[dict]:
        for sm in self.get_state_machines():
            diagram = self.get_statechart_diagram(sm["_id"])
            if not diagram:
                continue
            for view in diagram.get("ownedViews", []):
                if not isinstance(view, dict):
                    continue
                model = view.get("model")
                if isinstance(model, dict) and model.get("_id") == trans_model_id:
                    return view
        return None

    def get_all_state_views(self, sm_name_or_id: str) -> List[dict]:
        diagram = self.get_statechart_diagram(sm_name_or_id)
        if not diagram:
            return []
        return [v for v in diagram.get("ownedViews", [])
                if isinstance(v, dict) and v.get("model") is not None]

    def states_summary(self, sm_name_or_id: str) -> List[Dict[str, Any]]:
        sm = self.get_state_machine(sm_name_or_id)
        if not sm:
            return []
        states = self.get_states(sm_name_or_id)
        transitions = self.get_transitions(sm_name_or_id)
        result = []
        for s in states:
            info = {
                "id": s["_id"],
                "name": s.get("name", ""),
                "type": s["_type"],
                "kind": s.get("kind", ""),
                "incoming": [],
                "outgoing": [],
            }
            for t in transitions:
                src = t.get("source")
                tgt = t.get("target")
                sid = src.get("_id") if isinstance(src, dict) else None
                tid = tgt.get("_id") if isinstance(tgt, dict) else None
                if tid == s["_id"]:
                    info["incoming"].append({
                        "id": t["_id"],
                        "source": _vertex_name(src),
                        "guard": t.get("guard", ""),
                        "triggers": _event_names(t.get("triggers", [])),
                    })
                if sid == s["_id"]:
                    info["outgoing"].append({
                        "id": t["_id"],
                        "target": _vertex_name(tgt),
                        "guard": t.get("guard", ""),
                        "triggers": _event_names(t.get("triggers", [])),
                    })
            result.append(info)
        return result


def _vertex_name(ref) -> str:
    if isinstance(ref, dict):
        return ref.get("name", ref.get("_id", "?"))
    return str(ref)


def _event_names(events: list) -> list:
    result = []
    for e in events:
        if isinstance(e, dict):
            result.append(e.get("name", ""))
    return result
