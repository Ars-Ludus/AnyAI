# ui/code_block.py

import customtkinter

class CodePopup(customtkinter.CTkToplevel):
    def __init__(self, parent, code_text: str):
        super().__init__(parent)
        self.title("Code Block")
        self.geometry("600x400")
        self.grab_set()

        self.textbox = customtkinter.CTkTextbox(self, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self.textbox.insert("1.0", code_text)
        self.textbox.configure(state="disabled")

        self.copy_button = customtkinter.CTkButton(
            self,
            text="Copy Code",
            command=lambda: self.copy_code(code_text)
        )
        self.copy_button.pack(pady=10)

    def copy_code(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.copy_button.configure(text="Copied!")


def insert_code_block_button(chat_textbox: customtkinter.CTkTextbox, parent, code_text: str):
    tag_name = f"codeblock_{id(code_text)}"

    chat_textbox.configure(state="normal")
    chat_textbox.insert("end", "[ Code Block ]", tag_name)
    chat_textbox.tag_config(
        tag_name,
        foreground="#ffffff",
        background="#444444",
        underline=True,
    )

    def on_click(event):
        CodePopup(parent, code_text)

    chat_textbox.tag_bind(tag_name, "<Button-1>", on_click)
    chat_textbox.configure(state="disabled")
