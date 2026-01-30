import json
from llm.groq_client import generate

def extract_keywords_from_slide(text: str) -> dict:
    """
    Extracts system components and their implicit relationships
    from PPT slide text. No sentences, only entities.
    """

    prompt = f"""
From the text below, extract SYSTEM COMPONENTS only.

Rules:
- Return ONLY named components or services
- No explanations
- No sentences
- Preserve logical order if implied
- Group related components

Return JSON ONLY in this format:
{{
  "components": [
    {{ "name": "Component Name", "type": "platform|subsystem|compute|storage|service" }}
  ],
  "relations": [
    {{ "from": "A", "to": "B", "relation": "contains|flows_to|uses" }}
  ]
}}

TEXT:
\"\"\"{text}\"\"\"
"""

    try:
        response = generate(prompt)
        return json.loads(response)
    except Exception:
        return {"components": [], "relations": []}
