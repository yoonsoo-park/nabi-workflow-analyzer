# n8n_analyzer/analysis/error_analyzer.py
from typing import Optional, List, Dict, Any # Added Any
from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection
from n8n_analyzer.core.analyzer import get_nodes_by_type, get_incoming_connections

ERROR_TRIGGER_NODE_TYPE = "n8n-nodes-base.errorTrigger"

def has_error_trigger_node(workflow: N8nWorkflow) -> bool:
    """Checks if the workflow contains an Error Trigger node."""
    return bool(get_nodes_by_type(workflow, ERROR_TRIGGER_NODE_TYPE))

def get_workflow_error_setting(workflow: N8nWorkflow) -> Optional[str]:
    """
    Retrieves the ID of the designated error workflow from the workflow's settings.
    Returns None if no error workflow is set or settings are not present.
    """
    if workflow.settings and isinstance(workflow.settings, dict):
        return workflow.settings.get("errorWorkflow")
    return None

def count_connections_to_error_trigger(workflow: N8nWorkflow) -> int:
    """
    Counts how many connections are made TO any Error Trigger node within the workflow.
    This is unusual for a main workflow but could indicate an Error Trigger node
    is being used as a junction in a sub-workflow designed as an error handler.
    """
    error_trigger_nodes = get_nodes_by_type(workflow, ERROR_TRIGGER_NODE_TYPE)
    if not error_trigger_nodes:
        return 0

    count = 0
    for error_node in error_trigger_nodes:
        count += len(get_incoming_connections(workflow, error_node.id))
    return count

def analyze_error_handling(workflow: N8nWorkflow) -> Dict[str, Any]: # Changed from any to Any
    """
    Provides a basic summary of error handling features detected in the workflow.
    """
    return {
        "has_error_trigger": has_error_trigger_node(workflow),
        "designated_error_workflow_id": get_workflow_error_setting(workflow),
        "connections_to_error_trigger_nodes": count_connections_to_error_trigger(workflow)
        # Future: Add detection for 'Continue On Fail' usage on specific nodes,
        # or connections from known 'error' output ports of nodes like Try/Catch.
    }
