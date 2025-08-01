# chat_client.py
import asyncio
import httpx
import json

async def main():
    api_url = "http://127.0.0.1:8000/stream"
    
    print("Welcome to the Python AI Chat Client!")
    print("Type 'quit' or 'exit' to end the session.")

    while True:
        prompt = input("You: ")
        if prompt.lower() in ["quit", "exit"]:
            break
        
        # Prepare the request body
        payload = {"prompt": prompt}

        try:
            # Use httpx's async client to handle the streaming response
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST", 
                    api_url, 
                    json=payload,
                    timeout=None
                ) as response:
                    # Check for a successful response
                    response.raise_for_status()

                    print("AI:", end=" ", flush=True)
                    # Use an async for loop to iterate over the streamed chunks
                    async for chunk in response.aiter_bytes():
                        # Decode and print each chunk as it arrives
                        # The `end=""` and `flush=True` are crucial for real-time printing
                        print(chunk.decode(), end="", flush=True)
                    print("\n")

        except httpx.HTTPStatusError as e:
            print(f"Error: Server returned status code {e.response.status_code}")
            print(e.response.text)
            print("\n")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            print("\n")

if __name__ == "__main__":
    asyncio.run(main())