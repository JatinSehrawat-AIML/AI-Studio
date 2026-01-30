import json
from llm.groq_client import generate

def generate_architecture_plan(
    script: str,
    max_nodes: int = 6,
    slide_index: int | None = None
) -> dict:
    """
    Generates a TEACHING-FIRST architecture diagram plan.

    Guarantees:
    - Always returns a dict
    - Always has at least ONE node
    - Never exceeds max_nodes
    - Never crashes downstream
    """

    # ----------------------------
    # Slide-specific constraints
    # ----------------------------
    if slide_index == 0:
        slide_context = """
SPECIAL FIRST SLIDE RULES:
- Show ONLY the core platform
- NO downstream services
- NO storage, NO pipelines, NO inference
- Prefer a SINGLE central node
"""
        fallback_label = script.split(".")[0][:40]
    else:
        slide_context = """
GENERAL SLIDE RULES:
- Only show components explicitly explained in the text
- Prefer removing components if unsure
"""
        fallback_label = "ML Component"

    # ----------------------------
    # Prompt
    # ----------------------------
    prompt = f"""
You are generating diagrams for TEACHING, not documentation.

STRICT RULES (FAIL IF VIOLATED):
- MAXIMUM {max_nodes} nodes — NEVER exceed this
- Prefer fewer components over completeness
- Introduce concepts gradually
- Do NOT show downstream services unless explicitly explained
- Avoid crossing edges unless absolutely necessary
- Diagram must be understandable in under 3 seconds
- Break explanations into incremental visual steps
- Even if components stay the same, introduce them gradually

{slide_context}

OUTPUT REQUIREMENTS:
- nodes: list of objects {{ id, label }}
- edges: list of objects {{ from, to }}
- Node count MUST be ≤ {max_nodes}
- If unsure, REMOVE components instead of adding them
- NO explanatory text

SCRIPT:
\"\"\"{script}\"\"\"  

Return ONLY valid JSON.
"""

    # ----------------------------
    # LLM Call
    # ----------------------------
    response = generate(prompt)

    try:
        plan = json.loads(response)
    except Exception:
        return {
            "title": f"Slide {slide_index + 1}" if slide_index is not None else "Architecture",
            "nodes": [{"id": "core", "label": fallback_label}],
            "edges": [],
        }

    # ------------------------------------------------
    # 🔒 HARD TYPE NORMALIZATION (CRITICAL FIX)
    # ------------------------------------------------
    if isinstance(plan, list):
        plan = {
            "nodes": plan,
            "edges": []
        }

    if not isinstance(plan, dict):
        plan = {
            "nodes": [],
            "edges": []
        }

    nodes = plan.get("nodes", [])
    edges = plan.get("edges", [])

    # 🚨 Guarantee at least ONE node
    if not nodes:
        nodes = [{"id": "core", "label": fallback_label}]
        edges = []

    # Enforce max_nodes strictly
    if len(nodes) > max_nodes:
        nodes = nodes[:max_nodes]
        valid_ids = {n["id"] for n in nodes}
        edges = [
            e for e in edges
            if e.get("from") in valid_ids and e.get("to") in valid_ids
        ]

    return {
        "title": f"Slide {slide_index + 1}" if slide_index is not None else "Architecture",
        "nodes": nodes,
        "edges": edges,
    }
