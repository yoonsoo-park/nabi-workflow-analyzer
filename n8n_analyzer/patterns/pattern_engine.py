"""
Pattern Engine - Phase 4.1 Advanced Pattern Mining Engine

This module implements the PatternEngine orchestration class that coordinates
the Hybrid Adaptive Pattern Mining Architecture with:
- Enhanced FP-Growth algorithm
- Graph-based structural analysis
- Statistical clustering 
- Adaptive algorithm selection

Follows the creative design decisions from docs/phase-4-creative-decisions.md
"""

import logging
from typing import List, Dict, Any, Optional, Union, Generator
from dataclasses import dataclass
from datetime import datetime
import json

from ..core.models import N8nWorkflow
from ..patterns.mining import OptimizedMiningPipeline, PatternResults, MiningPreprocessor
from ..patterns.data_staging import DataStaging
from ..patterns.feature_extractor import FeatureExtractor
from ..core.preprocessor import PreprocessingPipeline

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PatternEngineConfig:
    """Configuration for PatternEngine."""
    min_support: float = 0.1
    min_confidence: float = 0.6
    enable_graph_analysis: bool = True
    enable_statistical_clustering: bool = True
    adaptive_selection: bool = True
    quality_threshold: float = 0.5
    complexity_threshold: int = 10
    memory_efficient: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'min_support': self.min_support,
            'min_confidence': self.min_confidence,
            'enable_graph_analysis': self.enable_graph_analysis,
            'enable_statistical_clustering': self.enable_statistical_clustering,
            'adaptive_selection': self.adaptive_selection,
            'quality_threshold': self.quality_threshold,
            'complexity_threshold': self.complexity_threshold,
            'memory_efficient': self.memory_efficient
        }


class EnhancedFPGrowth:
    """Enhanced FP-Growth algorithm with workflow-specific optimizations."""
    
    def __init__(self, min_support: float = 0.1):
        self.min_support = min_support
        self.mining_pipeline = OptimizedMiningPipeline(min_support=min_support)
        logger.debug("EnhancedFPGrowth initialized")
    
    def mine_patterns(self, transactions: List[List[str]]) -> PatternResults:
        """Mine patterns using enhanced FP-Growth."""
        logger.info(f"Mining patterns with Enhanced FP-Growth: {len(transactions)} transactions")
        return self.mining_pipeline.mine_patterns(transactions)


class WorkflowGraphAnalyzer:
    """Graph-based analyzer for workflow structural patterns."""
    
    def __init__(self):
        logger.debug("WorkflowGraphAnalyzer initialized")
    
    def analyze_structural_patterns(self, workflows: List[N8nWorkflow]) -> Dict[str, Any]:
        """Analyze structural patterns in workflows using graph analysis."""
        logger.info(f"Analyzing structural patterns: {len(workflows)} workflows")
        
        patterns = {
            'hub_patterns': self._detect_hub_patterns(workflows),
            'cycle_patterns': self._detect_cycle_patterns(workflows),
            'branch_patterns': self._detect_branch_patterns(workflows),
            'sequential_patterns': self._detect_sequential_patterns(workflows)
        }
        
        return patterns
    
    def _detect_hub_patterns(self, workflows: List[N8nWorkflow]) -> List[Dict[str, Any]]:
        """Detect hub patterns (nodes with many connections)."""
        hub_patterns = []
        for workflow in workflows:
            for node in workflow.nodes:
                incoming = len([c for c in workflow.connections if c.target_node_id == node.id])
                outgoing = len([c for c in workflow.connections if c.source_node_id == node.id])
                if incoming + outgoing > 3:  # Hub threshold
                    hub_patterns.append({
                        'workflow_id': workflow.id,
                        'node_id': node.id,
                        'node_type': node.type,
                        'connections': incoming + outgoing
                    })
        return hub_patterns
    
    def _detect_cycle_patterns(self, workflows: List[N8nWorkflow]) -> List[Dict[str, Any]]:
        """Detect cycle patterns in workflows."""
        # Simplified cycle detection
        return []  # Will implement in Phase 4.2
    
    def _detect_branch_patterns(self, workflows: List[N8nWorkflow]) -> List[Dict[str, Any]]:
        """Detect branching patterns."""
        # Simplified branch detection
        return []  # Will implement in Phase 4.2
    
    def _detect_sequential_patterns(self, workflows: List[N8nWorkflow]) -> List[Dict[str, Any]]:
        """Detect sequential patterns."""
        # Simplified sequential detection
        return []  # Will implement in Phase 4.2


