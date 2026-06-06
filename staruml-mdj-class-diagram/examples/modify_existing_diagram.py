"""
Example: load an existing .mdj file, inspect it, add a new class
with attributes and operations, add a relationship, auto-layout,
and save to a NEW file (never overwriting the original).

Usage:
    python examples/modify_existing_diagram.py

Before running, ensure "existing.mdj" exists in the working directory,
or adjust the file path below.
"""

from staruml_tool import ClassDiagram

INPUT_FILE = "existing.mdj"
OUTPUT_FILE = "existing_modified.mdj"

# Load the existing diagram
d = ClassDiagram.load(INPUT_FILE)

# Inspect current state
print("=== Current classes ===")
for c in d.list_classes():
    na = len(c.get("attributes", []))
    no = len(c.get("operations", []))
    nr = len(c.get("relationships", []))
    print(f"  {c['name']} ({c['type']}): {na} attrs, {no} ops, {nr} rels")

# Add a new class: PaymentService
d.add_class("PaymentService", x=100, y=500,
    attributes=[
        {"name": "paymentGateway", "type": "String", "visibility": "private"},
        {"name": "apiKey", "type": "String", "visibility": "private"},
        {"name": "transactionFee", "type": "Double", "visibility": "private"},
    ],
    operations=[
        {"name": "processPayment", "visibility": "public", "parameters": [
            {"name": "amount", "type": "Double", "direction": "in"},
            {"name": "currency", "type": "String", "direction": "in"},
            {"name": "", "type": "boolean", "direction": "return"},
        ]},
        {"name": "refund", "visibility": "public", "parameters": [
            {"name": "transactionId", "type": "String", "direction": "in"},
            {"name": "", "type": "void", "direction": "return"},
        ]},
    ],
)

# Add a dependency: PaymentService depends on an existing class
# NOTE: "Order" is used as an example. If your diagram doesn't have
# an "Order" class, change this to a class that exists, or use
# add_class() to create one first.
existing_classes = [c["name"] for c in d.list_classes()]
target_class = "Order" if "Order" in existing_classes else existing_classes[0]
d.add_dependency("PaymentService", target_class)

# Auto-layout to position the new class and reduce overlaps
d.auto_layout()

# Save to a NEW file (never overwrite the original)
d.save(OUTPUT_FILE)

print(f"\nModified diagram saved to: {OUTPUT_FILE}")
print(f"Added class: PaymentService")
print(f"Added dependency: PaymentService --> {target_class}")
print(f"Original file '{INPUT_FILE}' was NOT modified.")
