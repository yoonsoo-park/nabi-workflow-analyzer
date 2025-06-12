import os
import ujson
import logging
from typing import List, Dict, Any, Generator, Optional, Tuple
from pathlib import Path

from .models import N8nWorkflow, N8nNode, N8nConnection


# Configure logging for parser
logger = logging.getLogger(__name__)


class WorkflowParseError(Exception):
    """Custom exception for workflow parsing errors."""
    def __init__(self, message: str, file_path: Optional[str] = None, original_error: Optional[Exception] = None):
        self.file_path = file_path
        self.original_error = original_error
        
        error_msg = f"Workflow parsing error"
        if file_path:
            error_msg += f" in file '{file_path}'"
        error_msg += f": {message}"
        if original_error:
            error_msg += f" (Original error: {str(original_error)})"
        
        super().__init__(error_msg)


def parse_single_workflow(file_path: str) -> N8nWorkflow:
    """
    Parse a single n8n workflow JSON file into an N8nWorkflow object.
    
    Args:
        file_path: Path to the JSON workflow file
        
    Returns:
        N8nWorkflow: Parsed workflow object
        
    Raises:
        WorkflowParseError: If file cannot be read or parsed
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise WorkflowParseError("File not found", file_path)
        
        # Read and parse JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = ujson.load(f)
            except ujson.JSONDecodeError as e:
                raise WorkflowParseError("Invalid JSON format", file_path, e)
        
        # Validate required fields
        if not isinstance(data, dict):
            raise WorkflowParseError("JSON root must be an object", file_path)
        
        if 'name' not in data:
            raise WorkflowParseError("Missing required field 'name'", file_path)
        
        if 'nodes' not in data:
            raise WorkflowParseError("Missing required field 'nodes'", file_path)
        
        if 'connections' not in data:
            raise WorkflowParseError("Missing required field 'connections'", file_path)
        
        # Parse nodes and connections
        try:
            nodes = _parse_nodes(data['nodes'])
            connections = _parse_connections(data['connections'])
        except Exception as e:
            raise WorkflowParseError("Error parsing workflow structure", file_path, e)
        
        # Create workflow object
        workflow = N8nWorkflow(
            name=data['name'],
            nodes=nodes,
            connections=connections,
            id=data.get('id'),
            active=data.get('active'),
            tags=data.get('tags', {}),
            settings=data.get('settings', {}),
            meta=data.get('meta', {}),
            staticData=data.get('staticData', {}),
            file_path=file_path
        )
        
        logger.debug(f"Successfully parsed workflow '{workflow.name}' from {file_path}")
        return workflow
        
    except WorkflowParseError:
        raise
    except Exception as e:
        raise WorkflowParseError("Unexpected error during parsing", file_path, e)


def parse_workflows_batch(
    file_paths: List[str], 
    skip_errors: bool = False
) -> Generator[N8nWorkflow, None, None]:
    """
    Memory-efficient batch parsing of multiple workflow files using generators.
    
    Args:
        file_paths: List of paths to JSON workflow files
        skip_errors: If True, skip files that can't be parsed; if False, raise on first error
        
    Yields:
        N8nWorkflow: Parsed workflow objects one at a time
        
    Raises:
        WorkflowParseError: If skip_errors=False and any file fails to parse
    """
    for file_path in file_paths:
        try:
            workflow = parse_single_workflow(file_path)
            yield workflow
            
        except WorkflowParseError as e:
            if skip_errors:
                logger.warning(f"Skipping file due to parse error: {e}")
                continue
            else:
                raise
        except Exception as e:
            error = WorkflowParseError("Unexpected error during batch parsing", file_path, e)
            if skip_errors:
                logger.warning(f"Skipping file due to unexpected error: {error}")
                continue
            else:
                raise error


def _parse_nodes(nodes_data: List[Dict[str, Any]]) -> List[N8nNode]:
    """
    Parse node data from JSON into N8nNode objects.
    
    Args:
        nodes_data: List of node dictionaries from JSON
        
    Returns:
        List[N8nNode]: List of parsed node objects
        
    Raises:
        ValueError: If node data is invalid
    """
    nodes = []
    
    for node_data in nodes_data:
        try:
            # Validate required fields
            required_fields = ['id', 'name', 'type', 'typeVersion', 'position']
            for field in required_fields:
                if field not in node_data:
                    raise ValueError(f"Node missing required field '{field}': {node_data}")
            
            # Parse position - handle both list and tuple formats
            position = node_data['position']
            if isinstance(position, (list, tuple)) and len(position) >= 2:
                position_tuple = (int(position[0]), int(position[1]))
            else:
                raise ValueError(f"Invalid position format: {position}")
            
            # Create node object
            node = N8nNode(
                id=node_data['id'],
                name=node_data['name'],
                type=node_data['type'],
                typeVersion=int(node_data['typeVersion']),
                position=position_tuple,
                parameters=node_data.get('parameters', {}),
                notes=node_data.get('notes')
            )
            
            nodes.append(node)
            
        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"Error parsing node {node_data.get('id', 'unknown')}: {str(e)}")
    
    return nodes


def _parse_connections(connections_data: Dict[str, Any]) -> List[N8nConnection]:
    """
    Parse connection data from JSON into N8nConnection objects.
    
    n8n connection format:
    {
        "source_node_id": {
            "output_port": [
                [{"node": "target_node_id", "type": "main", "index": 0}]
            ]
        }
    }
    
    Args:
        connections_data: Dictionary of connection data from JSON
        
    Returns:
        List[N8nConnection]: List of parsed connection objects
        
    Raises:
        ValueError: If connection data is invalid
    """
    connections = []
    
    for source_node_id, source_outputs in connections_data.items():
        if not isinstance(source_outputs, dict):
            continue
            
        for output_port, output_connections in source_outputs.items():
            if not isinstance(output_connections, list):
                continue
                
            # Handle nested list structure: output_connections is a list of lists
            for connection_group in output_connections:
                if not isinstance(connection_group, list):
                    continue
                    
                for connection_data in connection_group:
                    try:
                        if not isinstance(connection_data, dict):
                            continue
                            
                        target_node_id = connection_data.get('node')
                        connection_type = connection_data.get('type', 'main')
                        target_index = connection_data.get('index', 0)
                        
                        if not target_node_id:
                            logger.warning(f"Skipping connection with missing target node from {source_node_id}")
                            continue
                        
                        # Map target index to input port name
                        target_input_port = 'main' if target_index == 0 else str(target_index)
                        
                        connection = N8nConnection(
                            source_node_id=source_node_id,
                            source_node_output_port=output_port,
                            target_node_id=target_node_id,
                            target_node_input_port=target_input_port
                        )
                        
                        connections.append(connection)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing connection from {source_node_id}: {e}")
                        continue
    
    return connections


def find_workflow_files(directory: str, recursive: bool = True) -> List[str]:
    """
    Find all JSON workflow files in a directory.
    
    Args:
        directory: Directory path to search
        recursive: Whether to search subdirectories
        
    Returns:
        List[str]: List of JSON file paths
        
    Raises:
        ValueError: If directory doesn't exist
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise ValueError(f"Directory does not exist: {directory}")
    
    if not dir_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")
    
    # Find JSON files
    if recursive:
        json_files = list(dir_path.rglob("*.json"))
    else:
        json_files = list(dir_path.glob("*.json"))
    
    return [str(f) for f in json_files]


