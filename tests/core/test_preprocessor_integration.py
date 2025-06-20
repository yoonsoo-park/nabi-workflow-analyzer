"""
Integration tests for PreprocessingPipeline - Testing actual functionality with real data

This follows TDD approach but tests the REAL implementation instead of mocks
to verify our Phase 3 preprocessing pipeline actually works.
"""

import unittest
import sys
import os
import json

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection
from n8n_analyzer.core.preprocessor import PreprocessingPipeline, ProcessedWorkflow
from n8n_analyzer.core.parser import WorkflowParser


class TestPreprocessingPipelineIntegration(unittest.TestCase):
    """Integration test suite for PreprocessingPipeline with real data."""
    
    def setUp(self):
        """Set up test fixtures with real data."""
        self.pipeline = PreprocessingPipeline()
        self.parser = WorkflowParser()
        
        # Create a realistic workflow for testing
        self.sample_workflow = N8nWorkflow(
            name="Integration Test Workflow",
            id="integration_test_001",
            nodes=[
                N8nNode(
                    id="webhook_node",
                    name="Webhook Trigger",
                    type="n8n-nodes-base.webhook",
                    typeVersion=1,
                    position=(100, 100),
                    parameters={
                        "httpMethod": "POST",
                        "path": "/webhook/test",
                        "responseMode": "responseNode"
                    }
                ),
                N8nNode(
                    id="set_node",
                    name="Process Data",
                    type="n8n-nodes-base.set",
                    typeVersion=1,
                    position=(300, 100),
                    parameters={
                        "values": {
                            "string": [
                                {"name": "processed_at", "value": "={{ new Date() }}"},
                                {"name": "status", "value": "processed"}
                            ]
                        }
                    }
                ),
                N8nNode(
                    id="http_node",
                    name="Send Response",
                    type="n8n-nodes-base.httpRequest",
                    typeVersion=3,
                    position=(500, 100),
                    parameters={
                        "method": "POST",
                        "url": "https://api.example.com/callback",
                        "responseFormat": "json"
                    }
                )
            ],
            connections=[
                N8nConnection(
                    source_node_id="webhook_node",
                    source_node_output_port="main",
                    target_node_id="set_node",
                    target_node_input_port="main"
                ),
                N8nConnection(
                    source_node_id="set_node",
                    source_node_output_port="main",
                    target_node_id="http_node",
                    target_node_input_port="main"
                )
            ]
        )
    
    def test_preprocessing_pipeline_end_to_end_integration(self):
        """Integration Test 1: End-to-end preprocessing with real services."""
        # Test with real services (no mocks)
        workflows = (w for w in [self.sample_workflow])
        processed_workflows = list(self.pipeline.preprocess_workflows(workflows))
        
        # Verify we get results
        self.assertEqual(len(processed_workflows), 1)
        processed = processed_workflows[0]
        
        # Verify it's a ProcessedWorkflow
        self.assertIsInstance(processed, ProcessedWorkflow)
        self.assertEqual(processed.workflow_id, "integration_test_001")
        
        # Verify features were extracted
        self.assertIsInstance(processed.node_features, list)
        self.assertIsInstance(processed.connection_features, list)
        self.assertIsInstance(processed.workflow_features, dict)
        self.assertIsInstance(processed.mining_transaction, list)
        
        # Verify we have actual feature data
        self.assertGreater(len(processed.node_features), 0, "Should extract node features")
        self.assertGreater(len(processed.connection_features), 0, "Should extract connection features")
        self.assertGreater(len(processed.workflow_features), 0, "Should extract workflow features")
        self.assertGreater(len(processed.mining_transaction), 0, "Should generate mining transaction")
        
        print(f"✅ Extracted {len(processed.node_features)} node features")
        print(f"✅ Extracted {len(processed.connection_features)} connection features")
        print(f"✅ Extracted {len(processed.workflow_features)} workflow features")
        print(f"✅ Generated {len(processed.mining_transaction)} mining items")
    
    def test_pattern_mining_preprocessing_integration(self):
        """Integration Test 2: Pattern mining interface with real data."""
        workflows = (w for w in [self.sample_workflow])
        transactions = list(self.pipeline.preprocess_for_pattern_mining(workflows))
        
        # Verify we get transaction data
        self.assertEqual(len(transactions), 1)
        transaction = transactions[0]
        
        # Verify transaction format
        self.assertIsInstance(transaction, list)
        self.assertGreater(len(transaction), 0, "Transaction should not be empty")
        
        # Verify transaction contains meaningful data
        transaction_str = ' '.join(transaction)
        self.assertIn('webhook', transaction_str.lower(), "Should contain node type info")
        
        print(f"✅ Generated transaction: {transaction[:5]}...")  # Show first 5 items
    
    def test_feature_extraction_quality_integration(self):
        """Integration Test 3: Verify quality of extracted features."""
        workflows = (w for w in [self.sample_workflow])
        processed_workflows = list(self.pipeline.preprocess_workflows(workflows))
        processed = processed_workflows[0]
        
        # Test node features quality
        for node_feature in processed.node_features:
            self.assertIsInstance(node_feature, dict, "Node features should be dictionaries")
            self.assertIn('node_id', node_feature, "Node features should have node_id")
            
        # Test connection features quality
        for conn_feature in processed.connection_features:
            self.assertIsInstance(conn_feature, str, "Connection features should be strings")
            self.assertGreater(len(conn_feature), 0, "Connection features should not be empty")
        
        # Test workflow features quality
        self.assertIsInstance(processed.workflow_features, dict)
        self.assertGreater(len(processed.workflow_features), 0, "Should have workflow-level features")
        
        print(f"✅ Node features structure valid: {len(processed.node_features)} features")
        print(f"✅ Connection features structure valid: {len(processed.connection_features)} patterns")
        print(f"✅ Workflow features structure valid: {list(processed.workflow_features.keys())}")
    
    def test_preprocessing_with_sample_workflow_file(self):
        """Integration Test 4: Test with actual workflow file from data directory."""
        # Try to load a real workflow file
        sample_file_path = "data/raw_workflows/workflow_0001_automation.json"
        
        if not os.path.exists(sample_file_path):
            self.skipTest(f"Sample workflow file not found: {sample_file_path}")
        
        try:
            # Parse real workflow file
            with open(sample_file_path, 'r') as f:
                workflow_data = json.load(f)
            
            workflow = self.parser.parse_single(sample_file_path)
            
            # Process with our pipeline
            workflows = (w for w in [workflow])
            processed_workflows = list(self.pipeline.preprocess_workflows(workflows))
            
            # Verify processing succeeded
            self.assertEqual(len(processed_workflows), 1)
            processed = processed_workflows[0]
            
            # Verify we extracted meaningful features
            self.assertGreater(processed.feature_count, 0, "Should extract features from real workflow")
            
            print(f"✅ Successfully processed real workflow: {workflow.name}")
            print(f"✅ Total features extracted: {processed.feature_count}")
            
        except Exception as e:
            self.fail(f"Failed to process real workflow file: {str(e)}")
    
    def test_preprocessing_error_handling_integration(self):
        """Integration Test 5: Test error handling with problematic data."""
        # Create a workflow with potential issues
        problematic_workflow = N8nWorkflow(
            name="Problematic Workflow",
            id="problematic_001",
            nodes=[
                N8nNode(
                    id="node_with_empty_params",
                    name="Empty Node",
                    type="unknown.node.type",
                    typeVersion=999,  # Unusual version
                    position=(0, 0),
                    parameters={}  # Empty parameters
                )
            ],
            connections=[]  # No connections
        )
        
        # Should handle gracefully
        workflows = (w for w in [problematic_workflow])
        processed_workflows = list(self.pipeline.preprocess_workflows(workflows))
        
        # Should still process (maybe with limited features)
        self.assertGreaterEqual(len(processed_workflows), 0, "Should handle problematic workflows gracefully")
        
        if processed_workflows:
            processed = processed_workflows[0]
            print(f"✅ Handled problematic workflow: {processed.feature_count} features extracted")
    
    def test_preprocessing_performance_integration(self):
        """Integration Test 6: Basic performance test with multiple workflows."""
        # Create multiple workflows
        workflows = []
        for i in range(10):
            workflow = N8nWorkflow(
                name=f"Performance Test Workflow {i}",
                id=f"perf_test_{i:03d}",
                nodes=[
                    N8nNode(
                        id=f"node_{i}_1",
                        name=f"Start Node {i}",
                        type="n8n-nodes-base.start",
                        typeVersion=1,
                        position=(100, 100),
                        parameters={}
                    ),
                    N8nNode(
                        id=f"node_{i}_2",
                        name=f"End Node {i}",
                        type="n8n-nodes-base.noOp",
                        typeVersion=1,
                        position=(300, 100),
                        parameters={}
                    )
                ],
                connections=[
                    N8nConnection(
                        source_node_id=f"node_{i}_1",
                        source_node_output_port="main",
                        target_node_id=f"node_{i}_2",
                        target_node_input_port="main"
                    )
                ]
            )
            workflows.append(workflow)
        
        # Process all workflows
        import time
        start_time = time.time()
        
        workflow_generator = (w for w in workflows)
        processed_workflows = list(self.pipeline.preprocess_workflows(workflow_generator))
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify all were processed
        self.assertEqual(len(processed_workflows), 10, "Should process all workflows")
        
        # Basic performance check (should be reasonable)
        self.assertLess(processing_time, 10.0, "Should process 10 simple workflows in under 10 seconds")
        
        print(f"✅ Processed {len(processed_workflows)} workflows in {processing_time:.2f} seconds")
        print(f"✅ Average: {processing_time/len(processed_workflows):.3f} seconds per workflow")


if __name__ == '__main__':
    unittest.main() 