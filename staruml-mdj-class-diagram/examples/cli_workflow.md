# CLI Workflow: Create a Class Diagram from Scratch

This workflow demonstrates building a simple class diagram entirely via the CLI,
with validation at each step.

## 1. Create a new empty .mdj file

```bash
python -m staruml_tool.cli create library.mdj "LibrarySystem"
```

Diff output shows the Project, UMLModel, and UMLClassDiagram were created.

## 2. Add classes

```bash
python -m staruml_tool.cli add-class library.mdj User --x 100 --y 100
python -m staruml_tool.cli add-class library.mdj Book --x 400 --y 100
python -m staruml_tool.cli add-class library.mdj Loan --x 700 --y 100
```

Each command prints a diff showing `+ class <Name>`.

## 3. Add attributes

```bash
python -m staruml_tool.cli add-attr library.mdj User userId String --visibility private
python -m staruml_tool.cli add-attr library.mdj User name String --visibility private
python -m staruml_tool.cli add-attr library.mdj Book isbn String --visibility private
python -m staruml_tool.cli add-attr library.mdj Book title String --visibility private
python -m staruml_tool.cli add-attr library.mdj Loan loanId String --visibility private
python -m staruml_tool.cli add-attr library.mdj Loan dueDate Date --visibility private
```

Each prints `+ attr <name>: <type> (<visibility>)`.

## 4. Add operations

```bash
python -m staruml_tool.cli add-op library.mdj User borrowBook boolean --param book:Book
python -m staruml_tool.cli add-op library.mdj User returnBook void --param book:Book
python -m staruml_tool.cli add-op library.mdj Book isAvailable boolean
python -m staruml_tool.cli add-op library.mdj Loan isOverdue boolean
```

Each prints `+ op  <signature> (<visibility>)`.

## 5. Add relationships

```bash
python -m staruml_tool.cli add-assoc library.mdj User Loan --e1-mult 1 --e2-mult "0..*" --directed
python -m staruml_tool.cli add-assoc library.mdj Loan Book --e1-mult 1 --e2-mult 1 --directed
```

Each prints `+ association A -> B` with multiplicity details.

## 6. Auto-layout

```bash
python -m staruml_tool.cli auto-layout library.mdj
```

Positions classes to avoid overlaps and group related classes together.

## 7. Validate the result

```bash
# See all classes with their attributes and operations (JSON)
python -m staruml_tool.cli summary library.mdj

# See class positions grouped by layer
python -m staruml_tool.cli layout library.mdj

# See the relationship graph and per-class connectivity
python -m staruml_tool.cli rels library.mdj
```

## 8. Open in StarUML

Open `library.mdj` in StarUML to verify the class diagram renders correctly.

## Safety notes

- The `auto-layout` command is **essential** after adding multiple classes — otherwise they may overlap.
- Run `layout` or `rels` after every batch of changes to verify correctness.
- If you need to preserve the original state, copy the file first: `cp library.mdj library_backup.mdj`.
