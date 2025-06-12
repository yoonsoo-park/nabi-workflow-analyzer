# n8n_analyzer/core/models.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

@dataclass
class N8nNode:
    """Represents a single node in an n8n workflow."""
    id: str  # The unique identifier of the node within the workflow (e.g., "SET_ITEM_1")
    name: str  # User-defined display name (e.g., "Set Customer ID")
    type: str  # Type of the node (e.g., "n8n-nodes-base.set")
    typeVersion: int
    position: Tuple[int, int] # [x, y] coordinates on the canvas
    parameters: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None # If 'notesInFlow' is true and notes are present

@dataclass
class N8nConnection:
    """Represents a single connection between two nodes in an n8n workflow."""
    source_node_id: str
    source_node_output_port: str # e.g., "main", "0", "1" (for different output slots)
    target_node_id: str
    target_node_input_port: str  # e.g., "main", "0", "1" (for different input slots)

@dataclass
class N8nWorkflow:
    """Represents an entire n8n workflow."""
    name: str
    nodes: List[N8nNode]
    connections: List[N8nConnection]
    id: Optional[str] = None # Unique identifier for the workflow itself (from root JSON)
    active: Optional[bool] = None
    tags: Optional[Dict[str, Any]] = field(default_factory=dict) # Or List[Dict] depending on structure
    settings: Optional[Dict[str, Any]] = field(default_factory=dict) # e.g., error workflow, timezone
    meta: Optional[Dict[str, Any]] = field(default_factory=dict) # Info about n8n instance/user
    staticData: Optional[Dict[str, Any]] = field(default_factory=dict) # For 'Workflow static data'
    file_path: Optional[str] = None # Store the path of the file this workflow was loaded from

    def get_node_by_id(self, node_id: str) -> Optional[N8nNode]:
        """Helper to find a node by its ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

if __name__ == '__main__':
    node1 = N8nNode(id="StartNode_1", name="Start", type="n8n-nodes-base.start", typeVersion=1, position=(100, 100))
    node2 = N8nNode(id="SetNode_1", name="Set Data", type="n8n-nodes-base.set", typeVersion=2, position=(300, 100),
                    parameters={"values": {"string": [{"name": "city", "value": "New York"}]}})
    node3 = N8nNode(id="LogNode_1", name="Log Output", type="n8n-nodes-base.logMessage", typeVersion=1, position=(500, 100),
                    parameters={"message": "={{ $json.city }}"})
    conn1 = N8nConnection(source_node_id="StartNode_1", source_node_output_port="main",
                          target_node_id="SetNode_1", target_node_input_port="main")
    conn2 = N8nConnection(source_node_id="SetNode_1", source_node_output_port="main",
                          target_node_id="LogNode_1", target_node_input_port="main")
    workflow = N8nWorkflow(
        name="Sample Workflow",
        id="workflow_abc123",
        active=True,
        nodes=[node1, node2, node3],
        connections=[conn1, conn2],
        settings={"errorWorkflow": "error_handler_xyz"},
        file_path="path/to/sample_workflow.json"
    )
    print("Workflow Name:", workflow.name)
    print("Workflow ID:", workflow.id)
    print("Is Active:", workflow.active)
    print("Number of Nodes:", len(workflow.nodes))
    print("First Node Type:", workflow.nodes[0].type if workflow.nodes else "N/A")
    print("First Node Parameters:", workflow.nodes[1].parameters if len(workflow.nodes) > 1 else "N/A")
    print("Number of Connections:", len(workflow.connections))
    found_node = workflow.get_node_by_id("SetNode_1")
    if found_node:
        print(f"Found node by ID 'SetNode_1': {found_node.name}")
