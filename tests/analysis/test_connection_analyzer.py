# tests/analysis/test_connection_analyzer.py
import unittest
from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection
from n8n_analyzer.analysis.connection_analyzer import (
    get_common_node_type_pairs,
    get_node_io_degree,
    get_all_node_io_degrees,
    identify_trigger_nodes,
    identify_potential_terminal_nodes,
    DEFAULT_TRIGGER_NODE_TYPES,
    DEFAULT_TERMINAL_NODE_TYPES
)

class TestConnectionAnalyzer(unittest.TestCase):
    def setUp(self):
        self.node_start = N8nNode(id="start1", name="Start", type="n8n-nodes-base.start", typeVersion=1, position=(0,0), parameters={})
        self.node_set1 = N8nNode(id="set1", name="Set A", type="n8n-nodes-base.set", typeVersion=1, position=(0,0), parameters={})
        self.node_set2 = N8nNode(id="set2", name="Set B", type="n8n-nodes-base.set", typeVersion=1, position=(0,0), parameters={})
        self.node_if1 = N8nNode(id="if1", name="If C", type="n8n-nodes-base.if", typeVersion=1, position=(0,0), parameters={})
        self.node_log1 = N8nNode(id="log1", name="Log D", type="n8n-nodes-base.logMessage", typeVersion=1, position=(0,0), parameters={})
        self.node_webhook = N8nNode(id="hook1", name="Webhook", type="n8n-nodes-base.webhook", typeVersion=1, position=(0,0), parameters={})
        self.node_dangling = N8nNode(id="dangle1", name="Dangling Func", type="n8n-nodes-base.function", typeVersion=1, position=(0,0), parameters={})


        self.conn_s1_s1 = N8nConnection(source_node_id="start1", source_node_output_port="main", target_node_id="set1", target_node_input_port="main")
        self.conn_s1_if1 = N8nConnection(source_node_id="set1", source_node_output_port="main", target_node_id="if1", target_node_input_port="main")
        self.conn_if1_s2 = N8nConnection(source_node_id="if1", source_node_output_port="true", target_node_id="set2", target_node_input_port="main")
        self.conn_if1_log1 = N8nConnection(source_node_id="if1", source_node_output_port="false", target_node_id="log1", target_node_input_port="main")
        self.conn_hook_s2 = N8nConnection(source_node_id="hook1", source_node_output_port="main", target_node_id="set2", target_node_input_port="main")


        self.workflow1 = N8nWorkflow(
            name="Workflow 1",
            nodes=[self.node_start, self.node_set1, self.node_set2, self.node_if1, self.node_log1, self.node_webhook, self.node_dangling],
            connections=[self.conn_s1_s1, self.conn_s1_if1, self.conn_if1_s2, self.conn_if1_log1, self.conn_hook_s2]
        )

        self.empty_workflow = N8nWorkflow(name="Empty", nodes=[], connections=[])

    def test_get_common_node_type_pairs(self):
        pairs = get_common_node_type_pairs(self.workflow1)
        expected_pairs = {
            ("n8n-nodes-base.start", "n8n-nodes-base.set"): 1,
            ("n8n-nodes-base.set", "n8n-nodes-base.if"): 1,
            ("n8n-nodes-base.if", "n8n-nodes-base.set"): 1,
            ("n8n-nodes-base.if", "n8n-nodes-base.logMessage"): 1,
            ("n8n-nodes-base.webhook", "n8n-nodes-base.set"): 1,
        }
        self.assertEqual(pairs, expected_pairs)
        self.assertEqual(get_common_node_type_pairs(self.empty_workflow), {})

    def test_get_node_io_degree(self):
        # Start1: 0 in, 1 out
        self.assertEqual(get_node_io_degree(self.workflow1, "start1"), {'in_degree': 0, 'out_degree': 1})
        # Set1: 1 in, 1 out
        self.assertEqual(get_node_io_degree(self.workflow1, "set1"), {'in_degree': 1, 'out_degree': 1})
        # If1: 1 in, 2 out
        self.assertEqual(get_node_io_degree(self.workflow1, "if1"), {'in_degree': 1, 'out_degree': 2})
        # Set2: 2 in, 0 out
        self.assertEqual(get_node_io_degree(self.workflow1, "set2"), {'in_degree': 2, 'out_degree': 0})
        # Log1: 1 in, 0 out
        self.assertEqual(get_node_io_degree(self.workflow1, "log1"), {'in_degree': 1, 'out_degree': 0})
        # Hook1: 0 in, 1 out
        self.assertEqual(get_node_io_degree(self.workflow1, "hook1"), {'in_degree': 0, 'out_degree': 1})
        # Dangle1: 0 in, 0 out
        self.assertEqual(get_node_io_degree(self.workflow1, "dangle1"), {'in_degree': 0, 'out_degree': 0})
        # Non-existent node
        self.assertEqual(get_node_io_degree(self.workflow1, "unknown"), {'in_degree': 0, 'out_degree': 0})


    def test_get_all_node_io_degrees(self):
        degrees = get_all_node_io_degrees(self.workflow1)
        expected_degrees = {
            "start1": {'in_degree': 0, 'out_degree': 1},
            "set1": {'in_degree': 1, 'out_degree': 1},
            "if1": {'in_degree': 1, 'out_degree': 2},
            "set2": {'in_degree': 2, 'out_degree': 0},
            "log1": {'in_degree': 1, 'out_degree': 0},
            "hook1": {'in_degree': 0, 'out_degree': 1},
            "dangle1": {'in_degree': 0, 'out_degree': 0}
        }
        self.assertEqual(degrees, expected_degrees)
        self.assertEqual(get_all_node_io_degrees(self.empty_workflow), {})

    def test_identify_trigger_nodes(self):
        triggers = identify_trigger_nodes(self.workflow1) # Uses DEFAULT_TRIGGER_NODE_TYPES
        self.assertIn(self.node_start, triggers)
        self.assertIn(self.node_webhook, triggers)
        self.assertNotIn(self.node_dangling, triggers) # Not a default trigger type
        self.assertEqual(len(triggers), 2)

        # Test with custom trigger types
        custom_triggers = identify_trigger_nodes(self.workflow1, known_trigger_types=["n8n-nodes-base.function"])
        self.assertIn(self.node_dangling, custom_triggers)
        self.assertEqual(len(custom_triggers), 1)

    def test_identify_potential_terminal_nodes(self):
        # Case 1: known_terminal_types is None (function's default) - should return ALL nodes with no outputs
        all_no_outputs = identify_potential_terminal_nodes(self.workflow1)
        self.assertIn(self.node_set2, all_no_outputs, "Set2 should be in all_no_outputs")
        self.assertIn(self.node_log1, all_no_outputs, "Log1 should be in all_no_outputs")
        self.assertIn(self.node_dangling, all_no_outputs, "Dangling node should be in all_no_outputs")
        self.assertEqual(len(all_no_outputs), 3)

        # Case 2: known_terminal_types is DEFAULT_TERMINAL_NODE_TYPES (explicitly passed) - should filter by this list
        terminals_filtered_by_default = identify_potential_terminal_nodes(self.workflow1, known_terminal_types=DEFAULT_TERMINAL_NODE_TYPES)
        self.assertIn(self.node_set2, terminals_filtered_by_default, "Set2 should be in filtered (default list)")    # Is in default list
        self.assertIn(self.node_log1, terminals_filtered_by_default, "Log1 should be in filtered (default list)")    # Is in default list
        self.assertNotIn(self.node_dangling, terminals_filtered_by_default, "Dangling node should NOT be in filtered (default list)") # NOT in default list
        self.assertEqual(len(terminals_filtered_by_default), 2)

        # Case 3: Test with an empty list for known_terminal_types - should return NO nodes as type won't be in empty list
        custom_empty_terminals = identify_potential_terminal_nodes(self.workflow1, known_terminal_types=[])
        self.assertEqual(len(custom_empty_terminals), 0)

        # Case 4: Test with specific custom types (non-empty list)
        custom_terminals = identify_potential_terminal_nodes(self.workflow1, known_terminal_types=["n8n-nodes-base.function"])
        self.assertIn(self.node_dangling, custom_terminals)
        self.assertEqual(len(custom_terminals), 1)


if __name__ == '__main__':
    unittest.main()
