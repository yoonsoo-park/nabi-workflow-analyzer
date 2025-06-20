# n8n_analyzer/analysis/workflow_metadata.py
from typing import Dict, Any, List, Optional, Tuple
from n8n_analyzer.core.models import N8nWorkflow, N8nNode
from n8n_analyzer.analysis.connection_analyzer import identify_trigger_nodes, identify_potential_terminal_nodes

def extract_workflow_metadata(workflow: N8nWorkflow) -> Dict[str, Any]:
    """
    Extracts and organizes key metadata from an N8nWorkflow object.

    Args:
        workflow: The N8nWorkflow object.

    Returns:
        A dictionary containing structured metadata.
    """

    processed_tags: Optional[List[str]] = None
    if workflow.tags:
        # n8n tags are often like: [{"id": "...", "name": "TagName"}]
        # Or sometimes just a list of strings. We'll try to get names.
        if isinstance(workflow.tags, list):
            processed_tags = []
            for tag_entry in workflow.tags:
                if isinstance(tag_entry, dict) and "name" in tag_entry:
                    processed_tags.append(tag_entry["name"])
                elif isinstance(tag_entry, str):
                    processed_tags.append(tag_entry)
        elif isinstance(workflow.tags, dict): # Less common for top-level tags, but handle
             processed_tags = list(workflow.tags.keys())


    # Extract specific fields from meta if they exist
    meta_info = {}
    if workflow.meta and isinstance(workflow.meta, dict):
        meta_info['instance_id'] = workflow.meta.get('instanceId')
        # Assuming 'user' might be nested as in some n8n exports
        user_meta = workflow.meta.get('user')
        if isinstance(user_meta, dict):
            meta_info['user_id'] = user_meta.get('id')
            meta_info['user_email'] = user_meta.get('email') # if available
            meta_info['user_name'] = user_meta.get('name')   # if available
        meta_info['createdAt'] = workflow.meta.get('createdAt')
        meta_info['updatedAt'] = workflow.meta.get('updatedAt')

    metadata = {
        "workflow_id": workflow.id,
        "name": workflow.name,
        "is_active": workflow.active,
        "file_path": workflow.file_path,
        "tags": processed_tags if processed_tags is not None else [], # Ensure it's a list
        "settings": workflow.settings if workflow.settings is not None else {},
        "meta": meta_info if meta_info else {}, # Return extracted fields or empty
        "static_data_keys": list(workflow.staticData.keys()) if workflow.staticData else []
        # Add node_count and connection_count for convenience, though they are metrics
        # "node_count": len(workflow.nodes),
        # "connection_count": len(workflow.connections)
    }

    return metadata

def extract_basic_metadata(workflow: N8nWorkflow) -> Dict[str, Any]:
    """Extract basic metadata from a workflow."""
    return {
        'name': workflow.name,
        'id': workflow.id,
        'active': workflow.active,
        'node_count': len(workflow.nodes),
        'connection_count': len(workflow.connections),
        'has_tags': bool(workflow.tags),
        'tag_count': len(workflow.tags) if workflow.tags else 0,
        'has_settings': bool(workflow.settings),
        'has_meta': bool(workflow.meta),
        'has_static_data': bool(workflow.staticData),
        'file_path': workflow.file_path
    }

def extract_node_types_summary(workflow: N8nWorkflow) -> Dict[str, int]:
    """Extract summary of node types in the workflow."""
    node_types = {}
    for node in workflow.nodes:
        node_types[node.type] = node_types.get(node.type, 0) + 1
    return node_types

def extract_workflow_tags_and_settings(workflow: N8nWorkflow) -> Dict[str, Any]:
    """Extract detailed tags and settings information."""
    return {
        'tags': workflow.tags if workflow.tags else {},
        'settings': workflow.settings if workflow.settings else {},
        'meta': workflow.meta if workflow.meta else {},
        'staticData': workflow.staticData if workflow.staticData else {}
    }

def count_nodes_with_parameters(workflow: N8nWorkflow) -> Dict[str, int]:
    """Count nodes that have various parameter configurations."""
    nodes_with_params = 0
    nodes_without_params = 0
    total_param_keys = 0
    
    for node in workflow.nodes:
        if node.parameters:
            nodes_with_params += 1
            total_param_keys += len(node.parameters)
        else:
            nodes_without_params += 1
    
    return {
        'nodes_with_parameters': nodes_with_params,
        'nodes_without_parameters': nodes_without_params,
        'total_parameter_keys': total_param_keys,
        'avg_parameters_per_node': total_param_keys / len(workflow.nodes) if workflow.nodes else 0
    }


# === ENHANCED VALIDATION AND QUALITY ASSESSMENT FOR PHASE 2 ===

