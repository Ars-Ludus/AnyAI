import customtkinter
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

def insert_memory_button(chat_textbox: customtkinter.CTkTextbox, parent, memory_context_string: str):
    """
    Inserts a 'View Memory' button into the chat textbox.
    The button, when clicked, opens a popup displaying the provided memory_context_string.
    """
    if not memory_context_string.strip():
        memory_context_string = "[Memory Empty]"

    tag_name = f"viewmemory_{id(memory_context_string)}"

    chat_textbox.configure(state="normal")
    chat_textbox.insert("end", "[ View Memory ]\n\n", tag_name)
    chat_textbox.tag_config(
        tag_name,
        foreground="#ffffff",
        background="#445566",
        underline=True
    )

    def on_click(event):
        MemoryPopup(parent, memory_context_string)

    chat_textbox.tag_bind(tag_name, "<Button-1>", on_click)
    chat_textbox.configure(state="disabled")