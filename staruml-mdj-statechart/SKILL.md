---
name: staruml-mdj-statechart
description: Create, inspect, and safely modify StarUML .mdj UML statechart diagrams and state machines using the staruml_state_tool CLI or Python API. Use when the user asks to generate or edit state diagrams, add states, initial/final/pseudostates, transitions, triggers, guards, or inspect existing UML state machines.
compatibility: opencode
metadata:
  domain: uml
  tool: staruml_state_tool
  file_type: mdj
  supported_diagram: UMLStatechartDiagram
---
# StarUML MDJ Statechart Skill

## Purpose

This skill enables safe creation, inspection, and modification of UML Statechart Diagrams (State Machines) inside StarUML `.mdj` files via the `staruml_state_tool` package.

The `.mdj` format is a deeply nested JSON document with auto-generated IDs, `$ref` cross-references, `_parent` backlinks, `ownedElements`/`regions`/`vertices`/`transitions` containment arrays, `source`/`target` references, and view hierarchies (`ownedViews`, `model`, `tail`, `head`). **Do not construct or edit these structures manually.** Use the CLI or Python API instead.

This tool is **statechart-only**. It does not touch class diagrams or other UML diagram types.

## When to Use This Skill

- Create a new StarUML `.mdj` file with a state machine.
- Add a UML state machine to an existing `.mdj`.
- Add normal states, initial pseudostates, final states, and other pseudostates (choice, junction, fork, join, etc.).
- Add transitions between states, with optional triggers and guards.
- Edit an existing transition's guard, trigger, or kind.
- Rename or remove states and transitions.
- Inspect existing state machines: list states, transitions, guards, triggers.
- Generate a statechart from a natural language description (book lifecycle, order flow, door controller, traffic light, etc.).

## Do Not Use This Skill When

- The task involves **class diagrams, sequence diagrams, use case diagrams, activity diagrams, component diagrams, deployment diagrams, package diagrams, or object diagrams**.
- The task requires **composite states, nested states, multi-region state machines, entry/do/exit activities, or transition effects/actions** — these are not supported by the current tool API.
- The task requires **automatic layout** or **custom visual styling** (font, color, line style, custom edge routing, custom state sizes) — the tool uses fixed defaults.
- The `.mdj` file is **corrupted** and fails to parse.
- The user only wants a **textual explanation** and does not need to generate or modify a `.mdj` file.

## Supported Scope

**Model elements** — create, query, modify, delete:

- `UMLStateMachine`, `UMLRegion` (auto-created), `UMLStatechartDiagram` (auto-created)
- `UMLState` (add, remove, rename, list)
- `UMLPseudostate` with kinds: `initial`, `deepHistory`, `shallowHistory`, `join`, `fork`, `junction`, `choice`, `entryPoint`, `exitPoint`, `terminate`
- `UMLFinalState` (add, remove, list)
- `UMLTransition` (add, remove, edit guard/trigger/kind, list)
- `UMLEvent` — one trigger per transition via the current API
- `guard` — free-form string on each transition

**Not currently supported** (no API, or created as empty with no population API):

- Composite states, nested regions, orthogonal regions
- Entry/do/exit activities on states
- Transition effects/actions
- Multiple triggers per transition
- Automatic layout
- Guard grammar / trigger consistency validation
- Font, color, line style, state size customization

## Core Safety Rules

1. **Do not edit raw `.mdj` JSON.** Use `python -m staruml_state_tool.cli` or the `StateDiagram` Python API.
2. **Inspect before modifying.** Run `list-sm`, `list-states`, `list-transitions`, or `summary` first.
3. **All modifying CLI commands overwrite the input file in-place.** No `--output`, no `--dry-run`, no automatic backup.
4. **Copy the file before destructive edits:** `cp file.mdj file_backup.mdj`.
5. **For batch/complex changes, prefer the Python API** and save to a new path.
6. **Provide explicit `--x` and `--y` coordinates** for every state. Auto-layout does not exist.
7. **No automatic validation.** After modification, run the checklist manually (see Validation Checklist below).
8. **Avoid duplicate state names** in the same state machine — name-based lookups return the first match.
9. **`remove-state` cascades** and deletes all transitions referencing that state.
10. **If unsupported features are requested**, explain the limitation and offer a flat-state approximation.

