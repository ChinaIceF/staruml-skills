import sys
import json
from .parser import StateParser
from .state_diagram import StateDiagram


COMMANDS = {
    "create": "cmd_create",
    "list-sm": "cmd_list_sm",
    "list-states": "cmd_list_states",
    "list-transitions": "cmd_list_transitions",
    "summary": "cmd_summary",
    "add-sm": "cmd_add_sm",
    "remove-sm": "cmd_remove_sm",
    "rename-sm": "cmd_rename_sm",
    "add-state": "cmd_add_state",
    "remove-state": "cmd_remove_state",
    "rename-state": "cmd_rename_state",
    "add-initial": "cmd_add_initial",
    "add-final": "cmd_add_final",
    "add-pseudo": "cmd_add_pseudo",
    "add-transition": "cmd_add_transition",
    "remove-transition": "cmd_remove_transition",
    "edit-transition": "cmd_edit_transition",
}


def _diagram(filepath: str) -> StateDiagram:
    return StateDiagram.load(filepath)


def cmd_create(args):
    filepath = args[0]
    project_name = args[1] if len(args) > 1 else "Project"
    has_sm = "--with-sm" in args
    sm_name = None
    for i, a in enumerate(args):
        if a == "--with-sm" and i + 1 < len(args):
            sm_name = args[i + 1]

    d = StateDiagram.create(project_name=project_name)
    if has_sm and sm_name:
        d.add_state_machine(sm_name)
    d.save(filepath)
    print(f"+ created '{filepath}' (project: '{project_name}')")
    if has_sm and sm_name:
        print(f"  + state machine '{sm_name}'")


def cmd_list_sm(args):
    filepath = args[0]
    d = _diagram(filepath)
    sms = d.list_state_machines()
    print(json.dumps(sms, indent=2, ensure_ascii=False))


def cmd_list_states(args):
    filepath = args[0]
    sm_name = args[1]
    d = _diagram(filepath)
    states = d.list_states(sm_name)
    print(json.dumps(states, indent=2, ensure_ascii=False))


def cmd_list_transitions(args):
    filepath = args[0]
    sm_name = args[1]
    d = _diagram(filepath)
    trans = d.list_transitions(sm_name)
    print(json.dumps(trans, indent=2, ensure_ascii=False))


def cmd_summary(args):
    filepath = args[0]
    sm_name = args[1] if len(args) > 1 else ""
    d = _diagram(filepath)
    summary = d.summary(sm_name)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def cmd_add_sm(args):
    filepath = args[0]
    name = args[1]
    d = _diagram(filepath)
    sm = d.add_state_machine(name)
    d.save(filepath)
    print(f"+ state machine '{name}' (id: {sm['_id']})")
    print(f"  file: {filepath}")


def cmd_remove_sm(args):
    filepath = args[0]
    name = args[1]
    d = _diagram(filepath)
    ok = d.remove_state_machine(name)
    d.save(filepath)
    if ok:
        print(f"- state machine '{name}'")
    else:
        print(f"State machine '{name}' not found")
    print(f"  file: {filepath}")


def cmd_rename_sm(args):
    filepath = args[0]
    old_name = args[1]
    new_name = args[2]
    d = _diagram(filepath)
    ok = d.rename_state_machine(old_name, new_name)
    d.save(filepath)
    if ok:
        print(f"~ rename state machine '{old_name}' -> '{new_name}'")
    else:
        print(f"State machine '{old_name}' not found")
    print(f"  file: {filepath}")


def cmd_add_state(args):
    filepath = args[0]
    sm_name = args[1]
    state_name = args[2]
    x = 200
    y = 200
    for i, a in enumerate(args):
        if a == "--x" and i + 1 < len(args):
            x = float(args[i + 1])
        elif a == "--y" and i + 1 < len(args):
            y = float(args[i + 1])
    d = _diagram(filepath)
    state = d.add_state(sm_name, state_name, x=x, y=y)
    d.save(filepath)
    if state:
        print(f"+ state '{state_name}' (id: {state['_id']}) in '{sm_name}'")
    else:
        print(f"State machine '{sm_name}' not found")
    print(f"  file: {filepath}")


