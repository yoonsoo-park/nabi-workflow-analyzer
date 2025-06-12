# tests/analysis/test_node_analyzer.py
import unittest
from n8n_analyzer.core.models import N8nWorkflow, N8nNode
from n8n_analyzer.analysis.node_analyzer import (
    calculate_node_type_distribution, # Existing import
    extract_parameter_keys_for_node,    # New import
    extract_all_parameter_keys_by_type, # New import
    get_nodes_with_specific_parameter,  # New import
    get_nodes_with_specific_parameter_value # New import
)

class TestNodeAnalyzer(unittest.TestCase): # Existing class
    # ... existing test methods for calculate_node_type_distribution ...
    def test_calculate_node_type_distribution_empty_workflow(self):
        workflow = N8nWorkflow(name="Empty Workflow", nodes=[], connections=[])
        distribution = calculate_node_type_distribution(workflow)
        self.assertEqual(distribution, {})

    def test_calculate_node_type_distribution_single_type(self):
        nodes = [
            N8nNode(id="1", name="Start", type="n8n-nodes-base.start", typeVersion=1, position=(0,0), parameters={}),
            N8nNode(id="2", name="Start Again", type="n8n-nodes-base.start", typeVersion=1, position=(0,0), parameters={})
        ]
        workflow = N8nWorkflow(name="Single Type Workflow", nodes=nodes, connections=[])
        distribution = calculate_node_type_distribution(workflow)
        expected = {
            "n8n-nodes-base.start": {"count": 2, "percentage": 100.0}
        }
        self.assertEqual(distribution, expected)

    def test_calculate_node_type_distribution_mixed_types(self):
        nodes = [
            N8nNode(id="1", name="Start", type="n8n-nodes-base.start", typeVersion=1, position=(0,0), parameters={}),
            N8nNode(id="2", name="Set Data", type="n8n-nodes-base.set", typeVersion=1, position=(0,0), parameters={}),
            N8nNode(id="3", name="Another Set", type="n8n-nodes-base.set", typeVersion=1, position=(0,0), parameters={}),
            N8nNode(id="4", name="IF Condition", type="n8n-nodes-base.if", typeVersion=1, position=(0,0), parameters={}),
            N8nNode(id="5", name="HTTP Call", type="n8n-nodes-base.httpRequest", typeVersion=1, position=(0,0), parameters={}),
            N8nNode(id="6", name="Set Again", type="n8n-nodes-base.set", typeVersion=1, position=(0,0), parameters={}),
        ]
        workflow = N8nWorkflow(name="Mixed Type Workflow", nodes=nodes, connections=[])
        distribution = calculate_node_type_distribution(workflow)
        expected = {
            "n8n-nodes-base.start": {"count": 1, "percentage": 16.67},
            "n8n-nodes-base.set": {"count": 3, "percentage": 50.00},
            "n8n-nodes-base.if": {"count": 1, "percentage": 16.67},
            "n8n-nodes-base.httpRequest": {"count": 1, "percentage": 16.67}
        }
        self.assertEqual(distribution, expected)

    def test_calculate_node_type_distribution_percentages_rounding(self):
        nodes = [
            N8nNode(id="1", name="A", type="typeA", typeVersion=1, position=(0,0), parameters={}),
            N8nNode(id="2", name="B", type="typeB", typeVersion=1, position=(0,0), parameters={}),
            N8nNode(id="3", name="C", type="typeC", typeVersion=1, position=(0,0), parameters={})
        ]
        workflow = N8nWorkflow(name="Rounding Test", nodes=nodes, connections=[])
        distribution = calculate_node_type_distribution(workflow)
        expected = {
            "typeA": {"count": 1, "percentage": 33.33},
            "typeB": {"count": 1, "percentage": 33.33},
            "typeC": {"count": 1, "percentage": 33.33}
        }
        self.assertEqual(distribution, expected)

    # --- New tests for parameter functions ---
    def setUpParameterTests(self): # Helper to avoid redefining nodes in each test
        self.node_p1 = N8nNode(id="pnode1", name="PNode1", type="typeA", typeVersion=1, position=(0,0),
                               parameters={"keyA": "valA", "keyB": 123})
        self.node_p2 = N8nNode(id="pnode2", name="PNode2", type="typeA", typeVersion=1, position=(0,0),
                               parameters={"keyB": 456, "keyC": True, "commonKey": "valX"})
        self.node_p3 = N8nNode(id="pnode3", name="PNode3", type="typeB", typeVersion=1, position=(0,0),
                               parameters={"keyD": "valD", "commonKey": "valY"})
        self.node_p4_no_params = N8nNode(id="pnode4", name="PNode4NoParams", type="typeB", typeVersion=1, position=(0,0), parameters={})
        self.param_workflow = N8nWorkflow(name="Param Test WF",
                                        nodes=[self.node_p1, self.node_p2, self.node_p3, self.node_p4_no_params],
                                        connections=[])

    def test_extract_parameter_keys_for_node(self):
        self.setUpParameterTests()
        self.assertEqual(extract_parameter_keys_for_node(self.node_p1), ["keyA", "keyB"])
        self.assertEqual(extract_parameter_keys_for_node(self.node_p2), ["commonKey", "keyB", "keyC"]) # Sorted
        self.assertEqual(extract_parameter_keys_for_node(self.node_p3), ["commonKey", "keyD"])
        self.assertEqual(extract_parameter_keys_for_node(self.node_p4_no_params), [])

    def test_extract_all_parameter_keys_by_type(self):
        self.setUpParameterTests()
        result = extract_all_parameter_keys_by_type(self.param_workflow)
        expected = {
            "typeA": {"keyA": 1, "keyB": 2, "keyC": 1, "commonKey": 1},
            "typeB": {"keyD": 1, "commonKey": 1}
        }
        self.assertEqual(result, expected)

        empty_workflow = N8nWorkflow(name="Empty", nodes=[], connections=[])
        self.assertEqual(extract_all_parameter_keys_by_type(empty_workflow), {})

    def test_get_nodes_with_specific_parameter(self):
        self.setUpParameterTests()
        nodes_with_keyB = get_nodes_with_specific_parameter(self.param_workflow, "keyB")
        self.assertIn(self.node_p1, nodes_with_keyB)
        self.assertIn(self.node_p2, nodes_with_keyB)
        self.assertEqual(len(nodes_with_keyB), 2)

        nodes_with_commonKey = get_nodes_with_specific_parameter(self.param_workflow, "commonKey")
        self.assertIn(self.node_p2, nodes_with_commonKey)
        self.assertIn(self.node_p3, nodes_with_commonKey)
        self.assertEqual(len(nodes_with_commonKey), 2)

        nodes_with_nonExistentKey = get_nodes_with_specific_parameter(self.param_workflow, "nonExistentKey")
        self.assertEqual(len(nodes_with_nonExistentKey), 0)

    def test_get_nodes_with_specific_parameter_value(self):
        self.setUpParameterTests()
        # keyB = 123
        nodes_keyB_123 = get_nodes_with_specific_parameter_value(self.param_workflow, "keyB", 123)
        self.assertIn(self.node_p1, nodes_keyB_123)
        self.assertEqual(len(nodes_keyB_123), 1)

        # commonKey = "valX"
        nodes_commonKey_valX = get_nodes_with_specific_parameter_value(self.param_workflow, "commonKey", "valX")
        self.assertIn(self.node_p2, nodes_commonKey_valX)
        self.assertEqual(len(nodes_commonKey_valX), 1)

        # commonKey = "nonExistentValue"
        nodes_commonKey_nonExistent = get_nodes_with_specific_parameter_value(self.param_workflow, "commonKey", "nonExistentValue")
        self.assertEqual(len(nodes_commonKey_nonExistent), 0)

        # keyC = True
        nodes_keyC_True = get_nodes_with_specific_parameter_value(self.param_workflow, "keyC", True)
        self.assertIn(self.node_p2, nodes_keyC_True)
        self.assertEqual(len(nodes_keyC_True), 1)


if __name__ == '__main__':
    unittest.main()
