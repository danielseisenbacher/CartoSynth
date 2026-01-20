#!/usr/bin/env bash
set -e

echo "Building Custom Font Using FontForge..."
fontforge -script /workspaces/SynthMap/scripts/create_custom_font.py
echo "Done Building Custom Font."
