# config/manager.py

import os
import importlib
import json
from dotenv import load_dotenv

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
            cls._instance._discover_module_configs('memory')
            cls._instance._discover_module_configs('llms')
        return cls._instance

    def _load_config(self):
        # Load environment variables from .env file
        load_dotenv()
        
        self.config = {
            "llm": {
                "active_model": "gemini",
                "modules": {},
                "api_keys": {
                    "gemini": os.getenv("GEMINI_API_KEY")
                }
            },
            "memory": {
                "active_module": "stm_eth",
                "modules": {}
            }
        }
        
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                file_config = json.load(f)
                self._recursive_update(self.config, file_config)

    def _discover_module_configs(self, module_category):
        """
        Dynamically discovers and loads configuration options from modules in a given category.
        """
        module_path = os.path.join(os.path.dirname(__file__), '..', module_category)
        
        config_key = "llm" if module_category == "llms" else module_category

        for filename in os.listdir(module_path):
            if filename.endswith('.py') and filename != '__init__.py' and filename != 'base.py':
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f"{module_category}.{module_name}")
                    if hasattr(module, 'module_config'):
                        module_config = getattr(module, 'module_config')
                        self.config[config_key]['modules'][module_name] = module_config
                        print(f"Discovered configuration for {config_key} module: {module_name}")
                except ImportError as e:
                    print(f"Warning: Could not import {config_key} module {module_name}: {e}")
                except FileNotFoundError as e:
                    print(f"Warning: Module directory not found for {config_key}: {e}")

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
        
    def get_memory_config(self, module_name: str = None):
        if module_name and module_name in self.config['memory']['modules']:
            return self.config['memory']['modules'][module_name]
        return self.config['memory']['modules']
        
    def get_api_key(self, llm_name: str) -> str:
        return self.config['llm']['api_keys'].get(llm_name)


config_manager = ConfigManager()