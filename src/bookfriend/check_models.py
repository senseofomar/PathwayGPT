# src/bookfriend/check_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: No API Key found in .env")
else:
    genai.configure(api_key=api_key)
    print(f"🔑 Key found. Listing available models for this key...\n")
    try:
        count = 0
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ AVAILABLE: {m.name}")
                count += 1
        if count == 0:
            print("⚠️ No models found. Check if 'Generative Language API' is enabled in Google Cloud Console.")
    except Exception as e:
        print(f"💥 Error listing models: {e}")