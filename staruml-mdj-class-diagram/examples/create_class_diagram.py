"""
Complete example: create a Library System class diagram from scratch.

Creates four classes (User, Book, Library, Loan) with attributes,
operations, and relationships, then auto-layouts and saves.

Usage:
    python examples/create_class_diagram.py
"""

from staruml_tool import ClassDiagram


d = ClassDiagram.create("LibrarySystem")

# ---- User ----
d.add_class("User", x=100, y=80,
    attributes=[
        {"name": "userId", "type": "String", "visibility": "private"},
        {"name": "name", "type": "String", "visibility": "private"},
        {"name": "email", "type": "String", "visibility": "private"},
        {"name": "maxBooks", "type": "Integer", "visibility": "private"},
    ],
    operations=[
        {"name": "borrowBook", "visibility": "public", "parameters": [
            {"name": "book", "type": "Book", "direction": "in"},
            {"name": "", "type": "boolean", "direction": "return"},
        ]},
        {"name": "returnBook", "visibility": "public", "parameters": [
            {"name": "book", "type": "Book", "direction": "in"},
            {"name": "", "type": "void", "direction": "return"},
        ]},
    ],
)

# ---- Book ----
d.add_class("Book", x=400, y=80,
    attributes=[
        {"name": "isbn", "type": "String", "visibility": "private"},
        {"name": "title", "type": "String", "visibility": "private"},
        {"name": "author", "type": "String", "visibility": "private"},
        {"name": "category", "type": "String", "visibility": "private"},
        {"name": "available", "type": "boolean", "visibility": "private"},
    ],
    operations=[
        {"name": "checkOut", "visibility": "public", "parameters": [
            {"name": "", "type": "void", "direction": "return"},
        ]},
        {"name": "checkIn", "visibility": "public", "parameters": [
            {"name": "", "type": "void", "direction": "return"},
        ]},
        {"name": "isAvailable", "visibility": "public", "parameters": [
            {"name": "", "type": "boolean", "direction": "return"},
        ]},
    ],
)

# ---- Library ----
d.add_class("Library", x=100, y=320,
    attributes=[
        {"name": "name", "type": "String", "visibility": "private"},
        {"name": "address", "type": "String", "visibility": "private"},
        {"name": "books", "type": "List<Book>", "visibility": "private"},
        {"name": "users", "type": "List<User>", "visibility": "private"},
    ],
    operations=[
        {"name": "addBook", "visibility": "public", "parameters": [
            {"name": "book", "type": "Book", "direction": "in"},
            {"name": "", "type": "void", "direction": "return"},
        ]},
        {"name": "removeBook", "visibility": "public", "parameters": [
            {"name": "isbn", "type": "String", "direction": "in"},
            {"name": "", "type": "boolean", "direction": "return"},
        ]},
        {"name": "registerUser", "visibility": "public", "parameters": [
            {"name": "user", "type": "User", "direction": "in"},
            {"name": "", "type": "void", "direction": "return"},
        ]},
        {"name": "searchBook", "visibility": "public", "parameters": [
            {"name": "keyword", "type": "String", "direction": "in"},
            {"name": "", "type": "List<Book>", "direction": "return"},
        ]},
    ],
)

# ---- Loan ----
d.add_class("Loan", x=400, y=320,
    attributes=[
        {"name": "loanId", "type": "String", "visibility": "private"},
        {"name": "borrowDate", "type": "Date", "visibility": "private"},
        {"name": "dueDate", "type": "Date", "visibility": "private"},
        {"name": "returnDate", "type": "Date", "visibility": "private"},
    ],
    operations=[
        {"name": "extendDueDate", "visibility": "public", "parameters": [
            {"name": "days", "type": "Integer", "direction": "in"},
            {"name": "", "type": "void", "direction": "return"},
        ]},
        {"name": "isOverdue", "visibility": "public", "parameters": [
            {"name": "", "type": "boolean", "direction": "return"},
        ]},
    ],
)

# ---- Relationships ----
# Library has a collection of Books
d.add_association("Library", "Book",
    end1_multiplicity="1", end2_multiplicity="0..*")

# User borrows Books through Loans (ternary-like: two associations)
d.add_association("User", "Loan",
    end1_multiplicity="1", end2_multiplicity="0..*",
    end2_navigable="navigable")

d.add_association("Loan", "Book",
    end1_multiplicity="1", end2_multiplicity="1",
    end2_navigable="navigable")

# ---- Layout & Save ----
d.auto_layout()
d.save("library_system.mdj")

print("Saved library_system.mdj")
print("Open with StarUML to view the class diagram.")