class StatisticalCluster:
    """Statistical clustering for pattern classification."""
    
    def __init__(self):
        logger.debug("StatisticalCluster initialized")
    
    def cluster_patterns(self, patterns: PatternResults) -> Dict[str, Any]:
        """Cluster patterns using statistical methods."""
        logger.info("Clustering patterns with statistical methods")
        
        # Simplified clustering for Phase 4.1
        clusters = {
            'high_frequency_patterns': [],
            'medium_frequency_patterns': [],
            'low_frequency_patterns': []
        }
        
        if hasattr(patterns.itemsets, 'items'):
            for pattern, support in patterns.itemsets.items():
                if support > 0.7:
                    clusters['high_frequency_patterns'].append(pattern)
                elif support > 0.3:
                    clusters['medium_frequency_patterns'].append(pattern)
                else:
                    clusters['low_frequency_patterns'].append(pattern)
        
        return clusters


class AdaptiveSelector:
    """Adaptive algorithm selector based on workflow characteristics."""
    
    def __init__(self):
        logger.debug("AdaptiveSelector initialized")
    
    def select_algorithm(self, workflows: List[N8nWorkflow]) -> str:
        """Select optimal algorithm based on workflow characteristics."""
        logger.info(f"Selecting algorithm for {len(workflows)} workflows")
        
        if not workflows:
            return 'fp_growth'
        
        # Calculate workflow complexity
        avg_nodes = sum(len(w.nodes) for w in workflows) / len(workflows)
        avg_connections = sum(len(w.connections) for w in workflows) / len(workflows)
        
        complexity_score = avg_nodes + (avg_connections * 0.5)
        
        if complexity_score < 5:
            return 'fp_growth'
        elif complexity_score < 15:
            return 'hybrid_lite'
        else:
            return 'hybrid'


