# main.py

import uvicorn
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llms.llm_manager import llm_manager
from memory.memory_manager import MemoryManager # Import the class, not the instance
from config.manager import ConfigManager

# Load configuration on startup
config_manager = ConfigManager()

# Create a global instance of the MemoryManager for our application to use
# Pass the config_manager instance to break circular dependency
memory_manager = MemoryManager(config_manager_instance=config_manager)

# Pydantic model for incoming chat messages
class QueryRequest(BaseModel):
    query: str
    session_id: str
    max_tokens: int = 4096
    temperature: float = 0.7

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to AryAI's backend! Visit /docs for the API documentation."}

@app.post("/stream")
async def handle_stream(request: QueryRequest):
    """
    Handles streaming chat requests.
    """
    # Use the memory manager to get the full conversation history
    memory_manager.add_message(role="user", content=request.query, session_id=request.session_id)
    messages = memory_manager.get_messages(session_id=request.session_id)

    # Use the LLM manager to get the current LLM adapter
    current_llm = llm_manager.get_current_llm()

    # Get additional keyword arguments from the request
    kwargs = {
        "temperature": request.temperature,
        "max_tokens": request.max_tokens
    }

    async def stream_response_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        try:
            async for chunk in current_llm.stream(messages=messages, **kwargs):
                full_response += chunk
                yield chunk
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM streaming error: {e}")
        finally:
            # Add the complete AI response to memory
            memory_manager.add_message(role="model", content=full_response, session_id=request.session_id)

    return StreamingResponse(stream_response_generator(), media_type="text/event-stream")

@app.post("/query")
async def handle_query(request: QueryRequest):
    """
    Handles non-streaming chat requests.
    """
    memory_manager.add_message(role="user", content=request.query, session_id=request.session_id)
    messages = memory_manager.get_messages(session_id=request.session_id)

    current_llm = llm_manager.get_current_llm()

    kwargs = {
        "temperature": request.temperature,
        "max_tokens": request.max_tokens
    }

    try:
        response_content = await current_llm.generate(messages=messages, **kwargs)
        memory_manager.add_message(role="model", content=response_content, session_id=request.session_id)
        return {"response": response_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation error: {e}")

@app.get("/memory/history")
async def get_memory_history(session_id: str = "default"):
    """
    Retrieves the full conversation history from memory.
    """
    return {"history": memory_manager.get_messages(session_id)}

@app.get("/memory/context_string")
async def get_memory_context_string(session_id: str = "default"):
    """
    Retrieves the conversation history as a single formatted string from memory.
    """
    return {"context_string": memory_manager.get_context_string(session_id)}

@app.post("/memory/clear")
async def clear_memory(session_id: str = "default"):
    """
    Clears the entire conversation history from memory.
    """
    memory_manager.clear(session_id)
    return {"message": f"Memory for session '{session_id}' has been cleared."}

@app.get("/config/llm/modules")
async def get_llm_modules():
    """
    Returns a list of all available LLM modules.
    """
    return {"modules": list(config_manager.config['llm']['modules'].keys())}

@app.post("/config/llm/select/{module_name}")
async def select_llm_module(module_name: str):
    """
    Sets the active LLM module.
    """
    if module_name not in config_manager.config['llm']['modules']:
        raise HTTPException(status_code=404, detail=f"LLM module '{module_name}' not found.")
    
    config_manager.set_current_model(module_name)
    llm_manager.reload_llm_module()
    return {"message": f"LLM module set to '{module_name}'."}

@app.get("/config/memory/modules")
async def get_memory_modules():
    """
    Returns a list of all available memory modules.
    """
    return {"modules": list(config_manager.config['memory']['modules'].keys())}

@app.get("/config/memory/current")
async def get_current_memory_module():
    """
    Returns the currently active memory module.
    """
    return {"current_module": config_manager.get_memory_module()}

@app.post("/config/memory/select/{module_name}")
async def select_memory_module(module_name: str):
    """
    Sets the active memory module.
    """
    if module_name not in config_manager.config['memory']['modules']:
        raise HTTPException(status_code=404, detail=f"Memory module '{module_name}' not found.")
    
    config_manager.set_memory_module(module_name)
    memory_manager.reload_memory_module()
    return {"message": f"Memory module set to '{module_name}'."}

@app.get("/ping")
async def ping():
    """
    A simple health check endpoint to confirm the server is running.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)