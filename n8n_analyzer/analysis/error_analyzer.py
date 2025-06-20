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


# === MISSING FUNCTIONS FOR PHASE 2 INTEGRATION ===

def detect_potential_errors(workflow: N8nWorkflow) -> Dict[str, Any]:
    """
    Detect potential errors and issues in the workflow structure.
    
    Args:
        workflow: The N8nWorkflow to analyze
    
    Returns:
        Dict containing potential error information
    """
    potential_errors = {
        'structural_issues': [],
        'configuration_issues': [],
        'best_practice_violations': [],
        'error_handling_analysis': analyze_error_handling(workflow)
    }
    
    # Check for structural issues
    node_ids = set(node.id for node in workflow.nodes)
    
    # Check for orphaned connections
    for conn in workflow.connections:
        if conn.source_node_id not in node_ids:
            potential_errors['structural_issues'].append({
                'type': 'orphaned_connection',
                'message': f"Connection references non-existent source node: {conn.source_node_id}"
            })
        
        if conn.target_node_id not in node_ids:
            potential_errors['structural_issues'].append({
                'type': 'orphaned_connection',
                'message': f"Connection references non-existent target node: {conn.target_node_id}"
            })
    
    # Check for nodes without proper configuration
    for node in workflow.nodes:
        # Check for missing required parameters based on node type
        if not node.parameters and 'base.set' not in node.type and 'base.start' not in node.type:
            potential_errors['configuration_issues'].append({
                'type': 'missing_parameters',
                'node_id': node.id,
                'node_type': node.type,
                'message': f"Node {node.id} ({node.type}) has no parameters configured"
            })
        
        # Check for missing node names
        if not node.name or not node.name.strip():
            potential_errors['best_practice_violations'].append({
                'type': 'missing_node_name',
                'node_id': node.id,
                'message': f"Node {node.id} has no descriptive name"
            })
    
    # Check for potential infinite loops (simplified check)
    if _has_potential_cycles(workflow):
        potential_errors['structural_issues'].append({
            'type': 'potential_cycle',
            'message': "Workflow may contain cycles that could lead to infinite loops"
        })
    
    # Check for missing error handling
    if not has_error_trigger_node(workflow) and not get_workflow_error_setting(workflow):
        potential_errors['best_practice_violations'].append({
            'type': 'no_error_handling',
            'message': "Workflow has no error handling configured"
        })
    
    return potential_errors

def analyze_error_patterns(workflow: N8nWorkflow) -> Dict[str, Any]:
    """
    Analyze patterns related to error handling and recovery in the workflow.
    
    Args:
        workflow: The N8nWorkflow to analyze
    
    Returns:
        Dict containing error pattern analysis
    """
    patterns = {
        'error_handling_patterns': [],
        'recovery_patterns': [],
        'failure_points': [],
        'resilience_score': 100.0
    }
    
    # Analyze error handling patterns
    error_triggers = get_nodes_by_type(workflow, ERROR_TRIGGER_NODE_TYPE)
    if error_triggers:
        patterns['error_handling_patterns'].append({
            'type': 'error_trigger_present',
            'count': len(error_triggers),
            'message': f"Found {len(error_triggers)} error trigger node(s)"
        })
    
    # Check for nodes with potential failure points
    high_risk_types = [
        'webhook', 'http', 'api', 'database', 'email', 'file'
    ]
    
    failure_points = []
    for node in workflow.nodes:
        node_type_lower = node.type.lower()
        if any(risk_type in node_type_lower for risk_type in high_risk_types):
            failure_points.append({
                'node_id': node.id,
                'node_type': node.type,
                'risk_category': next(risk for risk in high_risk_types if risk in node_type_lower),
                'message': f"Node {node.id} ({node.type}) represents a potential failure point"
            })
    
    patterns['failure_points'] = failure_points
    
    # Calculate resilience score
    resilience_score = 100.0
    
    # Reduce score for each failure point without error handling
    if failure_points and not (error_triggers or get_workflow_error_setting(workflow)):
        resilience_score -= len(failure_points) * 10
    
    # Reduce score for missing error workflows
    if not get_workflow_error_setting(workflow):
        resilience_score -= 20
    
    patterns['resilience_score'] = max(0.0, resilience_score)
    
    return patterns

def _has_potential_cycles(workflow: N8nWorkflow) -> bool:
    """
    Simple cycle detection using DFS to identify potential infinite loops.
    
    Args:
        workflow: The N8nWorkflow to check
    
    Returns:
        bool: True if potential cycles are detected
    """
    if not workflow.connections:
        return False
    
    # Build adjacency list
    graph = {}
    for node in workflow.nodes:
        graph[node.id] = []
    
    for conn in workflow.connections:
        if conn.source_node_id in graph and conn.target_node_id in graph:
            graph[conn.source_node_id].append(conn.target_node_id)
    
    # DFS cycle detection
    visited = set()
    rec_stack = set()
    
    def dfs(node_id):
        if node_id in rec_stack:
            return True  # Cycle detected
        
        if node_id in visited:
            return False
        
        visited.add(node_id)
        rec_stack.add(node_id)
        
        for neighbor in graph.get(node_id, []):
            if dfs(neighbor):
                return True
        
        rec_stack.remove(node_id)
        return False
    
    # Check all nodes for cycles
    for node_id in graph:
        if node_id not in visited:
            if dfs(node_id):
                return True
    
    return False
