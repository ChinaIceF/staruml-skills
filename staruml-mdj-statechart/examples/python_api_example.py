"""
Python API example for staruml_state_tool.

Creates a book lifecycle state machine using the StateDiagram API
and saves it to a new .mdj file without overwriting any existing files.
"""

from staruml_state_tool.state_diagram import StateDiagram


def build_book_lifecycle():
    # Create a new project (in-memory only until save)
    d = StateDiagram.create(project_name="LibrarySystem")

    # Add a state machine
    sm = d.add_state_machine("BookFSM")
    print(f"Created state machine: {sm['_id']}")

    # Add states with explicit positions (no auto-layout)
    d.add_initial("BookFSM", name="init", x=80, y=200)
    d.add_state("BookFSM", "OnBookshelf", x=200, y=120)
    d.add_state("BookFSM", "BorrowedByUser", x=380, y=120)
    d.add_state("BookFSM", "BorrowReturnOffice", x=380, y=280)
    d.add_final("BookFSM", x=600, y=120)

    # Add transitions
    d.add_transition("BookFSM", "init", "OnBookshelf")
    d.add_transition("BookFSM", "OnBookshelf", "BorrowedByUser",
                     trigger_name="borrow")
    d.add_transition("BookFSM", "BorrowedByUser", "BorrowReturnOffice",
                     trigger_name="returnBook")
    d.add_transition("BookFSM", "BorrowReturnOffice", "OnBookshelf",
                     trigger_name="arrange")

    # Query
    print("\nState machines:")
    for sm in d.list_state_machines():
        print(f"  {sm['name']}: {sm['num_states']} states, {sm['num_transitions']} transitions")

    print("\nStates:")
    for s in d.list_states("BookFSM"):
        print(f"  {s['name']} ({s['type']}): {len(s['outgoing'])} outgoing")

    print("\nTransitions:")
    for t in d.list_transitions("BookFSM"):
        trigger = t['triggers'][0] if t['triggers'] else '(none)'
        guard = t['guard'] if t['guard'] else '(none)'
        print(f"  {t['source']} -> {t['target']}  trigger={trigger}  guard={guard}")

    # Save to a new file (does not overwrite any existing file)
    output = "book_lifecycle_api.mdj"
    d.save(output)
    print(f"\nSaved to {output}")

    return d


if __name__ == "__main__":
    build_book_lifecycle()
