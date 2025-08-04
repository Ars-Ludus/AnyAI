# config/manager.py

import os
import importlib
import json
from dotenv import load_dotenv
from typing import List, Dict
import logging
# from memory.memory_manager import MemoryManager # Removed to break circular import

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        # Load environment variables from .env file
        load_dotenv()
        
        self.config = {
            "llm": {
                "active_model": "gemini",
                "api_keys": {
                    "gemini": os.getenv("GEMINI_API_KEY")
                }
            },
            "memory": {
                "active_module": "stm_eth"
            }
        }
        
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                file_config = json.load(f)
                self._recursive_update(self.config, file_config)

    def _recursive_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._recursive_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def _save_config(self):
        """Saves the current configuration to config.json."""
        # Create a deep copy to avoid modifying the live config
        config_to_save = json.loads(json.dumps(self.config))
        
        # Remove sensitive data like API keys before saving
        if 'api_keys' in config_to_save.get('llm', {}):
            del config_to_save['llm']['api_keys']
            
        with open('config.json', 'w') as f:
            json.dump(config_to_save, f, indent=4)
            f.flush()
            os.fsync(f.fileno())

    def get_current_model(self) -> str:
        return self.config['llm']['active_model']

    def set_current_model(self, model_name: str):
        self.config['llm']['active_model'] = model_name
        self._save_config()

    def get_memory_module(self) -> str:
        return self.config['memory']['active_module']
        
    def set_memory_module(self, module_name: str):
        self.config['memory']['active_module'] = module_name
        self._save_config()
        
    def get_api_key(self, llm_name: str) -> str:
        return self.config['llm']['api_keys'].get(llm_name)

# Global instance will be created and memory_manager set in main.py
# config_manager = ConfigManager() # Removed global instance creation here