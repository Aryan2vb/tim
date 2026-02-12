#!/bin/bash
set -e

echo "🧹 Clearing development caches..."

# 1. Clear uv cache (fixes 'Operation not permitted' errors)
if [ -d "$HOME/.cache/uv" ]; then
    echo "Removing $HOME/.cache/uv..."
    rm -rf "$HOME/.cache/uv"
fi

if [ -d "$HOME/.uv" ]; then
    echo "Removing $HOME/.uv..."
    rm -rf "$HOME/.uv"
fi

# 2. Clear pip cache
echo "Clearing pip cache..."
pip cache purge 2>/dev/null || rm -rf "$HOME/Library/Caches/pip"

# 3. Clean local project state
echo "Cleaning local project artifacts (.venv, uv.lock, __pycache__)..."
rm -rf .venv
rm -rf uv.lock
find . -type d -name "__pycache__" -exec rm -rf {} +

echo "✨ All caches cleared! You can now run './start.sh' to start fresh."
