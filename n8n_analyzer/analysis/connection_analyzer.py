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


# === ENHANCED PATTERN ANALYSIS FOR PHASE 2 ===

def get_sequential_patterns(workflow: N8nWorkflow, max_length: int = 3) -> Dict[Tuple[str, ...], int]:
    """
    Identifies sequential patterns of node types up to max_length.
    Returns patterns as tuples of node types with their occurrence counts.
    
    Args:
        workflow: The N8nWorkflow to analyze
        max_length: Maximum length of patterns to detect (default: 3)
    
    Returns:
        Dict mapping pattern tuples to occurrence counts
    """
    patterns = Counter()
    
    def dfs_pattern(current_node: N8nNode, path: List[str], visited: set, depth: int):
        if depth >= max_length:
            return
        
        outgoing = get_outgoing_connections(workflow, current_node.id)
        for conn in outgoing:
            target_node = get_target_node_from_connection(workflow, conn)
            if target_node and target_node.id not in visited:
                new_path = path + [target_node.type]
                patterns[tuple(new_path)] += 1
                
                new_visited = visited.copy()
                new_visited.add(target_node.id)
                dfs_pattern(target_node, new_path, new_visited, depth + 1)
    
    # Start pattern detection from trigger nodes
    trigger_nodes = identify_trigger_nodes(workflow)
    for trigger in trigger_nodes:
        dfs_pattern(trigger, [trigger.type], {trigger.id}, 0)
    
    return dict(patterns)

def analyze_workflow_paths(workflow: N8nWorkflow) -> Dict[str, any]:
    """
    Comprehensive path analysis of the workflow structure.
    
    Returns:
        Dict containing path statistics and analysis
    """
    trigger_nodes = identify_trigger_nodes(workflow)
    terminal_nodes = identify_potential_terminal_nodes(workflow)
    
    def find_all_paths(start_node: N8nNode, visited: set = None) -> List[List[str]]:
        if visited is None:
            visited = set()
        
        if start_node.id in visited:
            return []
        
        visited = visited.copy()
        visited.add(start_node.id)
        
        outgoing = get_outgoing_connections(workflow, start_node.id)
        if not outgoing:  # Terminal node
            return [[start_node.type]]
        
        all_paths = []
        for conn in outgoing:
            target_node = get_target_node_from_connection(workflow, conn)
            if target_node:
                sub_paths = find_all_paths(target_node, visited)
                for sub_path in sub_paths:
                    all_paths.append([start_node.type] + sub_path)
        
        return all_paths
    
    # Collect all paths from triggers to terminals
    all_paths = []
    for trigger in trigger_nodes:
        paths = find_all_paths(trigger)
        all_paths.extend(paths)
    
    # Analyze path characteristics
    path_lengths = [len(path) for path in all_paths]
    
    return {
        'total_paths': len(all_paths),
        'avg_path_length': sum(path_lengths) / len(path_lengths) if path_lengths else 0,
        'min_path_length': min(path_lengths) if path_lengths else 0,
        'max_path_length': max(path_lengths) if path_lengths else 0,
        'unique_paths': len(set(tuple(path) for path in all_paths)),
        'trigger_count': len(trigger_nodes),
        'terminal_count': len(terminal_nodes),
        'paths_sample': all_paths[:10]  # Sample for inspection
    }

def detect_common_integration_patterns(workflow: N8nWorkflow) -> Dict[str, int]:
    """
    Detects common integration patterns in workflows.
    
    Returns:
        Dict mapping pattern names to occurrence counts
    """
    patterns = {}
    
    # Pattern: Webhook -> Process -> Response
    webhook_response_count = 0
    for node in workflow.nodes:
        if 'webhook' in node.type.lower() and get_outgoing_connections(workflow, node.id):
            # Check if there's a path to a response node
            def has_response_in_path(current_node: N8nNode, visited: set = None) -> bool:
                if visited is None:
                    visited = set()
                if current_node.id in visited:
                    return False
                
                if 'respond' in current_node.type.lower():
                    return True
                
                visited = visited.copy()
                visited.add(current_node.id)
                
                for conn in get_outgoing_connections(workflow, current_node.id):
                    target = get_target_node_from_connection(workflow, conn)
                    if target and has_response_in_path(target, visited):
                        return True
                return False
            
            if has_response_in_path(node):
                webhook_response_count += 1
    
    patterns['webhook_to_response'] = webhook_response_count
    
    # Pattern: Data Collection -> Processing -> Storage
    collection_storage_count = 0
    data_collection_types = ['http', 'api', 'webhook', 'database', 'file']
    storage_types = ['sheets', 'database', 'file', 'storage']
    
    for node in workflow.nodes:
        node_type_lower = node.type.lower()
        if any(dt in node_type_lower for dt in data_collection_types):
            # Check if leads to storage
            def has_storage_in_path(current_node: N8nNode, visited: set = None) -> bool:
                if visited is None:
                    visited = set()
                if current_node.id in visited:
                    return False
                
                if any(st in current_node.type.lower() for st in storage_types):
                    return True
                
                visited = visited.copy()
                visited.add(current_node.id)
                
                for conn in get_outgoing_connections(workflow, current_node.id):
                    target = get_target_node_from_connection(workflow, conn)
                    if target and has_storage_in_path(target, visited):
                        return True
                return False
            
            if has_storage_in_path(node):
                collection_storage_count += 1
    
    patterns['data_collection_to_storage'] = collection_storage_count
    
    return patterns

def get_connection_statistics(workflow: N8nWorkflow) -> Dict[str, any]:
    """
    Comprehensive connection statistics for the workflow.
    
    Returns:
        Dict containing various connection metrics
    """
    total_connections = len(workflow.connections)
    total_nodes = len(workflow.nodes)
    
    # Calculate density
    max_possible_connections = total_nodes * (total_nodes - 1) if total_nodes > 1 else 0
    density = total_connections / max_possible_connections if max_possible_connections > 0 else 0
    
    # Degree analysis
    degrees = get_all_node_io_degrees(workflow)
    in_degrees = [d['in_degree'] for d in degrees.values()]
    out_degrees = [d['out_degree'] for d in degrees.values()]
    
    # Hub analysis (nodes with high connectivity)
    high_in_degree_nodes = [(node_id, deg['in_degree']) for node_id, deg in degrees.items() 
                           if deg['in_degree'] > 2]
    high_out_degree_nodes = [(node_id, deg['out_degree']) for node_id, deg in degrees.items() 
                            if deg['out_degree'] > 2]
    
    return {
        'total_connections': total_connections,
        'total_nodes': total_nodes,
        'density': round(density, 4),
        'avg_in_degree': sum(in_degrees) / len(in_degrees) if in_degrees else 0,
        'avg_out_degree': sum(out_degrees) / len(out_degrees) if out_degrees else 0,
        'max_in_degree': max(in_degrees) if in_degrees else 0,
        'max_out_degree': max(out_degrees) if out_degrees else 0,
        'hub_nodes_in': high_in_degree_nodes,
        'hub_nodes_out': high_out_degree_nodes,
        'isolated_nodes': [node.id for node in workflow.nodes 
                          if degrees[node.id]['in_degree'] == 0 and degrees[node.id]['out_degree'] == 0]
    }
