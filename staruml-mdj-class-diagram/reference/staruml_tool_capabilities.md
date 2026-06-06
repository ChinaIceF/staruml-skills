# staruml_tool Capabilities Reference

## Supported Model Elements

| Element | API | Notes |
|---------|-----|-------|
| `UMLClass` | `add_class()` / `rename_class()` / `remove_class()` / `get_class()` / `find_class()` | Full CRUD |
| `UMLAttribute` | `add_attribute()` / `remove_attribute()` | Per-class, requires view rebuild |
| `UMLOperation` | `add_operation()` / `remove_operation()` | Parameters via `--param` or `parameters` list |
| `UMLParameter` | Created automatically with operations | `direction` values: `in`, `return`, `inout`, `out` |
| `UMLEnumeration` | Created via `add_class()` as `UMLEnumeration` type (not regular UMLClass) | No high-level API for `literals` array |

## Supported Relationships

| Relationship | API | Notes |
|-------------|-----|-------|
| `UMLAssociation` | `add_association()` | Supports `end1_name`, `end2_name`, `end1_multiplicity`, `end2_multiplicity`, `end1_aggregation`, `end2_aggregation`, `end1_navigable`, `end2_navigable` |
| Directed Association | `add_association(..., end2_navigable="navigable")` | `--directed` flag in CLI sets end2 navigable |
| `UMLGeneralization` | `add_generalization()` | Inheritance (child -> parent) |
| `UMLDependency` | `add_dependency()` | Optional `stereotype` and `mapping` parameters |

## Supported Diagram Types

- **UMLClassDiagram** — only

Not supported: UMLSequenceDiagram, UMLUseCaseDiagram, UMLActivityDiagram, UMLStatechartDiagram, UMLComponentDiagram, UMLDeploymentDiagram, UMLPackageDiagram, UMLObjectDiagram.

## CLI Commands

All commands: `python -m staruml_tool.cli <command> <file.mdj> <args...>`

### Inspection (read-only)

| Command | Output |
|---------|--------|
| `list` | JSON: all classes with attributes, operations, relationships, view positions |
| `summary` | JSON: classes + relationships |
| `layout` | Human-readable: classes grouped by layer (y-position), showing UML type, position, and size |
| `rels` | Human-readable: all relationships grouped by type, per-class connectivity degree |

### Creation

| Command | Args |
|---------|------|
| `create` | `<file> [project_name]` — creates Project + UMLModel + UMLClassDiagram |

### Class management

| Command | Args |
|---------|------|
| `add-class` | `<name> [--abstract] [--stereotype ST] [--x X] [--y Y]` |
| `remove-class` | `<name>` |
| `rename-class` | `<old_name> <new_name>` |

### Attribute / Operation management

| Command | Args |
|---------|------|
| `add-attr` | `<class> <name> <type> [--visibility V] [--static]` |
| `remove-attr` | `<class> <name>` |
| `add-op` | `<class> <name> <return_type> [--visibility V] [--static] [--abstract] [--param name:type]...` |
| `remove-op` | `<class> <name>` |

`--param` can be repeated. Format: `name:type` or `name:type:direction` (default direction is `in`).

### Relationship management

| Command | Args |
|---------|------|
| `add-assoc` | `<A> <B> [--directed] [--e1-mult M] [--e2-mult M] [--e1-agg AGG] [--e2-agg AGG] [--e1-nav NAV] [--e2-nav NAV]` |
| `add-gen` | `<child> <parent>` |
| `add-dep` | `<source> <target> [--stereotype ST]` |
| `remove-rel` | `<relationship_id>` |

`--directed` is shorthand for `--e2-nav navigable`.

### Layout

| Command | Args |
|---------|------|
| `auto-layout` | `[--layer-spacing N] [--node-spacing N]` — layered graph layout |

## Python API Overview

