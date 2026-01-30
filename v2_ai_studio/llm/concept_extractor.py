import json
from llm.groq_client import generate

def extract_concepts(script: str, max_concepts: int = 6) -> dict:
    prompt = f"""
You MUST create a VISUAL TEACHING SEQUENCE from the text below.

DO NOT summarize.
DO NOT return vague nouns.
DO NOT return fewer than 4 steps unless impossible.

INSTRUCTIONS:
- Decompose the explanation into ordered teaching steps
- Each step must represent an action, stage, or transformation
- Use verbs when possible (e.g., Ingest Data, Train Model)
- Steps MUST form a flow suitable for animation

If you cannot create at least 4 steps, STILL TRY by splitting the explanation logically.

Return ONLY valid JSON. No text. No markdown.

FORMAT:
{{
  "concepts": [
    {{ "id": "s1", "label": "Step Name" }}
  ],
  "relations": [
    {{ "from": "s1", "to": "s2" }}
  ]
}}

TEXT:
\"\"\"{script}\"\"\"
"""

    response = generate(prompt)

    print("===== RAW CONCEPT RESPONSE =====")
    print(response)

    try:
        data = json.loads(response)
        if len(data.get("concepts", [])) < 4:
            return {}
        return data
    except Exception:
        return {}
