# n8n_analyzer/analysis/workflow_metrics.py
from typing import Dict, Union, List, Optional
from n8n_analyzer.core.models import N8nWorkflow

# Default list of node types considered "complex" for complexity metrics
DEFAULT_COMPLEX_NODE_TYPES = [
    "n8n-nodes-base.function",
    "n8n-nodes-base.functionItem", # If item-based function nodes are different
    "n8n-nodes-base.merge",
    "n8n-nodes-base.switch", # Switch can be complex
    "n8n-nodes-base.executeWorkflow", # Sub-workflow
    # Add others as identified, e.g. specific complex integration nodes
]

def count_nodes(workflow: N8nWorkflow) -> int:
    """Counts the total number of nodes in the workflow."""
    return len(workflow.nodes)

def count_connections(workflow: N8nWorkflow) -> int:
    """Counts the total number of connections in the workflow."""
    return len(workflow.connections)

def count_unique_node_types(workflow: N8nWorkflow) -> int:
    """Counts the number of unique node types present in the workflow."""
    if not workflow.nodes:
        return 0
    return len(set(node.type for node in workflow.nodes))

def calculate_workflow_density(workflow: N8nWorkflow) -> float:
    """
    Calculates the density of the workflow graph.
    Density = E / (V * (V-1)) for a directed graph, where E is edges, V is vertices.
    Returns 0 if V < 2 (as density is undefined or trivially 0).
    """
    num_nodes = count_nodes(workflow)
    num_connections = count_connections(workflow)

    if num_nodes < 2:
        return 0.0

    max_possible_connections = num_nodes * (num_nodes - 1)
    if max_possible_connections == 0: # Should be covered by num_nodes < 2, but for safety
        return 0.0

    density = num_connections / max_possible_connections
    return round(density, 4) # Round to a few decimal places

def average_parameters_per_node(workflow: N8nWorkflow) -> float:
    """
    Calculates the average number of top-level parameter keys per node.
    This is a simple metric and might not reflect true parameter complexity.
    """
    if not workflow.nodes:
        return 0.0

    total_parameter_keys = sum(len(node.parameters) for node in workflow.nodes)
    return round(total_parameter_keys / len(workflow.nodes), 2)

def count_complex_node_types(
    workflow: N8nWorkflow,
    complex_types: Optional[List[str]] = None
) -> int:
    """
    Counts the number of nodes that are of types considered "complex".
    Args:
        workflow: The N8nWorkflow object.
        complex_types: A list of node type strings to consider complex.
                       Defaults to DEFAULT_COMPLEX_NODE_TYPES.
    """
    if complex_types is None:
        complex_types = DEFAULT_COMPLEX_NODE_TYPES

    if not workflow.nodes:
        return 0

    return sum(1 for node in workflow.nodes if node.type in complex_types)

def calculate_all_complexity_metrics(workflow: N8nWorkflow) -> Dict[str, Union[int, float]]:
    """
    Calculates and returns a dictionary of all defined complexity metrics for the workflow.
    """
    return {
        "node_count": count_nodes(workflow),
        "connection_count": count_connections(workflow),
        "unique_node_type_count": count_unique_node_types(workflow),
        "density": calculate_workflow_density(workflow),
        "average_parameters_per_node": average_parameters_per_node(workflow),
        "complex_node_count": count_complex_node_types(workflow)
        # Add more metrics here as they are defined
    }
