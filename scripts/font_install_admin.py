#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys

# Source directory (one level up: ../fonts)
FONT_ROOT = os.path.join(os.path.dirname(os.getcwd()), "fonts")

# Target font directory inside container
FONT_DIR = "/app/fonts"

if not os.path.isdir(FONT_ROOT):
    print(f"Error: not a directory: {FONT_ROOT}")
    sys.exit(1)

os.makedirs(FONT_DIR, exist_ok=True)

installed = 0

for root, dirs, files in os.walk(FONT_ROOT):
    for name in files:
        if name.lower().endswith(".ttf"):
            src = os.path.join(root, name)
            dst = os.path.join(FONT_DIR, name)

            print(f"Installing font: {src}")
            shutil.copy2(src, dst)
            installed += 1

if installed == 0:
    print("No .ttf fonts found.")
    sys.exit(0)

print(f"Copied {installed} fonts. Rebuilding font cache...")

# Rebuild font cache once (fast + correct)
subprocess.run(["fc-cache", "-f", FONT_DIR], check=True)

print("All fonts installed and registered.")