```python
from staruml_tool import ClassDiagram

# Load / Create
ClassDiagram.load("file.mdj")          # Open existing
ClassDiagram.create("ProjectName")     # New from scratch

# Save
d.save("output.mdj")                   # Write to file (overwrites!)
d.dumps()                              # JSON string

# Query
d.list_classes()                       # List of class summaries
d.list_relationships()                 # List of relationship summaries
d.get_class("ClassName")               # Single class dict
d.find_class("name_or_id")             # By name or ID

# Add / Remove classes
d.add_class("Name", x=100, y=100, is_abstract=False, stereotype=None,
    attributes=[{"name": "x", "type": "int", "visibility": "private"}, ...],
    operations=[{"name": "foo", "visibility": "public", "parameters": [...]}, ...])
d.remove_class("Name")
d.rename_class("Old", "New")

# Attributes
d.add_attribute("ClassName", {"name": str, "type": str, ...})
d.remove_attribute("ClassName", "attrName")

# Operations
d.add_operation("ClassName", {"name": str, "parameters": [...], ...})
d.remove_operation("ClassName", "opName")

# Relationships
d.add_association("A", "B", ...)
d.add_generalization("Child", "Parent")
d.add_dependency("Source", "Target")
d.remove_relationship("relationship_id")

# Layout
d.auto_layout(start_x=80, start_y=80, layer_spacing=80, node_spacing=80)
```

## Important MDJ Structure Rules

The `.mdj` file is a JSON document with these rules:

1. **Every element** has `_type` (string) and `_id` (16-char base64). Never modify these manually.
2. **Cross-references** use `{"$ref": "<id>"}` format. The writer automatically converts element dicts to `$ref`.
3. **`_parent`** on every child element points to its container via `$ref`. Maintained automatically.
4. **`ownedElements`** is the standard container for model-level children. `ownedViews` is the container for view-level children.
5. **Associations** use `end1.reference` and `end2.reference` to point to the connected classes.
6. **Directed relationships** (generalization, dependency) use `source` and `target`.
7. **Views** reference their model via the `model` field, which is a `$ref` to the model element.

The tool handles all of this. Do NOT construct these structures manually.

## Input / Output Conventions

- **File encoding**: UTF-8
- **JSON indentation**: tabs (`\t`), matching StarUML native format
- **Output**: `save(filepath)` overwrites the target path without backup
- **Recommendation**: always write to a new path (e.g. `result_modified.mdj`) unless you have a backup
- **CLI write commands**: automatically print a diff summary showing what changed

## Known Limitations

1. Only `UMLClassDiagram` is supported. No other diagram types.
2. No high-level API for `UMLInterface`, `UMLEnumeration` literals, `UMLPackage`, `UMLComponent`, `UMLNode`, `UMLConstraint`.
3. No API for Notes, Comments, or free-text annotations.
4. No precise visual styling (font, color, line decoration control). The tool preserves existing styles from the original file but does not expose create/update APIs for them.
5. `edit_property()` can break cross-references if used on reference fields (`_parent`, `model`, `source`, `target`, `end1`, `end2`, etc.).
6. `save()` overwrites without backup. Use version control or copy the file first.
7. File size changes by ~4-8% after round-trip due to default-value omission. This is normal and does not affect StarUML rendering.

## Troubleshooting

| Problem | Check |
|---------|-------|
| Class not found | Run `list` or `summary` to check exact class names (case-sensitive) |
| Relationship not appearing | Run `rels` to inspect all relationships and verify endpoints exist |
| Classes overlap after adding | Run `auto-layout` |
| Unknown command error | Run `python -m staruml_tool.cli` (no args) to see available commands |
| StarUML cannot open file | Verify JSON validity: `python -c "import json; json.load(open('file.mdj'))"` |
| Association arrows missing after save | Ensure you are running the latest version; older versions had a writer bug that dropped edge view attributes |
| auto-layout puts everything in one row | The file may have no generalizations; the tool now uses association-based BFS for layering. Update to latest version. |