class WorkflowValidationResult:
    """Container for workflow validation results."""
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.quality_score = 100.0
        self.metadata: Dict[str, Any] = {}
    
    def add_error(self, message: str):
        """Add a validation error."""
        self.errors.append(message)
        self.is_valid = False
        self.quality_score -= 20  # Errors are serious
    
    def add_warning(self, message: str):
        """Add a validation warning."""
        self.warnings.append(message)
        self.quality_score -= 5  # Warnings are less serious
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results."""
        return {
            'is_valid': self.is_valid,
            'quality_score': max(0, self.quality_score),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata
        }

def validate_workflow_structure(workflow: N8nWorkflow) -> WorkflowValidationResult:
    """
    Comprehensive workflow structure validation.
    
    Returns:
        WorkflowValidationResult with validation details
    """
    result = WorkflowValidationResult()
    
    # Basic structure validation
    if not workflow.name or not workflow.name.strip():
        result.add_error("Workflow has no name or empty name")
    
    if not workflow.nodes:
        result.add_error("Workflow has no nodes")
        return result  # Can't continue without nodes
    
    # Node validation
    node_ids = set()
    for node in workflow.nodes:
        # Check for duplicate node IDs
        if node.id in node_ids:
            result.add_error(f"Duplicate node ID found: {node.id}")
        node_ids.add(node.id)
        
        # Check node structure
        if not node.name or not node.name.strip():
            result.add_warning(f"Node {node.id} has no name")
        
        if not node.type:
            result.add_error(f"Node {node.id} has no type")
        
        # Check position (basic coordinate validation)
        if node.position is None or len(node.position) != 2:
            result.add_warning(f"Node {node.id} has invalid position")
    
    # Connection validation
    if workflow.connections:
        for conn in workflow.connections:
            # Check if source and target nodes exist
            if conn.source_node_id not in node_ids:
                result.add_error(f"Connection references non-existent source node: {conn.source_node_id}")
            
            if conn.target_node_id not in node_ids:
                result.add_error(f"Connection references non-existent target node: {conn.target_node_id}")
    
    # Workflow topology validation
    trigger_nodes = identify_trigger_nodes(workflow)
    terminal_nodes = identify_potential_terminal_nodes(workflow)
    
    if not trigger_nodes:
        result.add_warning("Workflow has no identifiable trigger nodes")
    
    if not terminal_nodes:
        result.add_warning("Workflow has no terminal nodes")
    
    # Check for isolated nodes
    connected_node_ids = set()
    for conn in workflow.connections:
        connected_node_ids.add(conn.source_node_id)
        connected_node_ids.add(conn.target_node_id)
    
    isolated_nodes = node_ids - connected_node_ids
    if isolated_nodes and len(workflow.nodes) > 1:
        result.add_warning(f"Found {len(isolated_nodes)} isolated nodes: {list(isolated_nodes)}")
    
    # Store metadata for further analysis
    result.metadata = {
        'node_count': len(workflow.nodes),
        'connection_count': len(workflow.connections),
        'trigger_count': len(trigger_nodes),
        'terminal_count': len(terminal_nodes),
        'isolated_count': len(isolated_nodes)
    }
    
    return result

def assess_workflow_quality(workflow: N8nWorkflow) -> Dict[str, Any]:
    """
    Comprehensive quality assessment of a workflow.
    
    Returns:
        Dict containing quality metrics and recommendations
    """
    # Start with structure validation
    validation_result = validate_workflow_structure(workflow)
    
    # Additional quality metrics
    quality_metrics = {
        'structure_validation': validation_result.get_summary(),
        'complexity_assessment': {},
        'maintainability_score': 100.0,
        'best_practices_score': 100.0,
        'recommendations': []
    }
    
    # Complexity assessment
    node_count = len(workflow.nodes)
    connection_count = len(workflow.connections)
    unique_node_types = len(set(node.type for node in workflow.nodes))
    
    complexity_score = 'low'
    if node_count > 20 or connection_count > 30:
        complexity_score = 'high'
    elif node_count > 10 or connection_count > 15:
        complexity_score = 'medium'
    
    quality_metrics['complexity_assessment'] = {
        'complexity_level': complexity_score,
        'node_count': node_count,
        'connection_count': connection_count,
        'unique_node_types': unique_node_types,
        'avg_connections_per_node': connection_count / node_count if node_count > 0 else 0
    }
    
    # Maintainability assessment
    # Check for node naming conventions
    unnamed_nodes = sum(1 for node in workflow.nodes if not node.name or node.name.strip() == '')
    if unnamed_nodes > 0:
        quality_metrics['maintainability_score'] -= unnamed_nodes * 5
        quality_metrics['recommendations'].append(f"Consider naming {unnamed_nodes} unnamed nodes for better maintainability")
    
    # Check for documentation (notes)
    undocumented_nodes = sum(1 for node in workflow.nodes if not node.notes)
    if undocumented_nodes > node_count * 0.7:  # More than 70% undocumented
        quality_metrics['maintainability_score'] -= 10
        quality_metrics['recommendations'].append("Consider adding notes to more nodes for documentation")
    
    # Best practices assessment
    if not workflow.active and 'test' not in workflow.name.lower():
        quality_metrics['recommendations'].append("Workflow is inactive - consider activating if ready for production")
    
    # Check for excessive complexity
    if complexity_score == 'high':
        quality_metrics['recommendations'].append("Consider breaking down this complex workflow into smaller, manageable parts")
    
    # Parameter usage assessment
    nodes_with_params = sum(1 for node in workflow.nodes if node.parameters)
    if nodes_with_params == 0:
        quality_metrics['best_practices_score'] -= 15
        quality_metrics['recommendations'].append("No nodes have parameters configured - ensure proper configuration")
    
    # Final quality score calculation
    final_score = min(
        validation_result.quality_score,
        quality_metrics['maintainability_score'],
        quality_metrics['best_practices_score']
    )
    
    quality_metrics['overall_quality_score'] = max(0, final_score)
    
    return quality_metrics

def extract_workflow_signatures(workflow: N8nWorkflow) -> Dict[str, Any]:
    """
    Extract workflow signatures for pattern matching and similarity analysis.
    
    Returns:
        Dict containing various workflow signatures
    """
    # Node type signature (ordered by frequency)
    node_types = extract_node_types_summary(workflow)
    sorted_node_types = sorted(node_types.items(), key=lambda x: x[1], reverse=True)
    
    # Connection pattern signature
    connection_patterns = []
    for conn in workflow.connections:
        source_node = workflow.get_node_by_id(conn.source_node_id)
        target_node = workflow.get_node_by_id(conn.target_node_id)
        if source_node and target_node:
            connection_patterns.append((source_node.type, target_node.type))
    
    # Parameter usage signature
    parameter_keys = set()
    for node in workflow.nodes:
        if node.parameters:
            parameter_keys.update(node.parameters.keys())
    
    return {
        'node_type_signature': sorted_node_types,
        'connection_pattern_signature': connection_patterns,
        'parameter_signature': sorted(list(parameter_keys)),
        'structural_signature': {
            'node_count': len(workflow.nodes),
            'connection_count': len(workflow.connections),
            'density': len(workflow.connections) / (len(workflow.nodes) * (len(workflow.nodes) - 1)) if len(workflow.nodes) > 1 else 0
        }
    }

def compare_workflow_similarity(workflow1: N8nWorkflow, workflow2: N8nWorkflow) -> Dict[str, float]:
    """
    Compare similarity between two workflows based on various metrics.
    
    Returns:
        Dict containing similarity scores (0.0 to 1.0)
    """
    sig1 = extract_workflow_signatures(workflow1)
    sig2 = extract_workflow_signatures(workflow2)
    
    # Node type similarity (Jaccard similarity)
    types1 = set(node_type for node_type, _ in sig1['node_type_signature'])
    types2 = set(node_type for node_type, _ in sig2['node_type_signature'])
    node_type_similarity = len(types1 & types2) / len(types1 | types2) if types1 | types2 else 0.0
    
    # Parameter similarity
    params1 = set(sig1['parameter_signature'])
    params2 = set(sig2['parameter_signature'])
    parameter_similarity = len(params1 & params2) / len(params1 | params2) if params1 | params2 else 0.0
    
    # Structural similarity (based on size and density)
    struct1 = sig1['structural_signature']
    struct2 = sig2['structural_signature']
    
    # Normalize size difference (smaller value = more similar)
    size_diff = abs(struct1['node_count'] - struct2['node_count']) / max(struct1['node_count'], struct2['node_count']) if max(struct1['node_count'], struct2['node_count']) > 0 else 0
    size_similarity = 1.0 - size_diff
    
    # Density similarity
    density_diff = abs(struct1['density'] - struct2['density'])
    density_similarity = 1.0 - density_diff
    
    # Overall similarity (weighted average)
    overall_similarity = (
        node_type_similarity * 0.4 +
        parameter_similarity * 0.3 +
        size_similarity * 0.2 +
        density_similarity * 0.1
    )
    
    return {
        'node_type_similarity': node_type_similarity,
        'parameter_similarity': parameter_similarity,
        'size_similarity': size_similarity,
        'density_similarity': density_similarity,
        'overall_similarity': overall_similarity
    }
