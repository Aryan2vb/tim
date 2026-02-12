import { useCallback, useRef, useState } from "react";
import {
  PipecatClient,
  RTVIEvent,
  TransportState,
} from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import { LogsPanel } from "./LogsPanel";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type BotState = "idle" | "connecting" | "listening" | "thinking" | "speaking";

interface TranscriptEntry {
  role: "user" | "bot";
  text: string;
}

// Backend URL — Pipecat's built-in runner serves WebRTC at this address
// Backend URL — Pipecat's built-in runner serves WebRTC at this address
const BACKEND_URL = `${window.location.protocol}//${window.location.hostname}:7860`;

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
export default function App() {
  const [botState, setBotState] = useState<BotState>("idle");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const clientRef = useRef<PipecatClient | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // --- Connect ---
  const handleConnect = useCallback(async () => {
    setBotState("connecting");

    try {
      const transport = new SmallWebRTCTransport();

      const client = new PipecatClient({
        transport,
        enableMic: true,
        enableCam: false,
      });

      // Handle incoming audio track
      client.on(RTVIEvent.TrackStarted, (track, participant) => {
        if (track.kind === "audio" && audioRef.current) {
          audioRef.current.srcObject = new MediaStream([track]);
        }
      });

      // Bot starts speaking
      client.on(RTVIEvent.BotStartedSpeaking, () => {
        setBotState("speaking");
      });

      // Bot stops speaking → back to listening
      client.on(RTVIEvent.BotStoppedSpeaking, () => {
        setBotState("listening");
      });

      // User starts speaking
      client.on(RTVIEvent.UserStartedSpeaking, () => {
        setBotState("listening");
      });

      // LLM started thinking
      client.on(RTVIEvent.BotLlmStarted, () => {
        setBotState("thinking");
      });

      // User transcript (what the user said)
      client.on(RTVIEvent.UserTranscript, (data) => {
        if (data.final && data.text) {
          setTranscript((prev) => [
            ...prev.slice(-8),
            { role: "user", text: data.text },
          ]);
        }
      });

      // Bot transcript (what the bot said)
      client.on(RTVIEvent.BotTranscript, (data) => {
        if (data.text) {
          setTranscript((prev) => [
            ...prev.slice(-8),
            { role: "bot", text: data.text },
          ]);
        }
      });

      // Transport state changes
      client.on(RTVIEvent.TransportStateChanged, (state: TransportState) => {
        if (state === "ready") {
          setBotState("listening");
        } else if (state === "disconnected" || state === "error") {
          setBotState("idle");
        }
      });

      // Connect using the SmallWebRTC offer endpoint
      await client.connect({
        webrtcRequestParams: {
          endpoint: `${BACKEND_URL}/api/offer`,
        },
      });

      clientRef.current = client;
    } catch (err) {
      console.error("Failed to connect:", err);
      setBotState("idle");
    }
  }, []);

  // --- Disconnect ---
  const handleDisconnect = useCallback(async () => {
    if (clientRef.current) {
      await clientRef.current.disconnect();
      clientRef.current = null;
    }
    setBotState("idle");
    setTranscript([]);
  }, []);

  const isConnected = botState !== "idle" && botState !== "connecting";

  // --- Status label ---
  const statusLabel: Record<BotState, string> = {
    idle: "Ready to connect",
    connecting: "Connecting…",
    listening: "Listening",
    thinking: "Thinking…",
    speaking: "Aero is speaking",
  };

  const visualizerState = isConnected ? botState : "idle";

  return (
    <>
      {/* Background gradient orbs */}
      <div className="bg-orbs">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      <div className="app-container">
        {/* Glass card */}
        <div className="glass-card">
          {/* Logo */}
          <div className="logo">
            <div className="logo-icon">⚡</div>
            <h1>Aero</h1>
            <p>Multilingual Voice Assistant</p>
          </div>

          {/* Status badge */}
          <div className={`status ${isConnected ? botState : ""} ${isConnected ? "connected" : ""}`}>
            <span className="dot" />
            {statusLabel[botState]}
          </div>

          {/* Voice Visualizer */}
          <div className={`visualizer ${visualizerState}`}>
            {Array.from({ length: 9 }).map((_, i) => (
              <div key={i} className="bar" />
            ))}
          </div>

          {/* Connect / Disconnect */}
          {!isConnected ? (
            <button
              id="connect-btn"
              className="connect-btn primary"
              onClick={handleConnect}
              disabled={botState === "connecting"}
            >
              {botState === "connecting" ? (
                <>
                  <div className="spinner" />
                  Connecting…
                </>
              ) : (
                <>🎤 Start Talking</>
              )}
            </button>
          ) : (
            <button
              id="disconnect-btn"
              className="connect-btn danger"
              onClick={handleDisconnect}
            >
              ✕ Disconnect
            </button>
          )}

          {/* Transcript */}
          {transcript.length > 0 && (
            <div className="transcript">
              <div className="label">Conversation</div>
              {transcript.map((entry, i) => (
                <div key={i} className={entry.role === "user" ? "user-text" : "bot-text"}>
                  <strong>{entry.role === "user" ? "You" : "Aero"}:</strong> {entry.text}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="footer">
          Powered by{" "}
          <a href="https://pipecat.ai" target="_blank" rel="noopener">
            Pipecat
          </a>{" "}
          +{" "}
          <a href="https://sarvam.ai" target="_blank" rel="noopener">
            Sarvam AI
          </a>
        </div>
      </div>

      {clientRef.current && (
        <LogsPanel client={clientRef.current} />
      )}
      
      {/* Hidden audio element for playback */}
      <audio ref={audioRef} autoPlay playsInline style={{ display: "none" }} />
    </>
  );
}
