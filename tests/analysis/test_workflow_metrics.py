# tests/analysis/test_workflow_metrics.py
import unittest
from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection
from n8n_analyzer.analysis.workflow_metrics import (
    count_nodes,
    count_connections,
    count_unique_node_types,
    calculate_workflow_density,
    average_parameters_per_node,
    count_complex_node_types,
    calculate_all_complexity_metrics,
    DEFAULT_COMPLEX_NODE_TYPES
)

class TestWorkflowMetrics(unittest.TestCase):
    def setUp(self):
        self.empty_workflow = N8nWorkflow(name="Empty", nodes=[], connections=[])

        self.simple_node1 = N8nNode(id="s1", name="Start", type="n8n-nodes-base.start", typeVersion=1, position=(0,0), parameters={"p1":"v1"})
        self.simple_node2 = N8nNode(id="s2", name="Set", type="n8n-nodes-base.set", typeVersion=1, position=(0,0), parameters={"p2":"v2", "p3":"v3"})
        self.simple_conn1 = N8nConnection(source_node_id="s1", source_node_output_port="main", target_node_id="s2", target_node_input_port="main")
        self.linear_workflow = N8nWorkflow(
            name="Linear",
            nodes=[self.simple_node1, self.simple_node2],
            connections=[self.simple_conn1]
        )

        self.complex_node1 = N8nNode(id="c1", name="Func", type="n8n-nodes-base.function", typeVersion=1, position=(0,0), parameters={}) # Complex
        self.complex_node2 = N8nNode(id="c2", name="Merge", type="n8n-nodes-base.merge", typeVersion=1, position=(0,0), parameters={"p":"v"})    # Complex
        self.complex_node3 = N8nNode(id="c3", name="HTTP", type="n8n-nodes-base.httpRequest", typeVersion=1, position=(0,0), parameters={}) # Not default complex

        self.conn_c1_c2 = N8nConnection(source_node_id="c1", source_node_output_port="main", target_node_id="c2", target_node_input_port="main")
        self.conn_c2_c3 = N8nConnection(source_node_id="c2", source_node_output_port="main", target_node_id="c3", target_node_input_port="main")
        self.conn_c1_c3 = N8nConnection(source_node_id="c1", source_node_output_port="output1", target_node_id="c3", target_node_input_port="input1") # Makes it denser

        self.complex_workflow = N8nWorkflow(
            name="Complex",
            nodes=[self.simple_node1, self.simple_node2, self.complex_node1, self.complex_node2, self.complex_node3], # 5 nodes
            connections=[self.simple_conn1, self.conn_c1_c2, self.conn_c2_c3, self.conn_c1_c3] # 4 connections
        )


    def test_count_nodes(self):
        self.assertEqual(count_nodes(self.empty_workflow), 0)
        self.assertEqual(count_nodes(self.linear_workflow), 2)
        self.assertEqual(count_nodes(self.complex_workflow), 5)

    def test_count_connections(self):
        self.assertEqual(count_connections(self.empty_workflow), 0)
        self.assertEqual(count_connections(self.linear_workflow), 1)
        self.assertEqual(count_connections(self.complex_workflow), 4)

    def test_count_unique_node_types(self):
        self.assertEqual(count_unique_node_types(self.empty_workflow), 0)
        self.assertEqual(count_unique_node_types(self.linear_workflow), 2) # start, set
        # complex_workflow: start, set, function, merge, httpRequest = 5 unique
        self.assertEqual(count_unique_node_types(self.complex_workflow), 5)

    def test_calculate_workflow_density(self):
        self.assertEqual(calculate_workflow_density(self.empty_workflow), 0.0)
        # Linear: 2 nodes, 1 conn. Max possible = 2 * 1 = 2. Density = 1/2 = 0.5
        self.assertEqual(calculate_workflow_density(self.linear_workflow), 0.5)
        # Workflow with 1 node
        one_node_wf = N8nWorkflow(name="OneNode", nodes=[self.simple_node1], connections=[])
        self.assertEqual(calculate_workflow_density(one_node_wf), 0.0)
        # Complex: 5 nodes, 4 conn. Max possible = 5 * 4 = 20. Density = 4/20 = 0.2
        self.assertEqual(calculate_workflow_density(self.complex_workflow), 0.2)

    def test_average_parameters_per_node(self):
        self.assertEqual(average_parameters_per_node(self.empty_workflow), 0.0)
        # Linear: node1 has 1 param, node2 has 2 params. Total 3 params / 2 nodes = 1.5
        self.assertEqual(average_parameters_per_node(self.linear_workflow), 1.5)
        # Complex: s1(1), s2(2), c1(0), c2(1), c3(0). Total 4 params / 5 nodes = 0.8
        self.assertEqual(average_parameters_per_node(self.complex_workflow), 0.8)

    def test_count_complex_node_types(self):
        self.assertEqual(count_complex_node_types(self.empty_workflow), 0)
        self.assertEqual(count_complex_node_types(self.linear_workflow), 0) # No default complex nodes
        # Complex workflow has 'n8n-nodes-base.function' and 'n8n-nodes-base.merge'
        self.assertEqual(count_complex_node_types(self.complex_workflow), 2)
        # Test with custom complex types
        custom_complex = ["n8n-nodes-base.httpRequest"]
        self.assertEqual(count_complex_node_types(self.complex_workflow, custom_complex), 1)


    def test_calculate_all_complexity_metrics(self):
        metrics_linear = calculate_all_complexity_metrics(self.linear_workflow)
        expected_linear = {
            "node_count": 2, "connection_count": 1, "unique_node_type_count": 2,
            "density": 0.5, "average_parameters_per_node": 1.5, "complex_node_count": 0
        }
        self.assertEqual(metrics_linear, expected_linear)

        metrics_complex = calculate_all_complexity_metrics(self.complex_workflow)
        expected_complex = {
            "node_count": 5, "connection_count": 4, "unique_node_type_count": 5,
            "density": 0.2, "average_parameters_per_node": 0.8, "complex_node_count": 2
        }
        self.assertEqual(metrics_complex, expected_complex)

if __name__ == '__main__':
    unittest.main()
