# memory/stm.py

from datetime import datetime, timedelta

class STMEntry:
    def __init__(self, role, content, timestamp=None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()

class STM:
    def __init__(self, max_turns=15, max_age_minutes=15):
        self.entries = []
        self.max_turns = max_turns
        self.max_age = timedelta(minutes=max_age_minutes)

    def add(self, role: str, content: str):
        self.entries.append(STMEntry(role, content))
        self.trim()

    def trim(self):
        now = datetime.now()
        self.entries = [
            e for e in self.entries
            if now - e.timestamp <= self.max_age
        ]
        if len(self.entries) > self.max_turns:
            self.entries = self.entries[-self.max_turns:]

    def get_context(self) -> str:
        return "\n".join(f"{e.role}: {e.content}" for e in self.entries)

    def clear(self):
        self.entries = []
