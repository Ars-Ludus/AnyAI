# llms/gemini.py
import asyncio
from typing import List, Optional, Dict, AsyncGenerator
from base import LLMAdapter
from google import genai
from google.genai import types

# Gemini model names
DEFAULT_MODEL = "gemini-2.5-flash-lite"
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"

class GeminiAdapter(LLMAdapter):
    id = "gemini"
    name = "Gemini 2.5 Flash Lite (google-genai)"

    def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL, embed_model: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        self.embedding_model = embed_model
        if not api_key:
            raise ValueError("API key not provided to GeminiAdapter")
        self.client = genai.Client(api_key=api_key)

    async def generate(self, prompt: str, context: Optional[str] = "", **kwargs) -> str:
        """Generate response using Gemini chat API"""
        full_prompt = prompt if not context else context + "\n\n" + prompt
        
        contents = [full_prompt]
        
        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature"),
            top_k=kwargs.get("top_k"),
            top_p=kwargs.get("top_p"),
        )
        
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=contents,
                config=config,
            )
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            return f"Error: {e}"

    async def generate_stream(self, prompt: str, context: Optional[str] = "", **kwargs) -> AsyncGenerator[str, None]:
        """Generate a streaming response using Gemini chat API"""
        full_prompt = prompt if not context else context + "\n\n" + prompt
        
        # We need a chat object to use the streaming method
        chat = self.client.aio.chats.create(model=self.model_name)
        
        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature"),
            top_k=kwargs.get("top_k"),
            top_p=kwargs.get("top_p"),
        )

        try:
            # CORRECTED: This method is async, so we must await the call
            response_stream = await chat.send_message_stream(full_prompt, config=config)
            
            async for chunk in response_stream:
                if chunk and chunk.candidates and chunk.candidates[0].content.parts[0].text:
                    yield chunk.candidates[0].content.parts[0].text

        except Exception as e:
            yield f"Error: {e}"

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Synchronously generate embeddings (only call from sync context)"""
        try:
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
            return [e.values for e in response.embeddings]
        except Exception as e:
            raise RuntimeError(f"Embedding error: {e}")

    def count_tokens(self, texts: List[str]) -> int:
        """Synchronously count tokens (only call from sync context)"""
        try:
            response = self.client.models.count_tokens(
                model=self.model_name,
                contents=texts,
            )
            return response.total_tokens
        except Exception as e:
            raise RuntimeError(f"Token count error: {e}")

    def supports_embeddings(self) -> bool:
        return True