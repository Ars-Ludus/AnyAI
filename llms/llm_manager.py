# llms/llm_manager.py

import os
import importlib
from typing import List, Dict, AsyncGenerator
from llms.base import LLMAdapter
from config.manager import ConfigManager

class LLMManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.modules = {}
        self._instances = {}  # Cache for module instances
        self.active_module_name = None
        self.active_module = None
        self._discover_modules()
        self.set_active_module(self.config_manager.get_current_model())

    def _discover_modules(self):
        """
        Dynamically discovers and registers LLM modules from the 'llms' directory.
        """
        module_path = os.path.dirname(__file__)
        for filename in os.listdir(module_path):
            if filename.endswith('.py') and filename not in ['__init__.py', 'base.py', 'llm_manager.py']:
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f"llms.{module_name}")
                    class_name = f"{module_name.capitalize()}Adapter"
                    if hasattr(module, class_name):
                        self.modules[module_name] = {
                            "class": getattr(module, class_name),
                            "config": getattr(module, "module_config", {})
                        }
                        print(f"Discovered LLM module: {module_name}")
                except (ImportError, AttributeError) as e:
                    print(f"Warning: Could not load LLM module {module_name}: {e}")

    def set_active_module(self, module_name: str):
        """
        Sets the active LLM module, using a cached instance if available.
        """
        if module_name in self.modules:
            if module_name not in self._instances:
                api_key = self.config_manager.get_api_key(module_name)
                if not api_key:
                    raise ValueError(f"API key for '{module_name}' not found.")
                
                module_info = self.modules[module_name]
                self._instances[module_name] = module_info["class"](api_key=api_key)
                print(f"Initialized and cached new instance for LLM module: {module_name}")

            self.active_module_name = module_name
            self.active_module = self._instances[module_name]
            self.config_manager.set_current_model(module_name)
            print(f"Active LLM module set to: {module_name}")
        else:
            raise ValueError(f"LLM module '{module_name}' not found.")

    def get_active_module(self) -> LLMAdapter:
        if not self.active_module:
            raise ValueError("No active LLM module set.")
        return self.active_module

    async def generate_text(self, messages: List[Dict], **kwargs) -> str:
        return await self.get_active_module().generate(messages, **kwargs)

    async def stream_text(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        async for chunk in self.get_active_module().stream(messages, **kwargs):
            yield chunk

    async def embed(self, text: str) -> List[float]:
        return await self.get_active_module().embed([text])

# Global instance will be created in main.py