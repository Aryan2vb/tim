#
# Adaptive Learning System for Debt Collection Bot
# The bot learns from each conversation and improves its prompt
#

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# File paths for storing learning data
CONVERSATIONS_DIR = Path("conversations")
PROMPT_HISTORY_FILE = Path("prompts/prompt_history.json")
EVOLVED_PROMPT_FILE = Path("prompts/evolved_prompt.txt")

# Ensure directories exist
CONVERSATIONS_DIR.mkdir(exist_ok=True)
Path("prompts").mkdir(exist_ok=True)


class ConversationLearner:
    """Learns from conversations and evolves the system prompt."""
    
    def __init__(self):
        self.current_conversation: List[Dict[str, str]] = []
        self.conversation_id = None
        
    def start_conversation(self) -> str:
        """Start tracking a new conversation."""
        self.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_conversation = []
        logger.info(f"Started conversation tracking: {self.conversation_id}")
        return self.conversation_id
    
    def log_message(self, role: str, content: str):
        """Log a message in the current conversation."""
        if self.conversation_id:
            self.current_conversation.append({
                "timestamp": datetime.now().isoformat(),
                "role": role,
                "content": content
            })
    
    def end_conversation(self, outcome: str = ""):
        """End conversation and save it for learning."""
        if not self.conversation_id:
            return
            
        conversation_data = {
            "conversation_id": self.conversation_id,
            "ended_at": datetime.now().isoformat(),
            "outcome": outcome,
            "messages": self.current_conversation,
            "total_turns": len([m for m in self.current_conversation if m["role"] in ["user", "assistant"]])
        }
        
        # Save conversation
        filepath = CONVERSATIONS_DIR / f"{self.conversation_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved conversation: {filepath}")
        
        # Trigger learning
        self._learn_from_conversation(conversation_data)
        
        # Reset
        self.conversation_id = None
        self.current_conversation = []
    
    def _learn_from_conversation(self, conversation_data: Dict[str, Any]):
        """Analyze conversation and update the prompt."""
        logger.info("Learning from conversation...")
        
        # Analyze the conversation
        analysis = self._analyze_conversation(conversation_data)
        
        # Generate improved prompt
        improved_prompt = self._generate_improved_prompt(analysis)
        
        # Save to history
        self._save_prompt_to_history(improved_prompt, analysis)
        
        # Update evolved prompt file
        with open(EVOLVED_PROMPT_FILE, 'w', encoding='utf-8') as f:
            f.write(improved_prompt)
        
        logger.info(f"Evolved prompt saved to: {EVOLVED_PROMPT_FILE}")
    
    def _analyze_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze what worked and what didn't in the conversation."""
        messages = conversation_data["messages"]
        
        # Extract key metrics
        user_messages = [m for m in messages if m["role"] == "user"]
        assistant_messages = [m for m in messages if m["role"] == "assistant"]
        
        analysis = {
            "total_user_messages": len(user_messages),
            "total_bot_messages": len(assistant_messages),
            "customer_resistance_signals": [],
            "successful_approaches": [],
            "failed_approaches": [],
            "language_switches": 0,
            "emotional_triggers": []
        }
        
        # Analyze user responses for resistance/success signals
        for i, msg in enumerate(user_messages):
            content_lower = msg["content"].lower()
            
            # Detect resistance
            if any(word in content_lower for word in ["nahi", "no", "refuse", "impossible", "can't"]):
                analysis["customer_resistance_signals"].append({
                    "message": msg["content"],
                    "turn": i,
                    "type": "rejection"
                })
            
            # Detect cooperation
            if any(word in content_lower for word in ["haan", "yes", "theek", "okay", "karunga", "pay"]):
                analysis["successful_approaches"].append({
                    "message": msg["content"],
                    "turn": i,
                    "type": "cooperation"
                })
            
            # Detect language switches
            if any(hindi_word in msg["content"] for hindi_word in ["namaste", "hai", "nahi", "hoon", "rupee"]):
                analysis["language_switches"] += 1
        
        return analysis
    
    def _generate_improved_prompt(self, analysis: Dict[str, Any]) -> str:
        """Generate an improved prompt based on analysis."""
        
        # Load current evolved prompt or base prompt
        if EVOLVED_PROMPT_FILE.exists():
            with open(EVOLVED_PROMPT_FILE, 'r', encoding='utf-8') as f:
                current_prompt = f.read()
        else:
            from prompts.base_prompt import BASE_SYSTEM_PROMPT
            current_prompt = BASE_SYSTEM_PROMPT
        
        # Add learning insights as appendix
        insights = []
        
        if analysis["customer_resistance_signals"]:
            insights.append(f"\n\nLEARNING INSIGHT #{len(analysis['customer_resistance_signals'])}:")
            insights.append("When customers show resistance, try:")
            insights.append("- Acknowledging their situation with more empathy")
            insights.append("- Offering smaller payment amounts initially")
            insights.append("- Using softer language like 'kya aap thoda help kar sakte hain' instead of demanding")
        
        if analysis["language_switches"] > 2:
            insights.append(f"\n\nLEARNING INSIGHT #{analysis['language_switches']}:")
            insights.append("Customer frequently switched to Hindi - prioritize Hinglish responses")
            insights.append("- Start conversations directly in Hindi/Hinglish")
            insights.append("- Use more Hindi words for emotional connection")
            insights.append("- Numbers and amounts can remain in English for clarity")
        
        if len(analysis["successful_approaches"]) > len(analysis["customer_resistance_signals"]):
            insights.append("\n\nLEARNING INSIGHT - POSITIVE:")
            insights.append("The empathetic approach is working well - continue emphasizing:")
            insights.append("- Understanding customer's situation first")
            insights.append("- Offering flexible solutions")
            insights.append("- Building rapport before discussing payments")
        
        # Combine current prompt with new insights
        improved_prompt = current_prompt + "\n\n" + "="*50 + "\n"
        improved_prompt += "ADAPTIVE LEARNINGS FROM PAST CONVERSATIONS:\n"
        improved_prompt += "="*50 + "\n"
        improved_prompt += "\n".join(insights) if insights else "Continue current approach - monitor for patterns."
        
        return improved_prompt
    
    def _save_prompt_to_history(self, prompt: str, analysis: Dict[str, Any]):
        """Save prompt evolution to history."""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "analysis_summary": {
                "total_turns": analysis.get("total_user_messages", 0),
                "resistance_signals": len(analysis.get("customer_resistance_signals", [])),
                "successful_approaches": len(analysis.get("successful_approaches", [])),
                "language_switches": analysis.get("language_switches", 0)
            },
            "evolved_prompt": prompt
        }
        
        # Load existing history
        if PROMPT_HISTORY_FILE.exists():
            with open(PROMPT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = {"evolution_history": []}
        
        # Add new entry
        history["evolution_history"].append(history_entry)
        
        # Save updated history
        with open(PROMPT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def get_current_prompt(self) -> str:
        """Get the current evolved prompt for use in conversations."""
        if EVOLVED_PROMPT_FILE.exists():
            with open(EVOLVED_PROMPT_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            from prompts.base_prompt import BASE_SYSTEM_PROMPT
            return BASE_SYSTEM_PROMPT


# Global learner instance
learner = ConversationLearner()
