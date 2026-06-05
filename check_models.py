#!/usr/bin/env python3
"""
Script to analyze model responsibilities and check if they are being followed.
"""
import ast
import inspect
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Parse the main file
with open('xauusd_god_bot.py', 'r') as f:
    source = f.read()

tree = ast.parse(source)

# Find all classes that inherit from BaseModel
models = []
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'BaseModel':
                models.append(node.name)

print(f"Found {len(models)} model classes inheriting from BaseModel:")
for m in models:
    print(f"  - {m}")

# Now we need to examine each model's train method.
# We'll use regex to find train methods and see if they contain actual training code.
import re

with open('xauusd_god_bot.py', 'r') as f:
    lines = f.readlines()

# Find each model's train method
current_class = None
in_train = False
train_lines = []
train_methods = {}

for i, line in enumerate(lines):
    # Detect class definitions
    class_match = re.match(r'^class (\w+)\(BaseModel\):', line)
    if class_match:
        current_class = class_match.group(1)
        in_train = False
        train_lines = []
        continue
    
    if current_class is None:
        continue
    
    # Detect train method
    if re.match(r'    def train\(self, X.*?, y.*?\) -> None:', line):
        in_train = True
        train_lines = [line]
        continue
    
    if in_train:
        # End of method when we hit another method or class
        if re.match(r'    def \w+\(self', line) or re.match(r'^class ', line):
            train_methods[current_class] = ''.join(train_lines)
            in_train = False
            train_lines = []
        else:
            train_lines.append(line)

if in_train:
    train_methods[current_class] = ''.join(train_lines)

print(f"\nFound {len(train_methods)} train methods.")
print("\nAnalysis of each model's train method:")
for model, code in train_methods.items():
    # Check if the train method does anything besides setting flags
    # Simple heuristic: if it contains "self.model.fit" or "self.model.learn" or "self.actor" etc.
    # or if it contains loops (for, while) or assignments to self.model
    lines = code.split('\n')
    meaningful = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') or stripped == '':
            continue
        if 'self.is_trained = True' in stripped:
            continue
        if 'self.last_train_time' in stripped:
            continue
        if 'self.train_count' in stripped:
            continue
        # Check for any actual training logic
        if any(keyword in stripped for keyword in ['fit', 'learn', 'train_on_batch', 'update', 'optimize', 'fit_', 'partial_fit']):
            meaningful = True
            break
        # Check for loops
        if stripped.startswith('for ') or stripped.startswith('while '):
            meaningful = True
            break
        # Check for model assignment
        if 'self.model =' in stripped and 'self.model = None' not in stripped:
            meaningful = True
            break
    
    print(f"\n{model}:")
    print(f"  Length: {len(train_lines)} lines")
    if meaningful:
        print("  Status: ✅ Contains actual training logic")
    else:
        print("  Status: ❌ Only sets flags (no actual training)")
        print("  Code snippet:")
        for line in train_lines[:5]:
            print(f"    {line.rstrip()}")
        if len(train_lines) > 5:
            print(f"    ... ({len(train_lines)-5} more lines)")