## Recommended Interface

### CLI (simple incremental edits)

```bash
python -m staruml_state_tool.cli <command> <args...>
```

### Python API (batch generation, inspection, saving to new files)

```python
from staruml_state_tool.state_diagram import StateDiagram
```

## Standard Workflow

```
1. Understand the user's statechart task.
2. Check the task is within scope (flat state machine only).
3. Choose CLI for small edits; Python API for batch generation.
4. If editing an existing file, inspect it first:
     list-sm → list-states → list-transitions → summary
5. Copy the original file if modifying in-place.
6. Create/modify states, pseudostates, and transitions.
7. Provide explicit --x/--y for every state (no auto-layout).
8. Validate with summary/list-states/list-transitions.
9. Run manual validation checklist.
10. Report: changed elements, assumptions, limitations, output file.
```

## CLI Quick Reference

All commands operate on `.mdj` files.

**Read-only (safe, no file modification):**

```bash
python -m staruml_state_tool.cli list-sm            <file.mdj>
python -m staruml_state_tool.cli list-states        <file.mdj> <sm_name>
python -m staruml_state_tool.cli list-transitions   <file.mdj> <sm_name>
python -m staruml_state_tool.cli summary            <file.mdj> [sm_name]
```

**Create new file:**

```bash
python -m staruml_state_tool.cli create <file.mdj> [project_name] [--with-sm SM_NAME]
```

**State machine CRUD (overwrites file):**

```bash
python -m staruml_state_tool.cli add-sm      <file.mdj> <name>
python -m staruml_state_tool.cli remove-sm   <file.mdj> <name>
python -m staruml_state_tool.cli rename-sm   <file.mdj> <old> <new>
```

**States (overwrites file):**

```bash
python -m staruml_state_tool.cli add-state    <file.mdj> <sm_name> <state_name> [--x X] [--y Y]
python -m staruml_state_tool.cli remove-state <file.mdj> <sm_name> <state_name>
python -m staruml_state_tool.cli rename-state <file.mdj> <sm_name> <old> <new>

python -m staruml_state_tool.cli add-initial  <file.mdj> <sm_name> [--name NAME] [--x X] [--y Y]
python -m staruml_state_tool.cli add-final    <file.mdj> <sm_name> [--name NAME] [--x X] [--y Y]
python -m staruml_state_tool.cli add-pseudo   <file.mdj> <sm_name> <kind> [--name NAME] [--x X] [--y Y]
```

**Transitions (overwrites file):**

```bash
python -m staruml_state_tool.cli add-transition    <file.mdj> <sm_name> <source> <target> [--guard G] [--trigger EVENT] [--trigger-kind K]
python -m staruml_state_tool.cli remove-transition <file.mdj> <sm_name> <trans_id>
python -m staruml_state_tool.cli edit-transition   <file.mdj> <trans_id> [--guard G] [--trigger EVENT] [--trigger-kind K] [--kind K]
```

## Python API Quick Reference

```python
from staruml_state_tool.state_diagram import StateDiagram

# Create from scratch or load existing
d = StateDiagram.create(project_name="MyProject")
d = StateDiagram.load("existing.mdj")

# State machine CRUD
d.add_state_machine("OrderFSM")
d.remove_state_machine("OrderFSM")
d.rename_state_machine("Old", "New")

# States (x, y coordinates required — no auto-layout)
d.add_state("OrderFSM", "Pending", x=250, y=200)
d.add_initial("OrderFSM", name="init", x=80, y=200)
d.add_final("OrderFSM", x=600, y=200)
d.add_pseudostate("OrderFSM", "choice", name="Pick", x=350, y=200)
d.remove_state("OrderFSM", "OldState")
d.rename_state("OrderFSM", "OldName", "NewName")

# Transitions
d.add_transition("OrderFSM", "init", "Pending")
d.add_transition("OrderFSM", "Pending", "Shipped",
                 trigger_name="ship", guard="paymentConfirmed")
d.edit_transition("AAAA...", guard="x > 0", trigger_name="go")
d.remove_transition("OrderFSM", "AAAA...")

# Query
d.list_state_machines()      # list[{id, name, num_states, num_transitions}]
d.list_states("OrderFSM")    # states with incoming/outgoing transitions
d.list_transitions("OrderFSM")  # transitions with source, target, guard, triggers
d.summary("OrderFSM")        # full state machine summary

# Save
d.save("output.mdj")
```

