# main.py
import os
import asyncio
import logging
from starlette.responses import StreamingResponse
from typing import AsyncGenerator
from config.manager import ConfigManager
from memory.stm_eth import STM
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from llms import gemini
from memory.global_memory import stm

from base import LLMAdapter
from typing import Dict, AsyncGenerator

# Load environment variables from .env file
load_dotenv()
config = ConfigManager()

class PingFilter(logging.Filter):
    def filter(self, record):
        return "/ping" not in record.getMessage()

logging.getLogger("uvicorn.access").addFilter(PingFilter())
app = FastAPI(title="AryAI LLM Backend", description="Modular LLM Gateway for Reasoning Agents")

# Config instance
config = ConfigManager()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Register available models
model_registry: Dict[str, LLMAdapter] = {
    "gemini": gemini.GeminiAdapter(api_key=GEMINI_API_KEY),
}
default_model_id = config.get("model.core.active") or "gemini"
current_model = model_registry.get(default_model_id, model_registry["gemini"])
# ---------------------------
# LLM Query Endpoint (Non-streaming)
# ---------------------------
@app.post("/query")
async def query(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    context = stm.get_context()
    params = data.get("params", {})

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    try:
        response_text = await current_model.generate(prompt, context, **params)
        stm.add("user", prompt)
        stm.add("assistant", response_text)
        print("STM Context:\n", stm.get_context())

        return {"model": current_model.id, "response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")

# ---------------------------
# Streaming LLM Endpoint
# ---------------------------
async def generate_response_stream(prompt: str, context: str, params: Dict) -> AsyncGenerator[str, None]:
    async for chunk in current_model.generate_stream(prompt, context, **params):
        yield chunk

@app.post("/stream")
async def stream(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    context = stm.get_context()  # ✅ Use STM here
    params = data.get("params", {})

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    async def stream_and_store() -> AsyncGenerator[str, None]:
        full_response = ""

        async for chunk in current_model.generate_stream(prompt, context, **params):
            full_response += chunk
            yield chunk

        # ✅ After streaming ends, update STM
        stm.add("user", prompt)
        stm.add("assistant", full_response)
        print("STM Context:\n", stm.get_context())

    return StreamingResponse(stream_and_store(), media_type="text/plain")

# ---------------------------
# Embedding Endpoint
# ---------------------------
@app.post("/embed")
async def embed(request: Request):
    data = await request.json()
    texts = data.get("texts", [])

    if not texts:
        raise HTTPException(status_code=400, detail="Texts list is required.")

    if not current_model.supports_embeddings():
        raise HTTPException(status_code=400, detail=f"Model {current_model.id} does not support embeddings.")
    
    try:
        embeddings = await asyncio.to_thread(current_model.embed, texts)
        return {"model": current_model.id, "embeddings": embeddings}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# Token Count Endpoint
# ---------------------------
@app.post("/tokens")
async def count_tokens(request: Request):
    data = await request.json()
    texts = data.get("texts", [])

    if not texts:
        raise HTTPException(status_code=400, detail="Texts list is required.")
    
    try:
        count = await asyncio.to_thread(current_model.count_tokens, texts)
        return {"model": current_model.id, "token_count": count}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# Model Registry + Control
# ---------------------------
@app.get("/models")
def list_models():
    return [
        {"id": m.id, "name": m.name, "supports_embeddings": m.supports_embeddings()}
        for m in model_registry.values()
    ]

@app.get("/models/current")
def get_current_model():
    return {"id": current_model.id, "name": current_model.name}

@app.post("/models/select")
async def select_model(request: Request):
    data = await request.json()
    model_id = data.get("model")
    
    if not model_id:
        raise HTTPException(status_code=400, detail="Model ID is required.")

    global current_model
    if model_id not in model_registry:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found in registry.")
    
    current_model = model_registry[model_id]
    return {"message": f"Switched to model: {current_model.name}"}

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.get("/memory")
def get_memory():
    return {"memory": stm.get_context()}