import customtkinter
import httpx
import threading
import asyncio
from PIL import Image
import json
import os

# --- UI Setup ---
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("AryAI Chat Client")
        self.geometry("600x600")
        self.chat_font = customtkinter.CTkFont(family="Segoe UI", size=15)

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
        self.settings_window = SettingsWindow(self)

    def clear_chat_history(self):
        self.chat_textbox.configure(state="normal")
        self.chat_textbox.delete("1.0", "end")
        self.insert_message("Welcome to AryAI. How can I help you today?", sender="ai")
        self.chat_textbox.configure(state="disabled")

    def insert_message(self, message, sender):
        self.chat_textbox.configure(state="normal")
        self.chat_textbox.insert("end", f"\n{message}\n", sender)
        self.chat_textbox.see("end")
        self.chat_textbox.configure(state="disabled")

    async def _send_and_stream(self, prompt: str):
        api_url = "http://127.0.0.1:8000/stream"
        payload = {"prompt": prompt}
        response_text = ""

        self.insert_message("AI: ...", "ai")

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST", 
                    api_url, 
                    json=payload,
                    timeout=None
                ) as response:
                    response.raise_for_status()
                    self.chat_textbox.configure(state="normal")
                    self.chat_textbox.delete("end-2l", "end-1l")
                    self.chat_textbox.configure(state="disabled")

                    self.insert_message("AI: ", "ai")
                    
                    self.chat_textbox.configure(state="normal")
                    async for chunk in response.aiter_bytes():
                        decoded_chunk = chunk.decode()
                        self.chat_textbox.insert("end", decoded_chunk, "ai")
                        response_text += decoded_chunk
                        self.chat_textbox.see("end")
                        self.update()
                    self.chat_textbox.configure(state="disabled")
                    self.insert_message("", "ai")

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

class SettingsWindow(customtkinter.CTkToplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.main_app = master
        self.title("Settings")
        self.geometry("400x300")
        self.grab_set()

        self.settings_frame = customtkinter.CTkFrame(self)
        self.settings_frame.pack(padx=8, pady=8, fill="both", expand=True)

        self.title_label = customtkinter.CTkLabel(
            self.settings_frame,
            text="Application Settings",
            font=customtkinter.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(0, 10))

        self.user_color_label = customtkinter.CTkLabel(
            self.settings_frame,
            text="User Bubble Color (Hex Code):"
        )
        self.user_color_label.pack(anchor="w", padx=4, pady=(4, 0))

        self.user_color_entry = customtkinter.CTkEntry(
            self.settings_frame,
            placeholder_text="#B7E9C7"
        )
        self.user_color_entry.insert(0, self.main_app.user_pastel_color)
        self.user_color_entry.pack(fill="x", padx=4, pady=(0, 4))

        self.ai_color_label = customtkinter.CTkLabel(
            self.settings_frame,
            text="AI Bubble Color (Hex Code):"
        )
        self.ai_color_label.pack(anchor="w", padx=4, pady=(4, 0))

        self.ai_color_entry = customtkinter.CTkEntry(
            self.settings_frame,
            placeholder_text="#F8B195"
        )
        self.ai_color_entry.insert(0, self.main_app.ai_pastel_color)
        self.ai_color_entry.pack(fill="x", padx=4, pady=(0, 20))
        
        self.hover_color_label = customtkinter.CTkLabel(
            self.settings_frame,
            text="Hover Color (Hex Code):"
        )
        self.hover_color_label.pack(anchor="w", padx=4, pady=(4, 0))

        self.hover_color_entry = customtkinter.CTkEntry(
            self.settings_frame,
            placeholder_text="#D6CDEA"
        )
        self.hover_color_entry.insert(0, self.main_app.hover_pastel_color)
        self.hover_color_entry.pack(fill="x", padx=4, pady=(0, 20))

        self.save_button = customtkinter.CTkButton(
            self.settings_frame,
            text="Save Settings",
            command=self.save_settings
        )
        self.save_button.pack(pady=4)

    def save_settings(self):
        user_color = self.user_color_entry.get()
        ai_color = self.ai_color_entry.get()
        hover_color = self.hover_color_entry.get()

        self.main_app.update_app_settings(user_color, ai_color, hover_color)

        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()