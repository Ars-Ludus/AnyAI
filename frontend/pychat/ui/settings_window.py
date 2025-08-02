import customtkinter
import httpx
import threading

class SettingsWindow(customtkinter.CTkToplevel):
    def __init__(self, master, modules, current_module, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.main_app = master
        self.title("Settings")
        self.geometry("400x450")
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

        self.memory_module_label = customtkinter.CTkLabel(
            self.settings_frame,
            text="Memory Module:"
        )
        self.memory_module_label.pack(anchor="w", padx=4, pady=(4, 0))

        self.memory_module_menu = customtkinter.CTkOptionMenu(
            self.settings_frame,
            values=modules if modules else ["No modules found"]
        )
        self.memory_module_menu.pack(fill="x", padx=4, pady=(0, 20))
        if current_module in modules:
            self.memory_module_menu.set(current_module)
        
        self.save_button = customtkinter.CTkButton(
            self.settings_frame,
            text="Save Settings",
            command=self.save_settings
        )
        self.save_button.pack(pady=4)

    def save_settings(self):
        """
        Saves all settings and closes the window.
        """
        user_color = self.user_color_entry.get()
        ai_color = self.ai_color_entry.get()
        hover_color = self.hover_color_entry.get()
        selected_memory_module = self.memory_module_menu.get()

        self.main_app.update_app_settings(user_color, ai_color, hover_color)
        
        threading.Thread(target=self.save_memory_module_thread, args=(selected_memory_module,), daemon=True).start()

        self.destroy()

    def save_memory_module_thread(self, module_name: str):
        """
        Posts the selected memory module to the backend.
        """
        try:
            response = httpx.post(f"{self.main_app.backend_url}/config/memory/select/{module_name}", timeout=5.0)
            response.raise_for_status()
            print(f"Successfully set memory module to {module_name}")
        except Exception as e:
            print(f"Failed to set memory module: {e}")