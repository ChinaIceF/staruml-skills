# CLI Example — Book Lifecycle Statechart

Creates a simple book lifecycle state machine from scratch with four states and transitions.

```bash
# 1. Create a new project with a state machine
python -m staruml_state_tool.cli create book_lifecycle.mdj LibrarySystem --with-sm BookFSM

# 2. Add initial, states, and final
python -m staruml_state_tool.cli add-initial book_lifecycle.mdj BookFSM --name init          --x 80  --y 200
python -m staruml_state_tool.cli add-state   book_lifecycle.mdj BookFSM OnBookshelf          --x 200 --y 120
python -m staruml_state_tool.cli add-state   book_lifecycle.mdj BookFSM BorrowedByUser       --x 380 --y 120
python -m staruml_state_tool.cli add-state   book_lifecycle.mdj BookFSM BorrowReturnOffice   --x 380 --y 280
python -m staruml_state_tool.cli add-final   book_lifecycle.mdj BookFSM                      --x 600 --y 120

# 3. Add transitions
python -m staruml_state_tool.cli add-transition book_lifecycle.mdj BookFSM init OnBookshelf
python -m staruml_state_tool.cli add-transition book_lifecycle.mdj BookFSM OnBookshelf BorrowedByUser     --trigger borrow
python -m staruml_state_tool.cli add-transition book_lifecycle.mdj BookFSM BorrowedByUser BorrowReturnOffice --trigger returnBook
python -m staruml_state_tool.cli add-transition book_lifecycle.mdj BookFSM BorrowReturnOffice OnBookshelf     --trigger arrange

# 4. Verify
python -m staruml_state_tool.cli summary book_lifecycle.mdj BookFSM
```

## Notes

- This example creates a new file, so no backup is needed.
- If modifying an existing `.mdj` instead, copy it first: `cp statechart.mdj statechart_backup.mdj`.
- All `--x` and `--y` values are explicit because auto-layout is not supported.
