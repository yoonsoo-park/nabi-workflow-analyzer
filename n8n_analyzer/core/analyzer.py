# n8n_analyzer/core/analyzer.py
from typing import List, Optional, Dict
from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection

def get_nodes_by_type(workflow: N8nWorkflow, node_type: str) -> List[N8nNode]:
    """Returns all nodes of a specific type from the workflow."""
    return [node for node in workflow.nodes if node.type == node_type]

def get_incoming_connections(workflow: N8nWorkflow, node_id: str) -> List[N8nConnection]:
    """Returns all connections targeting the specified node_id."""
    return [conn for conn in workflow.connections if conn.target_node_id == node_id]

def get_outgoing_connections(workflow: N8nWorkflow, source_node_id: str) -> List[N8nConnection]:
    """Returns all connections originating from the specified source_node_id."""
    return [conn for conn in workflow.connections if conn.source_node_id == source_node_id]

def get_node_by_id(workflow: N8nWorkflow, node_id: str) -> Optional[N8nNode]:
    """
    Retrieves a node by its ID from the workflow.
    This is a convenience wrapper around the N8nWorkflow.get_node_by_id method
    for use in analysis contexts where a standalone function might be preferred.
    """
    return workflow.get_node_by_id(node_id)

def get_source_node_from_connection(workflow: N8nWorkflow, connection: N8nConnection) -> Optional[N8nNode]:
    """Helper to get the actual source node object from a connection object."""
    return workflow.get_node_by_id(connection.source_node_id)

def get_target_node_from_connection(workflow: N8nWorkflow, connection: N8nConnection) -> Optional[N8nNode]:
    """Helper to get the actual target node object from a connection object."""
    return workflow.get_node_by_id(connection.target_node_id)

def get_dangling_nodes(
    workflow: N8nWorkflow,
    input_dangling_exclude_types: Optional[List[str]] = None,
    output_dangling_exclude_types: Optional[List[str]] = None
) -> Dict[str, List[N8nNode]]:
    """
    Identifies nodes with no incoming connections (excluding specified types like 'start' nodes)
    and nodes with no outgoing connections (excluding specified types).

    Args:
        workflow: The N8nWorkflow object to analyze.
        input_dangling_exclude_types: List of node types to exclude from input dangling check
                                      (e.g., trigger nodes). Defaults to common triggers.
        output_dangling_exclude_types: List of node types to exclude from output dangling check
                                       (e.g., terminal logging/response nodes). Defaults to common terminals.

    Returns:
        A dictionary with keys 'inputs_dangling' and 'outputs_dangling',
        each containing a list of N8nNode objects.
    """
    if input_dangling_exclude_types is None:
        input_dangling_exclude_types = [
            "n8n-nodes-base.start",
            "n8n-nodes-base.manualTrigger",
            "n8n-nodes-base.webhook",
            "n8n-nodes-base.cron",
            # Add other common trigger node types
        ]

    if output_dangling_exclude_types is None:
        output_dangling_exclude_types = [
            "n8n-nodes-base.logMessage",
            "n8n-nodes-base.respondToWebhook",
            # Add other common terminal/response node types
        ]

    inputs_dangling: List[N8nNode] = []
    outputs_dangling: List[N8nNode] = []

    all_target_node_ids = {conn.target_node_id for conn in workflow.connections}
    all_source_node_ids = {conn.source_node_id for conn in workflow.connections}

    for node in workflow.nodes:
        # Check for dangling inputs
        if node.id not in all_target_node_ids and node.type not in input_dangling_exclude_types:
            inputs_dangling.append(node)

        # Check for dangling outputs
        if node.id not in all_source_node_ids and node.type not in output_dangling_exclude_types:
            outputs_dangling.append(node)

    return {"inputs_dangling": inputs_dangling, "outputs_dangling": outputs_dangling}
