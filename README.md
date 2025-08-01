# AryAI Chat Client

A customizable chat client built with Python and CustomTkinter for interacting with a local large language model (LLM) API. Currently supports Gemini API and is pre-configured for Flash 2.5 Lite. You only need to create your own .env with GEMINI_API_KEY="your-api-key"

### Features
-   Clean, modern user interface.
-   Persistent settings for chat bubble and hover colors.
-   Customizable UI with a vertical toolbar.
-   Clear chat history button.

### Prerequisites
-   Python 3.x
-   A running local LLM API (e.g., a FastAPI server like the one we've built).

### Installation
1.  Clone this repository to your local machine.
2.  Navigate to the project directory.
3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### How to Run
1.  Ensure your local LLM API server is running
    ```bash
    uvicorn main:app --reload
   ```
2.  Run the application from your terminal:
    ```bash
    python chat_ui.py
    ```

### Customization
You can change the chat bubble and hover colors by clicking the settings icon and entering a new hex code. These settings are saved persistently.