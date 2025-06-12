# n8n_analyzer/analysis/node_analyzer.py
from collections import Counter, defaultdict
from typing import Dict, Union, List, Any
from n8n_analyzer.core.models import N8nWorkflow, N8nNode

# calculate_node_type_distribution function (already exists, keep it) ...
def calculate_node_type_distribution(workflow: N8nWorkflow) -> Dict[str, Dict[str, Union[int, float]]]:
    """
    Calculates the distribution of node types within a single workflow.
    """
    if not workflow.nodes:
        return {}
    node_type_counts = Counter(node.type for node in workflow.nodes)
    total_nodes = len(workflow.nodes)
    distribution = {}
    for node_type, count in node_type_counts.items():
        percentage = round((count / total_nodes) * 100, 2) if total_nodes > 0 else 0
        distribution[node_type] = {"count": count, "percentage": percentage}
    return distribution

# --- New Parameter Analysis Functions ---

def extract_parameter_keys_for_node(node: N8nNode) -> List[str]:
    """Returns a sorted list of top-level keys from the node's parameters dictionary."""
    if not node.parameters:
        return []
    return sorted(list(node.parameters.keys()))

def extract_all_parameter_keys_by_type(workflow: N8nWorkflow) -> Dict[str, Dict[str, int]]:
    """
    Aggregates parameter key counts for each node type in the workflow.
    Output: {"node_type_A": {"param_key1": count, "param_key2": count}, ...}
    """
    keys_by_type = defaultdict(lambda: Counter()) # type: ignore
    for node in workflow.nodes:
        if node.parameters:
            for key in node.parameters.keys():
                keys_by_type[node.type][key] += 1

    # Convert Counter objects to dicts for the final output
    result = {node_type: dict(param_counts) for node_type, param_counts in keys_by_type.items()}
    return result

def get_nodes_with_specific_parameter(workflow: N8nWorkflow, parameter_key: str) -> List[N8nNode]:
    """Finds all nodes in the workflow that have a specific top-level parameter key."""
    return [
        node for node in workflow.nodes
        if node.parameters and parameter_key in node.parameters
    ]

def get_nodes_with_specific_parameter_value(
    workflow: N8nWorkflow,
    parameter_key: str,
    parameter_value: Any
) -> List[N8nNode]:
    """
    Finds all nodes in the workflow where a specific parameter key has a specific value.
    Uses simple direct comparison for the value.
    """
    return [
        node for node in workflow.nodes
        if node.parameters and
           parameter_key in node.parameters and
           node.parameters[parameter_key] == parameter_value
    ]
