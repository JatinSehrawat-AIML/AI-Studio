# llm/semantic_extractor.py
import json
from llm.groq_client import generate

def extract_semantic_roles(text: str) -> list[dict]:
    """
    Extracts semantic roles in a format directly usable
    by roles_to_graph()
    """

    prompt = f"""
Extract SYSTEM DIAGRAM roles from the text.

Return JSON ONLY as a LIST of objects:
[
  {{ "id": "input", "label": "User Data", "role": "input" }},
  {{ "id": "core", "label": "ML Model", "role": "core" }},
  {{ "id": "output", "label": "Predictions", "role": "output" }}
]

Rules:
- Use roles: input, core, output, storage, external
- Use short labels (1–4 words)
- Be conservative
- Return EMPTY LIST if unsure

TEXT:
\"\"\"{text}\"\"\"
"""

    try:
        response = generate(prompt)
        roles = json.loads(response)

        if not isinstance(roles, list):
            return []

        return roles

    except Exception:
        return []
