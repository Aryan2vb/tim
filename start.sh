#!/bin/bash
set -e

echo "🚀 Setting up Aero Voice Bot..."

# 1. Check Python version
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 is required but not found."
    echo "Please install it: brew install python@3.12"
    exit 1
fi

# 2. Clean previous attempts
echo "🧹 Cleaning previous environments (if possible)..."
rm -rf .venv || true
rm -rf uv.lock || true

# 3. Create venv manually (bypass uv cache issues)
echo "📦 Creating virtual environment with Python 3.12..."
python3.12 -m venv .venv
source .venv/bin/activate

# 4. Install dependencies
echo "⬇️ Installing dependencies..."
pip install --upgrade pip
pip install "pipecat-ai[sarvam,google,openai,groq,silero,runner,daily,webrtc]" "python-dotenv"

# 5. Run bot
echo "✅ Setup complete. Starting bot..."
python bot.py --host 0.0.0.0 --port 7860
