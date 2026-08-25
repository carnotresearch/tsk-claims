"""
Quick sanity-check for the Gemini API key and model.

Usage:
    # On VM:
    docker compose -f docker-compose.prod.yml exec backend python scripts/test_gemini.py

    # Locally (with venv active):
    python scripts/test_gemini.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings

settings = get_settings()

print(f"LLM provider : {settings.llm_provider}")
print(f"Gemini model : {settings.gemini_model}")
print(f"API key      : {settings.gemini_api_key[:8]}{'*' * 10}  (first 8 chars shown)")
print()


async def main():
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        generation_config=GenerationConfig(temperature=0, max_output_tokens=64),
    )

    print("Sending test prompt to Gemini...")
    try:
        response = await model.generate_content_async("Reply with exactly: OK")
        print(f"Response: {response.text.strip()}")
        print()
        print("✓ Gemini API key and model are working correctly.")
    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        print("Common fixes:")
        print("  - Wrong model name. Valid options: gemini-1.5-flash, gemini-2.0-flash, gemini-2.5-flash")
        print("  - Invalid or expired API key. Generate a new one at https://aistudio.google.com/apikey")
        print("  - API key not set: check GEMINI_API_KEY in your .env file")
        sys.exit(1)


asyncio.run(main())
