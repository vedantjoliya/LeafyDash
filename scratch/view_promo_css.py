import sys

file_path = "frontend/promo.html"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_snippet(start_line, end_line):
    print(f"--- Lines {start_line} to {end_line} ---")
    for i in range(start_line - 1, min(end_line, len(lines))):
        print(f"{i+1}: {lines[i]}", end="")
    print()

print_snippet(300, 420)
print_snippet(421, 540)
