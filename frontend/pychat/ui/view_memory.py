import customtkinter
import httpx
import asyncio

class MemoryPopup(customtkinter.CTkToplevel):
    def __init__(self, parent, memory_string: str):
        super().__init__(parent)
        self.title("Short-Term Memory")
        self.geometry("600x400")
        self.grab_set()

        self.textbox = customtkinter.CTkTextbox(self, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self.textbox.insert("1.0", memory_string)
        self.textbox.configure(state="disabled")

        self.copy_button = customtkinter.CTkButton(
            self,
            text="Copy to Clipboard",
            command=lambda: self.copy_text(memory_string)
        )
        self.copy_button.pack(pady=10)

    def copy_text(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.copy_button.configure(text="Copied!")

async def insert_memory_button(chat_textbox: customtkinter.CTkTextbox, parent, api_url: str):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(api_url)
            memory_context = resp.json().get("memory", "[STM Empty]")
        except Exception:
            memory_context = "[STM Unavailable]"

    tag_name = f"viewmemory_{id(memory_context)}"

    chat_textbox.configure(state="normal")
    chat_textbox.insert("end", "[ View Memory ]\n\n", tag_name)
    chat_textbox.tag_config(
        tag_name,
        foreground="#ffffff",
        background="#445566",
        underline=True
    )

    def on_click(event):
        MemoryPopup(parent, memory_context)

    chat_textbox.tag_bind(tag_name, "<Button-1>", on_click)
    chat_textbox.configure(state="disabled")