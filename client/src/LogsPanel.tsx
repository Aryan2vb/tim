import { useState, useEffect } from "react";
import { PipecatClient, RTVIEvent } from "@pipecat-ai/client-js";

type LogType = "STT" | "LLM" | "TTS" | "SYSTEM";
interface LogEntry {
  timestamp: number;
  type: LogType;
  message: string;
}

export function LogsPanel({ client }: { client: PipecatClient | null }) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState("ALL");
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (!client) return;

    const addLog = (type: LogType, message: string) => {
      setLogs((prev) => [
        { timestamp: Date.now(), type, message },
        ...prev.slice(0, 99), // Keep last 100
      ]);
    };

    // STT (User Transcript)
    client.on(RTVIEvent.UserTranscript, (data) => {
      if (data.final) addLog("STT", `USER: ${data.text}`);
    });

    // LLM (Thinking & Response)
    client.on(RTVIEvent.BotLlmStarted, () => addLog("LLM", "Thinking..."));
    client.on(RTVIEvent.BotLlmStopped, () => addLog("LLM", "Done thinking"));
    client.on(RTVIEvent.BotTranscript, (data) => {
      if (data.text) addLog("LLM", `RESPONSE: ${data.text}`);
    });

    // TTS (Speaking)
    client.on(RTVIEvent.BotTtsStarted, () => addLog("TTS", "Started speaking"));
    client.on(RTVIEvent.BotTtsStopped, () => addLog("TTS", "Stopped speaking"));

    // System (Errors)
    client.on(RTVIEvent.Error, (msg) => addLog("SYSTEM", `ERROR: ${JSON.stringify(msg)}`));

  }, [client]);

  if (!isOpen) {
    return (
      <button 
        className="logs-toggle"
        onClick={() => setIsOpen(true)}
      >
        Show Logs
      </button>
    );
  }

  const filteredLogs = filter === "ALL" 
    ? logs 
    : logs.filter(log => log.type === filter);

  return (
    <div className="logs-panel glass-card">
      <div className="logs-header">
        <h3>Debug Console</h3>
        <button onClick={() => setIsOpen(false)}>✕</button>
      </div>
      
      <div className="logs-filters">
        {["ALL", "STT", "LLM", "TTS"].map(f => (
          <button 
            key={f}
            className={filter === f ? "active" : ""}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="logs-list">
        {filteredLogs.map((log, i) => (
          <div key={i} className={`log-item ${log.type}`}>
            <span className="log-time">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
            <span className="log-type">{log.type}</span>
            <span className="log-msg">{log.message}</span>
          </div>
        ))}
        {filteredLogs.length === 0 && (
          <div className="log-empty">No logs yet...</div>
        )}
      </div>
    </div>
  );
}