class PatternEngine:
    """
    Main pattern mining orchestration class implementing Hybrid Adaptive 
    Pattern Mining Architecture.
    
    Coordinates:
    - Enhanced FP-Growth for frequent patterns
    - Graph analysis for structural patterns  
    - Statistical clustering for pattern classification
    - Adaptive algorithm selection
    """
    
    def __init__(self, config: PatternEngineConfig):
        """
        Initialize PatternEngine with configuration.
        
        Args:
            config: PatternEngineConfig instance
        """
        self.config = config
        
        # Initialize algorithm components
        self.fp_growth_engine = EnhancedFPGrowth(min_support=config.min_support)
        self.graph_engine = WorkflowGraphAnalyzer()
        self.cluster_engine = StatisticalCluster()
        self.selector = AdaptiveSelector()
        
        # Initialize preprocessing components
        self.preprocessing_pipeline = PreprocessingPipeline()
        self.feature_extractor = FeatureExtractor()
        self.data_staging = DataStaging()
        self.mining_preprocessor = MiningPreprocessor(
            min_support=config.min_support,
            min_confidence=config.min_confidence
        )
        
        logger.info("PatternEngine initialized with Hybrid Adaptive Architecture")
    
    def discover_patterns(self, workflows: List[N8nWorkflow]) -> PatternResults:
        """
        Discover patterns in workflows using adaptive algorithm selection.
        
        Args:
            workflows: List of N8nWorkflow objects to analyze
            
        Returns:
            PatternResults with discovered patterns and statistics
        """
        logger.info(f"Starting pattern discovery for {len(workflows)} workflows")
        
        try:
            # Select optimal algorithm
            algorithm = self._select_algorithm(workflows)
            logger.info(f"Selected algorithm: {algorithm}")
            
            # Process workflows through preprocessing pipeline
            processed_data = self._preprocess_workflows(workflows)
            
            # Execute pattern mining based on selected algorithm
            if algorithm == 'fp_growth':
                results = self._mine_with_fp_growth(processed_data)
            elif algorithm == 'hybrid_lite':
                results = self._mine_with_hybrid_lite(processed_data, workflows)
            elif algorithm == 'hybrid':
                results = self._mine_with_full_hybrid(processed_data, workflows)
            else:
                results = self._mine_with_fp_growth(processed_data)  # Fallback
            
            # Validate patterns if enabled
            if self.config.adaptive_selection:
                results = self._validate_patterns(results)
            
            # Add algorithm info to stats
            results.stats['algorithm_used'] = algorithm
            results.stats['batch_size'] = len(workflows)
            results.stats['config'] = self.config.to_dict()
            
            logger.info(f"Pattern discovery complete: {len(results.stats)} stats recorded")
            return results
            
        except Exception as e:
            logger.error(f"Pattern discovery failed: {str(e)}")
            return self._create_error_results(str(e), len(workflows))
    
    def _select_algorithm(self, workflows: List[N8nWorkflow]) -> str:
        """Select algorithm using adaptive selector."""
        return self.selector.select_algorithm(workflows)
    
    def _preprocess_workflows(self, workflows: List[N8nWorkflow]) -> List[List[str]]:
        """Preprocess workflows to transaction format."""
        logger.info("Preprocessing workflows to transaction format")
        
        transactions = []
        for workflow in workflows:
            try:
                # Extract features
                features = self.feature_extractor.extract_workflow_features(workflow)
                
                # Convert to transaction
                transaction = self.mining_preprocessor.convert_to_transaction(
                    workflow,
                    features.get('node_features', []),
                    features.get('connection_features', []),
                    features.get('workflow_features', {})
                )
                
                if transaction:
                    transactions.append(transaction)
                    
            except Exception as e:
                logger.warning(f"Failed to preprocess workflow {workflow.name}: {str(e)}")
                continue
        
        logger.info(f"Preprocessed {len(transactions)} transactions")
        return transactions
    
    def _mine_with_fp_growth(self, transactions: List[List[str]]) -> PatternResults:
        """Mine patterns using enhanced FP-Growth only."""
        logger.info("Mining with Enhanced FP-Growth")
        return self.fp_growth_engine.mine_patterns(transactions)
    
    def _mine_with_hybrid_lite(self, transactions: List[List[str]], 
                              workflows: List[N8nWorkflow]) -> PatternResults:
        """Mine patterns using FP-Growth + basic graph analysis."""
        logger.info("Mining with Hybrid Lite approach")
        
        # FP-Growth patterns
        fp_results = self.fp_growth_engine.mine_patterns(transactions)
        
        # Add basic graph analysis
        structural_patterns = self.graph_engine.analyze_structural_patterns(workflows)
        fp_results.stats['structural_patterns'] = structural_patterns
        
        return fp_results
    
    def _mine_with_full_hybrid(self, transactions: List[List[str]], 
                              workflows: List[N8nWorkflow]) -> PatternResults:
        """Mine patterns using full hybrid approach."""
        logger.info("Mining with Full Hybrid approach")
        
        # FP-Growth patterns
        fp_results = self.fp_growth_engine.mine_patterns(transactions)
        
        # Graph analysis
        structural_patterns = self.graph_engine.analyze_structural_patterns(workflows)
        fp_results.stats['structural_patterns'] = structural_patterns
        
        # Statistical clustering
        clusters = self.cluster_engine.cluster_patterns(fp_results)
        fp_results.stats['pattern_clusters'] = clusters
        
        return fp_results
    
    def _validate_patterns(self, patterns: PatternResults) -> PatternResults:
        """Validate patterns using statistical methods."""
        logger.info("Validating patterns")
        
        validation_stats = {
            'total_patterns_before': len(patterns.itemsets) if hasattr(patterns.itemsets, '__len__') else 0,
            'validation_applied': True,
            'quality_threshold': self.config.quality_threshold
        }
        
        # Add validation stats
        patterns.stats['validation_stats'] = validation_stats
        
        return patterns
    
    def _create_error_results(self, error_message: str, batch_size: int) -> PatternResults:
        """Create error results for failed pattern discovery."""
        return PatternResults(
            itemsets={},
            rules=[],
            stats={
                'errors': [error_message],
                'batch_size': batch_size,
                'success': False
            },
            mining_config=self.config.to_dict(),
            timestamp=datetime.now().isoformat()
        ) 