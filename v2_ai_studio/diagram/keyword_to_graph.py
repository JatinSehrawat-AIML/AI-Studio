def infer_role(component_type: str) -> str:
    if component_type == "storage":
        return "storage"
    if component_type == "compute":
        return "process"
    if component_type == "platform":
        return "core"
    if component_type == "service":
        return "external"
    return "process"


def keywords_to_graph(keyword_data: dict) -> dict:
    components = keyword_data.get("components", [])
    relations = keyword_data.get("relations", [])

    if not components:
        return {}

    nodes = []
    for c in components:
        nodes.append({
            "id": c["name"].lower().replace(" ", "_"),
            "label": c["name"],
            "role": infer_role(c.get("type", "process"))
        })

    edges = []
    for r in relations:
        edges.append({
            "from": r["from"].lower().replace(" ", "_"),
            "to": r["to"].lower().replace(" ", "_"),
        })

    return {
        "title": "System Architecture",
        "nodes": nodes,
        "edges": edges
    }
