# llms/llm_manager.py

import os
import importlib
from llms.base import LLMAdapter
from config.manager import ConfigManager

class LLMManager:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.llm_adapter_instance = self._load_active_llm_adapter()

    def _load_active_llm_adapter(self) -> LLMAdapter:
        module_name = self.config_manager.get_current_model()
        class_name = f"{module_name.capitalize()}Adapter"
        
        try:
            module = importlib.import_module(f"llms.{module_name}")
            llm_class = getattr(module, class_name)
            
            # Get the API key from the ConfigManager, which loaded it from the .env file
            api_key = self.config_manager.get_api_key(module_name)
            if not api_key:
                raise ValueError(f"API key for '{module_name}' not found in configuration.")

            return llm_class(api_key=api_key)
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not load LLM adapter '{module_name}': {e}")
            
    def reload_llm_module(self):
        """
        Reloads the LLM adapter based on the current configuration.
        """
        self.llm_adapter_instance = self._load_active_llm_adapter()

    def get_current_llm(self) -> LLMAdapter:
        return self.llm_adapter_instance

# Create a global instance of the LLMManager
llm_manager = LLMManager()