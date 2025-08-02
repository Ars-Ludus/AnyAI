# config/manager.py
class ConfigManager:
    def __init__(self):
        self._config = {
            "stm.eth.turns": 15,  # 🧠 STM: ethereal variant, 15-turn decay window
        }

    def get(self, key: str):
        return self._config.get(key)

    def set(self, key: str, value):
        self._config[key] = value

    def update(self, updates: dict):
        self._config.update(updates)

    def all(self):
        return dict(self._config)

    def keys(self):
        return self._config.keys()

    def values(self):
        return self._config.values()

    def items(self):
        return self._config.items()
