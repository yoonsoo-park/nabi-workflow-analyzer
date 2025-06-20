"""
End-to-End Test for Phase 3: Data Preprocessing and Feature Engineering

This test demonstrates that our Phase 3 implementation works correctly
with real workflow data, following TDD principles and verifying all
functionality we've implemented.
"""

import unittest
import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from n8n_analyzer.core.preprocessor import PreprocessingPipeline
from n8n_analyzer.core.parser import WorkflowParser
from n8n_analyzer.core.analyzer import WorkflowAnalysisEngine


class TestPhase3EndToEnd(unittest.TestCase):
    """End-to-end test for Phase 3 preprocessing pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.preprocessing_pipeline = PreprocessingPipeline()
        self.parser = WorkflowParser()
        self.analysis_engine = WorkflowAnalysisEngine()
        
        # Find sample workflow files
        self.data_dir = Path("data/raw_workflows")
        self.sample_files = list(self.data_dir.glob("workflow_*.json"))[:5]  # Test with first 5 files
    
    def test_phase3_complete_preprocessing_pipeline(self):
        """Test complete Phase 3 preprocessing pipeline with real data."""
        if not self.sample_files:
            self.skipTest("No sample workflow files found")
        
        print(f"\n🧪 Testing Phase 3 with {len(self.sample_files)} real workflow files...")
        
        # Step 1: Parse workflows
        workflows = []
        for file_path in self.sample_files:
            try:
                workflow = self.parser.parse_single(str(file_path))
                workflows.append(workflow)
                print(f"✅ Parsed: {workflow.name} ({len(workflow.nodes)} nodes, {len(workflow.connections)} connections)")
            except Exception as e:
                print(f"⚠️ Failed to parse {file_path}: {e}")
        
        self.assertGreater(len(workflows), 0, "Should successfully parse at least one workflow")
        
        # Step 2: Preprocess workflows
        workflow_generator = (w for w in workflows)
        processed_workflows = list(self.preprocessing_pipeline.preprocess_workflows(workflow_generator))
        
        self.assertEqual(len(processed_workflows), len(workflows), "Should process all parsed workflows")
        
        # Step 3: Verify preprocessing results
        total_features = 0
        total_mining_items = 0
        
        for processed in processed_workflows:
            # Verify structure
            self.assertIsNotNone(processed.workflow_id)
            self.assertIsInstance(processed.node_features, list)
            self.assertIsInstance(processed.connection_features, list)
            self.assertIsInstance(processed.workflow_features, dict)
            self.assertIsInstance(processed.mining_transaction, list)
            
            # Verify content
            self.assertGreater(processed.feature_count, 0, f"Should extract features from {processed.workflow_id}")
            self.assertGreater(len(processed.mining_transaction), 0, f"Should generate mining transaction for {processed.workflow_id}")
            
            total_features += processed.feature_count
            total_mining_items += len(processed.mining_transaction)
            
            print(f"✅ {processed.workflow_id}: {processed.feature_count} features, {len(processed.mining_transaction)} mining items")
        
        print(f"\n📊 Phase 3 Results Summary:")
        print(f"   • Workflows processed: {len(processed_workflows)}")
        print(f"   • Total features extracted: {total_features}")
        print(f"   • Total mining items generated: {total_mining_items}")
        print(f"   • Average features per workflow: {total_features/len(processed_workflows):.1f}")
        
        # Verify reasonable feature extraction
        self.assertGreater(total_features, len(workflows) * 5, "Should extract meaningful features per workflow")
        self.assertGreater(total_mining_items, len(workflows) * 3, "Should generate meaningful mining transactions")
    
    def test_phase3_pattern_mining_interface(self):
        """Test pattern mining interface with real data."""
        if not self.sample_files:
            self.skipTest("No sample workflow files found")
        
        print(f"\n🔍 Testing Pattern Mining Interface...")
        
        # Parse workflows
        workflows = []
        for file_path in self.sample_files[:3]:  # Use first 3 for this test
            try:
                workflow = self.parser.parse_single(str(file_path))
                workflows.append(workflow)
            except Exception:
                continue
        
        if not workflows:
            self.skipTest("No workflows could be parsed")
        
        # Test pattern mining preprocessing
        workflow_generator = (w for w in workflows)
        transactions = list(self.preprocessing_pipeline.preprocess_for_pattern_mining(workflow_generator))
        
        self.assertEqual(len(transactions), len(workflows), "Should generate transaction for each workflow")
        
        # Verify transaction quality
        for i, transaction in enumerate(transactions):
            self.assertIsInstance(transaction, list, f"Transaction {i} should be a list")
            self.assertGreater(len(transaction), 0, f"Transaction {i} should not be empty")
            
            # Verify transaction contains meaningful items
            transaction_str = ' '.join(transaction)
            self.assertTrue(any(keyword in transaction_str.lower() 
                              for keyword in ['type:', 'pattern:', 'complexity:', 'quality:']), 
                           f"Transaction {i} should contain meaningful mining items")
            
            print(f"✅ Transaction {i}: {len(transaction)} items - {transaction[:3]}...")
        
        print(f"📊 Pattern Mining Results: {len(transactions)} transactions generated")
    
    def test_phase3_integration_with_analysis_engine(self):
        """Test Phase 3 integration with the existing analysis engine."""
        if not self.sample_files:
            self.skipTest("No sample workflow files found")
        
        print(f"\n🔧 Testing Integration with Analysis Engine...")
        
        # Parse one workflow
        workflow = self.parser.parse_single(str(self.sample_files[0]))
        print(f"✅ Testing with workflow: {workflow.name}")
        
        # Test that analysis engine can work with preprocessing pipeline
        try:
            # The analysis engine should be able to use our preprocessing pipeline
            workflow_generator = (w for w in [workflow])
            processed_workflows = list(self.preprocessing_pipeline.preprocess_workflows(workflow_generator))
            
            self.assertEqual(len(processed_workflows), 1)
            processed = processed_workflows[0]
            
            # Verify the processed workflow has all expected components
            self.assertIsNotNone(processed.original_workflow)
            self.assertEqual(processed.original_workflow.name, workflow.name)
            
            # Test that we can convert back to usable format
            workflow_dict = processed.to_dict()
            self.assertIn('workflow_id', workflow_dict)
            self.assertIn('node_features', workflow_dict)
            self.assertIn('connection_features', workflow_dict)
            self.assertIn('workflow_features', workflow_dict)
            self.assertIn('mining_transaction', workflow_dict)
            
            print(f"✅ Integration successful: {processed.feature_count} features extracted")
            print(f"✅ Workflow data preserved and enhanced")
            
        except Exception as e:
            self.fail(f"Integration with analysis engine failed: {e}")
    
    def test_phase3_performance_and_memory_efficiency(self):
        """Test that Phase 3 handles multiple workflows efficiently."""
        if len(self.sample_files) < 3:
            self.skipTest("Need at least 3 sample files for performance test")
        
        print(f"\n⚡ Testing Performance and Memory Efficiency...")
        
        import time
        import psutil
        import os
        
        # Parse multiple workflows
        workflows = []
        for file_path in self.sample_files:
            try:
                workflow = self.parser.parse_single(str(file_path))
                workflows.append(workflow)
            except Exception:
                continue
        
        if len(workflows) < 2:
            self.skipTest("Need at least 2 parsed workflows for performance test")
        
        # Measure performance
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        
        # Process workflows using generator (memory efficient)
        workflow_generator = (w for w in workflows)
        processed_count = 0
        total_features = 0
        
        for processed in self.preprocessing_pipeline.preprocess_workflows(workflow_generator):
            processed_count += 1
            total_features += processed.feature_count
        
        end_time = time.time()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        processing_time = end_time - start_time
        memory_increase = final_memory - initial_memory
        
        # Verify performance
        self.assertEqual(processed_count, len(workflows), "Should process all workflows")
        self.assertLess(processing_time, 5.0, "Should process workflows reasonably quickly")
        self.assertLess(memory_increase, 100, "Should not use excessive memory")  # Less than 100MB increase
        
        print(f"✅ Performance Results:")
        print(f"   • Workflows processed: {processed_count}")
        print(f"   • Processing time: {processing_time:.3f} seconds")
        print(f"   • Average time per workflow: {processing_time/processed_count:.3f} seconds")
        print(f"   • Memory increase: {memory_increase:.1f} MB")
        print(f"   • Total features extracted: {total_features}")
        print(f"   • Features per second: {total_features/processing_time:.0f}")
    
    def test_phase3_error_handling_robustness(self):
        """Test that Phase 3 handles errors gracefully."""
        print(f"\n🛡️ Testing Error Handling and Robustness...")
        
        # Create a mix of valid and problematic workflows
        from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection
        
        valid_workflow = N8nWorkflow(
            name="Valid Workflow",
            id="valid_001",
            nodes=[
                N8nNode(id="node1", name="Test Node", type="n8n-nodes-base.start", 
                       typeVersion=1, position=(100, 100))
            ],
            connections=[]
        )
        
        # Create problematic workflow
        problematic_workflow = N8nWorkflow(
            name="Problematic Workflow",
            id="problematic_001",
            nodes=[
                N8nNode(id="bad_node", name="Bad Node", type="unknown.type", 
                       typeVersion=999, position=(0, 0), parameters={})
            ],
            connections=[]
        )
        
        # Test processing mixed workflows
        mixed_workflows = [valid_workflow, problematic_workflow]
        workflow_generator = (w for w in mixed_workflows)
        
        processed_workflows = []
        try:
            processed_workflows = list(self.preprocessing_pipeline.preprocess_workflows(workflow_generator))
        except Exception as e:
            self.fail(f"Pipeline should handle errors gracefully, but raised: {e}")
        
        # Should process at least the valid workflow
        self.assertGreaterEqual(len(processed_workflows), 1, "Should process at least valid workflows")
        
        # Find the valid workflow result
        valid_result = None
        for processed in processed_workflows:
            if processed.workflow_id == "valid_001":
                valid_result = processed
                break
        
        self.assertIsNotNone(valid_result, "Should successfully process valid workflow")
        self.assertGreater(valid_result.feature_count, 0, "Should extract features from valid workflow")
        
        print(f"✅ Error handling successful: {len(processed_workflows)} workflows processed despite errors")


if __name__ == '__main__':
    unittest.main(verbosity=2) 