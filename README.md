# Aero — Multilingual Voice Bot

Ultra-fast, multilingual voice assistant built with **Pipecat**, **Sarvam AI**, and **Google Gemini**.

## Architecture

```
🎤 Browser Mic → WebRTC → Silero VAD → Sarvam STT → Gemini LLM → Sarvam TTS → WebRTC → 🔊 Speaker
```

| Component | Provider                           | Role                            |
| --------- | ---------------------------------- | ------------------------------- |
| Transport | SmallWebRTC (local) / Daily (prod) | Real-time audio                 |
| VAD       | Silero (250ms timeout)             | Fast turn detection             |
| STT       | Sarvam Saarika v2.5                | Multilingual speech recognition |
| LLM       | Google Gemini 2.0 Flash            | Multilingual intelligence       |
| TTS       | Sarvam Bulbul v2                   | Natural Indian language voices  |

## Quick Start

### 1. Configure API keys

```bash
cp .env.example .env
# Edit .env with your actual keys
```

### 2. Start the backend

```bash
uv sync              # Install Python dependencies
uv run bot.py        # Starts WebRTC server at http://localhost:7860
```

Open `http://localhost:7860/client` for the built-in minimal client.

### 3. Start the custom frontend (optional)

```bash
cd client
npm install
npm run dev           # Opens at http://localhost:5173
```

## Speed Hacks

- **Aggressive VAD**: 250ms silence timeout — bot responds fast
- **Streaming pipeline**: TTS starts speaking before LLM finishes
- **Barge-in**: Speak over the bot and it stops immediately
- **Short responses**: System prompt forces concise output (<25 words)

## Swapping the LLM

Change one line in `bot.py`:

```python
# Google Gemini (default)
llm = GoogleLLMService(api_key=os.getenv("GOOGLE_API_KEY"), model="gemini-2.0-flash")

# OpenAI
llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

# Groq (Llama)
llm = OpenAILLMService(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1", model="llama-3.1-70b-versatile")
```

## License

MIT
