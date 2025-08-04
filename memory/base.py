# memory/base.py

from abc import ABC, abstractmethod
from typing import List, Dict

class BaseMemory(ABC):
    """
    Abstract Base Class for all memory modules.
    This defines the common interface for interacting with any memory system.
    """
    id: str
    name: str

    @abstractmethod
    def add_message(self, role: str, content: str, session_id: str = "default"):
        """
        Adds a new message to the memory.
        """
        pass

    @abstractmethod
    def get_messages(self, session_id: str = "default") -> List[Dict]:
        """
        Retrieves all messages for a given session.
        """
        pass

    @abstractmethod
    def clear(self, session_id: str = "default"):
        """
        Clears the memory for a given session.
        """
        pass

    @abstractmethod
    def get_context_string(self, session_id: str = "default") -> str:
        """
        Retrieves the conversation history as a single formatted string.
        """
        pass