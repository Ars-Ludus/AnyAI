# llms/gemini.py

import os
from typing import List, Dict, AsyncGenerator
from google import genai
from google.genai import types

from llms.base import LLMAdapter

# The configuration dictionary for this module, as we discussed
module_config = {
    "name": "Gemini",
    "generation_model": "gemini-2.0-flash-001",
    "embedding_model": "text-embedding-004"
}

class GeminiAdapter(LLMAdapter):
    """
    Adapter for the Google Gemini API.
    """

    def __init__(self, api_key: str):
        self.id = "gemini"
        self.name = "Google Gemini"
        
        # Directly use the API key passed in from the LLMManager
        if not api_key:
            raise ValueError("API key for Gemini is missing.")
        
        # Set the environment variable for the Google SDK
        os.environ["GOOGLE_API_KEY"] = api_key
        
        self.client = genai.Client()
        self.generation_model = module_config["generation_model"]
        self.embedding_model = module_config["embedding_model"]

    async def generate(self, messages: List[Dict], **kwargs) -> str:
        """
        Generate a non-streaming text response from the Gemini model.
        """
        contents = self._prepare_chat_contents(messages)
                        
        response = await self.client.aio.models.generate_content(
            model=self.generation_model,
            contents=contents,
        )
        return response.text

    async def stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate a streaming text response from the Gemini model.
        """
        contents = self._prepare_chat_contents(messages)
        
        async for chunk in await self.client.aio.models.generate_content_stream(
            model=self.generation_model,
            contents=contents,
        ):
            if chunk.text:
                yield chunk.text

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using a dedicated embedding model.
        """
        response = await self.client.aio.models.embed_content(
            model=self.embedding_model,
            contents=texts
        )
        return [embedding.values for embedding in response.embeddings]

    async def count_tokens(self, texts: List[str]) -> int:
        """
        Count the number of tokens in a list of texts.
        """
        response = await self.client.aio.models.count_tokens(
            model=self.generation_model,
            contents=texts,
        )
        return response.total_tokens

    def _prepare_chat_contents(self, messages: List[Dict]):
        """
        Prepares the chat message format for the Gemini SDK's generate/stream methods.
        """
        contents = []
        for msg in messages:
            contents.append(
                types.Content(
                    role=msg['role'],
                    parts=[types.Part(text=msg['content'])]
                )
            )
        return contents
        
    def supports_embeddings(self) -> bool:
        """
        Returns True because Gemini supports embedding generation.
        """
        return True