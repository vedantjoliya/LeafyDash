import re

file_path = "frontend/promo.html"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "cart" in line.lower() or "split" in line.lower() or "checkout-" in line.lower():
        if idx < 540: # styling range
            print(f"Line {idx+1}: {line.strip()}")
