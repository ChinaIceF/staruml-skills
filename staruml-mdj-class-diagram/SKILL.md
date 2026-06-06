---
name: staruml-mdj-class-diagram
description: Create, inspect, and safely modify StarUML .mdj UML class diagrams using the staruml_tool Python API or CLI. Use this when the user asks to generate UML class diagrams, edit existing .mdj files, add classes, attributes, operations, associations, generalizations, dependencies, or auto-layout class diagrams.
compatibility: opencode
metadata:
  domain: uml
  tool: staruml_tool
  file_type: mdj
  supported_diagram: UMLClassDiagram
---

# StarUML MDJ Class Diagram Skill

## Purpose

This skill enables safe creation, inspection, and modification of StarUML `.mdj` files that contain UML Class Diagrams. The `.mdj` format is a deeply nested JSON document with intricate cross-references (`_id`, `$ref`, `_parent`, `model`, `source`, `target`, `ownedElements`, `ownedViews`). Manually editing this JSON is error-prone. This skill wraps the `staruml_tool` Python package to provide safe, high-level APIs and CLI commands.

Always use `staruml_tool` rather than editing `.mdj` JSON directly.

## When to Use This Skill

- Create a new StarUML `.mdj` class diagram from scratch.
- Add, remove, or rename UML classes in an existing `.mdj`.
- Add or remove attributes and operations on classes.
- Add or remove associations (undirected or directed), generalizations, or dependencies.
- Inspect an existing `.mdj` to understand its class layout, relationships, and connectivity.
- Generate a UML class diagram from natural language requirements or code structure descriptions.
- Auto-layout a class diagram to improve visual readability.

## Do Not Use This Skill When

- The user asks for **sequence diagrams**, **use case diagrams**, **activity diagrams**, **statechart diagrams**, **component diagrams**, **deployment diagrams**, **package diagrams**, or **object diagrams**. None of these are supported. Clearly state: "This skill only supports UML Class Diagrams."
- The user requires precise font, color, line style, or visual styling control. The tool does not expose high-level styling APIs.
- The `.mdj` file is corrupted and cannot be parsed as valid JSON.
- The user needs true `UMLInterface` API, `UMLEnumeration` literal editing, `UMLPackage`, `UMLComponent`, `UMLNode`, or `UMLConstraint` manipulation. These model element types are not exposed via high-level API.

## Supported Scope

**Model elements with high-level API:**

- `UMLClass` (create, rename, delete, query)
- `UMLAttribute` (add, remove per class)
- `UMLOperation` (add, remove per class; parameters supported)
- `UMLParameter` (created automatically with operations)

**Relationships with high-level API:**

- `UMLAssociation` (undirected or directed via `end2_navigable`)
- `UMLGeneralization` (inheritance)
- `UMLDependency` (dashed arrow with optional stereotype)

**Diagram type:**

- `UMLClassDiagram` only

**Not supported / no high-level API:**

- Sequence, Use Case, Activity, Statechart, Component, Deployment, Package, Object diagrams
- True UMLInterface / UMLEnumeration literal / UMLPackage / UMLComponent / UMLNode APIs
- Precise visual styling (fonts, colors, line decorations)

## Core Safety Rules

1. **Never** directly edit raw `.mdj` JSON. Always use `ClassDiagram` Python API or CLI commands.
2. **Before modifying** an existing `.mdj`, inspect it with `summary`, `list`, `layout`, or `rels`.
3. **Never overwrite** the user's only copy. Write to a new file (e.g. `input_modified.mdj`) or create a backup first.
4. **After adding/removing/moving classes**, run `auto-layout`.
5. **After every modification**, validate with at least one inspection command (`summary`, `layout`, or `rels`).
6. **Do not manually construct** `_id`, `$ref`, `_parent`, `model`, `source`, `target`, `ownedElements`, or `ownedViews`.
7. **Avoid `edit_property()`** for reference-type fields unless you fully understand the cross-reference structure.
8. **Do not invent** APIs that do not exist. Check `reference/staruml_tool_capabilities.md` if unsure.
9. **If the user asks for an unsupported diagram type**, state the limitation clearly rather than attempting to fake support.
10. **If UML semantics are ambiguous**, choose conservative defaults (visibility `private` for attributes, `public` for operations, association without multiplicities) and state your assumptions.

