# memory/memory_manager.py

from typing import List, Dict
import importlib
from memory.stm_eth import stm_eth
# Removed: from config.manager import config_manager # Avoid circular import

class MemoryManager:
    def __init__(self, config_manager_instance):
        self.config_manager = config_manager_instance
        self.memory_module_instance = self._load_active_memory_module()

    def _load_active_memory_module(self):
        module_name = self.config_manager.get_memory_module()
        class_name = f"{module_name}"
        
        try:
            module = importlib.import_module(f"memory.{module_name}")
            memory_class = getattr(module, class_name)
            # Pass session_id to the memory module's constructor if it supports it
            # For now, assuming it's handled by methods, not constructor
            return memory_class()
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not load memory module '{module_name}': {e}")

    def reload_memory_module(self):
        """
        Reloads the memory module based on the current configuration.
        This is called when the configuration is changed via an API endpoint.
        """
        self.memory_module_instance = self._load_active_memory_module()

    def add_message(self, role: str, content: str, session_id: str = "default"):
        """
        Adds a new message to the active memory module.
        """
        self.memory_module_instance.add_message(role, content, session_id=session_id)

    def get_messages(self, session_id: str = "default") -> List[Dict]:
        """
        Retrieves all messages from the active memory module.
        """
        return self.memory_module_instance.get_messages(session_id=session_id)

    def clear(self, session_id: str = "default"):
        """
        Clears the active memory module.
        """
        self.memory_module_instance.clear(session_id=session_id)

    def get_context_string(self, session_id: str = "default") -> str:
        """
        Retrieves the conversation history as a single string.
        """
        return self.memory_module_instance.get_context_string(session_id=session_id)

# The global instance will now be created in main.py after config_manager is available
# Removed: memory_manager = MemoryManager()