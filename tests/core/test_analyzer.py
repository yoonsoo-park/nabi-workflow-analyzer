# tests/core/test_analyzer.py
import unittest
from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection
from n8n_analyzer.core.analyzer import (
    get_nodes_by_type,
    get_incoming_connections,
    get_outgoing_connections,
    get_node_by_id,
    get_source_node_from_connection,
    get_target_node_from_connection,
    get_dangling_nodes
)

class TestCoreAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create sample nodes
        self.node1 = N8nNode(id="Start_1", name="Start", type="n8n-nodes-base.start", typeVersion=1, position=(100,100), parameters={})
        self.node2 = N8nNode(id="Set_1", name="Set Data", type="n8n-nodes-base.set", typeVersion=1, position=(200,100), parameters={})
        self.node3 = N8nNode(id="Log_1", name="Log Output", type="n8n-nodes-base.logMessage", typeVersion=1, position=(300,100), parameters={})
        self.node4 = N8nNode(id="Set_2", name="Another Set", type="n8n-nodes-base.set", typeVersion=1, position=(200,200), parameters={})
        self.node5 = N8nNode(id="Dangling_1", name="Dangling Node", type="n8n-nodes-base.function", typeVersion=1, position=(400,200), parameters={}) # No connections
        self.node6 = N8nNode(id="Webhook_1", name="Webhook Trigger", type="n8n-nodes-base.webhook", typeVersion=1, position=(50,50), parameters={})


        # Create sample connections
        self.conn1 = N8nConnection(source_node_id="Start_1", source_node_output_port="main", target_node_id="Set_1", target_node_input_port="main")
        self.conn2 = N8nConnection(source_node_id="Set_1", source_node_output_port="main", target_node_id="Log_1", target_node_input_port="main")
        self.conn3 = N8nConnection(source_node_id="Start_1", source_node_output_port="main", target_node_id="Set_2", target_node_input_port="main") # Start to Set_2
        self.conn4 = N8nConnection(source_node_id="Webhook_1", source_node_output_port="main", target_node_id="Set_1", target_node_input_port="main")


        self.workflow = N8nWorkflow(
            name="Test Workflow",
            nodes=[self.node1, self.node2, self.node3, self.node4, self.node5, self.node6],
            connections=[self.conn1, self.conn2, self.conn3, self.conn4]
        )

    def test_get_nodes_by_type(self):
        set_nodes = get_nodes_by_type(self.workflow, "n8n-nodes-base.set")
        self.assertEqual(len(set_nodes), 2)
        self.assertIn(self.node2, set_nodes)
        self.assertIn(self.node4, set_nodes)

        start_nodes = get_nodes_by_type(self.workflow, "n8n-nodes-base.start")
        self.assertEqual(len(start_nodes), 1)
        self.assertEqual(start_nodes[0], self.node1)

        non_existent_nodes = get_nodes_by_type(self.workflow, "non-existent.type")
        self.assertEqual(len(non_existent_nodes), 0)

    def test_get_node_by_id(self):
        self.assertEqual(get_node_by_id(self.workflow, "Set_1"), self.node2)
        self.assertIsNone(get_node_by_id(self.workflow, "Unknown_ID"))

    def test_get_incoming_connections(self):
        set_1_incoming = get_incoming_connections(self.workflow, "Set_1")
        self.assertEqual(len(set_1_incoming), 2)
        self.assertIn(self.conn1, set_1_incoming)
        self.assertIn(self.conn4, set_1_incoming)

        start_1_incoming = get_incoming_connections(self.workflow, "Start_1")
        self.assertEqual(len(start_1_incoming), 0)

    def test_get_outgoing_connections(self):
        start_1_outgoing = get_outgoing_connections(self.workflow, "Start_1")
        self.assertEqual(len(start_1_outgoing), 2)
        self.assertIn(self.conn1, start_1_outgoing)
        self.assertIn(self.conn3, start_1_outgoing)

        log_1_outgoing = get_outgoing_connections(self.workflow, "Log_1")
        self.assertEqual(len(log_1_outgoing), 0)

    def test_get_source_target_nodes_from_connection(self):
        self.assertEqual(get_source_node_from_connection(self.workflow, self.conn1), self.node1)
        self.assertEqual(get_target_node_from_connection(self.workflow, self.conn1), self.node2)

    def test_get_dangling_nodes(self):
        dangling = get_dangling_nodes(self.workflow)
        # self.node5 (Dangling_1) has no inputs and is not an excluded input type
        self.assertIn(self.node5, dangling["inputs_dangling"])
        # self.node6 (Webhook_1) has no inputs but IS an excluded input type
        self.assertNotIn(self.node6, dangling["inputs_dangling"])
        # self.node1 (Start_1) has no inputs but IS an excluded input type
        self.assertNotIn(self.node1, dangling["inputs_dangling"])

        # self.node3 (Log_1) has no outputs but IS an excluded output type
        self.assertNotIn(self.node3, dangling["outputs_dangling"])
        # self.node4 (Set_2) has no outputs and is NOT an excluded output type
        self.assertIn(self.node4, dangling["outputs_dangling"])
        # self.node5 (Dangling_1) has no outputs and is NOT an excluded output type
        self.assertIn(self.node5, dangling["outputs_dangling"])
        # self.node2 (Set_1) has an output (to Log_1)
        self.assertNotIn(self.node2, dangling["outputs_dangling"])


if __name__ == '__main__':
    unittest.main()
