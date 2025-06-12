#!/usr/bin/env python3
"""
Sample n8n Workflow Data Generator

Generates realistic sample n8n workflow JSON files for testing and development.
Creates a minimum of 100 workflows with various node types, complexities, and patterns.
"""

import os
import ujson
import random
from typing import List, Dict, Any, Tuple
from pathlib import Path


# Common n8n node types and their configurations
NODE_TYPES = {
    "n8n-nodes-base.start": {
        "name_prefix": "Start",
        "parameters": {},
        "outputs": ["main"]
    },
    "n8n-nodes-base.set": {
        "name_prefix": "Set",
        "parameters": {
            "values": {
                "string": [
                    {"name": "variable", "value": "sample_value"}
                ]
            }
        },
        "outputs": ["main"]
    },
    "n8n-nodes-base.httpRequest": {
        "name_prefix": "HTTP Request",
        "parameters": {
            "url": "https://api.example.com/data",
            "method": "GET",
            "headers": {
                "Content-Type": "application/json"
            }
        },
        "outputs": ["main"]
    },
    "n8n-nodes-base.if": {
        "name_prefix": "IF",
        "parameters": {
            "conditions": {
                "string": [
                    {
                        "value1": "={{ $json.status }}",
                        "operation": "equal",
                        "value2": "active"
                    }
                ]
            }
        },
        "outputs": ["main", "false"]
    },
    "n8n-nodes-base.function": {
        "name_prefix": "Function",
        "parameters": {
            "functionCode": "return items.map(item => ({ json: { ...item.json, processed: true } }));"
        },
        "outputs": ["main"]
    },
    "n8n-nodes-base.webhook": {
        "name_prefix": "Webhook",
        "parameters": {
            "path": "webhook-path",
            "httpMethod": "POST"
        },
        "outputs": ["main"]
    },
    "n8n-nodes-base.slack": {
        "name_prefix": "Slack",
        "parameters": {
            "channel": "#general",
            "text": "Hello from n8n!"
        },
        "outputs": ["main"]
    },
    "n8n-nodes-base.googleSheets": {
        "name_prefix": "Google Sheets",
        "parameters": {
            "operation": "append",
            "sheetId": "1234567890",
            "values": {
                "A": "={{ $json.name }}",
                "B": "={{ $json.email }}"
            }
        },
        "outputs": ["main"]
    },
    "n8n-nodes-base.emailSend": {
        "name_prefix": "Send Email",
        "parameters": {
            "toEmail": "user@example.com",
            "subject": "Notification",
            "text": "This is a notification from your workflow."
        },
        "outputs": ["main"]
    },
    "n8n-nodes-base.wait": {
        "name_prefix": "Wait",
        "parameters": {
            "amount": 5,
            "unit": "seconds"
        },
        "outputs": ["main"]
    }
}

# Workflow templates for different complexity levels
WORKFLOW_TEMPLATES = [
    {
        "name": "Simple Linear Workflow",
        "pattern": "linear",
        "node_count": (3, 5),
        "complexity": "simple"
    },
    {
        "name": "Conditional Workflow",
        "pattern": "conditional",
        "node_count": (5, 8),
        "complexity": "medium"
    },
    {
        "name": "Complex Multi-Branch",
        "pattern": "multi_branch",
        "node_count": (8, 15),
        "complexity": "complex"
    },
    {
        "name": "API Integration",
        "pattern": "api_integration",
        "node_count": (6, 10),
        "complexity": "medium"
    },
    {
        "name": "Data Processing Pipeline",
        "pattern": "data_pipeline",
        "node_count": (10, 20),
        "complexity": "complex"
    }
]

# Sample workflow categories and tags
WORKFLOW_CATEGORIES = [
    "data-processing",
    "api-integration",
    "notification",
    "automation",
    "webhook-handling",
    "social-media",
    "email-marketing",
    "file-processing",
    "database-sync",
    "monitoring"
]


def generate_node_id(node_type: str, index: int) -> str:
    """Generate a unique node ID."""
    type_short = node_type.split('.')[-1].upper()
    return f"{type_short}_{index}"