## Recommended Interface

Two interfaces are available. Choose based on task complexity.

### CLI (simple, step-by-step edits)

```bash
python -m staruml_tool.cli <command> <file.mdj> <args...>
```

Best for: simple queries, adding a few elements one at a time, small modifications. Every write command prints a diff summary.

### Python API (batch generation, complex logic)

```python
from staruml_tool import ClassDiagram
```

Best for: generating complete diagrams from specs, batch-creating many classes/relationships, programmatic layout control.

## Standard Workflow

```
1. Understand the user's UML class diagram task.
2. Confirm the request is within UML Class Diagram scope.
3. Choose CLI for simple incremental edits, Python API for batch generation.
4. If editing an existing file, inspect it first (summary / list / layout / rels).
5. Create a backup or choose a new output path (e.g. "result_modified.mdj").
6. Apply changes using ClassDiagram API or CLI commands.
7. Run auto-layout after adding or repositioning elements.
8. Validate with summary, layout, and rels.
9. Report: classes created, relationships added, output file path.
10. Mention any assumptions made or unsupported features that were skipped.
```

## CLI Quick Reference

**Inspection (read-only):**
```bash
python -m staruml_tool.cli summary design.mdj
python -m staruml_tool.cli list design.mdj
python -m staruml_tool.cli layout design.mdj
python -m staruml_tool.cli rels design.mdj
```

**Create:**
```bash
python -m staruml_tool.cli create design.mdj "ProjectName"
```

**Classes:**
```bash
python -m staruml_tool.cli add-class design.mdj User --x 100 --y 100
python -m staruml_tool.cli add-class design.mdj Admin --x 300 --y 100 --stereotype entity --abstract
python -m staruml_tool.cli remove-class design.mdj OldClass
python -m staruml_tool.cli rename-class design.mdj Foo Bar
```

**Attributes:**
```bash
python -m staruml_tool.cli add-attr design.mdj User name String
python -m staruml_tool.cli add-attr design.mdj User email String --visibility private
python -m staruml_tool.cli add-attr design.mdj User count Integer --visibility protected --static
python -m staruml_tool.cli remove-attr design.mdj User count
```

**Operations:**
```bash
python -m staruml_tool.cli add-op design.mdj User login boolean --param password:String
python -m staruml_tool.cli add-op design.mdj Service process void --param input:String --param options:Map
python -m staruml_tool.cli add-op design.mdj Calc add Integer --param a:Integer --param b:Integer --static
python -m staruml_tool.cli remove-op design.mdj User login
```

**Relationships:**
```bash
python -m staruml_tool.cli add-assoc design.mdj User Order --e1-mult 1 --e2-mult "0..*"
python -m staruml_tool.cli add-assoc design.mdj A B --directed
python -m staruml_tool.cli add-gen design.mdj Admin User
python -m staruml_tool.cli add-dep design.mdj Service Repository
python -m staruml_tool.cli remove-rel design.mdj <relationship_id>
```

**Layout:**
```bash
python -m staruml_tool.cli auto-layout design.mdj
python -m staruml_tool.cli auto-layout design.mdj --layer-spacing 120 --node-spacing 100
```

## Python API Quick Reference

