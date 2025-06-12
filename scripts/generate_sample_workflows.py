import os
import uuid
import random
import json # Use standard json for generating, ujson is for parsing speed primarily

# Ensure the target directory exists
TARGET_DIR = "data/raw_workflows"
NUM_WORKFLOWS_TO_GENERATE = 25 # Target for this run

# --- Workflow Templates ---
# Define 3-4 diverse templates here.
# Template 1: Simple Linear (Start -> Set -> Log)
TEMPLATE_LINEAR = {
    "name_prefix": "Simple Linear Workflow",
    "nodes_template": [
        {"base_id": "Start", "name": "Start Trigger", "type": "n8n-nodes-base.start", "typeVersion": 1, "position_x": 50, "position_y": 100, "parameters": {}},
        {"base_id": "SetData", "name": "Set Some Info", "type": "n8n-nodes-base.set", "typeVersion": 1.2, "position_x": 250, "position_y": 100, "parameters": {"values": {"string": [{"name": "message", "value": "Hello from n8n!"}]}, "keepOnlySet": True, "options": {}}},
        {"base_id": "LogOutput", "name": "Log Message", "type": "n8n-nodes-base.logMessage", "typeVersion": 1, "position_x": 450, "position_y": 100, "parameters": {"message": "={{$json.message}}", "logLevel": "notice"}}
    ],
    "connections_template": [
        ("Start", "main", "SetData", "main"),
        ("SetData", "main", "LogOutput", "main")
    ]
}

# Template 2: Simple Branching (Start -> If -> (Set A | Set B) -> Merge -> Log)
TEMPLATE_BRANCHING = {
    "name_prefix": "Basic Conditional Workflow",
    "nodes_template": [
        {"base_id": "Start", "name": "Start", "type": "n8n-nodes-base.start", "typeVersion": 1, "position_x": 50, "position_y": 200, "parameters": {}},
        {"base_id": "IfCondition", "name": "Check Condition", "type": "n8n-nodes-base.if", "typeVersion": 1, "position_x": 250, "position_y": 200, "parameters": {"conditions": {"string": [{"value1": "={{$json.input_value}}", "operation": "equal", "value2": "true"}]}}},
        {"base_id": "SetTrue", "name": "Path A Data", "type": "n8n-nodes-base.set", "typeVersion": 1.2, "position_x": 450, "position_y": 100, "parameters": {"values": {"string": [{"name": "branch_result", "value": "Took Path A"}]}}},
        {"base_id": "SetFalse", "name": "Path B Data", "type": "n8n-nodes-base.set", "typeVersion": 1.2, "position_x": 450, "position_y": 300, "parameters": {"values": {"string": [{"name": "branch_result", "value": "Took Path B"}]}}},
        {"base_id": "MergePaths", "name": "Merge Branches", "type": "n8n-nodes-base.merge", "typeVersion": 1.2, "position_x": 650, "position_y": 200, "parameters": {"mode": "append"}},
        {"base_id": "LogResult", "name": "Log Final", "type": "n8n-nodes-base.logMessage", "typeVersion": 1, "position_x": 850, "position_y": 200, "parameters": {"message": "Result: {{$json.branch_result}}"}}
    ],
    "connections_template": [
        ("Start", "main", "IfCondition", "main"),
        ("IfCondition", "0", "SetTrue", "main"), # Output 0 (true)
        ("IfCondition", "1", "SetFalse", "main"),# Output 1 (false)
        ("SetTrue", "main", "MergePaths", "main"),
        ("SetFalse", "main", "MergePaths", "main"),
        ("MergePaths", "main", "LogResult", "main")
    ]
}

# Template 3: HTTP Request -> Set
TEMPLATE_HTTP = {
    "name_prefix": "API Call Workflow",
    "nodes_template": [
        {"base_id": "Start", "name": "Manual Trigger", "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position_x": 50, "position_y": 100, "parameters": {}},
        {"base_id": "GetAPI", "name": "Fetch Data", "type": "n8n-nodes-base.httpRequest", "typeVersion": 3.2, "position_x": 250, "position_y": 100, "parameters": {"url": "https://jsonplaceholder.typicode.com/todos/{{ $runIndex + 1 }}", "method": "GET", "json":True, "options": {}}},
        {"base_id": "SetOutput", "name": "Store API Result", "type": "n8n-nodes-base.set", "typeVersion": 1.2, "position_x": 450, "position_y": 100, "parameters": {"values": {"string": [{"name": "api_title", "value": "={{$json.title}}"}]}, "options":{}}}
    ],
    "connections_template": [
        ("Start", "main", "GetAPI", "main"),
        ("GetAPI", "main", "SetOutput", "main")
    ]
}

