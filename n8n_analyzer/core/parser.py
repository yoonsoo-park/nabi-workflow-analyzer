# n8n_analyzer/core/parser.py
import os
import json
import logging
from typing import Iterator, Optional, Dict, Any # Added Dict, Any

# Import the actual N8nWorkflow model
from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection # Added N8nNode, N8nConnection

logger = logging.getLogger(__name__)

def _parse_single_workflow_data(workflow_data: Dict[str, Any], file_path: str) -> Optional[N8nWorkflow]:
    """
    (Placeholder) Parses a dictionary representing a single workflow's JSON data
    into an N8nWorkflow object.
    This is a simplified placeholder. Real implementation will need robust error handling
    and detailed parsing of nodes and connections.
    """
    try:
        # Basic structure validation (very minimal)
        if not all(k in workflow_data for k in ['name', 'nodes', 'connections']):
            logger.warning(f"Missing essential keys in workflow data from {file_path}")
            return None

        # Placeholder node parsing
        parsed_nodes = []
        raw_nodes = workflow_data.get('nodes', [])
        for node_data in raw_nodes:
            if not isinstance(node_data, dict) or not all(k in node_data for k in ['id', 'name', 'type', 'typeVersion', 'position']):
                logger.warning(f"Skipping malformed node data in {file_path}: {node_data}")
                continue
            parsed_nodes.append(N8nNode(
                id=node_data['id'],
                name=node_data['name'],
                type=node_data['type'],
                typeVersion=node_data['typeVersion'],
                position=(node_data['position'][0], node_data['position'][1]) if isinstance(node_data.get('position'), list) and len(node_data['position']) == 2 else (0,0), # Simplified
                parameters=node_data.get('parameters', {})
            ))

        # Placeholder connection parsing
        # n8n connections are stored as a dictionary where keys are source node IDs
        # and values are dictionaries of output ports, which then list target inputs.
        # Example: "connections": { "Start_node_id": { "main": [ [ { "node": "Target_node_id", "type": "main" } ] ] } }
        parsed_connections = []
        raw_connections = workflow_data.get('connections', {})
        if isinstance(raw_connections, dict):
            for source_node_id, outputs in raw_connections.items():
                if isinstance(outputs, dict):
                    for source_port, targets_list in outputs.items():
                        if isinstance(targets_list, list):
                            for target_array in targets_list: # This is usually an array with one item
                                if isinstance(target_array, list) and len(target_array) > 0:
                                    target_info = target_array[0]
                                    if isinstance(target_info, dict) and 'node' in target_info and 'type' in target_info:
                                        parsed_connections.append(N8nConnection(
                                            source_node_id=source_node_id,
                                            source_node_output_port=source_port,
                                            target_node_id=target_info['node'],
                                            target_node_input_port=target_info['type']
                                        ))
                                    else:
                                        logger.warning(f"Malformed target_info in connection for {source_node_id} in {file_path}: {target_info}")
                        else:
                             logger.warning(f"Malformed targets_list for {source_node_id} output {source_port} in {file_path}")
                else:
                    logger.warning(f"Malformed outputs structure for source node {source_node_id} in {file_path}")
        else:
            logger.warning(f"Connections data is not a dictionary in {file_path}")


        return N8nWorkflow(
            id=workflow_data.get('id'),
            name=workflow_data['name'],
            nodes=parsed_nodes,
            connections=parsed_connections,
            active=workflow_data.get('active', False),
            tags=workflow_data.get('tags', {}),
            settings=workflow_data.get('settings', {}),
            file_path=file_path
        )
    except Exception as e:
        logger.error(f"Error parsing workflow data from {file_path}: {e}", exc_info=True)
        return None


def stream_workflows_from_directory(directory_path: str) -> Iterator[Optional[N8nWorkflow]]:
    """
    (Placeholder) Scans a directory for .json files, attempts to parse each into
    an N8nWorkflow object, and yields them.

    This is a simplified placeholder. Real implementation will need:
    - Memory efficiency for large numbers of files (yield is good).
    - Robust error handling for malformed JSON or files not matching n8n structure.
    - Potentially, filtering for n8n-specific JSON structures if other JSONs exist.
    """
    logger.info(f"Streaming workflows from directory: {directory_path}")
    if not os.path.isdir(directory_path):
        logger.error(f"Provided path is not a directory: {directory_path}")
        return

    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            logger.debug(f"Attempting to parse file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # For true streaming and memory efficiency with huge files,
                    # one might consider ijson or similar, but for typical n8n JSONs,
                    # json.load() is often acceptable per file. The generator pattern
                    # here ensures we don't load all files into memory at once.
                    data = json.load(f)

                # Basic check if it's an n8n workflow (very simplistic)
                # Actual n8n files are arrays of objects if multiple workflows are in one file (usually not for individual .json exports)
                # or a single object if it's one workflow.
                # The provided samples are single objects.
                if isinstance(data, dict) and 'nodes' in data and 'connections' in data:
                     yield _parse_single_workflow_data(data, file_path)
                elif isinstance(data, list) and data and isinstance(data[0], dict) and 'nodes' in data[0] and 'connections' in data[0]:
                    # Handle case where file might contain a list of workflows
                    logger.info(f"File {file_path} contains a list of workflows. Processing first one for now.") # Placeholder behavior
                    yield _parse_single_workflow_data(data[0], file_path) # Process only the first one as a simplification
                else:
                    logger.warning(f"File {file_path} does not appear to be a standard n8n workflow JSON structure. Skipping.")
                    yield None


            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in file: {file_path}. Skipping.")
                yield None # Yield None for parsing failures to allow batch processor to count
            except Exception as e:
                logger.error(f"Unexpected error reading or parsing file {file_path}: {e}", exc_info=True)
                yield None
        else:
            logger.debug(f"Skipping non-JSON file: {filename}")
