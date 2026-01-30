from pathlib import Path
import subprocess

FRAMES_DIR = Path("static/frames")
FRAMES_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# NODE STYLING (NEW ✅)
# --------------------------------------------------

def node_style(role: str) -> str:
    if role == "core":
        return 'style.fill: "#e0f2fe"; style.stroke: "#0369a1"'
    if role == "input":
        return 'style.fill: "#dcfce7"; style.stroke: "#166534"'
    if role == "output":
        return 'style.fill: "#fee2e2"; style.stroke: "#991b1b"'
    if role == "external":
        return 'style.fill: "#ede9fe"; style.stroke: "#5b21b6"'
    return ""

# --------------------------------------------------
# FRAME PLANNING (UNCHANGED LOGIC ✅)
# --------------------------------------------------

def progressive_frames(plan: dict, mode="architecture"):
    nodes = plan.get("nodes", [])
    edges = plan.get("edges", [])

    if not nodes:
        return [plan]

    # Ensure every node has a role
    for n in nodes:
        n.setdefault("role", "process")

    ROLE_ORDER = ["input", "storage", "core", "process", "output", "external"]

    frames = []
    visible = set()

    for role in ROLE_ORDER:
        role_nodes = [n for n in nodes if n["role"] == role]
        if not role_nodes:
            continue

        for n in role_nodes:
            visible.add(n["id"])

        frame_nodes = [n for n in nodes if n["id"] in visible]
        frame_edges = [
            e for e in edges
            if e["from"] in visible and e["to"] in visible
        ]

        frames.append({
            "title": plan.get("title", "Architecture"),
            "nodes": frame_nodes,
            "edges": frame_edges,
            "focus": role_nodes[-1]["id"]
        })

    return frames or [plan]

# --------------------------------------------------
# D2 CONVERSION (CORRECT SYNTAX ✅)
# --------------------------------------------------

def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", " ")
            .replace(":", " -")
            .strip()
    )

def plan_to_d2(plan: dict) -> str:
    lines = [
        "direction: right",
        ""
    ]

    for node in plan["nodes"]:
        style = node_style(node.get("role", ""))
        lines.append(
            f'{node["id"]}: "{node["label"]}" {{ {style} }}'
        )

    lines.append("")

    for e in plan["edges"]:
        lines.append(f'{e["from"]} -> {e["to"]}')

    return "\n".join(lines)

# --------------------------------------------------
# FRAME RENDERING (D2 CLI ✅)
# --------------------------------------------------

def render_frame(plan: dict, frame_id: int) -> str:
    d2_text = plan_to_d2(plan)

    d2_path = FRAMES_DIR / f"frame_{frame_id}.d2"
    png_path = FRAMES_DIR / f"frame_{frame_id}.png"

    d2_path.write_text(d2_text)

    result = subprocess.run(
        ["d2", str(d2_path), str(png_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("❌ D2 render failed:")
        print(result.stderr)
        return ""

    return png_path.as_posix()
