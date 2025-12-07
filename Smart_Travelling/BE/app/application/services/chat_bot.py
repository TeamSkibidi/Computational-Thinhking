import os, json 
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY= os.getenv("GEMINI_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

async def chat_bot_with_ai(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text