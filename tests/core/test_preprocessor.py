"""
Tests for PreprocessingPipeline - Phase 3 Data Preprocessing and Feature Engineering

Following TDD approach:
1. Test for expected/happy path behavior
2. Test for edge case handling  
3. Test for failure conditions and error handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection
from n8n_analyzer.core.preprocessor import PreprocessingPipeline, ProcessedWorkflow, PreprocessingError


class TestPreprocessingPipeline(unittest.TestCase):
    """Test suite for PreprocessingPipeline following TDD principles."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = PreprocessingPipeline()
        
        # Create sample workflow for testing
        self.sample_workflow = N8nWorkflow(
            id="test_workflow_001",
            name="Test Workflow",
            nodes=[
                N8nNode(
                    id="node1",
                    name="Webhook Node",
                    type="n8n-nodes-base.webhook",
                    typeVersion=1,
                    position=(100, 100),
                    parameters={"httpMethod": "POST", "path": "/test"}
                ),
                N8nNode(
                    id="node2", 
                    name="Set Node",
                    type="n8n-nodes-base.set",
                    typeVersion=1,
                    position=(300, 100),
                    parameters={"values": {"key": "value"}}
                )
            ],
            connections=[
                N8nConnection(
                    source_node_id="node1",
                    source_node_output_port="main",
                    target_node_id="node2",
                    target_node_input_port="main"
                )
            ]
        )
    
    def test_pipeline_initialization_happy_path(self):
        """Test 1: Expected behavior - Pipeline initializes with default services."""
        pipeline = PreprocessingPipeline()
        
        # Verify pipeline has required components
        self.assertIsNotNone(pipeline.feature_extractor)
        self.assertIsNotNone(pipeline.data_staging)
        self.assertIsNotNone(pipeline.mining_preprocessor)
        self.assertIsInstance(pipeline.config, dict)
        self.assertIn('batch_size', pipeline.config)
    
    def test_pipeline_initialization_with_custom_services(self):
        """Test 2: Expected behavior - Pipeline accepts custom service dependencies."""
        mock_feature_extractor = Mock()
        mock_data_staging = Mock()
        mock_mining_preprocessor = Mock()
        
        pipeline = PreprocessingPipeline(
            feature_extractor=mock_feature_extractor,
            data_staging=mock_data_staging,
            mining_preprocessor=mock_mining_preprocessor
        )
        
        self.assertEqual(pipeline.feature_extractor, mock_feature_extractor)
        self.assertEqual(pipeline.data_staging, mock_data_staging)
        self.assertEqual(pipeline.mining_preprocessor, mock_mining_preprocessor)
    
    def test_preprocess_single_workflow_happy_path(self):
        """Test 3: Expected behavior - Single workflow preprocessing succeeds."""
        # Mock the service dependencies to control their behavior
        self.pipeline.feature_extractor.extract_node_features = Mock(return_value=[
            {'node_id': 'node1', 'type': 'webhook', 'complexity': 2.0}
        ])
        self.pipeline.feature_extractor.extract_connection_patterns = Mock(return_value=[
            'seq:webhook→set'
        ])
        self.pipeline.feature_extractor.extract_workflow_features = Mock(return_value={
            'node_count': 2,
            'quality_score': 0.8
        })
        self.pipeline.data_staging.stage_features = Mock(return_value=Mock(handle_id='test_handle'))
        self.pipeline.mining_preprocessor.convert_to_transaction = Mock(return_value=[
            'type:webhook', 'pattern:webhook→set', 'quality:High'
        ])
        
        # Test preprocessing (convert to generator)
        workflows = (w for w in [self.sample_workflow])
        processed_workflows = list(self.pipeline.preprocess_workflows(workflows))
        
        # Verify results
        self.assertEqual(len(processed_workflows), 1)
        processed = processed_workflows[0]
        self.assertIsInstance(processed, ProcessedWorkflow)
        self.assertEqual(processed.workflow_id, "test_workflow_001")
        self.assertTrue(len(processed.mining_transaction) > 0)
    
    def test_preprocess_workflows_edge_case_empty_input(self):
        """Test 4: Edge case - Empty workflow list."""
        empty_workflows = (w for w in [])
        processed_workflows = list(self.pipeline.preprocess_workflows(empty_workflows))
        
        self.assertEqual(len(processed_workflows), 0)
    
    def test_preprocess_workflows_edge_case_workflow_with_no_nodes(self):
        """Test 5: Edge case - Workflow with no nodes."""
        empty_workflow = N8nWorkflow(
            name="Empty Workflow",
            id="empty_workflow", 
            nodes=[],
            connections=[]
        )
        
        # Mock services to handle empty workflow - provide at least one transaction item
        self.pipeline.feature_extractor.extract_node_features = Mock(return_value=[])
        self.pipeline.feature_extractor.extract_connection_patterns = Mock(return_value=[])
        self.pipeline.feature_extractor.extract_workflow_features = Mock(return_value={
            'node_count': 0
        })
        self.pipeline.mining_preprocessor.convert_to_transaction = Mock(return_value=['empty:workflow'])
        
        workflows = (w for w in [empty_workflow])
        processed_workflows = list(self.pipeline.preprocess_workflows(workflows))
        
        self.assertEqual(len(processed_workflows), 1)
        processed = processed_workflows[0]
        self.assertEqual(len(processed.node_features), 0)
        self.assertEqual(len(processed.connection_features), 0)
    
    def test_preprocess_workflows_failure_condition_invalid_workflow(self):
        """Test 6: Failure condition - Invalid workflow causes graceful failure."""
        # Create a workflow that will cause an exception
        invalid_workflow = Mock()
        invalid_workflow.name = "Invalid Workflow"
        invalid_workflow.nodes = None  # This should cause an error
        
        workflows = (w for w in [invalid_workflow])
        
        # Should not raise exception, but continue processing
        processed_workflows = list(self.pipeline.preprocess_workflows(workflows))
        
        # Should return empty list due to processing failure
        self.assertEqual(len(processed_workflows), 0)
    
    def test_preprocess_workflows_failure_condition_feature_extraction_error(self):
        """Test 7: Failure condition - Feature extraction service fails."""
        # Mock feature extractor to raise exception
        self.pipeline.feature_extractor.extract_node_features = Mock(
            side_effect=Exception("Feature extraction failed")
        )
        
        workflows = (w for w in [self.sample_workflow])
        
        # Should handle the error gracefully and continue
        processed_workflows = list(self.pipeline.preprocess_workflows(workflows))
        
        # Should return empty list due to processing failure
        self.assertEqual(len(processed_workflows), 0)
    
    def test_preprocess_for_pattern_mining_happy_path(self):
        """Test 8: Expected behavior - Pattern mining preprocessing interface."""
        # Mock the preprocessing to return a transaction
        mock_processed = ProcessedWorkflow(
            original_workflow=self.sample_workflow,
            node_features=[],
            connection_features=[],
            workflow_features={},
            mining_transaction=['type:webhook', 'pattern:webhook→set']
        )
        
        with patch.object(self.pipeline, 'preprocess_workflows', return_value=[mock_processed]):
            workflows = (w for w in [self.sample_workflow])
            transactions = list(self.pipeline.preprocess_for_pattern_mining(workflows))
            
            self.assertEqual(len(transactions), 1)
            self.assertEqual(transactions[0], ['type:webhook', 'pattern:webhook→set'])
    
    def test_processed_workflow_properties(self):
        """Test 9: Expected behavior - ProcessedWorkflow properties work correctly."""
        processed = ProcessedWorkflow(
            original_workflow=self.sample_workflow,
            node_features=[{'node_id': 'node1'}, {'node_id': 'node2'}],
            connection_features=['pattern1', 'pattern2'],
            workflow_features={'quality': 0.8, 'complexity': 2.0},
            mining_transaction=['item1', 'item2', 'item3']
        )
        
        # Test properties
        self.assertEqual(processed.workflow_id, "test_workflow_001")
        self.assertEqual(processed.feature_count, 6)  # 2 + 2 + 2
        
        # Test to_dict conversion
        result_dict = processed.to_dict()
        self.assertIn('workflow_id', result_dict)
        self.assertIn('mining_transaction', result_dict)
        self.assertEqual(result_dict['feature_count'], 6)
    
    def test_validation_failure_condition_empty_transaction(self):
        """Test 10: Failure condition - Validation fails for empty transaction."""
        processed = ProcessedWorkflow(
            original_workflow=self.sample_workflow,
            node_features=[],
            connection_features=[],
            workflow_features={},
            mining_transaction=[]  # Empty transaction should fail validation
        )
        
        # This should raise a validation error
        with self.assertRaises(ValueError):
            self.pipeline._validate_processed_workflow(processed)
    
    def test_validation_failure_condition_wrong_data_types(self):
        """Test 11: Failure condition - Validation fails for wrong data types."""
        processed = ProcessedWorkflow(
            original_workflow=self.sample_workflow,
            node_features="not a list",  # Wrong type
            connection_features=[],
            workflow_features={},
            mining_transaction=['item1']
        )
        
        # This should raise a type error
        with self.assertRaises(TypeError):
            self.pipeline._validate_processed_workflow(processed)
    
    def test_get_preprocessing_stats(self):
        """Test 12: Expected behavior - Statistics retrieval works."""
        stats = self.pipeline.get_preprocessing_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('pipeline_config', stats)
        self.assertIn('feature_extractor_type', stats)
        self.assertIn('data_staging_type', stats)
        self.assertIn('mining_preprocessor_type', stats)


if __name__ == '__main__':
    unittest.main() 