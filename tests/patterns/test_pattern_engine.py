"""
Test module for Pattern Engine - Phase 4.1 Advanced Pattern Mining Engine

Tests the PatternEngine orchestration class that implements the 
Hybrid Adaptive Pattern Mining Architecture with:
- Enhanced FP-Growth
- Graph-based structural analysis  
- Statistical clustering
- Adaptive algorithm selection
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection
from n8n_analyzer.patterns.pattern_engine import PatternEngine, PatternEngineConfig
from n8n_analyzer.patterns.mining import PatternResults


class TestPatternEngine(unittest.TestCase):
    """Test cases for PatternEngine orchestration class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PatternEngineConfig(
            min_support=0.1,
            min_confidence=0.6,
            enable_graph_analysis=True,
            enable_statistical_clustering=True,
            adaptive_selection=True
        )
        
        # Create test workflow
        self.test_workflow = N8nWorkflow(
            id="test_workflow_1",
            name="Test Workflow",
            nodes=[
                N8nNode(id="1", name="Webhook", type="n8n-nodes-base.webhook", 
                       typeVersion=1, position=(100, 100)),
                N8nNode(id="2", name="Set", type="n8n-nodes-base.set", 
                       typeVersion=1, position=(200, 100)),
                N8nNode(id="3", name="HTTP Request", type="n8n-nodes-base.httpRequest", 
                       typeVersion=1, position=(300, 100))
            ],
            connections=[
                N8nConnection(source_node_id="1", source_node_output_port="main",
                             target_node_id="2", target_node_input_port="main"),
                N8nConnection(source_node_id="2", source_node_output_port="main",
                             target_node_id="3", target_node_input_port="main")
            ]
        )
        
        self.pattern_engine = PatternEngine(self.config)
    
    def test_pattern_engine_initialization(self):
        """Test PatternEngine initialization."""
        self.assertIsInstance(self.pattern_engine, PatternEngine)
        self.assertEqual(self.pattern_engine.config, self.config)
        self.assertIsNotNone(self.pattern_engine.fp_growth_engine)
        self.assertIsNotNone(self.pattern_engine.graph_engine)
        self.assertIsNotNone(self.pattern_engine.cluster_engine)
        self.assertIsNotNone(self.pattern_engine.selector)
    
    def test_discover_patterns_single_workflow(self):
        """Test pattern discovery for single workflow."""
        # This test will fail initially - TDD approach
        results = self.pattern_engine.discover_patterns([self.test_workflow])
        
        self.assertIsInstance(results, PatternResults)
        self.assertIsNotNone(results.itemsets)
        self.assertIsNotNone(results.stats)
        self.assertGreater(len(results.stats), 0)
    
    def test_discover_patterns_batch(self):
        """Test pattern discovery for batch of workflows."""
        workflows = [self.test_workflow, self.test_workflow]  # Duplicate for testing
        
        results = self.pattern_engine.discover_patterns(workflows)
        
        self.assertIsInstance(results, PatternResults)
        self.assertIn('batch_size', results.stats)
        self.assertEqual(results.stats['batch_size'], 2)
    
    def test_adaptive_algorithm_selection(self):
        """Test adaptive algorithm selection based on workflow characteristics."""
        # Test with small workflow (should prefer FP-Growth)
        small_workflow = N8nWorkflow(
            id="small", name="Small", nodes=[], connections=[]
        )
        
        selected_algorithm = self.pattern_engine._select_algorithm([small_workflow])
        self.assertIn('fp_growth', selected_algorithm)
        
        # Test with complex workflow (should prefer hybrid approach)
        complex_nodes = [N8nNode(id=str(i), name=f"Node{i}", type="test", 
                                typeVersion=1, position=(i*10, 100)) for i in range(20)]
        complex_workflow = N8nWorkflow(
            id="complex", name="Complex", nodes=complex_nodes, connections=[]
        )
        
        selected_algorithm = self.pattern_engine._select_algorithm([complex_workflow])
        self.assertIn('hybrid', selected_algorithm)
    
    def test_statistical_validation_integration(self):
        """Test statistical validation integration."""
        # Mock pattern results
        mock_patterns = PatternResults(
            itemsets={"pattern1": 0.8, "pattern2": 0.3},
            rules=[],
            stats={"total_patterns": 2},
            mining_config={},
            timestamp="2024-12-20"
        )
        
        validated_results = self.pattern_engine._validate_patterns(mock_patterns)
        
        self.assertIsInstance(validated_results, PatternResults)
        self.assertIn('validation_stats', validated_results.stats)
        
    def test_memory_efficiency_large_batch(self):
        """Test memory efficiency with large batch processing."""
        # Create large batch simulation
        large_batch = [self.test_workflow for _ in range(100)]
        
        # Should not raise memory error
        results = self.pattern_engine.discover_patterns(large_batch)
        self.assertIsInstance(results, PatternResults)
        
    def test_error_handling_invalid_workflow(self):
        """Test error handling with invalid workflow data."""
        invalid_workflow = N8nWorkflow(id=None, name="", nodes=[], connections=[])
        
        results = self.pattern_engine.discover_patterns([invalid_workflow])
        
        # Should handle gracefully and still return valid results
        self.assertIsInstance(results, PatternResults)
        # Invalid workflows may still process successfully with empty patterns
        # The key is that it doesn't crash and returns a PatternResults object
        self.assertIn('batch_size', results.stats)
        self.assertEqual(results.stats['batch_size'], 1)


class TestPatternEngineConfig(unittest.TestCase):
    """Test cases for PatternEngine configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PatternEngineConfig()
        
        self.assertEqual(config.min_support, 0.1)
        self.assertEqual(config.min_confidence, 0.6)
        self.assertTrue(config.enable_graph_analysis)
        self.assertTrue(config.enable_statistical_clustering)
        self.assertTrue(config.adaptive_selection)
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = PatternEngineConfig(
            min_support=0.05,
            min_confidence=0.8,
            enable_graph_analysis=False
        )
        
        self.assertEqual(config.min_support, 0.05)
        self.assertEqual(config.min_confidence, 0.8)
        self.assertFalse(config.enable_graph_analysis)


if __name__ == '__main__':
    unittest.main() 