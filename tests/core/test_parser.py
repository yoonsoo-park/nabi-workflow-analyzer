import unittest
import tempfile
import os
import ujson
from typing import List
from unittest.mock import patch, mock_open

from n8n_analyzer.core.parser import (
    parse_single_workflow, 
    parse_workflows_batch,
    WorkflowParseError,
    _parse_nodes,
    _parse_connections
)
from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection


class TestWorkflowParser(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures with sample n8n workflow data."""
        self.sample_workflow_data = {
            "name": "Test Workflow",
            "id": "workflow_123",
            "active": True,
            "nodes": [
                {
                    "id": "start_node",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [100, 100],
                    "parameters": {}
                },
                {
                    "id": "set_node",
                    "name": "Set Data",
                    "type": "n8n-nodes-base.set",
                    "typeVersion": 2,
                    "position": [300, 100],
                    "parameters": {
                        "values": {
                            "string": [{"name": "city", "value": "New York"}]
                        }
                    }
                }
            ],
            "connections": {
                "start_node": {
                    "main": [
                        [{"node": "set_node", "type": "main", "index": 0}]
                    ]
                }
            },
            "settings": {"errorWorkflow": "error_handler"},
            "tags": {"tag1": "value1"},
            "meta": {"version": "1.0"},
            "staticData": {"data": "test"}
        }
        
        self.minimal_workflow_data = {
            "name": "Minimal Workflow",
            "nodes": [],
            "connections": {}
        }

    def test_parse_single_workflow_success(self):
        """Test successful parsing of a complete workflow."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            ujson.dump(self.sample_workflow_data, f)
            temp_path = f.name
        
        try:
            workflow = parse_single_workflow(temp_path)
            
            # Verify workflow metadata
            self.assertEqual(workflow.name, "Test Workflow")
            self.assertEqual(workflow.id, "workflow_123")
            self.assertTrue(workflow.active)
            self.assertEqual(workflow.file_path, temp_path)
            
            # Verify nodes
            self.assertEqual(len(workflow.nodes), 2)
            start_node = workflow.get_node_by_id("start_node")
            self.assertIsNotNone(start_node)
            self.assertEqual(start_node.name, "Start")
            self.assertEqual(start_node.type, "n8n-nodes-base.start")
            
            # Verify connections
            self.assertEqual(len(workflow.connections), 1)
            conn = workflow.connections[0]
            self.assertEqual(conn.source_node_id, "start_node")
            self.assertEqual(conn.target_node_id, "set_node")
            
        finally:
            os.unlink(temp_path)

    def test_parse_single_workflow_minimal(self):
        """Test parsing of minimal workflow with only required fields."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            ujson.dump(self.minimal_workflow_data, f)
            temp_path = f.name
        
        try:
            workflow = parse_single_workflow(temp_path)
            
            self.assertEqual(workflow.name, "Minimal Workflow")
            self.assertEqual(len(workflow.nodes), 0)
            self.assertEqual(len(workflow.connections), 0)
            self.assertEqual(workflow.file_path, temp_path)
            
        finally:
            os.unlink(temp_path)

    def test_parse_single_workflow_file_not_found(self):
        """Test error handling for non-existent file."""
        with self.assertRaises(WorkflowParseError) as context:
            parse_single_workflow("non_existent_file.json")
        
        self.assertIn("File not found", str(context.exception))

    def test_parse_single_workflow_invalid_json(self):
        """Test error handling for malformed JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json content")
            temp_path = f.name
        
        try:
            with self.assertRaises(WorkflowParseError) as context:
                parse_single_workflow(temp_path)
            
            self.assertIn("Invalid JSON", str(context.exception))
            
        finally:
            os.unlink(temp_path)

    def test_parse_single_workflow_missing_required_fields(self):
        """Test error handling for workflow missing required fields."""
        invalid_data = {"nodes": [], "connections": {}}  # Missing 'name'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            ujson.dump(invalid_data, f)
            temp_path = f.name
        
        try:
            with self.assertRaises(WorkflowParseError) as context:
                parse_single_workflow(temp_path)
            
            self.assertIn("Missing required field", str(context.exception))
            
        finally:
            os.unlink(temp_path)

    def test_parse_workflows_batch_success(self):
        """Test batch processing of multiple workflow files."""
        # Create multiple temp files
        temp_files = []
        workflows_data = [
            {"name": "Workflow 1", "nodes": [], "connections": {}},
            {"name": "Workflow 2", "nodes": [], "connections": {}},
            {"name": "Workflow 3", "nodes": [], "connections": {}}
        ]
        
        try:
            for i, data in enumerate(workflows_data):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    ujson.dump(data, f)
                    temp_files.append(f.name)
            
            # Test generator behavior
            workflows = list(parse_workflows_batch(temp_files))
            
            self.assertEqual(len(workflows), 3)
            self.assertEqual(workflows[0].name, "Workflow 1")
            self.assertEqual(workflows[1].name, "Workflow 2")
            self.assertEqual(workflows[2].name, "Workflow 3")
            
        finally:
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    def test_parse_workflows_batch_with_errors(self):
        """Test batch processing continues after individual file errors."""
        temp_files = []
        try:
            # Create valid file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                ujson.dump({"name": "Valid Workflow", "nodes": [], "connections": {}}, f)
                temp_files.append(f.name)
            
            # Create invalid file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write("{ invalid json")
                temp_files.append(f.name)
            
            # Add non-existent file
            temp_files.append("non_existent.json")
            
            # Should yield only the valid workflow, skip errors
            workflows = list(parse_workflows_batch(temp_files, skip_errors=True))
            
            self.assertEqual(len(workflows), 1)
            self.assertEqual(workflows[0].name, "Valid Workflow")
            
        finally:
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    def test_parse_workflows_batch_memory_efficiency(self):
        """Test that batch parsing uses generators and doesn't load all files at once."""
        # This test verifies generator behavior by checking it yields one at a time
        temp_files = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    ujson.dump({"name": f"Workflow {i}", "nodes": [], "connections": {}}, f)
                    temp_files.append(f.name)
            
            generator = parse_workflows_batch(temp_files)
            
            # Verify it's a generator
            self.assertTrue(hasattr(generator, '__next__'))
            
            # Verify lazy evaluation - first call to next() should work
            first_workflow = next(generator)
            self.assertIsInstance(first_workflow, N8nWorkflow)
            
        finally:
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    def test_parse_nodes_success(self):
        """Test node parsing helper function."""
        nodes_data = self.sample_workflow_data["nodes"]
        nodes = _parse_nodes(nodes_data)
        
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].id, "start_node")
        self.assertEqual(nodes[0].name, "Start")
        self.assertEqual(nodes[1].parameters["values"]["string"][0]["name"], "city")

    def test_parse_connections_success(self):
        """Test connection parsing helper function."""
        connections_data = self.sample_workflow_data["connections"]
        connections = _parse_connections(connections_data)
        
        self.assertEqual(len(connections), 1)
        conn = connections[0]
        self.assertEqual(conn.source_node_id, "start_node")
        self.assertEqual(conn.source_node_output_port, "main")
        self.assertEqual(conn.target_node_id, "set_node")
        self.assertEqual(conn.target_node_input_port, "main")

    def test_parse_connections_empty(self):
        """Test connection parsing with empty connections."""
        connections = _parse_connections({})
        self.assertEqual(len(connections), 0)


if __name__ == '__main__':
    unittest.main()
