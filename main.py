# main.py
import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from llms import gemini
from base import LLMAdapter
from typing import Dict, AsyncGenerator

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="AryAI LLM Backend", description="Modular LLM Gateway for Reasoning Agents")

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Register available models
model_registry: Dict[str, LLMAdapter] = {
    "gemini": gemini.GeminiAdapter(api_key=GEMINI_API_KEY),
}
current_model = model_registry["gemini"]  # Default to gemini

# ---------------------------
# LLM Query Endpoint (Non-streaming)
# ---------------------------
@app.post("/query")
async def query(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    context = data.get("context", "")
    params = data.get("params", {})
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    try:
        response = await current_model.generate(prompt, context, **params)
        return {"model": current_model.id, "response": response}
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
    context = data.get("context", "")
    params = data.get("params", {})

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    return StreamingResponse(generate_response_stream(prompt, context, params), media_type="text/plain")

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