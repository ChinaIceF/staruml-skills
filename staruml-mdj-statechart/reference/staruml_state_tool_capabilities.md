# staruml_state_tool Capabilities Reference

## Supported Diagram Types

This tool supports **only** UML Statechart Diagrams (State Machines) inside StarUML `.mdj` files.

| Diagram Type | Supported? |
|---|---|
| `UMLStatechartDiagram` | **Yes** |
| `UMLStateMachine` | **Yes** |
| `UMLClassDiagram` | No — untouched when present in the same `.mdj` |
| Sequence, Use Case, Activity, Component, Deployment, Package, Object | No |

Multiple `UMLStateMachine` elements can coexist in one `.mdj`. They are direct children of the `Project` element, siblings to `UMLModel`.

---

## Supported Model Elements

| Element | Create | Modify | Delete | Query |
|---|---|---|---|---|
| `UMLStateMachine` | `add-sm` | `rename-sm` | `remove-sm` | `list-sm`, `summary` |
| `UMLRegion` | Auto with SM | — | Cascade with SM | Via parser |
| `UMLStatechartDiagram` | Auto with SM | — | Cascade with SM | Via parser |
| `UMLState` | `add-state` | `rename-state` | `remove-state` | `list-states`, `summary` |
| `UMLPseudostate` | `add-initial`, `add-pseudo` | — | `remove-state` | `list-states` |
| `UMLFinalState` | `add-final` | — | `remove-state` | `list-states` |
| `UMLTransition` | `add-transition` | `edit-transition` (guard/trigger/kind) | `remove-transition` | `list-transitions`, `summary` |
| `UMLEvent` (trigger) | Via `add-transition` or `edit-transition` | `edit-transition` (replaces all) | Cascade with transition | `list-transitions` |
| Guard (string) | `--guard` on `add-transition` | `edit-transition --guard` | — | `list-transitions` |

### Valid Pseudostate Kinds

`initial`, `deepHistory`, `shallowHistory`, `join`, `fork`, `junction`, `choice`, `entryPoint`, `exitPoint`, `terminate`

### Not Supported

- Composite/nested states (no API for sub-regions on `UMLState`)
- Entry/do/exit activities (arrays exist, always empty, no population API)
- Transition effects/actions (arrays exist, always empty, no population API)
- Multiple triggers per transition (API supports one; `edit-transition` replaces all)
- Submachine states (metamodel supports, no API)

---

## Supported View Elements

All view elements are **automatically created and maintained** by the tool. No manual view management needed.

- `UMLStateView` with `UMLNameCompartmentView` (name label + hidden stereotype/namespace/property labels), `UMLInternalActivityCompartmentView`, `UMLInternalTransitionCompartmentView`, `UMLDecompositionCompartmentView`
- `UMLPseudostateView` with `NodeLabelView` labels (name, stereotype, property)
- `UMLFinalStateView` (26×26)
- `UMLTransitionView` with `EdgeLabelView` labels (name showing trigger+guard, hidden stereotype/property)

Views are rebuilt automatically on rename. Views are cascade-deleted on remove.

---

## Supported CLI Commands

All commands: `python -m staruml_state_tool.cli <command> <args...>`

### Read-only Commands

| Command | Args | Output |
|---|---|---|
| `list-sm` | `<file.mdj>` | JSON: `[{id, name, num_states, num_transitions}]` |
| `list-states` | `<file.mdj> <sm_name>` | JSON: states with incoming/outgoing transition details |
| `list-transitions` | `<file.mdj> <sm_name>` | JSON: transitions with source, target, guard, triggers, kind |
| `summary` | `<file.mdj> [sm_name]` | JSON: full state machine summary |

### Modifying Commands (overwrite file in-place)

