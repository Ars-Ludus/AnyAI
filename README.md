### To run this project:

1.  **Install dependencies:**
    ```bash
    pip install "google-generativeai>=0.8.0" fastapi uvicorn python-dotenv
    ```
2.  **Create a `.env` file:**
    Create a file named `.env` in the same directory as `main.py`.
    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```
    Replace `"YOUR_API_KEY_HERE"` with your actual Gemini API key.

3.  **Run the server:**
    ```bash
    uvicorn main:app --reload
    ```