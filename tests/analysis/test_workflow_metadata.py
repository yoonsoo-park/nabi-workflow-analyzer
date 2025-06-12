# tests/analysis/test_workflow_metadata.py
import unittest
from n8n_analyzer.core.models import N8nWorkflow, N8nNode
from n8n_analyzer.analysis.workflow_metadata import extract_workflow_metadata

class TestWorkflowMetadataExtractor(unittest.TestCase):
    def test_extract_metadata_full(self):
        workflow = N8nWorkflow(
            id="wf123",
            name="Full Metadata Workflow",
            active=True,
            nodes=[N8nNode(id="n1", name="N", type="t", typeVersion=1, position=(0,0), parameters={})], # Needs at least one node for some logic
            connections=[],
            tags=[{"id": "tag_id_1", "name": "Urgent"}, {"name": "Finance"}], # Mix of structures
            settings={"errorWorkflow": "ewf_abc", "timezone": "Europe/Berlin"},
            meta={
                "instanceId": "instance_xyz",
                "user": {"id": "user_001", "email": "test@example.com", "name": "Test User"},
                "createdAt": "2023-01-01T00:00:00Z",
                "updatedAt": "2023-01-02T00:00:00Z"
            },
            staticData={"key1": "value1"},
            file_path="/path/to/workflow.json"
        )

        metadata = extract_workflow_metadata(workflow)

        self.assertEqual(metadata["workflow_id"], "wf123")
        self.assertEqual(metadata["name"], "Full Metadata Workflow")
        self.assertTrue(metadata["is_active"])
        self.assertEqual(metadata["file_path"], "/path/to/workflow.json")
        self.assertListEqual(sorted(metadata["tags"]), sorted(["Urgent", "Finance"]))
        self.assertEqual(metadata["settings"], {"errorWorkflow": "ewf_abc", "timezone": "Europe/Berlin"})

        expected_meta = {
            "instance_id": "instance_xyz",
            "user_id": "user_001",
            "user_email": "test@example.com",
            "user_name": "Test User",
            "createdAt": "2023-01-01T00:00:00Z",
            "updatedAt": "2023-01-02T00:00:00Z"
        }
        self.assertEqual(metadata["meta"], expected_meta)
        self.assertEqual(metadata["static_data_keys"], ["key1"])

    def test_extract_metadata_minimal_and_empty(self):
        workflow_minimal = N8nWorkflow(
            name="Minimal Workflow",
            nodes=[], # No nodes
            connections=[]
            # All optional fields (id, active, tags, settings, meta, staticData, file_path) are None/default
        )
        metadata_minimal = extract_workflow_metadata(workflow_minimal)

        self.assertIsNone(metadata_minimal["workflow_id"])
        self.assertEqual(metadata_minimal["name"], "Minimal Workflow")
        self.assertIsNone(metadata_minimal["is_active"])
        self.assertIsNone(metadata_minimal["file_path"])
        self.assertEqual(metadata_minimal["tags"], []) # Should default to empty list
        self.assertEqual(metadata_minimal["settings"], {}) # Should default to empty dict
        self.assertEqual(metadata_minimal["meta"], {}) # Should default to empty dict
        self.assertEqual(metadata_minimal["static_data_keys"], [])


    def test_extract_metadata_tags_various_formats(self):
        # Tags as list of strings
        workflow1 = N8nWorkflow(name="wf1", nodes=[], connections=[], tags=["simple_tag1", "simple_tag2"])
        meta1 = extract_workflow_metadata(workflow1)
        self.assertListEqual(sorted(meta1["tags"]), sorted(["simple_tag1", "simple_tag2"]))

        # Tags as list of mixed dicts (some with name, some without)
        workflow2 = N8nWorkflow(name="wf2", nodes=[], connections=[], tags=[{"name":"dict_tag1"}, {"id":"no_name_id"}])
        meta2 = extract_workflow_metadata(workflow2)
        self.assertListEqual(meta2["tags"], ["dict_tag1"]) # Only extracts named tags

        # Tags as a dictionary (less common, but handle)
        workflow3 = N8nWorkflow(name="wf3", nodes=[], connections=[], tags={"key_tag1": "val1", "key_tag2": "val2"})
        meta3 = extract_workflow_metadata(workflow3)
        self.assertListEqual(sorted(meta3["tags"]), sorted(["key_tag1", "key_tag2"]))

        # Tags as None
        workflow4 = N8nWorkflow(name="wf4", nodes=[], connections=[], tags=None)
        meta4 = extract_workflow_metadata(workflow4)
        self.assertListEqual(meta4["tags"], [])


if __name__ == '__main__':
    unittest.main()