| Command | Args | Notes |
|---|---|---|
| `create` | `<file.mdj> [project_name] [--with-sm NAME]` | Creates new `.mdj` |
| `add-sm` | `<file.mdj> <name>` | Adds state machine with auto region + diagram |
| `remove-sm` | `<file.mdj> <name>` | Cascade deletes all states/transitions/views |
| `rename-sm` | `<file.mdj> <old> <new>` | Renames state machine only |
| `add-state` | `<file.mdj> <sm> <name> [--x X] [--y Y]` | Default position: (200, 200) |
| `remove-state` | `<file.mdj> <sm> <name>` | Cascade deletes referencing transitions |
| `rename-state` | `<file.mdj> <sm> <old> <new>` | Rebuilds view to update label |
| `add-initial` | `<file.mdj> <sm> [--name N] [--x X] [--y Y]` | Default: name="init", (120, 200) |
| `add-final` | `<file.mdj> <sm> [--name N] [--x X] [--y Y]` | Default: (200, 400) |
| `add-pseudo` | `<file.mdj> <sm> <kind> [--name N] [--x X] [--y Y]` | Kind must be valid (see list above) |
| `add-transition` | `<file.mdj> <sm> <src> <tgt> [--guard G] [--trigger E] [--trigger-kind K]` | Trigger kind: signal/call/change/time/anyReceive (default) |
| `remove-transition` | `<file.mdj> <sm> <trans_id>` | ID from `list-transitions` |
| `edit-transition` | `<file.mdj> <trans_id> [--guard G] [--trigger E] [--trigger-kind K] [--kind K]` | `--kind`: external/internal/local. Setting `--trigger ""` clears triggers. |

---

## Python API Overview

### Primary entry point: `StateDiagram`

```python
from staruml_state_tool.state_diagram import StateDiagram
```

| Method | Signature |
|---|---|
| `StateDiagram.create()` | `create(project_name: str = "Project") -> StateDiagram` |
| `StateDiagram.load()` | `load(filepath: str) -> StateDiagram` |
| `save()` | `save(filepath: str = "")` |
| `list_state_machines()` | `-> List[Dict]` (id, name, num_states, num_transitions) |
| `list_states()` | `(sm_name_or_id: str) -> List[Dict]` |
| `list_transitions()` | `(sm_name_or_id: str) -> List[Dict]` |
| `summary()` | `(sm_name_or_id: str = "") -> Dict[str, Any]` |
| `add_state_machine()` | `(name: str) -> dict` |
| `remove_state_machine()` | `(name_or_id: str) -> bool` |
| `rename_state_machine()` | `(name_or_id: str, new_name: str) -> bool` |
| `add_state()` | `(sm, name, x=200, y=200) -> Optional[dict]` |
| `add_initial()` | `(sm, name="init", x=120, y=200) -> Optional[dict]` |
| `add_final()` | `(sm, name="", x=200, y=400) -> Optional[dict]` |
| `add_pseudostate()` | `(sm, kind, name="", x=200, y=200) -> Optional[dict]` |
| `remove_state()` | `(sm, name_or_id) -> bool` |
| `rename_state()` | `(sm, old_name, new_name) -> bool` |
| `add_transition()` | `(sm, src, tgt, guard="", trigger_name="", trigger_kind="anyReceive") -> Optional[dict]` |
| `remove_transition()` | `(sm, trans_id) -> bool` |
| `edit_transition()` | `(trans_id, guard=None, trigger_name=None, trigger_kind="anyReceive", kind=None) -> bool` |

### Secondary: `StateParser`

```python
from staruml_state_tool.parser import StateParser

p = StateParser().load("file.mdj")
p.get_state_machines()
p.get_state("sm_name", "state_name")
p.get_transitions("sm_name")
p.get_region("sm_name")
p.get_statechart_diagram("sm_name")
p.get_state_view("model_id")
p.get_transition_view("model_id")
```

---

## Important MDJ Structure Rules

The `.mdj` format uses these structural elements. **Do not construct or edit these manually.** The tool manages them.

### Element hierarchy for state machines

```
Project.ownedElements[]
  ├── UMLModel (class diagram stuff, untouched)
  └── UMLStateMachine
      ├── ownedElements[]
      │   └── UMLStatechartDiagram
      │       └── ownedViews[]  (all view elements)
      └── regions[]
          └── UMLRegion
              ├── vertices[]    (UMLState, UMLPseudostate, UMLFinalState)
              └── transitions[] (UMLTransition)
```

### Critical fields

| Field | Purpose | Must NOT edit manually |
|---|---|---|
| `_id` | Globally unique base64 identifier | Yes — ids are auto-generated and cross-referenced |
| `_parent` | `{"$ref": parent_id}` — backlink to container | Yes — must match the containment array |
| `$ref` | `{"$ref": target_id}` — cross-reference to another element | Yes — must point to an existing element |
| `model` | On views: `$ref` to the model element | Yes |
| `source` / `target` | On `UMLTransition`: `$ref` to vertex model elements | Yes |
| `tail` / `head` | On `UMLTransitionView`: `$ref` to state views | Yes |
| `vertices[]` | Containment array on `UMLRegion` | Yes — elements are full typed objects, not `$ref` |
| `transitions[]` | Containment array on `UMLRegion` | Yes |
| `ownedViews[]` | On `UMLStatechartDiagram` | Yes |
| `triggers[]` | On `UMLTransition`: `UMLEvent` elements | Yes — containment |
| `guard` | Plain string on `UMLTransition` | Free-form, safe to edit via API |