def cmd_remove_state(args):
    filepath = args[0]
    sm_name = args[1]
    state_name = args[2]
    d = _diagram(filepath)
    ok = d.remove_state(sm_name, state_name)
    d.save(filepath)
    if ok:
        print(f"- state '{state_name}' from '{sm_name}'")
    else:
        print(f"State '{state_name}' not found in '{sm_name}'")
    print(f"  file: {filepath}")


def cmd_rename_state(args):
    filepath = args[0]
    sm_name = args[1]
    old_name = args[2]
    new_name = args[3]
    d = _diagram(filepath)
    ok = d.rename_state(sm_name, old_name, new_name)
    d.save(filepath)
    if ok:
        print(f"~ rename state '{old_name}' -> '{new_name}' in '{sm_name}'")
    else:
        print(f"State '{old_name}' not found in '{sm_name}'")
    print(f"  file: {filepath}")


def cmd_add_initial(args):
    filepath = args[0]
    sm_name = args[1]
    name = "init"
    x = 120
    y = 200
    for i, a in enumerate(args):
        if a == "--name" and i + 1 < len(args):
            name = args[i + 1]
        elif a == "--x" and i + 1 < len(args):
            x = float(args[i + 1])
        elif a == "--y" and i + 1 < len(args):
            y = float(args[i + 1])
    d = _diagram(filepath)
    pseudo = d.add_initial(sm_name, name=name, x=x, y=y)
    d.save(filepath)
    if pseudo:
        print(f"+ initial '{name}' (id: {pseudo['_id']}) in '{sm_name}'")
    else:
        print(f"State machine '{sm_name}' not found")
    print(f"  file: {filepath}")


def cmd_add_final(args):
    filepath = args[0]
    sm_name = args[1]
    name = ""
    x = 200
    y = 400
    for i, a in enumerate(args):
        if a == "--name" and i + 1 < len(args):
            name = args[i + 1]
        elif a == "--x" and i + 1 < len(args):
            x = float(args[i + 1])
        elif a == "--y" and i + 1 < len(args):
            y = float(args[i + 1])
    d = _diagram(filepath)
    final_state = d.add_final(sm_name, name=name, x=x, y=y)
    d.save(filepath)
    if final_state:
        print(f"+ final state (id: {final_state['_id']}) in '{sm_name}'")
    else:
        print(f"State machine '{sm_name}' not found")
    print(f"  file: {filepath}")


def cmd_add_pseudo(args):
    filepath = args[0]
    sm_name = args[1]
    kind = args[2]
    name = ""
    x = 200
    y = 200
    for i, a in enumerate(args):
        if a == "--name" and i + 1 < len(args):
            name = args[i + 1]
        elif a == "--x" and i + 1 < len(args):
            x = float(args[i + 1])
        elif a == "--y" and i + 1 < len(args):
            y = float(args[i + 1])
    d = _diagram(filepath)
    try:
        pseudo = d.add_pseudostate(sm_name, kind, name=name, x=x, y=y)
        d.save(filepath)
        print(f"+ pseudostate '{kind}' (id: {pseudo['_id']}) in '{sm_name}'")
    except ValueError as e:
        print(f"Error: {e}")
        return
    print(f"  file: {filepath}")


def cmd_add_transition(args):
    filepath = args[0]
    sm_name = args[1]
    source = args[2]
    target = args[3]
    guard = ""
    trigger_name = ""
    trigger_kind = "anyReceive"
    for i, a in enumerate(args):
        if a == "--guard" and i + 1 < len(args):
            guard = args[i + 1]
        elif a == "--trigger" and i + 1 < len(args):
            trigger_name = args[i + 1]
        elif a == "--trigger-kind" and i + 1 < len(args):
            trigger_kind = args[i + 1]
    d = _diagram(filepath)
    trans = d.add_transition(
        sm_name, source, target,
        guard=guard, trigger_name=trigger_name, trigger_kind=trigger_kind,
    )
    d.save(filepath)
    if trans:
        desc = f"+ transition {source} -> {target}"
        if trigger_name:
            desc += f" [{trigger_name}]"
        if guard:
            desc += f" [{guard}]"
        print(f"{desc} (id: {trans['_id']})")
    else:
        print(f"Source or target not found in '{sm_name}'")
    print(f"  file: {filepath}")


