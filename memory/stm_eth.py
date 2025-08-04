# memory/stm_eth.py

from datetime import datetime, timedelta
from typing import List, Dict
from memory.base import BaseMemory

class stm_eth_entry:
    def __init__(self, role, content, timestamp=None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()

class stm_eth(BaseMemory):
    id = "stm_eth"
    name = "Ephemeral Memory"

    def __init__(self, max_turns=15, max_age_minutes=15):
        self.sessions = {} # Dictionary to hold memory for different sessions
        self.max_turns = max_turns
        self.max_age = timedelta(minutes=max_age_minutes)

    def _get_session_entries(self, session_id: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def add_message(self, role: str, content: str, session_id: str = "default"):
        entries = self._get_session_entries(session_id)
        entries.append(stm_eth_entry(role, content))
        self.trim(session_id)

    def get_messages(self, session_id: str = "default") -> List[Dict]:
        """
        Returns the message history for a given session as a list of dictionaries.
        """
        self.trim(session_id) # Ensure memory is fresh before returning
        entries = self._get_session_entries(session_id)
        return [{"role": e.role, "content": e.content} for e in entries]

    def trim(self, session_id: str = "default"):
        now = datetime.now()
        entries = self._get_session_entries(session_id)
        entries = [
            e for e in entries
            if now - e.timestamp <= self.max_age
        ]
        if len(entries) > self.max_turns:
            entries = entries[-self.max_turns:]
        self.sessions[session_id] = entries # Update the session's entries

    def get_context_string(self, session_id: str = "default") -> str:
        """
        Returns the conversation history for a given session as a single string.
        """
        self.trim(session_id) # Ensure memory is fresh before returning
        entries = self._get_session_entries(session_id)
        return "\n".join(f"{e.role}: {e.content}" for e in entries)

    def clear(self, session_id: str = "default"):
        """
        Clears the memory for a specific session.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]

module_config = {
    "name": "Ephemeral Memory",
    "description": "Stores conversation history in memory, limited by time and number of turns."
}