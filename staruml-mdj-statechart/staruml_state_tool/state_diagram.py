import time
import random
from typing import Any, Dict, List, Optional, Tuple

from staruml_tool.diagram import generate_id, _make_element
from staruml_tool.parser import _get_all_attributes, get_default_value
from .parser import StateParser


FONT = "Arial;13;0"
FONT_BOLD = "Arial;13;1"
LINE_HEIGHT = 13
STATE_W = 80
STATE_H = 40
INITIAL_W = 20
INITIAL_H = 20
FINAL_W = 26
FINAL_H = 26


class StateDiagram:

    def __init__(self, parser: StateParser, filepath: str = ""):
        self._parser = parser
        self._filepath = filepath

    @classmethod
    def load(cls, filepath: str) -> "StateDiagram":
        parser = StateParser().load(filepath)
        return cls(parser, filepath)

    @classmethod
    def create(cls, project_name: str = "Project") -> "StateDiagram":
        project_id = generate_id()
        model_id = generate_id()

        project = {
            "_type": "Project",
            "_id": project_id,
            "name": project_name,
            "ownedElements": [
                {
                    "_type": "UMLModel",
                    "_id": model_id,
                    "_parent": {"$ref": project_id},
                    "name": "Model",
                    "ownedElements": [],
                }
            ],
            "documentVersion": 1,
        }

        parser = StateParser()
        parser._parse(project)
        return cls(parser, "")

    def save(self, filepath: str = ""):
        fp = filepath or self._filepath
        from staruml_tool.writer import MdjWriter
        writer = MdjWriter(self._parser)
        writer.save(fp)

    # -----------------------------------------------------------------------
    # List / Query
    # -----------------------------------------------------------------------

    def list_state_machines(self) -> List[Dict[str, Any]]:
        result = []
        for sm in self._parser.get_state_machines():
            states = self._parser.get_states(sm["_id"])
            trans = self._parser.get_transitions(sm["_id"])
            result.append({
                "id": sm["_id"],
                "name": sm.get("name", ""),
                "num_states": len(states),
                "num_transitions": len(trans),
            })
        return result

    def list_states(self, sm_name_or_id: str) -> List[Dict[str, Any]]:
        return self._parser.states_summary(sm_name_or_id)

    def list_transitions(self, sm_name_or_id: str) -> List[Dict[str, Any]]:
        result = []
        for t in self._parser.get_transitions(sm_name_or_id):
            src = t.get("source")
            tgt = t.get("target")
            result.append({
                "id": t["_id"],
                "source": _vertex_name(src),
                "target": _vertex_name(tgt),
                "guard": t.get("guard", ""),
                "kind": t.get("kind", "external"),
                "triggers": [_event_name_text(e) for e in t.get("triggers", []) if isinstance(e, dict)],
            })
        return result

    def summary(self, sm_name_or_id: str = "") -> Dict[str, Any]:
        if sm_name_or_id:
            sms = [self._parser.get_state_machine(sm_name_or_id)]
            if not sms[0]:
                return {"error": f"State machine '{sm_name_or_id}' not found"}
        else:
            sms = self._parser.get_state_machines()
        result = {"state_machines": []}
        for sm in sms:
            result["state_machines"].append({
                "id": sm["_id"],
                "name": sm.get("name", ""),
                "states": self._parser.states_summary(sm["_id"]),
                "transitions": self.list_transitions(sm["_id"]),
            })
        return result

    # -----------------------------------------------------------------------
    # State machine CRUD
    # -----------------------------------------------------------------------

    def add_state_machine(self, name: str) -> dict:
        project = self._parser.root
        sm = _make_element(
            "UMLStateMachine",
            name=name,
            _parent=project,
            ownedElements=[],
            regions=[],
        )
        region = _make_element(
            "UMLRegion",
            _parent=sm,
            vertices=[],
            transitions=[],
        )
        sm["regions"].append(region)
        self._parser._by_id[region["_id"]] = region

        diagram = _make_element(
            "UMLStatechartDiagram",
            name=f"{name}Diagram",
            _parent=sm,
            ownedViews=[],
            defaultDiagram=True,
        )
        sm["ownedElements"].append(diagram)
        self._parser._by_id[diagram["_id"]] = diagram

        project.setdefault("ownedElements", []).append(sm)
        self._parser._by_id[sm["_id"]] = sm
        return sm

    def remove_state_machine(self, name_or_id: str) -> bool:
        sm = self._parser.get_state_machine(name_or_id)
        if not sm:
            return False
        sid = sm["_id"]

        for region in sm.get("regions", []):
            if isinstance(region, dict):
                for v in region.get("vertices", []):
                    if isinstance(v, dict) and v["_id"] in self._parser._by_id:
                        del self._parser._by_id[v["_id"]]
                for t in region.get("transitions", []):
                    if isinstance(t, dict):
                        for ev in t.get("triggers", []):
                            if isinstance(ev, dict) and ev["_id"] in self._parser._by_id:
                                del self._parser._by_id[ev["_id"]]
                        if t["_id"] in self._parser._by_id:
                            del self._parser._by_id[t["_id"]]
                if region["_id"] in self._parser._by_id:
                    del self._parser._by_id[region["_id"]]

        for elem in sm.get("ownedElements", []):
            if isinstance(elem, dict) and elem["_id"] in self._parser._by_id:
                del self._parser._by_id[elem["_id"]]

        if sid in self._parser._by_id:
            del self._parser._by_id[sid]

        project = self._parser.root
        try:
            project["ownedElements"].remove(sm)
        except ValueError:
            pass
        return True

    def rename_state_machine(self, name_or_id: str, new_name: str) -> bool:
        sm = self._parser.get_state_machine(name_or_id)
        if not sm:
            return False
        sm["name"] = new_name
        return True

    # -----------------------------------------------------------------------
    # State CRUD
    # -----------------------------------------------------------------------

    def add_state(
        self,
        sm_name_or_id: str,
        name: str,
        x: float = 200,
        y: float = 200,
    ) -> Optional[dict]:
        sm = self._parser.get_state_machine(sm_name_or_id)
        if not sm:
            return None
        region = self._parser.get_region(sm_name_or_id)
        if not region:
            return None

        state = _make_element(
            "UMLState",
            name=name,
            _parent=region,
            regions=[],
            entryActivities=[],
            doActivities=[],
            exitActivities=[],
            connections=[],
        )
        region.setdefault("vertices", []).append(state)
        self._parser._by_id[state["_id"]] = state

        self._create_state_view(sm, state, x, y, STATE_W, STATE_H)
        return state

    def add_initial(
        self,
        sm_name_or_id: str,
        name: str = "init",
        x: float = 120,
        y: float = 200,
    ) -> Optional[dict]:
        sm = self._parser.get_state_machine(sm_name_or_id)
        if not sm:
            return None
        region = self._parser.get_region(sm_name_or_id)
        if not region:
            return None

        pseudo = _make_element(
            "UMLPseudostate",
            name=name,
            kind="initial",
            _parent=region,
        )
        region.setdefault("vertices", []).append(pseudo)
        self._parser._by_id[pseudo["_id"]] = pseudo

        self._create_pseudostate_view(sm, pseudo, x, y, INITIAL_W, INITIAL_H)
        return pseudo

    def add_final(
        self,
        sm_name_or_id: str,
        name: str = "",
        x: float = 200,
        y: float = 400,
    ) -> Optional[dict]:
        sm = self._parser.get_state_machine(sm_name_or_id)
        if not sm:
            return None
        region = self._parser.get_region(sm_name_or_id)
        if not region:
            return None

        final_state = _make_element(
            "UMLFinalState",
            name=name,
            _parent=region,
        )
        region.setdefault("vertices", []).append(final_state)
        self._parser._by_id[final_state["_id"]] = final_state

        self._create_final_state_view(sm, final_state, x, y)
        return final_state

    def add_pseudostate(
        self,
        sm_name_or_id: str,
        kind: str,
        name: str = "",
        x: float = 200,
        y: float = 200,
    ) -> Optional[dict]:
        valid_kinds = {"initial", "deepHistory", "shallowHistory", "join", "fork", "junction", "choice", "entryPoint", "exitPoint", "terminate"}
        if kind not in valid_kinds:
            raise ValueError(f"Invalid pseudostate kind: {kind}. Valid: {valid_kinds}")
        sm = self._parser.get_state_machine(sm_name_or_id)
        if not sm:
            return None
        region = self._parser.get_region(sm_name_or_id)
        if not region:
            return None

        pseudo = _make_element(
            "UMLPseudostate",
            name=name,
            kind=kind,
            _parent=region,
        )
        region.setdefault("vertices", []).append(pseudo)
        self._parser._by_id[pseudo["_id"]] = pseudo

        w = INITIAL_W if kind in ("initial", "terminate") else STATE_W
        h = INITIAL_H if kind in ("initial", "terminate") else STATE_H
        self._create_pseudostate_view(sm, pseudo, x, y, w, h)
        return pseudo

    def remove_state(self, sm_name_or_id: str, state_name_or_id: str) -> bool:
        sm = self._parser.get_state_machine(sm_name_or_id)
        if not sm:
            return False
        region = self._parser.get_region(sm_name_or_id)
        if not region:
            return False

        target = self._parser.get_state(sm_name_or_id, state_name_or_id)
        if not target:
            return False
        tid = target["_id"]

        transitions_to_remove = []
        for t in region.get("transitions", []):
            if not isinstance(t, dict):
                continue
            src = t.get("source")
            tgt = t.get("target")
            sid = src.get("_id") if isinstance(src, dict) else None
            tgtid = tgt.get("_id") if isinstance(tgt, dict) else None
            if sid == tid or tgtid == tid:
                transitions_to_remove.append(t)

        for t in transitions_to_remove:
            self._remove_transition_internal(sm, region, t)

        self._remove_state_view(sm, tid)

        try:
            region["vertices"].remove(target)
        except ValueError:
            pass
        if tid in self._parser._by_id:
            del self._parser._by_id[tid]
        return True

    def rename_state(self, sm_name_or_id: str, old_name: str, new_name: str) -> bool:
        state = self._parser.get_state(sm_name_or_id, old_name)
        if not state:
            return False
        state["name"] = new_name
        self._rebuild_state_view(sm_name_or_id, state)
        return True

    # -----------------------------------------------------------------------
    # Transition CRUD
    # -----------------------------------------------------------------------

    def add_transition(
        self,
        sm_name_or_id: str,
        source_name_or_id: str,
        target_name_or_id: str,
        guard: str = "",
        trigger_name: str = "",
        trigger_kind: str = "anyReceive",
    ) -> Optional[dict]:
        sm = self._parser.get_state_machine(sm_name_or_id)
        if not sm:
            return None
        region = self._parser.get_region(sm_name_or_id)
        if not region:
            return None
        src = self._parser.get_state(sm_name_or_id, source_name_or_id)
        tgt = self._parser.get_state(sm_name_or_id, target_name_or_id)
        if not src or not tgt:
            return None

        trans = _make_element(
            "UMLTransition",
            name="",
            _parent=region,
            source=src,
            target=tgt,
            guard=guard,
            kind="external",
            triggers=[],
            effects=[],
        )

        if trigger_name:
            event = _make_element(
                "UMLEvent",
                name=trigger_name,
                kind=trigger_kind,
                _parent=trans,
            )
            trans["triggers"].append(event)
            self._parser._by_id[event["_id"]] = event

        region.setdefault("transitions", []).append(trans)
        self._parser._by_id[trans["_id"]] = trans

        self._create_transition_view(sm, trans, src, tgt)
        return trans

    def remove_transition(self, sm_name_or_id: str, trans_id: str) -> bool:
        sm = self._parser.get_state_machine(sm_name_or_id)
        if not sm:
            return False
        region = self._parser.get_region(sm_name_or_id)
        if not region:
            return False
        trans = self._parser.get_transition(sm_name_or_id, trans_id)
        if not trans:
            return False
        return self._remove_transition_internal(sm, region, trans)

    def _remove_transition_internal(self, sm, region, trans) -> bool:
        for ev in trans.get("triggers", []):
            if isinstance(ev, dict) and ev["_id"] in self._parser._by_id:
                del self._parser._by_id[ev["_id"]]

        self._remove_transition_view(sm, trans["_id"])

        try:
            region["transitions"].remove(trans)
        except ValueError:
            pass
        if trans["_id"] in self._parser._by_id:
            del self._parser._by_id[trans["_id"]]
        return True

    def edit_transition(
        self,
        trans_id: str,
        guard: str = None,
        trigger_name: str = None,
        trigger_kind: str = "anyReceive",
        kind: str = None,
    ) -> bool:
        trans = self._parser.by_id(trans_id)
        if not trans or trans.get("_type") != "UMLTransition":
            return False

        if guard is not None:
            trans["guard"] = guard
        if kind is not None:
            trans["kind"] = kind

        if trigger_name is not None:
            for ev in trans.get("triggers", []):
                if isinstance(ev, dict) and ev["_id"] in self._parser._by_id:
                    del self._parser._by_id[ev["_id"]]
            trans["triggers"] = []
            if trigger_name:
                event = _make_element(
                    "UMLEvent",
                    name=trigger_name,
                    kind=trigger_kind,
                    _parent=trans,
                )
                trans["triggers"].append(event)
                self._parser._by_id[event["_id"]] = event

        self._rebuild_transition_view(trans)
        return True

    # -----------------------------------------------------------------------
    # View management
    # -----------------------------------------------------------------------

    def _create_state_view(self, sm: dict, state: dict, x: float, y: float, w: float, h: float):
        diagram = self._parser.get_statechart_diagram(sm["_id"])
        if not diagram:
            return

        name_compartment = _make_element(
            "UMLNameCompartmentView",
            _parent=None,
            model=state,
            subViews=[],
            font=FONT,
            parentStyle=True,
            left=x,
            top=y,
            width=w,
            height=25,
        )

        stereo_label = _make_element(
            "LabelView",
            _parent=name_compartment,
            visible=False,
            font=FONT,
            parentStyle=True,
            left=x,
            top=y,
            height=LINE_HEIGHT,
        )
        name_label = _make_element(
            "LabelView",
            _parent=name_compartment,
            font=FONT_BOLD,
            parentStyle=True,
            left=x + 5,
            top=y + 6,
            width=w - 10,
            height=LINE_HEIGHT,
            text=state.get("name", ""),
        )
        ns_label = _make_element(
            "LabelView",
            _parent=name_compartment,
            visible=False,
            font=FONT,
            parentStyle=True,
            left=x,
            top=y,
            width=50,
            height=LINE_HEIGHT,
            text="(from )",
        )
        prop_label = _make_element(
            "LabelView",
            _parent=name_compartment,
            visible=False,
            font=FONT,
            parentStyle=True,
            left=x,
            top=y,
            height=LINE_HEIGHT,
            horizontalAlignment=1,
        )
        name_compartment["subViews"] = [stereo_label, name_label, ns_label, prop_label]
        name_compartment["stereotypeLabel"] = stereo_label
        name_compartment["nameLabel"] = name_label
        name_compartment["namespaceLabel"] = ns_label
        name_compartment["propertyLabel"] = prop_label

        activity_comp = _make_element(
            "UMLInternalActivityCompartmentView",
            _parent=None,
            model=state,
            visible=False,
            font=FONT,
            parentStyle=True,
            left=x,
            top=y,
            width=10,
            height=10,
        )
        trans_comp = _make_element(
            "UMLInternalTransitionCompartmentView",
            _parent=None,
            model=state,
            visible=False,
            font=FONT,
            parentStyle=True,
            left=x,
            top=y,
            width=10,
            height=10,
        )
        decomp_comp = _make_element(
            "UMLDecompositionCompartmentView",
            _parent=None,
            model=state,
            font=FONT,
            parentStyle=True,
            left=x,
            top=y + 25,
            width=w,
        )

        state_view = _make_element(
            "UMLStateView",
            _parent=diagram,
            model=state,
            subViews=[name_compartment, activity_comp, trans_comp, decomp_comp],
            font=FONT,
            parentStyle=False,
            containerChangeable=True,
            left=x,
            top=y,
            width=w,
            height=h,
            nameCompartment=name_compartment,
            internalActivityCompartment=activity_comp,
            internalTransitionCompartment=trans_comp,
            decompositionCompartment=decomp_comp,
        )

        name_compartment["_parent"] = state_view
        activity_comp["_parent"] = state_view
        trans_comp["_parent"] = state_view
        decomp_comp["_parent"] = state_view

        self._register_view(diagram, state_view)

    def _create_pseudostate_view(self, sm: dict, pseudo: dict, x: float, y: float, w: float, h: float):
        diagram = self._parser.get_statechart_diagram(sm["_id"])
        if not diagram:
            return

        name_label = _make_element(
            "NodeLabelView",
            _parent=None,
            model=pseudo,
            font=FONT,
            parentStyle=False,
            left=x + w + 6,
            top=y + 3,
            width=60,
            height=LINE_HEIGHT,
            alpha=2.356194490192345,
            distance=20,
            text=pseudo.get("name", ""),
        )
        stereo_label = _make_element(
            "NodeLabelView",
            _parent=None,
            model=pseudo,
            visible=False,
            font=FONT,
            parentStyle=False,
            left=x,
            top=y - 20,
            height=LINE_HEIGHT,
            alpha=2.356194490192345,
            distance=35,
        )
        prop_label = _make_element(
            "NodeLabelView",
            _parent=None,
            model=pseudo,
            visible=False,
            font=FONT,
            parentStyle=False,
            left=x + w + 6,
            top=y + h + 6,
            height=LINE_HEIGHT,
            alpha=-2.356194490192345,
            distance=20,
        )

        view = _make_element(
            "UMLPseudostateView",
            _parent=diagram,
            model=pseudo,
            subViews=[name_label, stereo_label, prop_label],
            font=FONT,
            parentStyle=False,
            containerChangeable=True,
            left=x,
            top=y,
            width=w,
            height=h,
            nameLabel=name_label,
            stereotypeLabel=stereo_label,
            propertyLabel=prop_label,
        )
        name_label["_parent"] = view
        stereo_label["_parent"] = view
        prop_label["_parent"] = view

        self._register_view(diagram, view)

    def _create_final_state_view(self, sm: dict, final_state: dict, x: float, y: float):
        diagram = self._parser.get_statechart_diagram(sm["_id"])
        if not diagram:
            return

        view = _make_element(
            "UMLFinalStateView",
            _parent=diagram,
            model=final_state,
            font=FONT,
            parentStyle=False,
            containerChangeable=True,
            left=x,
            top=y,
            width=FINAL_W,
            height=FINAL_H,
        )
        self._register_view(diagram, view)

    def _create_transition_view(self, sm: dict, trans: dict, src_state: dict, tgt_state: dict):
        diagram = self._parser.get_statechart_diagram(sm["_id"])
        if not diagram:
            return
        src_view = self._parser.get_state_view(src_state["_id"])
        tgt_view = self._parser.get_state_view(tgt_state["_id"])
        if not src_view or not tgt_view:
            return

        sx = src_view.get("left", 0) + src_view.get("width", 0) / 2
        sy = src_view.get("top", 0) + src_view.get("height", 0) / 2
        tx = tgt_view.get("left", 0) + tgt_view.get("width", 0) / 2
        ty = tgt_view.get("top", 0) + tgt_view.get("height", 0) / 2

        points = f"{sx:.0f},{sy:.0f};{tx:.0f},{ty:.0f}"

        trigger_text = ""
        for ev in trans.get("triggers", []):
            if isinstance(ev, dict) and ev.get("name"):
                trigger_text = ev["name"]
                break
        if trans.get("guard"):
            if trigger_text:
                trigger_text += f" [{trans['guard']}]"
            else:
                trigger_text = f"[{trans['guard']}]"

        name_label = _make_element(
            "EdgeLabelView",
            _parent=None,
            model=trans,
            font=FONT,
            parentStyle=False,
            left=(sx + tx) / 2,
            top=(sy + ty) / 2 - 15,
            height=LINE_HEIGHT,
            alpha=1.5707963267948966,
            distance=15,
            hostEdge=None,
            edgePosition=1,
            text=trigger_text,
            visible=bool(trigger_text),
        )
        stereo_label = _make_element(
            "EdgeLabelView",
            _parent=None,
            model=trans,
            visible=False,
            font=FONT,
            parentStyle=False,
            left=(sx + tx) / 2,
            top=(sy + ty) / 2 - 30,
            height=LINE_HEIGHT,
            alpha=1.5707963267948966,
            distance=30,
            hostEdge=None,
            edgePosition=1,
        )
        prop_label = _make_element(
            "EdgeLabelView",
            _parent=None,
            model=trans,
            visible=False,
            font=FONT,
            parentStyle=False,
            left=(sx + tx) / 2,
            top=(sy + ty) / 2,
            height=LINE_HEIGHT,
            alpha=-1.5707963267948966,
            distance=15,
            hostEdge=None,
            edgePosition=1,
        )

        view = _make_element(
            "UMLTransitionView",
            _parent=diagram,
            model=trans,
            subViews=[name_label, stereo_label, prop_label],
            font=FONT,
            parentStyle=False,
            head=tgt_view,
            tail=src_view,
            lineStyle=1,
            points=points,
            showVisibility=True,
            nameLabel=name_label,
            stereotypeLabel=stereo_label,
            propertyLabel=prop_label,
        )
        name_label["_parent"] = view
        stereo_label["_parent"] = view
        prop_label["_parent"] = view
        name_label["hostEdge"] = view
        stereo_label["hostEdge"] = view
        prop_label["hostEdge"] = view

        self._register_view(diagram, view)

    def _register_view(self, diagram: dict, view: dict):
        diagram.setdefault("ownedViews", []).append(view)
        self._parser._by_id[view["_id"]] = view
        for sub in view.get("subViews", []):
            if isinstance(sub, dict) and "_id" in sub:
                self._parser._by_id[sub["_id"]] = sub

    def _remove_state_view(self, sm: dict, state_model_id: str):
        diagram = self._parser.get_statechart_diagram(sm["_id"])
        if not diagram:
            return
        to_remove = []
        for view in diagram.get("ownedViews", []):
            if not isinstance(view, dict):
                continue
            model = view.get("model")
            if isinstance(model, dict) and model.get("_id") == state_model_id:
                to_remove.append(view)
        for v in to_remove:
            self._remove_view_recursive(diagram, v)

    def _remove_transition_view(self, sm: dict, trans_model_id: str):
        diagram = self._parser.get_statechart_diagram(sm["_id"])
        if not diagram:
            return
        to_remove = []
        for view in diagram.get("ownedViews", []):
            if not isinstance(view, dict):
                continue
            model = view.get("model")
            if isinstance(model, dict) and model.get("_id") == trans_model_id:
                to_remove.append(view)
        for v in to_remove:
            self._remove_view_recursive(diagram, v)

    def _remove_view_recursive(self, diagram: dict, view: dict):
        for sub in view.get("subViews", []):
            if isinstance(sub, dict):
                self._remove_view_recursive(diagram, sub)
        try:
            diagram["ownedViews"].remove(view)
        except ValueError:
            pass
        if view["_id"] in self._parser._by_id:
            del self._parser._by_id[view["_id"]]

    def _rebuild_state_view(self, sm_name_or_id: str, state: dict):
        sm = self._parser.get_state_machine(sm_name_or_id)
        if not sm:
            return
        old_view = self._parser.get_state_view(state["_id"])
        if old_view:
            x = old_view.get("left", 200)
            y = old_view.get("top", 200)
            w = old_view.get("width", STATE_W)
            h = old_view.get("height", STATE_H)
            self._remove_state_view(sm, state["_id"])
        else:
            x, y, w, h = 200, 200, STATE_W, STATE_H
        self._create_state_view(sm, state, x, y, w, h)

    def _rebuild_transition_view(self, trans: dict):
        for sm in self._parser.get_state_machines():
            diagram = self._parser.get_statechart_diagram(sm["_id"])
            if not diagram:
                continue
            region = self._parser.get_region(sm["_id"])
            if not region:
                continue
            if trans not in region.get("transitions", []):
                continue

            old_view = self._parser.get_transition_view(trans["_id"])
            if old_view:
                self._remove_transition_view(sm, trans["_id"])

            src = trans.get("source")
            tgt = trans.get("target")
            if isinstance(src, dict) and isinstance(tgt, dict):
                self._create_transition_view(sm, trans, src, tgt)
            return


def _vertex_name(ref) -> str:
    if isinstance(ref, dict):
        return ref.get("name", ref.get("_id", "?"))
    return str(ref)


def _event_name_text(event: dict) -> str:
    return event.get("name", "")