### ID generation

IDs follow StarUML's format: `timestamp(16 hex) + counter(4 hex) + random(4 hex)` → custom base64. The tool generates these automatically. Never hardcode or reuse IDs.

---

## Input / Output Conventions

| Aspect | Detail |
|---|---|
| File format | `.mdj` — UTF-8 JSON with tab indentation |
| Encoding | UTF-8, `ensure_ascii=False` |
| Modifying behavior | **Overwrites the input file in-place** |
| Backup | None automatic — copy manually before editing |
| Output path control | CLI: none. Python API: `save(new_filepath)` |
| Dry-run | Not supported |
| Default values | Omitted from output unless in `{visible, horizontalAlignment}` |
| `$ref` serialization | `{"$ref": "..."}` for cross-references; full typed elements for containment |
| Class diagram preservation | Yes — `UMLModel` and its children are untouched |

---

## Statechart Modeling Conventions

The tool does **not enforce** these — the agent must apply them.

- State names: PascalCase (`OnBookshelf`, `BorrowedByUser`)
- One initial pseudostate per state machine
- 0–1 final state
- Trigger names: verb-like (`borrow`, `returnBook`, `start`, `reset`)
- Time triggers: `"after(Ns)"`, `"after(Nd)"` (StarUML convention)
- Guard expressions: C/Java-like booleans (`count > 0`, `door.isLocked()`)
- Non-initial transitions should have at least a trigger or guard
- Guards on same-trigger branches should be mutually exclusive
- All states reachable from initial; all non-final states reach final

---

## Layout and View Behavior

- **No automatic layout** — every state needs explicit `--x`/`--y`
- Default state view size: 80×40 (fixed)
- Default initial pseudostate: 20×20
- Default final state: 26×26
- Transition edge paths: straight lines between view centers (auto-computed)
- Edge labels: positioned radially from edge midpoint
- No font, color, line style, or size customization
- Views are created/rebuilt automatically; no manual view API

---

## Validation Responsibilities

The tool performs **no automatic validation**. The agent must check:

1. Exactly one initial pseudostate (`UMLPseudostate` with kind `"initial"`)
2. 0–1 final state (`UMLFinalState`)
3. All transition source/target names exist in the state machine
4. All non-initial transitions have a trigger or guard
5. All states reachable from initial (BFS on outgoing transitions)
6. All non-final states can reach a final state (if one exists)
7. No duplicate state names within the same state machine
8. Guard expressions are short, evaluator-friendly strings
9. Coordinates are spaced to avoid overlap

Use `list-states`, `list-transitions`, and `summary` outputs to check these.

---

## Known Limitations

| Limitation | Detail |
|---|---|
| Flat states only | No composite states, nested regions, orthogonal regions |
| Single region | Operates on first/only `UMLRegion` |
| No entry/do/exit | Arrays exist, always empty, no API to populate |
| No transition effects | Array exists, always empty, no API |
| One trigger per transition | `add_transition` creates one; `edit-transition` replaces all |
| No auto-layout | Explicit coordinates required |
| No auto-validation | Agent must check manually |
| No visual customization | Font, color, line style, size are fixed |
| In-place overwrite | Modifying commands overwrite input file; no `--output`/`--dry-run` |
| Name-based lookup | Duplicate names resolve to first match |
| Statechart only | No class/sequence/use case/activity diagrams |

---

## Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `State machine 'X' not found` | Name mismatch | Use exact name from `list-sm` |
| `State 'Y' not found in 'X'` | State doesn't exist or wrong SM | Use exact name from `list-states` |
| `Source or target not found` | Transition references renamed/removed state | Check `list-states`; recreate transition |
| `Transition 'Z' not found` | Wrong ID or wrong SM | Use ID from `list-transitions` |
| `ValueError: Invalid pseudostate kind` | Invalid kind string | Use only: initial, deepHistory, shallowHistory, join, fork, junction, choice, entryPoint, exitPoint, terminate |
| File fails to open in StarUML | Corrupt JSON or orphaned `$ref` | Restore from backup; check all `_type`/`_id` fields |
| State has no visible name | View not rebuilt after rename | `rename-state` triggers automatic view rebuild |
| `KeyError: '_id'` | Malformed element without `_id` | File may have been manually edited — restore from backup |
