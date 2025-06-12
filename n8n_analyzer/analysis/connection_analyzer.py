# n8n_analyzer/analysis/connection_analyzer.py
from collections import Counter
from typing import Dict, Tuple, List, Optional
from n8n_analyzer.core.models import N8nWorkflow, N8nNode
from n8n_analyzer.core.analyzer import (
    get_incoming_connections,
    get_outgoing_connections,
    get_source_node_from_connection,
    get_target_node_from_connection
)

DEFAULT_TRIGGER_NODE_TYPES = [
    "n8n-nodes-base.start",
    "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.cron",
    "n8n-nodes-base.executeWorkflowTrigger", # If n8n has such a thing for called workflows
    # Add other event-based triggers from various integrations if known
]

DEFAULT_TERMINAL_NODE_TYPES = [
    "n8n-nodes-base.logMessage",
    "n8n-nodes-base.respondToWebhook",
    "n8n-nodes-base.set", # Set can sometimes be a terminal if it's just outputting final data
    "n8n-nodes-base.googleSheets", # Often a data sink
    "n8n-nodes-base.dataDog", #Metric sinks
    # Add other common data sinks or final action nodes
]


def get_common_node_type_pairs(workflow: N8nWorkflow) -> Dict[Tuple[str, str], int]:
    """
    Counts occurrences of connected (source_type, target_type) node pairs.
    """
    pairs_counter = Counter()
    for conn in workflow.connections:
        source_node = get_source_node_from_connection(workflow, conn)
        target_node = get_target_node_from_connection(workflow, conn)

        if source_node and target_node:
            pairs_counter[(source_node.type, target_node.type)] += 1
    return dict(pairs_counter)

def get_node_io_degree(workflow: N8nWorkflow, node_id: str) -> Dict[str, int]:
    """
    Calculates in-degree and out-degree for a specific node.
    Returns {'in_degree': count, 'out_degree': count}
    Returns {'in_degree': 0, 'out_degree': 0} if node_id is not found.
    """
    node = workflow.get_node_by_id(node_id)
    if not node:
        return {'in_degree': 0, 'out_degree': 0}

    in_degree = len(get_incoming_connections(workflow, node_id))
    out_degree = len(get_outgoing_connections(workflow, node_id))
    return {'in_degree': in_degree, 'out_degree': out_degree}

def get_all_node_io_degrees(workflow: N8nWorkflow) -> Dict[str, Dict[str, int]]:
    """
    Calculates in-degree and out-degree for all nodes in the workflow.
    Returns a dictionary: {node_id: {'in_degree': count, 'out_degree': count}, ...}
    """
    degrees = {}
    for node in workflow.nodes:
        degrees[node.id] = get_node_io_degree(workflow, node.id)
    return degrees

def identify_trigger_nodes(
    workflow: N8nWorkflow,
    known_trigger_types: Optional[List[str]] = None
) -> List[N8nNode]:
    """
    Identifies nodes that are likely triggers based on having no incoming connections
    and matching a list of known trigger types.
    """
    if known_trigger_types is None:
        known_trigger_types = DEFAULT_TRIGGER_NODE_TYPES

    trigger_nodes: List[N8nNode] = []
    for node in workflow.nodes:
        if not get_incoming_connections(workflow, node.id) and node.type in known_trigger_types:
            trigger_nodes.append(node)
    return trigger_nodes

def identify_potential_terminal_nodes(
    workflow: N8nWorkflow,
    known_terminal_types: Optional[List[str]] = None
) -> List[N8nNode]:
    """
    Identifies nodes that are potential terminals based on having no outgoing connections
    and optionally matching a list of known terminal types.
    If known_terminal_types is None, it returns all nodes with no outgoing connections.
    """
    terminal_nodes: List[N8nNode] = []
    for node in workflow.nodes:
        if not get_outgoing_connections(workflow, node.id):
            if known_terminal_types is None or node.type in known_terminal_types:
                terminal_nodes.append(node)
    return terminal_nodes
