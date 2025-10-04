import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    # Configure the API key from your .env file
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    print("Available models that support 'generateContent':")
    # List all models and filter for the ones that can generate content
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")

except Exception as e:
    print(f"An error occurred: {e}")
    print("\nThis could be due to an incorrect API key or network issues.")