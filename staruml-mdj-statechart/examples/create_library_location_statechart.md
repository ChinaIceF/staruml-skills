# CLI Example — Library Location Statechart

Creates a book location flow state machine with seven states and transitions including triggers and guards.

```bash
# 1. Create new project
python -m staruml_state_tool.cli create library_room.mdj Library --with-sm BookLocationFSM

# 2. Add initial pseudostate
python -m staruml_state_tool.cli add-initial library_room.mdj BookLocationFSM --name init --x 80 --y 200

# 3. Add states (layout: grid, 180px apart horizontally, 140px vertically)
python -m staruml_state_tool.cli add-state library_room.mdj BookLocationFSM NormalBookshelf     --x 200 --y 80
python -m staruml_state_tool.cli add-state library_room.mdj BookLocationFSM TreasuredBookshelf  --x 380 --y 80
python -m staruml_state_tool.cli add-state library_room.mdj BookLocationFSM ReadingRoom         --x 560 --y 80
python -m staruml_state_tool.cli add-state library_room.mdj BookLocationFSM AppointmentOffice   --x 200 --y 220
python -m staruml_state_tool.cli add-state library_room.mdj BookLocationFSM BorrowedByUser      --x 560 --y 220
python -m staruml_state_tool.cli add-state library_room.mdj BookLocationFSM BorrowReturnOffice  --x 380 --y 360

# 4. Add transitions

# Reading flow
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM init NormalBookshelf
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM NormalBookshelf ReadingRoom       --trigger read --guard "user.hasPermission()"
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM ReadingRoom NormalBookshelf       --trigger "after(4h)"

# Treasured book flow (classification with guard)
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM NormalBookshelf TreasuredBookshelf  --trigger classify --guard "score >= 4"
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM TreasuredBookshelf ReadingRoom      --trigger read

# Appointment flow
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM TreasuredBookshelf AppointmentOffice --trigger requestRead --guard "user.isScholar()"
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM AppointmentOffice ReadingRoom     --trigger pickup
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM AppointmentOffice NormalBookshelf  --trigger "after(24h)"

# Borrowing flow
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM NormalBookshelf BorrowedByUser    --trigger borrow
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM BorrowedByUser BorrowReturnOffice --trigger returnBook
python -m staruml_state_tool.cli add-transition library_room.mdj BookLocationFSM BorrowReturnOffice NormalBookshelf --trigger arrange

# 5. Verify
python -m staruml_state_tool.cli summary library_room.mdj BookLocationFSM
```

## Notes

- Triggers like `read`, `classify`, `borrow` should match method names in the user's codebase.
- Guards like `score >= 4`, `user.hasPermission()` are free-form strings — ensure they match the user's guard evaluation logic.
- All coordinates are explicit to avoid state overlap.
- If modifying an existing file, copy it first: `cp input.mdj input_backup.mdj`.