## Statechart Modeling Conventions

These are **recommendations** (not tool-enforced):

- **State names**: PascalCase — `OnBookshelf`, `BorrowedByUser`, `ReadingRoom`
- **One initial pseudostate** per state machine
- **0–1 final state** unless the task explicitly requires otherwise
- **Transition triggers**: verb-like — `"borrow"`, `"returnBook"`, `"start"`, `"reset"`, `"after(3s)"`
- **Guard format**: C/Java-like boolean — `"count > 0"`, `"door.isLocked()"`, `"score >= 4"`
- **Guard mutual exclusion**: if two transitions leave the same state on the same trigger, make guards mutually exclusive
- **Reachability**: every state reachable from initial; every non-final state has a path to a final state (if one exists)
- **Initial outgoing transitions** may be triggerless; all other transitions should have at least a trigger or guard

## Layout Guidelines

**No automatic layout exists.** You must provide explicit coordinates.

- Horizontal spacing: **140–180 px** between state centers
- Vertical spacing: **120–160 px** between state centers
- Put the initial state on the **left**, final state on the **right or bottom**
- For lifecycle/flow diagrams: horizontal left-to-right flow
- For location/grid diagrams: use a grid arrangement
- Avoid placing multiple states at the default `(200, 200)`
- Default state view size is 80×40 (fixed, not customizable)
- Initial pseudostate is 20×20; final state is 26×26
- Transition edge paths are computed automatically from view centers

## Validation Checklist

After every modification, verify manually (tool does NOT auto-validate):

```
[ ] Does list-sm show the expected state machine?
[ ] Does list-states show exactly one initial pseudostate?
[ ] Does list-states show 0 or 1 final state?
[ ] Do all transition source/target names reference existing states?
[ ] Do all non-initial transitions have at least a trigger or guard?
[ ] Are all normal states reachable from the initial state (BFS)?
[ ] If a final state exists, can every normal state reach it?
[ ] Are there no duplicate state names in the same state machine?
[ ] Are guard expressions short and evaluator-friendly?
[ ] Are coordinates spaced enough to avoid view overlap?
[ ] Was the original file preserved or backed up?
```

## Error Recovery

| Problem | Action |
|---|---|
| State machine not found | Run `list-sm` to see exact names/IDs |
| State not found | Run `list-states` to see exact names |
| Transition ID unknown | Run `list-transitions` |
| Transition source/target wrong | Remove and recreate with correct names |
| State accidentally removed | Restore from backup (transitions were cascade-deleted) |
| File fails to open in StarUML | Restore from backup; check JSON validity |
| Duplicate state names cause wrong match | Use state IDs from `list-states` instead of names |
| Unsupported feature requested | Explain limitation; offer flat-state approximation |

## Limitations

- **Statechart only** — not class, sequence, use case, activity, etc.
- **Flat states only** — no composite states, nested regions, orthogonal regions
- **Single region** — operates on the first/only region per state machine
- **No entry/do/exit activities** — arrays exist but are always empty
- **No transition effects/actions** — array exists but always empty
- **One trigger per transition** via current API
- **No automatic layout** — explicit coordinates required
- **No automatic validation** — agent must check manually
- **No visual style control** — font, color, size are fixed
- **Modifying commands overwrite in-place** — no `--dry-run`, no `--output`, no backup