def generate_position(index: int, pattern: str = "linear") -> Tuple[int, int]:
    """Generate canvas position for a node."""
    if pattern == "linear":
        return (100 + index * 200, 100)
    elif pattern == "grid":
        row = index // 3
        col = index % 3
        return (100 + col * 200, 100 + row * 150)
    else:
        # Random positioning
        return (random.randint(50, 800), random.randint(50, 600))


def create_node(node_type: str, index: int, position: Tuple[int, int]) -> Dict[str, Any]:
    """Create a single n8n node."""
    config = NODE_TYPES[node_type]
    
    # Add some variation to parameters
    parameters = config["parameters"].copy()
    if node_type == "n8n-nodes-base.set":
        # Randomize set node values
        var_name = random.choice(["user_id", "status", "timestamp", "category", "priority"])
        var_value = random.choice(["active", "processed", "pending", "high", "medium", "low"])
        parameters["values"]["string"][0] = {"name": var_name, "value": var_value}
    elif node_type == "n8n-nodes-base.httpRequest":
        # Randomize API endpoints
        endpoints = [
            "https://api.github.com/user",
            "https://jsonplaceholder.typicode.com/posts",
            "https://api.openweathermap.org/data/2.5/weather",
            "https://reqres.in/api/users"
        ]
        parameters["url"] = random.choice(endpoints)
    
    return {
        "id": generate_node_id(node_type, index),
        "name": f"{config['name_prefix']} {index}",
        "type": node_type,
        "typeVersion": random.choice([1, 1, 2]),  # Mostly version 1, some version 2
        "position": list(position),
        "parameters": parameters
    }


def create_connections(nodes: List[Dict[str, Any]], pattern: str) -> Dict[str, Any]:
    """Create connections between nodes based on pattern."""
    connections = {}
    
    if pattern == "linear":
        # Simple linear chain
        for i in range(len(nodes) - 1):
            source_id = nodes[i]["id"]
            target_id = nodes[i + 1]["id"]
            
            connections[source_id] = {
                "main": [
                    [{"node": target_id, "type": "main", "index": 0}]
                ]
            }
    
    elif pattern == "conditional":
        # Start -> IF -> two branches
        if len(nodes) >= 4:
            # First connection: Start -> IF
            connections[nodes[0]["id"]] = {
                "main": [
                    [{"node": nodes[1]["id"], "type": "main", "index": 0}]
                ]
            }
            
            # IF node connections (true and false branches)
            if_node_id = nodes[1]["id"]
            connections[if_node_id] = {
                "main": [
                    [{"node": nodes[2]["id"], "type": "main", "index": 0}]
                ],
                "false": [
                    [{"node": nodes[3]["id"], "type": "main", "index": 0}]
                ]
            }
            
            # Continue linear connections for remaining nodes
            for i in range(4, len(nodes)):
                connections[nodes[i-1]["id"]] = {
                    "main": [
                        [{"node": nodes[i]["id"], "type": "main", "index": 0}]
                    ]
                }
    
    elif pattern == "multi_branch":
        # More complex branching pattern
        if len(nodes) >= 3:
            # First node connects to multiple nodes
            source_id = nodes[0]["id"]
            connections[source_id] = {
                "main": [
                    [
                        {"node": nodes[1]["id"], "type": "main", "index": 0},
                        {"node": nodes[2]["id"], "type": "main", "index": 0}
                    ]
                ]
            }
            
            # Continue with linear connections for remaining nodes
            for i in range(3, len(nodes)):
                connections[nodes[i-1]["id"]] = {
                    "main": [
                        [{"node": nodes[i]["id"], "type": "main", "index": 0}]
                    ]
                }
    
    else:
        # Default to linear for other patterns
        for i in range(len(nodes) - 1):
            source_id = nodes[i]["id"]
            target_id = nodes[i + 1]["id"]
            
            connections[source_id] = {
                "main": [
                    [{"node": target_id, "type": "main", "index": 0}]
                ]
            }
    
    return connections


