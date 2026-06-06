"""
LLM-friendly CLI for manipulating UML class diagrams in StarUML .mdj files.

Usage:
  python -m staruml_tool.cli <command> <args...>

Commands:
  create       <file.mdj> [project_name]                  Create a new empty .mdj file
  list         <file.mdj>                                 List all classes with attributes and operations (JSON)
  layout       <file.mdj>                                 Show class layout by layer (position, type, size)
  rels         <file.mdj>                                 Show relationship graph and per-class connectivity
  summary      <file.mdj>                                 Full summary of the diagram (classes + relationships in JSON)
  add-class    <file.mdj> <name> [--abstract] [--stereotype ST] [--x X] [--y Y]
  remove-class <file.mdj> <name>
  rename-class <file.mdj> <old_name> <new_name>
  add-attr     <file.mdj> <class_name> <attr_name> <type> [--visibility V] [--static]
  remove-attr  <file.mdj> <class_name> <attr_name>
  add-op       <file.mdj> <class_name> <op_name> <return_type> [--visibility V] [--static] [--abstract]
               [--param name:type]...
  remove-op    <file.mdj> <class_name> <op_name>
  add-assoc    <file.mdj> <class_a> <class_b> [--directed] [--e1-mult M] [--e2-mult M] [--e1-agg AGG] [--e2-agg AGG] [--e1-nav NAV] [--e2-nav NAV]
  remove-rel   <file.mdj> <rel_id>
  add-gen      <file.mdj> <child_class> <parent_class>
  add-dep      <file.mdj> <source> <target> [--stereotype ST]
  auto-layout  <file.mdj> [--cols N]
  summary      <file.mdj>                                 Full summary of the diagram

Each command reads the .mdj file, applies changes, writes back, and prints a summary of changes.
"""

import sys
import json
import copy
from .diagram import ClassDiagram


# ---------------------------------------------------------------------------
# Diff / change-report helpers
# ---------------------------------------------------------------------------

def _snapshot_class(d, name: str) -> dict:
    """Capture a snapshot of a class's state."""
    c = d.get_class(name)
    if not c:
        return {}
    return {
        "name": c.get("name", ""),
        "attributes": [
            {"name": a.get("name", ""), "type": _str(a.get("type")),
             "visibility": a.get("visibility", "public")}
            for a in c.get("attributes", []) if isinstance(a, dict)
        ],
        "operations": [
            {"name": o.get("name", ""), "visibility": o.get("visibility", "public"),
             "parameters": [
                 {"name": p.get("name", ""), "type": _str(p.get("type")),
                  "direction": p.get("direction", "in")}
                 for p in o.get("parameters", []) if isinstance(p, dict)
             ]}
            for o in c.get("operations", []) if isinstance(o, dict)
        ],
    }


def _str(v):
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return v.get("name", "?")
    return str(v) if v else ""


def _class_diff(before: dict, after: dict) -> list:
    """Return a list of change description strings."""
    changes = []
    # Handle new class (before is empty, after has data)
    if not before or not before.get("name"):
        if after and after.get("name"):
            attrs = after.get("attributes", [])
            ops = after.get("operations", [])
            desc = f"+ class {after['name']}"
            if attrs:
                desc += f" ({len(attrs)} attrs)"
            if ops:
                desc += f" ({len(ops)} ops)"
            changes.append(desc)
            for a in attrs:
                changes.append(f"  attr {a['name']}: {a['type']} ({a['visibility']})")
            for o in ops:
                sig = _op_signature(o)
                changes.append(f"  op   {sig}")
            return changes
        return ["(no changes)"]

    # Handle removed class
    if not after or not after.get("name"):
        attrs = before.get("attributes", [])
        ops = before.get("operations", [])
        desc = f"- class {before['name']}"
        if attrs:
            desc += f" ({len(attrs)} attrs)"
        if ops:
            desc += f" ({len(ops)} ops)"
        changes.append(desc)
        for a in attrs:
            changes.append(f"  attr {a['name']}: {a['type']} ({a['visibility']})")
        for o in ops:
            sig = _op_signature(o)
            changes.append(f"  op   {sig}")
        return changes

    # Compare attributes
    b_attrs = {a["name"]: a for a in before.get("attributes", [])}
    a_attrs = {a["name"]: a for a in after.get("attributes", [])}
    added_attrs = set(a_attrs.keys()) - set(b_attrs.keys())
    removed_attrs = set(b_attrs.keys()) - set(a_attrs.keys())
    for name in sorted(added_attrs):
        a = a_attrs[name]
        changes.append(f"+ attr {name}: {a['type']} ({a['visibility']})")
    for name in sorted(removed_attrs):
        a = b_attrs[name]
        changes.append(f"- attr {name}: {a['type']}")

    # Compare operations
    b_ops = {o["name"]: o for o in before.get("operations", [])}
    a_ops = {o["name"]: o for o in after.get("operations", [])}
    added_ops = set(a_ops.keys()) - set(b_ops.keys())
    removed_ops = set(b_ops.keys()) - set(a_ops.keys())
    for name in sorted(added_ops):
        sig = _op_signature(a_ops[name])
        changes.append(f"+ op  {sig}")
    for name in sorted(removed_ops):
        sig = _op_signature(b_ops[name])
        changes.append(f"- op  {sig}")

    return changes if changes else ["(no changes)"]


