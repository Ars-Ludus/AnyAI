from abc import ABC, abstractmethod
from typing import List

class LLMAdapter(ABC):
    id: str
    name: str

    @abstractmethod
    async def generate(self, prompt: str, context: str = "", **kwargs) -> str:
        pass

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        pass

    def supports_embeddings(self) -> bool:
        return callable(getattr(self, "embed", None))