def generate_workflow(template: Dict[str, Any], workflow_id: int) -> Dict[str, Any]:
    """Generate a single workflow based on template."""
    node_count = random.randint(*template["node_count"])
    pattern = template["pattern"]
    
    # Select node types based on pattern
    if pattern == "api_integration":
        node_types = [
            "n8n-nodes-base.start",
            "n8n-nodes-base.httpRequest",
            "n8n-nodes-base.function",
            "n8n-nodes-base.set"
        ]
    elif pattern == "conditional":
        node_types = [
            "n8n-nodes-base.start",
            "n8n-nodes-base.if",
            "n8n-nodes-base.set",
            "n8n-nodes-base.emailSend"
        ]
    else:
        # Mix of common node types
        node_types = list(NODE_TYPES.keys())
    
    # Generate nodes
    nodes = []
    for i in range(node_count):
        if i == 0:
            # First node is always start
            node_type = "n8n-nodes-base.start"
        elif i == 1 and pattern == "conditional":
            # Second node in conditional is IF
            node_type = "n8n-nodes-base.if"
        else:
            node_type = random.choice(node_types)
        
        position = generate_position(i, pattern)
        node = create_node(node_type, i, position)
        nodes.append(node)
    
    # Generate connections
    connections = create_connections(nodes, pattern)
    
    # Generate workflow metadata
    category = random.choice(WORKFLOW_CATEGORIES)
    workflow_name = f"{template['name']} - {category.title()} {workflow_id}"
    
    workflow = {
        "name": workflow_name,
        "id": f"workflow_{workflow_id:04d}",
        "active": random.choice([True, True, False]),  # 2/3 chance of being active
        "nodes": nodes,
        "connections": connections,
        "tags": {
            "category": category,
            "complexity": template["complexity"],
            "pattern": pattern
        },
        "settings": {
            "errorWorkflow": "error_handler" if random.random() > 0.7 else None,
            "timezone": random.choice(["America/New_York", "Europe/London", "Asia/Tokyo"])
        },
        "meta": {
            "created": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "version": "1.0",
            "generator": "sample_data_generator"
        },
        "staticData": {}
    }
    
    return workflow


def generate_sample_workflows(
    output_dir: str = "data/raw_workflows", 
    num_workflows: int = 100
) -> None:
    """Generate sample workflow files."""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {num_workflows} sample workflows in {output_path}")
    
    workflows_created = 0
    
    for i in range(num_workflows):
        # Select random template
        template = random.choice(WORKFLOW_TEMPLATES)
        
        # Generate workflow
        workflow = generate_workflow(template, i + 1)
        
        # Save to file
        filename = f"workflow_{i+1:04d}_{workflow['tags']['category']}.json"
        file_path = output_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            ujson.dump(workflow, f, indent=2)
        
        workflows_created += 1
        
        if (i + 1) % 10 == 0:
            print(f"Created {i + 1} workflows...")
    
    print(f"\n✅ Successfully generated {workflows_created} sample workflows!")
    print(f"Files saved to: {output_path.absolute()}")
    
    # Generate summary stats
    complexity_counts = {"simple": 0, "medium": 0, "complex": 0}
    category_counts = {}
    
    for file_path in output_path.glob("*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow = ujson.load(f)
            complexity = workflow["tags"]["complexity"]
            category = workflow["tags"]["category"]
            
            complexity_counts[complexity] += 1
            category_counts[category] = category_counts.get(category, 0) + 1
    
    print("\n📊 Sample Data Summary:")
    print(f"Total workflows: {workflows_created}")
    print(f"Complexity distribution: {complexity_counts}")
    print(f"Category distribution: {dict(sorted(category_counts.items()))}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample n8n workflow data")
    parser.add_argument("--output-dir", default="data/raw_workflows", 
                       help="Output directory for workflow files")
    parser.add_argument("--count", type=int, default=100,
                       help="Number of workflows to generate")
    
    args = parser.parse_args()
    
    generate_sample_workflows(args.output_dir, args.count) 