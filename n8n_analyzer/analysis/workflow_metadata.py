# n8n_analyzer/analysis/workflow_metadata.py
from typing import Dict, Any, List, Optional
from n8n_analyzer.core.models import N8nWorkflow

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