ALL_TEMPLATES = [TEMPLATE_LINEAR, TEMPLATE_BRANCHING, TEMPLATE_HTTP]

def generate_unique_node_id(base_id: str, workflow_suffix: str) -> str:
    return f"{base_id}_{workflow_suffix}"

def create_workflow_from_template(template: dict, workflow_index: int) -> dict:
    workflow_suffix = str(uuid.uuid4())[:8] # Short UUID for some uniqueness
    workflow_json = {
        "name": f"{template['name_prefix']} #{workflow_index + 1}_{workflow_suffix}",
        "id": str(uuid.uuid4()), # Main workflow ID
        "active": random.choice([True, False]),
        "nodes": [],
        "connections": {},
        "settings": {"executionOrder": "v1"}, # Example setting
        "tags": [{"name": f"tag_{random.randint(1,3)}"}, {"name": "generated_sample"}]
    }

    node_id_map = {} # Maps template base_id to generated unique_id for this workflow

    # Create nodes
    for i, node_tpl in enumerate(template["nodes_template"]):
        unique_id = generate_unique_node_id(node_tpl["base_id"], workflow_suffix)
        node_id_map[node_tpl["base_id"]] = unique_id

        node = {
            "id": unique_id,
            "name": f"{node_tpl['name']} {workflow_index + 1}", # Vary name slightly
            "type": node_tpl["type"],
            "typeVersion": node_tpl["typeVersion"],
            "position": [node_tpl["position_x"] + random.randint(-10, 10), node_tpl["position_y"] + random.randint(-10, 10)],
            "parameters": json.loads(json.dumps(node_tpl["parameters"])) # Deep copy
        }
        # Slightly vary some parameters if possible (example for Set node)
        if node_tpl["type"] == "n8n-nodes-base.set" and "values" in node["parameters"]:
            if "string" in node["parameters"]["values"] and node["parameters"]["values"]["string"]:
                 node["parameters"]["values"]["string"][0]["value"] += f" (wf {workflow_index + 1})"
        elif node_tpl["type"] == "n8n-nodes-base.httpRequest" and "url" in node["parameters"]:
             node["parameters"]["url"] = node["parameters"]["url"].replace("{{ $runIndex + 1 }}", str(random.randint(1,20)))


        workflow_json["nodes"].append(node)

    # Create connections
    connections_dict = {}
    for src_base, src_port, tgt_base, tgt_port in template["connections_template"]:
        src_node_id_actual = node_id_map.get(src_base)
        tgt_node_id_actual = node_id_map.get(tgt_base)

        if not src_node_id_actual or not tgt_node_id_actual:
            print(f"Warning: Could not map node IDs for connection {src_base} -> {tgt_base} in workflow {workflow_json['name']}")
            continue

        if src_node_id_actual not in connections_dict:
            connections_dict[src_node_id_actual] = {}

        if src_port not in connections_dict[src_node_id_actual]:
            connections_dict[src_node_id_actual][src_port] = []

        connections_dict[src_node_id_actual][src_port].append([{"node": tgt_node_id_actual, "type": tgt_port}])

    workflow_json["connections"] = connections_dict

    return workflow_json

def main():
    os.makedirs(TARGET_DIR, exist_ok=True)

    generated_count = 0
    for i in range(NUM_WORKFLOWS_TO_GENERATE):
        template_choice = random.choice(ALL_TEMPLATES)
        workflow_data = create_workflow_from_template(template_choice, i)

        file_path = os.path.join(TARGET_DIR, f"sample_workflow_{str(uuid.uuid4())[:8]}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(workflow_data, f, indent=2)
            generated_count += 1
        except IOError as e:
            print(f"Error writing file {file_path}: {e}")

    print(f"Successfully generated {generated_count} sample workflow files in {TARGET_DIR}")

if __name__ == "__main__":
    main()
