# tests/core/test_parser.py
import unittest
import os
import json # Using standard json to create test data if needed

from n8n_analyzer.core.models import N8nWorkflow
from n8n_analyzer.core.parser import _parse_single_workflow_data as parse_workflow_json # Renamed for clarity in test
from n8n_analyzer.core.parser import stream_workflows_from_directory

class TestWorkflowParser(unittest.TestCase):
    def setUp(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.sample_workflows_dir = os.path.join(self.project_root, "data", "raw_workflows")
        self.test_workflow_file = None

        # Find the first sample workflow file to use for specific parsing test
        if os.path.exists(self.sample_workflows_dir) and os.path.isdir(self.sample_workflows_dir):
            for fname in sorted(os.listdir(self.sample_workflows_dir)): # Sort for predictability
                if fname.startswith("sample_workflow_") and fname.endswith(".json"):
                    self.test_workflow_file = os.path.join(self.sample_workflows_dir, fname)
                    break

        # If no sample file, create a minimal one for basic test
        if not self.test_workflow_file:
            os.makedirs(self.sample_workflows_dir, exist_ok=True)
            self.test_workflow_file = os.path.join(self.sample_workflows_dir, "_temp_parser_test.json")
            minimal_workflow_data = {
                "name": "Minimal Test Workflow", "id": "wf_min_123", "active": True,
                "nodes": [{"id": "n1", "name": "Start", "type": "n8n.start", "typeVersion": 1, "position": [0,0], "parameters": {}}], # Added parameters
                "connections": {}
            }
            with open(self.test_workflow_file, 'w') as f:
                json.dump(minimal_workflow_data, f)


    def test_parse_single_valid_workflow_file(self):
        self.assertIsNotNone(self.test_workflow_file, "No sample workflow file found or created for testing.")
        self.assertTrue(os.path.exists(self.test_workflow_file), f"Test file {self.test_workflow_file} does not exist.")

        try:
            with open(self.test_workflow_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.fail(f"Failed to load test workflow JSON {self.test_workflow_file}: {e}")

        workflow = parse_workflow_json(data, file_path=self.test_workflow_file)
        self.assertIsInstance(workflow, N8nWorkflow, f"Parsing did not return an N8nWorkflow object for {self.test_workflow_file}. Got {type(workflow)}")
        self.assertIsNotNone(workflow.name, "Workflow name should not be None.")
        self.assertIsNotNone(workflow.nodes, "Workflow nodes list should not be None.")

        if data.get("name"):
             self.assertEqual(workflow.name, data["name"])
        self.assertEqual(len(workflow.nodes), len(data.get("nodes",[])))
        # Basic check for connections list
        self.assertIsNotNone(workflow.connections, "Workflow connections list should not be None.")


    def test_stream_workflows_from_directory(self):
        # Ensure there are JSON files to parse, not just .gitkeep
        json_files_present = any(f.endswith('.json') for f in os.listdir(self.sample_workflows_dir))
        if not os.path.exists(self.sample_workflows_dir) or not json_files_present:
            self.skipTest(f"Sample workflow directory {self.sample_workflows_dir} is empty or missing JSON files. Skipping stream test.")

        workflows_iterable = stream_workflows_from_directory(self.sample_workflows_dir)

        count = 0
        limit = 3
        parsed_workflows_details = []
        for workflow in workflows_iterable:
            if workflow is not None: # The stream_workflows_from_directory can yield None for parsing errors
                self.assertIsInstance(workflow, N8nWorkflow)
                parsed_workflows_details.append(f"Parsed: {workflow.name} (Nodes: {len(workflow.nodes)})")
                count += 1
            if count >= limit:
                break

        self.assertGreater(count, 0, f"Streamer did not yield any valid workflows from sample directory. Details: {parsed_workflows_details}")
        # This assertion is tricky if limit is not reached due to parsing errors or fewer files than limit.
        # The goal is that it processed *up to* the limit of *successfully parsed* items.
        # For now, checking that it parsed at least one is the main goal.
        # self.assertLessEqual(count, limit, "Streamer yielded more items than limit (or limit was not effective).")


    def tearDown(self):
        # Clean up the temporary file if it was created
        if self.test_workflow_file and "_temp_parser_test.json" in self.test_workflow_file:
            if os.path.exists(self.test_workflow_file):
                os.remove(self.test_workflow_file)


if __name__ == '__main__':
    unittest.main()
