# llms/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Union, AsyncGenerator

class LLMAdapter(ABC):
    """
    Abstract Base Class for all LLM adapters.
    This defines the common interface for interacting with any LLM.
    """
    id: str
    name: str

    @abstractmethod
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        """
        Generate a non-streaming text response from the LLM.
        """
        pass

    @abstractmethod
    async def stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate a streaming text response from the LLM.
        """
        pass

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        """
        pass

    @abstractmethod
    async def count_tokens(self, texts: List[str]) -> int:
        """
        Count the number of tokens in a list of texts.
        """
        pass

    def supports_embeddings(self) -> bool:
        """
        Returns True if the adapter supports embedding generation.
        """
        return callable(getattr(self, "embed", None))