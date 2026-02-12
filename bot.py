#
# Aero — Multilingual Low-Latency Voice Bot
# Pipecat + Sarvam AI (STT/TTS) + Google Gemini (LLM)
# With Adaptive Learning System
#

import os

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.frames.frames import LLMRunFrame, TextFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.google.llm import GoogleLLMService
from pipecat.services.sarvam.stt import SarvamSTTService
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams

# Import adaptive learning system
from learning_system import learner

try:
    from pipecat.transports.daily.transport import DailyParams
except ImportError:
    # Daily transport is optional for local WebRTC dev
    DailyParams = None

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Transport parameters (WebRTC for local dev, Daily for production, Twilio for phone)
# ---------------------------------------------------------------------------
transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ) if DailyParams else None,
    "twilio": lambda: FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
}

# ---------------------------------------------------------------------------
# Load evolved system prompt from learning system
# The prompt improves automatically after each conversation
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = learner.get_current_prompt()


# ---------------------------------------------------------------------------
# Learning Logger - Captures conversation for adaptive learning
# ---------------------------------------------------------------------------
class LearningLogger(FrameProcessor):
    """Logs user and assistant messages for the learning system."""
    
    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        
        # Log user text (from STT)
        if isinstance(frame, TextFrame):
            if hasattr(frame, 'text'):
                learner.log_message("user", frame.text)
        
        # Log assistant responses (from LLM)
        if hasattr(frame, 'text') and direction.name == "DOWNSTREAM":
            if not isinstance(frame, TextFrame):  # Avoid double logging
                learner.log_message("assistant", str(frame))
        
        # Pass frame through
        await self.push_frame(frame, direction)


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    """Configure and run the Pipecat pipeline."""
    logger.info("Starting Aero voice bot")

    # --- STT: Sarvam Saarika (multilingual Indian + English) ---
    stt = SarvamSTTService(
        api_key=os.getenv("SARVAM_API_KEY"),
        model="saarika:v2.5",
    )

    # --- TTS: Sarvam Bulbul (natural Indian voices) ---
    tts = SarvamTTSService(
        api_key=os.getenv("SARVAM_API_KEY"),
        model="bulbul:v3-beta",
        voice_id="shreya",  # Hindi-speaking female voice
    )

    # --- LLM: Google Gemini 2.0 Flash (fast, multilingual) ---
    llm = GoogleLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.5-flash",
    )

    # --- Conversation context ---
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    context = LLMContext(messages)  # Default context management
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            # Conservative VAD: 1.2s silence = user finished speaking
            # Crucial for Gemini 2.5 Flash free tier to avoid 429 errors
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=1.2)),
        ),
    )

    # --- Create learning logger ---
    learning_logger = LearningLogger()

    # --- Build the streaming pipeline ---
    pipeline = Pipeline(
        [
            transport.input(),       # 🎤 Receive audio from browser
            stt,                     # 📝 Sarvam Saarika: speech → text
            learning_logger,         # 📚 Log for adaptive learning
            user_aggregator,         # 📋 Add user message to LLM context
            llm,                     # 🧠 Gemini: think & stream response
            tts,                     # 🔊 Sarvam Bulbul: text → speech
            transport.output(),      # 🔈 Send audio back to browser
            assistant_aggregator,    # 📋 Add bot response to context
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # --- Event handlers ---
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        # Start tracking conversation for learning
        learner.start_conversation()
        
        # Greet the user as soon as they connect
        greeting = "A customer just connected. Introduce yourself professionally as a debt collection agent. " \
                   "Greet in Hindi: 'Namaste, main Priya bol rahi hoon ABC Finance se. Aapka loan account number 4567 ke baare mein baat karni hai. Kya main account holder se baat kar sakti hoon?'"
        messages.append(
            {
                "role": "system",
                "content": greeting,
            }
        )
        learner.log_message("system", greeting)
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        # End conversation and trigger learning
        learner.end_conversation(outcome="completed")
        await task.cancel()

    # --- Run ---
    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main entry point — compatible with Pipecat Cloud."""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
