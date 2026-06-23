import re

file_path = "frontend/promo.html"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'id=' in line and '<div' in line or '<section' in line or '<form' in line:
        print(f"Line {idx+1}: {line.strip()}")
