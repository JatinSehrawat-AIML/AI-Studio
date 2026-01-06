# llm/gemini_client.py
from google import genai
from config.settings import GEMINI_API_KEY

# Create Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

def generate(prompt: str, model: str = "gemini-2.5-flash") -> str:
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )

        if not response.text:
            raise ValueError("Empty response from Gemini model")

        return response.text

    except Exception as e:
        raise RuntimeError(f"Gemini generation failed: {str(e)}")