def _op_signature(op: dict) -> str:
    """Format an operation as a signature string."""
    name = op.get("name", "")
    params = op.get("parameters", [])
    param_strs = []
    ret_type = ""
    for p in params:
        if p["direction"] == "return":
            ret_type = p["type"]
        elif p["name"]:
            pdir = p["direction"]
            prefix = "" if pdir == "in" else f"{pdir} "
            param_strs.append(f"{prefix}{p['name']}: {p['type']}")
        else:
            param_strs.append(p.get("type", ""))
    sig = f"{name}({', '.join(param_strs)})"
    if ret_type:
        sig += f": {ret_type}"
    sig += f" ({op.get('visibility', 'public')})"
    return sig


def _print_diff(filepath: str, summary: str, before_state: dict = None, after_state: dict = None, rel_diff: str = None):
    """Print a diff-like change report."""
    print(f"=== {summary} ===")
    if before_state is not None and after_state is not None:
        diffs = _class_diff(before_state, after_state)
        for d in diffs:
            print(f"  {d}")
    if rel_diff:
        print(f"  {rel_diff}")
    print(f"  file: {filepath}")
    print()


def _diagram(filepath: str) -> ClassDiagram:
    return ClassDiagram.load(filepath)


def cmd_list(args: list):
    filepath = args[0]
    d = _diagram(filepath)
    classes = d.list_classes()
    print(json.dumps(classes, indent=2, ensure_ascii=False))


