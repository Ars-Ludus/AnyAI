# memory/memory_manager.py

import os
import importlib
import inspect
from typing import List, Dict
from memory.base import BaseMemory
from config.manager import ConfigManager
import logging

class MemoryManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.modules = {}
        self._instances = {}  # Cache for module instances
        self.active_module_name = None
        self.active_module = None
        self._discover_modules()
        self.set_active_module(self.config_manager.get_memory_module())

    def _discover_modules(self):
        """
        Dynamically discovers and registers memory modules from the 'memory' directory
        by finding classes that inherit from BaseMemory.
        """
        module_path = os.path.dirname(__file__)
        for filename in os.listdir(module_path):
            if filename.endswith('.py') and filename not in ['__init__.py', 'base.py', 'memory_manager.py']:
                module_name_str = filename[:-3]
                try:
                    module = importlib.import_module(f"memory.{module_name_str}")
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseMemory) and obj is not BaseMemory:
                            # Use the class's `id` attribute for the module name
                            if hasattr(obj, 'id'):
                                module_id = obj.id
                                self.modules[module_id] = {
                                    "class": obj,
                                    "config": getattr(module, "module_config", {})
                                }
                                print(f"Discovered memory module: {module_id}")
                            else:
                                print(f"Warning: Memory module class {name} in {filename} does not have an 'id' attribute.")
                except (ImportError, AttributeError, SyntaxError) as e:
                    print(f"Warning: Could not load memory module from {filename}: {e}")

    def set_active_module(self, module_name: str):
        """
        Sets the active memory module, using a cached instance if available.
        """
        if module_name in self.modules:
            if module_name not in self._instances:
                module_info = self.modules[module_name]
                self._instances[module_name] = module_info["class"]()
                print(f"Initialized and cached new instance for memory module: {module_name}")

            self.active_module_name = module_name
            self.active_module = self._instances[module_name]
            self.config_manager.set_memory_module(module_name)
            print(f"Active memory module set to: {module_name}")
        else:
            raise ValueError(f"Memory module '{module_name}' not found.")

    def get_active_module(self) -> BaseMemory:
        if not self.active_module:
            raise ValueError("No active memory module set.")
        return self.active_module

    def add_message(self, role: str, content: str, session_id: str = "default"):
        logging.info(f"MemoryManager adding message to session '{session_id}'")
        self.get_active_module().add_message(role, content, session_id)

    def get_messages(self, session_id: str = "default") -> List[Dict]:
        return self.get_active_module().get_messages(session_id)

    def clear(self, session_id: str = "default"):
        self.get_active_module().clear(session_id)

    def get_context_string(self, session_id: str = "default") -> str:
        return self.get_active_module().get_context_string(session_id)

# Global instance will be created in main.py