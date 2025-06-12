# tests/analysis/test_error_analyzer.py
import unittest
from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection
from n8n_analyzer.analysis.error_analyzer import (
    has_error_trigger_node,
    get_workflow_error_setting,
    count_connections_to_error_trigger,
    analyze_error_handling,
    ERROR_TRIGGER_NODE_TYPE
)

class TestErrorAnalyzer(unittest.TestCase):
    def setUp(self):
        self.node_start = N8nNode(id="start1", name="Start", type="n8n-nodes-base.start", typeVersion=1, position=(0,0), parameters={})
        self.node_set1 = N8nNode(id="set1", name="Set A", type="n8n-nodes-base.set", typeVersion=1, position=(0,0), parameters={})
        self.node_err_trigger = N8nNode(id="err_trig1", name="Error Trigger", type=ERROR_TRIGGER_NODE_TYPE, typeVersion=1, position=(0,0), parameters={})
        self.node_connect_to_err = N8nNode(id="connect_to_err", name="Connect To Err", type="n8n-nodes-base.function", typeVersion=1, position=(0,0), parameters={})


        self.workflow_no_error_handling = N8nWorkflow(
            name="No Error Handling",
            nodes=[self.node_start, self.node_set1],
            connections=[N8nConnection("start1", "main", "set1", "main")]
        )

        self.workflow_with_error_trigger = N8nWorkflow(
            name="With Error Trigger",
            nodes=[self.node_start, self.node_set1, self.node_err_trigger],
            connections=[N8nConnection("start1", "main", "set1", "main")]
            # Error trigger is present but not connected to anything in this simple case
        )

        self.workflow_with_error_workflow_setting = N8nWorkflow(
            name="With Error Workflow Setting",
            nodes=[self.node_start, self.node_set1],
            connections=[N8nConnection("start1", "main", "set1", "main")],
            settings={"errorWorkflow": "error_workflow_123"}
        )

        self.workflow_with_connection_to_error_trigger = N8nWorkflow(
            name="Connection to Error Trigger",
            nodes=[self.node_start, self.node_connect_to_err, self.node_err_trigger],
            connections=[
                N8nConnection("start1", "main", "connect_to_err", "main"),
                N8nConnection("connect_to_err", "main", "err_trig1", "main")
            ]
        )


    def test_has_error_trigger_node(self):
        self.assertFalse(has_error_trigger_node(self.workflow_no_error_handling))
        self.assertTrue(has_error_trigger_node(self.workflow_with_error_trigger))

    def test_get_workflow_error_setting(self):
        self.assertIsNone(get_workflow_error_setting(self.workflow_no_error_handling))
        self.assertIsNone(get_workflow_error_setting(self.workflow_with_error_trigger)) # No settings dict

        workflow_empty_settings = N8nWorkflow(name="Empty Settings", nodes=[], connections=[], settings={})
        self.assertIsNone(get_workflow_error_setting(workflow_empty_settings))

        self.assertEqual(get_workflow_error_setting(self.workflow_with_error_workflow_setting), "error_workflow_123")

    def test_count_connections_to_error_trigger(self):
        self.assertEqual(count_connections_to_error_trigger(self.workflow_no_error_handling), 0)
        self.assertEqual(count_connections_to_error_trigger(self.workflow_with_error_trigger), 0)
        self.assertEqual(count_connections_to_error_trigger(self.workflow_with_connection_to_error_trigger), 1)

        # Add another connection to the same error trigger
        workflow_multi_conn_to_err = N8nWorkflow(
            name="Multi Connection to Error Trigger",
            nodes=[self.node_start, self.node_connect_to_err, self.node_err_trigger, self.node_set1],
            connections=[
                N8nConnection("start1", "main", "connect_to_err", "main"),
                N8nConnection("connect_to_err", "main", "err_trig1", "main"),
                N8nConnection("set1", "main", "err_trig1", "main") # Second connection to err_trig1
            ]
        )
        self.assertEqual(count_connections_to_error_trigger(workflow_multi_conn_to_err), 2)


    def test_analyze_error_handling(self):
        analysis1 = analyze_error_handling(self.workflow_no_error_handling)
        self.assertEqual(analysis1, {
            "has_error_trigger": False,
            "designated_error_workflow_id": None,
            "connections_to_error_trigger_nodes": 0
        })

        analysis2 = analyze_error_handling(self.workflow_with_error_trigger)
        self.assertEqual(analysis2, {
            "has_error_trigger": True,
            "designated_error_workflow_id": None,
            "connections_to_error_trigger_nodes": 0
        })

        analysis3 = analyze_error_handling(self.workflow_with_error_workflow_setting)
        self.assertEqual(analysis3, {
            "has_error_trigger": False,
            "designated_error_workflow_id": "error_workflow_123",
            "connections_to_error_trigger_nodes": 0
        })

        analysis4 = analyze_error_handling(self.workflow_with_connection_to_error_trigger)
        self.assertEqual(analysis4, {
            "has_error_trigger": True, # Error trigger is present
            "designated_error_workflow_id": None,
            "connections_to_error_trigger_nodes": 1
        })

if __name__ == '__main__':
    unittest.main()
