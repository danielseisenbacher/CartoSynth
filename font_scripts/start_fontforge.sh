#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building Custom Font Using FontForge..."
fontforge -script "$SCRIPT_DIR/create_custom_font.py"
echo "Done Building Custom Font."