def cmd_summary(args: list):
    filepath = args[0]
    d = _diagram(filepath)
    summary = {
        "classes": d.list_classes(),
        "relationships": d.list_relationships(),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def cmd_add_class(args: list):
    filepath = args[0]
    name = args[1]
    is_abstract = "--abstract" in args
    stereotype = None
    x = 320
    y = 240
    for i, a in enumerate(args):
        if a == "--stereotype" and i + 1 < len(args):
            stereotype = args[i + 1]
        elif a == "--x" and i + 1 < len(args):
            x = float(args[i + 1])
        elif a == "--y" and i + 1 < len(args):
            y = float(args[i + 1])
    d = _diagram(filepath)
    before = _snapshot_class(d, name)  # should be empty (class doesn't exist)
    elem = d.add_class(name, is_abstract=is_abstract, stereotype=stereotype, x=x, y=y)
    d.save(filepath)
    after = _snapshot_class(d, name)
    _print_diff(filepath, f"add-class {name}", before, after)


def cmd_remove_class(args: list):
    filepath = args[0]
    name = args[1]
    d = _diagram(filepath)
    before = _snapshot_class(d, name)
    ok = d.remove_class(name)
    d.save(filepath)
    _print_diff(filepath, f"remove-class {name}", before, {})


def cmd_rename_class(args: list):
    filepath = args[0]
    old_name = args[1]
    new_name = args[2]
    d = _diagram(filepath)
    before = _snapshot_class(d, old_name)
    ok = d.rename_class(old_name, new_name)
    d.save(filepath)
    after = _snapshot_class(d, new_name) if ok else None
    _print_diff(filepath, f"rename-class {old_name} -> {new_name}", before, after or {})


def cmd_add_attr(args: list):
    filepath = args[0]
    class_name = args[1]
    attr_name = args[2]
    attr_type = args[3]
    visibility = "private"
    is_static = False
    for i, a in enumerate(args):
        if a == "--visibility" and i + 1 < len(args):
            visibility = args[i + 1]
    if "--static" in args:
        is_static = True
    d = _diagram(filepath)
    before = _snapshot_class(d, class_name)
    attr = d.add_attribute(class_name, {
        "name": attr_name,
        "type": attr_type,
        "visibility": visibility,
        "isStatic": is_static,
    })
    d.save(filepath)
    after = _snapshot_class(d, class_name) if attr else None
    _print_diff(filepath, f"add-attr {class_name}.{attr_name}",
                before, after or {})


def cmd_remove_attr(args: list):
    filepath = args[0]
    class_name = args[1]
    attr_name = args[2]
    d = _diagram(filepath)
    before = _snapshot_class(d, class_name)
    ok = d.remove_attribute(class_name, attr_name)
    d.save(filepath)
    after = _snapshot_class(d, class_name) if ok else None
    _print_diff(filepath, f"remove-attr {class_name}.{attr_name}",
                before, after or {})


def cmd_add_op(args: list):
    filepath = args[0]
    class_name = args[1]
    op_name = args[2]
    return_type = args[3] if len(args) > 3 else ""
    visibility = "public"
    is_static = False
    is_abstract = False
    params = []

    # Scan for flag options and --param entries
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--visibility" and i + 1 < len(args):
            visibility = args[i + 1]
            i += 2
        elif a == "--static":
            is_static = True
            i += 1
        elif a == "--abstract":
            is_abstract = True
            i += 1
        elif a == "--param" and i + 1 < len(args):
            param_str = args[i + 1]
            # Parse "name:type" or "name:type:direction" format
            parts = param_str.split(":")
            p_name = parts[0].strip()
            p_type = parts[1].strip() if len(parts) > 1 else ""
            p_dir = parts[2].strip() if len(parts) > 2 else "in"
            params.append({"name": p_name, "type": p_type, "direction": p_dir})
            i += 2
        else:
            i += 1

    if return_type and not any(p.get("direction") == "return" for p in params):
        params.insert(0, {"name": "", "type": return_type, "direction": "return"})

    d = _diagram(filepath)
    before = _snapshot_class(d, class_name)
    op = d.add_operation(class_name, {
        "name": op_name,
        "visibility": visibility,
        "isStatic": is_static,
        "isAbstract": is_abstract,
        "parameters": params,
    })
    d.save(filepath)
    after = _snapshot_class(d, class_name) if op else None
    _print_diff(filepath, f"add-op {class_name}.{op_name}",
                before, after or {})


def cmd_remove_op(args: list):
    filepath = args[0]
    class_name = args[1]
    op_name = args[2]
    d = _diagram(filepath)
    before = _snapshot_class(d, class_name)
    ok = d.remove_operation(class_name, op_name)
    d.save(filepath)
    after = _snapshot_class(d, class_name) if ok else None
    _print_diff(filepath, f"remove-op {class_name}.{op_name}",
                before, after or {})


def cmd_add_assoc(args: list):
    filepath = args[0]
    class_a = args[1]
    class_b = args[2]
    e1_agg = "none"
    e2_agg = "none"
    e1_mult = ""
    e2_mult = ""
    e1_nav = "unspecified"
    e2_nav = "unspecified"
    directed = "--directed" in args
    for i, a in enumerate(args):
        if a == "--e1-agg" and i + 1 < len(args):
            e1_agg = args[i + 1]
        elif a == "--e2-agg" and i + 1 < len(args):
            e2_agg = args[i + 1]
        elif a == "--e1-mult" and i + 1 < len(args):
            e1_mult = args[i + 1]
        elif a == "--e2-mult" and i + 1 < len(args):
            e2_mult = args[i + 1]
        elif a == "--e1-nav" and i + 1 < len(args):
            e1_nav = args[i + 1]
        elif a == "--e2-nav" and i + 1 < len(args):
            e2_nav = args[i + 1]
    if directed:
        e2_nav = "navigable"
    d = _diagram(filepath)
    rel = d.add_association(
        class_a, class_b,
        end1_aggregation=e1_agg,
        end2_aggregation=e2_agg,
        end1_multiplicity=e1_mult,
        end2_multiplicity=e2_mult,
        end1_navigable=e1_nav,
        end2_navigable=e2_nav,
    )
    d.save(filepath)
    if rel:
        arrow = " -> " if (e2_nav == "navigable" or directed) else " -- "
        desc = f"\n  + association {class_a}{arrow}{class_b}"
        if e1_mult:
            desc += f"\n    end1 multiplicity: {e1_mult}"
        if e2_mult:
            desc += f"\n    end2 multiplicity: {e2_mult}"
        if e1_agg != "none":
            desc += f"\n    end1 aggregation: {e1_agg}"
        if e2_agg != "none":
            desc += f"\n    end2 aggregation: {e2_agg}"
        if e1_nav != "unspecified":
            desc += f"\n    end1 navigable: {e1_nav}"
        if e2_nav != "unspecified":
            desc += f"\n    end2 navigable: {e2_nav}"
        _print_diff(filepath, f"add-assoc {class_a}{arrow}{class_b}", rel_diff=desc)
    else:
        print(f"One or both classes not found: '{class_a}', '{class_b}'")


def cmd_remove_rel(args: list):
    filepath = args[0]
    rel_id = args[1]
    d = _diagram(filepath)
    rels_before = d.list_relationships()
    rel_info = next((r for r in rels_before if r["id"] == rel_id), None)
    ok = d.remove_relationship(rel_id)
    d.save(filepath)
    if rel_info:
        desc = f"\n  - {rel_info['type']} (id: {rel_id})"
        for k, v in rel_info.items():
            if k not in ("id", "type"):
                desc += f"\n    {k}: {v}"
        _print_diff(filepath, f"remove-rel {rel_id}", rel_diff=desc)
    else:
        print(f"Relationship '{rel_id}' not found")


def cmd_add_gen(args: list):
    filepath = args[0]
    child = args[1]
    parent = args[2]
    d = _diagram(filepath)
    rel = d.add_generalization(child, parent)
    d.save(filepath)
    if rel:
        desc = f"\n  + generalization {child} -> {parent}"
        _print_diff(filepath, f"add-gen {child} -> {parent}", rel_diff=desc)
    else:
        print(f"One or both classes not found: '{child}', '{parent}'")


def cmd_add_dep(args: list):
    filepath = args[0]
    source = args[1]
    target = args[2]
    stereotype = None
    for i, a in enumerate(args):
        if a == "--stereotype" and i + 1 < len(args):
            stereotype = args[i + 1]
    d = _diagram(filepath)
    rel = d.add_dependency(source, target, stereotype=stereotype or "")
    d.save(filepath)
    if rel:
        desc = f"\n  + dependency {source} --> {target}"
        if stereotype:
            desc += f"\n    stereotype: <<{stereotype}>>"
        _print_diff(filepath, f"add-dep {source} --> {target}", rel_diff=desc)
    else:
        print(f"One or both classes not found: '{source}', '{target}'")


def cmd_auto_layout(args: list):
    filepath = args[0]
    layer_spacing = 100
    node_spacing = 60
    for i, a in enumerate(args):
        if a == "--layer-spacing" and i + 1 < len(args):
            layer_spacing = int(args[i + 1])
        elif a == "--node-spacing" and i + 1 < len(args):
            node_spacing = int(args[i + 1])
    d = _diagram(filepath)
    d.auto_layout(layer_spacing=layer_spacing, node_spacing=node_spacing)
    d.save(filepath)
    _print_diff(filepath, f"auto-layout (layered, relationship-aware)",
                rel_diff=f"\n  rearrangement: layered layout by generalization hierarchy\n  associations: grouped within same layer")


def cmd_create(args: list):
    filepath = args[0]
    project_name = args[1] if len(args) > 1 else "UML"
    d = ClassDiagram.create(project_name=project_name)
    d.save(filepath)
    _print_diff(filepath, f"create {project_name}",
                {}, {"name": project_name, "attributes": [], "operations": []},
                rel_diff=f"\n  + Project '{project_name}' created\n  + UMLModel 'Model'\n  + UMLClassDiagram 'Main'")


def cmd_layout(args: list):
    """Print class layout positions sorted by layer (top) then column (left)."""
    filepath = args[0]
    d = _diagram(filepath)
    p = d._parser
    classes = p.get_diagram_classes()
    entries = []
    for c in classes:
        v = p.get_view_for_model(c["_id"])
        if v:
            entries.append({
                "name": c.get("name", "?"),
                "type": c.get("_type", "?"),
                "left": v.get("left") or 0,
                "top": v.get("top") or 0,
                "width": v.get("width") or 0,
                "height": v.get("height") or 0,
            })
    entries.sort(key=lambda e: (e["top"], e["left"]))
    if not entries:
        print("(no class views found)")
        return
    # Compute layer info
    layers = {}
    for e in entries:
        layers.setdefault(e["top"], []).append(e)
    print(f"Classes: {len(entries)} in {len(layers)} layer(s)")
    for y in sorted(layers):
        items = layers[y]
        print(f"  y={y:.0f} ({len(items)} class(es)):")
        for e in items:
            print(f"    {e['type']:30s} {e['name']:30s} pos=({e['left']:6.0f},{e['top']:6.0f})  size=({e['width']:.0f}x{e['height']:.0f})")


def cmd_rels(args: list):
    """Print relationship graph: associations, generalizations, dependencies, and per-class degree."""
    filepath = args[0]
    d = _diagram(filepath)
    p = d._parser
    all_ids = {c["_id"]: c["name"] for c in p.get_diagram_classes()}
    rels = p.get_relationships()

    if not rels:
        print("(no relationships found)")
        return

    # Group by type
    print(f"Relationships: {len(rels)} total")
    for t in ("UMLAssociation", "UMLGeneralization", "UMLDependency",
              "UMLInterfaceRealization", "UMLRealization", "UMLAbstraction"):
        of_type = [r for r in rels if r["_type"] == t]
        if not of_type:
            continue
        print(f"\n  [{t}] ({len(of_type)}):")
        for r in of_type:
            if t == "UMLAssociation":
                e1 = r.get("end1")
                e2 = r.get("end2")
                ref1 = e1.get("reference") if isinstance(e1, dict) else None
                ref2 = e2.get("reference") if isinstance(e2, dict) else None
                n1 = ref1.get("name", "?") if isinstance(ref1, dict) else "?"
                n2 = ref2.get("name", "?") if isinstance(ref2, dict) else "?"
                nav1 = e1.get("navigable", "") if isinstance(e1, dict) else ""
                nav2 = e2.get("navigable", "") if isinstance(e2, dict) else ""
                dir_str = " -> " if nav2 == "navigable" or nav1 == "navigable" else " -- "
                print(f"    {n1}{dir_str}{n2}")
            else:
                src = r.get("source")
                tgt = r.get("target")
                sn = src.get("name", "?") if isinstance(src, dict) else "?"
                tn = tgt.get("name", "?") if isinstance(tgt, dict) else "?"
                print(f"    {sn}  ->  {tn}")

    # Per-class degree summary
    degree = {name: {"assoc": 0, "gen_in": 0, "gen_out": 0, "dep": 0} for name in all_ids.values()}
    for r in rels:
        if r["_type"] == "UMLAssociation":
            e1 = r.get("end1"); e2 = r.get("end2")
            ref1 = e1.get("reference") if isinstance(e1, dict) else None
            ref2 = e2.get("reference") if isinstance(e2, dict) else None
            n1 = ref1.get("name") if isinstance(ref1, dict) else None
            n2 = ref2.get("name") if isinstance(ref2, dict) else None
            if n1 in degree: degree[n1]["assoc"] += 1
            if n2 in degree: degree[n2]["assoc"] += 1
        elif r["_type"] == "UMLGeneralization":
            sn = r.get("source", {}).get("name") if isinstance(r.get("source"), dict) else None
            tn = r.get("target", {}).get("name") if isinstance(r.get("target"), dict) else None
            if sn in degree: degree[sn]["gen_out"] += 1
            if tn in degree: degree[tn]["gen_in"] += 1
        else:
            sn = r.get("source", {}).get("name") if isinstance(r.get("source"), dict) else None
            tn = r.get("target", {}).get("name") if isinstance(r.get("target"), dict) else None
            if sn in degree: degree[sn]["dep"] += 1
            if tn in degree: degree[tn]["dep"] += 1

    # Sort by total links descending
    totals = [(n, d["assoc"] + d["gen_in"] + d["gen_out"] + d["dep"], d) for n, d in degree.items()]
    totals.sort(key=lambda x: -x[1])
    print(f"\n  Class connectivity (total links):")
    for name, total, d in totals:
        parts = []
        if d["assoc"]: parts.append(f"assoc:{d['assoc']}")
        if d["gen_in"]: parts.append(f"gen-in:{d['gen_in']}")
        if d["gen_out"]: parts.append(f"gen-out:{d['gen_out']}")
        if d["dep"]: parts.append(f"dep:{d['dep']}")
        if not parts:
            parts = ["--"]
        print(f"    {name:30s} degree={total}  ({', '.join(parts)})")


COMMANDS = {
    "list": cmd_list,
    "summary": cmd_summary,
    "layout": cmd_layout,
    "rels": cmd_rels,
    "create": cmd_create,
    "add-class": cmd_add_class,
    "remove-class": cmd_remove_class,
    "rename-class": cmd_rename_class,
    "add-attr": cmd_add_attr,
    "remove-attr": cmd_remove_attr,
    "add-op": cmd_add_op,
    "remove-op": cmd_remove_op,
    "add-assoc": cmd_add_assoc,
    "remove-rel": cmd_remove_rel,
    "add-gen": cmd_add_gen,
    "add-dep": cmd_add_dep,
    "auto-layout": cmd_auto_layout,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m staruml_tool.cli <command> <args...>")
        print("\nCommands:")
        for name in sorted(COMMANDS.keys()):
            print(f"  {name}")
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        print("Available commands:", ", ".join(sorted(COMMANDS.keys())))
        return

    try:
        COMMANDS[cmd](args)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