```python
from staruml_tool import ClassDiagram

# Create from scratch
d = ClassDiagram.create("ProjectName")

# Or load existing
d = ClassDiagram.load("existing.mdj")

# Add a class
d.add_class("User", x=100, y=100, is_abstract=False, stereotype="entity")

# Add an attribute
d.add_attribute("User", {
    "name": "name",
    "type": "String",
    "visibility": "private",
})

# Add an operation
d.add_operation("User", {
    "name": "login",
    "visibility": "public",
    "parameters": [
        {"name": "password", "type": "String", "direction": "in"},
        {"name": "", "type": "boolean", "direction": "return"},
    ],
})

# Add relationships
d.add_association("User", "Order", end1_multiplicity="1", end2_multiplicity="0..*")
d.add_generalization("Admin", "User")
d.add_dependency("Service", "Repository")

# Layout and save
d.auto_layout()
d.save("output.mdj")  # or d.dumps() for JSON string
```

## Class / Attribute / Operation Conventions

- **Class names**: PascalCase (e.g. `OrderService`, `BookCopy`).
- **Attribute names**: camelCase (e.g. `studentId`, `bookShelf`).
- **Operation names**: camelCase (e.g. `processCommand`, `getIsbn`).
- **Visibility**: one of `public`, `private`, `protected`, `package`.
- **Attribute dict**: `{"name": str, "type": str, "visibility": str, "isStatic": bool, "isDerived": bool, "multiplicity": str, "defaultValue": str}`. Only `name` is required.
- **Operation dict**: `{"name": str, "visibility": str, "isAbstract": bool, "isStatic": bool, "parameters": list}`. `name` and `parameters` are required.
- **Parameter dict**: `{"name": str, "type": str, "direction": str}`. `direction` is `"in"`, `"return"`, `"inout"`, or `"out"`. Return type is a parameter with `direction: "return"` and empty `name`.

## Relationship Conventions

- **Inheritance**: `add_generalization(child, parent)` — child inherits from parent.
- **Structural association**: `add_association(A, B)` — default is undirected.
- **Directed association**: `add_association(A, B, end2_navigable="navigable")` or `--directed`.
- **Dependency**: `add_dependency(source, target)` — one class uses/depends on another.
- **Multiplicity**: `"1"`, `"0..1"`, `"0..*"`, `"1..*"`, `"*"`.
- **Aggregation**: `"none"` (default), `"shared"`, `"composite"`.
- **Navigability**: `"unspecified"` (default), `"navigable"`, `"notNavigable"`.
- If semantics are unclear, prefer a simple undirected association and state the assumption.

## Validation Checklist

After every modification, verify:

```
- [ ] File parses as valid JSON.
- [ ] summary shows expected classes and relationships.
- [ ] layout shows reasonable positions with no overlaps.
- [ ] rels shows correct relationship graph and connectivity.
- [ ] Classes have their intended attributes and operations.
- [ ] auto-layout has been applied after adding/moving elements.
- [ ] Original file was backed up or output was written to a new path.
```

## Error Recovery

- **Class not found**: run `list` or `summary` to check exact class names.
- **Relationship looks wrong**: run `rels` to inspect all relationships and their endpoints.
- **Layout has overlaps or is too wide**: run `auto-layout` with larger `--layer-spacing` or `--node-spacing`.
- **StarUML cannot open the file**: revert to backup, check with `python -c "import json; json.load(open('file.mdj'))"` for JSON validity.
- **CLI command fails**: report the exact command and error message. Do not guess a fix.
- **Unsupported feature requested**: state "This skill only supports UML Class Diagrams" and suggest a class-diagram-compatible alternative if one exists.

## Limitations

- **Only UML Class Diagrams** are supported. Sequence, use case, activity, statechart, component, deployment, package, and object diagrams are not.
- No high-level API for true `UMLInterface`, `UMLEnumeration` literals, `UMLPackage`, `UMLComponent`, or `UMLNode`.
- No precise visual styling control (font, color, line style).
- `save(filepath)` overwrites the target without automatic backup. Write to a new path first.
- `edit_property()` can break cross-references if used on reference-type fields.
- CLI `add-op` return type is treated as a parameter with `direction: "return"` and empty name — this matches the tool's internal convention.
