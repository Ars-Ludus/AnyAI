import customtkinter
import httpx
import threading
import asyncio
from PIL import Image
import json
import os
import re
# Removed old imports for STM and ConfigManager
from .ui.code_block import insert_code_block_button
from .ui.view_memory import insert_memory_button
from .ui.settings_window import SettingsWindow

# --- UI Setup ---
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("AryAI Chat Client")
        self.geometry("600x600")
        self.chat_font = customtkinter.CTkFont(family="Segoe UI", size=15)
        self.backend_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

        self.ai_pastel_color = "#F8B195"
        self.user_pastel_color = "#B7E9C7"
        self.hover_pastel_color = "#D6CDEA"

        self.load_settings()

        self.clear_image = customtkinter.CTkImage(
            light_image=Image.open("assets/icon_clear.png"),
            dark_image=Image.open("assets/icon_clear.png"),
            size=(24, 24)
        )

        self.settings_image = customtkinter.CTkImage(
            light_image=Image.open("assets/icon_settings.png"),
            dark_image=Image.open("assets/icon_settings.png"),
            size=(24, 24)
        )

        self.toolbar_frame = customtkinter.CTkFrame(self, fg_color="transparent", width=50)
        self.toolbar_frame.pack(side="left", fill="y", padx=4, pady=4)

        #status light thingy
        self.status_light = customtkinter.CTkLabel(
            self.toolbar_frame,
            text="●",
            text_color="gray",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        self.status_light.pack(side="top", pady=(10, 10))

        self.clear_button = customtkinter.CTkButton(
            self.toolbar_frame,
            text="",
            image=self.clear_image,
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=self.hover_pastel_color,
            border_width=0,
            command=self.clear_chat_history
        )
        self.clear_button.pack(side="top", pady=4)

        self.settings_button = customtkinter.CTkButton(
            self.toolbar_frame,
            text="",
            image=self.settings_image,
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=self.hover_pastel_color,
            border_width=0,
            command=self.open_settings
        )
        self.settings_button.pack(side="top", pady=4)
        
        self.chat_frame = customtkinter.CTkFrame(self)
        self.chat_frame.pack(padx=4, pady=(0, 4), fill="both", expand=True)

        self.chat_textbox = customtkinter.CTkTextbox(self.chat_frame, wrap="word", font=self.chat_font)
        self.chat_textbox.pack(padx=4, pady=(4, 2), fill="both", expand=True)
        self.chat_textbox.configure(state="disabled")

        self.configure_chat_tags()

        self.input_frame = customtkinter.CTkFrame(self.chat_frame)
        self.input_frame.pack(padx=4, pady=(2, 4), fill="x")
        
        self.input_textbox = customtkinter.CTkTextbox(self.input_frame, height=35)
        self.input_textbox.pack(padx=4, pady=4, fill="x", expand=True)
        self.input_textbox.bind("<Return>", self.send_message)
        self.input_textbox.bind("<Shift-Return>", self.insert_newline)

        self.insert_message("Welcome to AryAI. How can I help you today?", sender="ai")
    
        #code block button

        #status light heartbeat
        self.after(1000, self.check_connection_loop)

    def configure_chat_tags(self):
        self.chat_textbox.tag_config("user",
                                     foreground="#222831",
                                     background=self.user_pastel_color,
                                     lmargin1=10,
                                     lmargin2=10,
                                     rmargin=10,
                                     justify="right")

        self.chat_textbox.tag_config("ai",
                                     foreground="#222831",
                                     background=self.ai_pastel_color,
                                     lmargin1=10,
                                     lmargin2=10,
                                     rmargin=10,
                                     justify="left")
    
    def load_settings(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    settings = json.load(f)
                    self.user_pastel_color = settings.get("user_color", self.user_pastel_color)
                    self.ai_pastel_color = settings.get("ai_color", self.ai_pastel_color)
                    self.hover_pastel_color = settings.get("hover_color", self.hover_pastel_color)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading config.json: {e}. Using default settings.")

    def save_settings(self, user_color, ai_color, hover_color):
        settings = {
            "user_color": user_color,
            "ai_color": ai_color,
            "hover_color": hover_color
        }
        with open("config.json", "w") as f:
            json.dump(settings, f, indent=4)
        
    def update_app_settings(self, user_color, ai_color, hover_color):
        try:
            self.user_pastel_color = user_color
            self.ai_pastel_color = ai_color
            self.hover_pastel_color = hover_color
            
            self.chat_textbox.tag_config("user", background=user_color)
            self.chat_textbox.tag_config("ai", background=ai_color)

            self.settings_button.configure(hover_color=hover_color)
            self.clear_button.configure(hover_color=hover_color)
            
            self.save_settings(user_color, ai_color, hover_color)

            self.update()

        except Exception as e:
            print(f"Failed to update colors: {e}")
            
    def open_settings(self):
        # Fetch data synchronously before opening the window
        try:
            modules_response = httpx.get(f"{self.backend_url}/config/memory/modules", timeout=5.0)
            modules_response.raise_for_status()
            modules = modules_response.json().get("modules", [])

            current_module_response = httpx.get(f"{self.backend_url}/config/memory/current", timeout=5.0)
            current_module_response.raise_for_status()
            current_module = current_module_response.json().get("current_module")

            self.settings_window = SettingsWindow(self, modules=modules, current_module=current_module)
        except Exception as e:
            print(f"Failed to open settings: {e}")
            # Optionally, show an error message to the user
            # For simplicity, we'll just print to console here.

    # NEW: Async method to clear memory on the backend
    async def _clear_memory_on_backend(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.backend_url}/memory/clear")
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Failed to clear memory on backend: {e}")
            return False

    # UPDATED: Synchronous method to clear UI and call backend
    def clear_chat_history(self):
        async def clear_and_reset():
            if await self._clear_memory_on_backend():
                self.chat_textbox.configure(state="normal")
                self.chat_textbox.delete("1.0", "end")
                self.insert_message("Welcome to AryAI. How can I help you today?", sender="ai")
                self.chat_textbox.configure(state="disabled")

        # Run the async function from the synchronous button command
        threading.Thread(target=asyncio.run, args=(clear_and_reset(),)).start()

    def insert_message(self, message, sender):
        self.chat_textbox.configure(state="normal")
        self.chat_textbox.insert("end", f"\n{message}\n", sender)
        self.chat_textbox.see("end")
        self.chat_textbox.configure(state="disabled")
    
    # Async method to fetch memory history from the backend
    async def get_memory_history_from_backend(self, session_id: str = "pychat_session"):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.backend_url}/memory/history", params={"session_id": session_id})
                response.raise_for_status()
                return response.json().get("history", [])
        except Exception as e:
            print(f"Failed to fetch memory history from backend: {e}")
            return []

    # NEW: Async method to fetch the formatted memory context string from the backend
    async def get_memory_context_string_from_backend(self, session_id: str = "pychat_session"):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.backend_url}/memory/context_string", params={"session_id": session_id})
                response.raise_for_status()
                return response.json().get("context_string", "")
        except Exception as e:
            print(f"Failed to fetch memory context string from backend: {e}")
            return ""

    # UPDATED: The core method to send and stream the response
    async def _send_and_stream(self, prompt: str):
        # NEW: Fetch conversation history from the backend for the specific session
        session_id = "pychat_session" # Ensure consistency
        
        # Fetch conversation history from the backend for the specific session
        memory_history = await self.get_memory_history_from_backend(session_id=session_id)
        
        # Fetch the formatted context string from the backend
        memory_context_string = await self.get_memory_context_string_from_backend(session_id=session_id)

        # NEW: The payload now includes the conversation history and a session ID
        payload = {
            "query": prompt,
            "messages": memory_history, # Still send history for LLM context
            "session_id": session_id,
            "temperature": 0.7,
            "max_tokens": 4096
        }

        # Update the memory button with the formatted context string
        insert_memory_button(self.chat_textbox, self, memory_context_string)

        response_text = ""
        self.insert_message("AI: ...", "ai")

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.backend_url}/stream",
                    json=payload,
                    timeout=None
                ) as response:
                    response.raise_for_status()
                    self.chat_textbox.configure(state="normal")
                    self.chat_textbox.delete("end-2l", "end-1l")

                    # Manually insert AI prefix to avoid extra newlines from insert_message
                    self.chat_textbox.insert("end-1l", "AI: ", "ai")
                    response_start_index = self.chat_textbox.index("end-1c")

                    # Stream response for live updates
                    async for chunk in response.aiter_bytes():
                        decoded_chunk = chunk.decode()
                        self.chat_textbox.insert("end", decoded_chunk, "ai")
                        response_text += decoded_chunk
                        self.chat_textbox.see("end")
                        self.update()

                    # Re-process the response for code blocks
                    self.chat_textbox.delete(response_start_index, "end")
                    
                    parts = re.split(r'(```[\s\S]*?```)', response_text)
                    for part in parts:
                        if not part:
                            continue
                        if part.startswith('```') and part.endswith('```'):
                            code = part[3:-3].strip()
                            if code:
                                insert_code_block_button(self.chat_textbox, self, code)
                        else:
                            self.chat_textbox.insert("end", part, "ai")
                    
                    self.chat_textbox.see("end")
                    
                    # Add a final newline for spacing and disable editing
                    self.insert_message("", "ai")
                    self.chat_textbox.configure(state="disabled")


        except httpx.HTTPStatusError as e:
            self.insert_message(f"\nError: Server returned status code {e.response.status_code}\n{e.response.text}", "ai")
        except Exception as e:
            self.insert_message(f"\nAn unexpected error occurred: {e}\n", "ai")

    def _run_async_task(self, prompt: str):
        asyncio.run(self._send_and_stream(prompt))

    def send_message(self, event=None):
        prompt = self.input_textbox.get("1.0", "end-1c").strip()
        if not prompt:
            return "break"
        
        self.input_textbox.delete("1.0", "end")
        self.insert_message(f"You: {prompt}", sender="user")
        
        thread = threading.Thread(target=self._run_async_task, args=(prompt,))
        thread.start()

        return "break"

    def insert_newline(self, event=None):
        self.input_textbox.insert("insert", "\n")
        return "break"

    #status light heartbeat
    def check_connection_loop(self):
        async def ping():
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{self.backend_url}/ping", timeout=2)
                    if resp.status_code == 200:
                        self.status_light.configure(text_color="#00d26a")  # green
                    else:
                        self.status_light.configure(text_color="#ffc700")  # yellow
            except:
                self.status_light.configure(text_color="#d0003f")  # red
        try:
            asyncio.run(ping())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.create_task(ping())

        self.after(3000, self.check_connection_loop)

if __name__ == "__main__":
    app = App()
    app.mainloop()