def get_workflow_stats(file_paths: List[str]) -> Dict[str, Any]:
    """
    Get basic statistics about a collection of workflow files without fully parsing them.
    Useful for large datasets where you want to get an overview first.
    
    Args:
        file_paths: List of workflow file paths
        
    Returns:
        Dict with statistics: total_files, readable_files, parse_errors, etc.
    """
    stats = {
        'total_files': len(file_paths),
        'readable_files': 0,
        'parse_errors': 0,
        'missing_files': 0,
        'invalid_json': 0,
        'missing_required_fields': 0,
        'total_nodes': 0,
        'total_connections': 0,
        'workflow_names': []
    }
    
    for file_path in file_paths:
        try:
            if not os.path.exists(file_path):
                stats['missing_files'] += 1
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = ujson.load(f)
                except ujson.JSONDecodeError:
                    stats['invalid_json'] += 1
                    continue
            
            # Check required fields
            if not all(field in data for field in ['name', 'nodes', 'connections']):
                stats['missing_required_fields'] += 1
                continue
            
            stats['readable_files'] += 1
            stats['total_nodes'] += len(data.get('nodes', []))
            stats['total_connections'] += sum(
                len(connections) for connections in data.get('connections', {}).values()
            )
            stats['workflow_names'].append(data['name'])
            
        except Exception:
            stats['parse_errors'] += 1
    
    return stats


# Example usage and testing
if __name__ == '__main__':
    # Example of how to use the parser
    
    # Test single workflow parsing
    sample_workflow = {
        "name": "Example Workflow",
        "id": "example_123",
        "active": True,
        "nodes": [
            {
                "id": "start",
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [100, 100],
                "parameters": {}
            }
        ],
        "connections": {}
    }
    
    # Save to temp file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        ujson.dump(sample_workflow, f)
        temp_path = f.name
    
    try:
        # Parse single workflow
        workflow = parse_single_workflow(temp_path)
        print(f"Parsed workflow: {workflow.name}")
        print(f"Number of nodes: {len(workflow.nodes)}")
        print(f"Number of connections: {len(workflow.connections)}")
        
        # Test batch parsing
        workflows = list(parse_workflows_batch([temp_path], skip_errors=True))
        print(f"Batch parsed {len(workflows)} workflows")
        
    finally:
        os.unlink(temp_path)