def cmd_remove_transition(args):
    filepath = args[0]
    sm_name = args[1]
    trans_id = args[2]
    d = _diagram(filepath)
    ok = d.remove_transition(sm_name, trans_id)
    d.save(filepath)
    if ok:
        print(f"- transition '{trans_id}' from '{sm_name}'")
    else:
        print(f"Transition '{trans_id}' not found in '{sm_name}'")
    print(f"  file: {filepath}")


def cmd_edit_transition(args):
    if len(args) < 2:
        print("Usage: edit-transition <file.mdj> <trans_id> [--guard G] [--trigger EVENT] [--trigger-kind K] [--kind K]")
        return
    filepath = args[0]
    trans_id = args[1]
    guard = None
    trigger_name = None
    trigger_kind = "anyReceive"
    kind = None
    for i, a in enumerate(args):
        if a == "--guard" and i + 1 < len(args):
            guard = args[i + 1]
        elif a == "--trigger" and i + 1 < len(args):
            trigger_name = args[i + 1]
        elif a == "--trigger-kind" and i + 1 < len(args):
            trigger_kind = args[i + 1]
        elif a == "--kind" and i + 1 < len(args):
            kind = args[i + 1]

    if guard is None and trigger_name is None and kind is None:
        print("No changes specified. Use --guard, --trigger, --trigger-kind, --kind")
        return

    d = _diagram(filepath)
    ok = d.edit_transition(
        trans_id,
        guard=guard,
        trigger_name=trigger_name,
        trigger_kind=trigger_kind,
        kind=kind,
    )
    d.save(filepath)
    if ok:
        print(f"~ transition '{trans_id}' updated")
    else:
        print(f"Transition '{trans_id}' not found")
    print(f"  file: {filepath}")


def _print_usage():
    print("Usage: python -m staruml_state_tool.cli <command> <args...>")
    print()
    print("Commands:")
    print("  create            <file.mdj> [project_name] [--with-sm SM_NAME]")
    print("  list-sm           <file.mdj>")
    print("  list-states       <file.mdj> <state_machine_name>")
    print("  list-transitions  <file.mdj> <state_machine_name>")
    print("  summary           <file.mdj> [state_machine_name]")
    print("  add-sm            <file.mdj> <name>")
    print("  remove-sm         <file.mdj> <name>")
    print("  rename-sm         <file.mdj> <old_name> <new_name>")
    print("  add-state         <file.mdj> <sm_name> <state_name> [--x X] [--y Y]")
    print("  remove-state      <file.mdj> <sm_name> <state_name>")
    print("  rename-state      <file.mdj> <sm_name> <old_name> <new_name>")
    print("  add-initial       <file.mdj> <sm_name> [--name NAME] [--x X] [--y Y]")
    print("  add-final         <file.mdj> <sm_name> [--name NAME] [--x X] [--y Y]")
    print("  add-pseudo        <file.mdj> <sm_name> <kind> [--name NAME] [--x X] [--y Y]")
    print("                     kind: initial|deepHistory|shallowHistory|join|fork|junction|choice|entryPoint|exitPoint|terminate")
    print("  add-transition    <file.mdj> <sm_name> <source> <target> [--guard G] [--trigger EVENT] [--trigger-kind K]")
    print("  remove-transition <file.mdj> <sm_name> <trans_id>")
    print("  edit-transition   <file.mdj> <trans_id> [--guard G] [--trigger EVENT] [--trigger-kind K] [--kind K]")
    print()


def main():
    if len(sys.argv) < 2:
        _print_usage()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        _print_usage()
        return

    try:
        func_name = COMMANDS[cmd]
        func = globals()[func_name]
        func(args)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
