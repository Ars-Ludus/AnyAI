from memory.stm_eth import STM
from config.manager import ConfigManager

config = ConfigManager()

stm = STM(
    max_turns=config.get("stm.eth.turns"),
    max_age_minutes=config.get("stm.eth.decay_minutes") or 15
)
