# n8n_analyzer/core/analyzer.py
"""
Workflow Analysis Engine for n8n Workflow Analysis

This module provides the main WorkflowAnalysisEngine that integrates
the Phase 3 preprocessing pipeline with the existing analysis capabilities.
"""

import logging
from typing import List, Optional, Dict, Any, Generator
from n8n_analyzer.core.models import N8nWorkflow, N8nNode, N8nConnection
from n8n_analyzer.core.preprocessor import PreprocessingPipeline, ProcessedWorkflow
from n8n_analyzer.patterns.mining import OptimizedMiningPipeline, PatternResults


# Configure logging
logger = logging.getLogger(__name__)

def get_nodes_by_type(workflow: N8nWorkflow, node_type: str) -> List[N8nNode]:
    """Returns all nodes of a specific type from the workflow."""
    return [node for node in workflow.nodes if node.type == node_type]

def get_incoming_connections(workflow: N8nWorkflow, node_id: str) -> List[N8nConnection]:
    """Returns all connections targeting the specified node_id."""
    return [conn for conn in workflow.connections if conn.target_node_id == node_id]

def get_outgoing_connections(workflow: N8nWorkflow, source_node_id: str) -> List[N8nConnection]:
    """Returns all connections originating from the specified source_node_id."""
    return [conn for conn in workflow.connections if conn.source_node_id == source_node_id]

def get_node_by_id(workflow: N8nWorkflow, node_id: str) -> Optional[N8nNode]:
    """
    Retrieves a node by its ID from the workflow.
    This is a convenience wrapper around the N8nWorkflow.get_node_by_id method
    for use in analysis contexts where a standalone function might be preferred.
    """
    return workflow.get_node_by_id(node_id)

def get_source_node_from_connection(workflow: N8nWorkflow, connection: N8nConnection) -> Optional[N8nNode]:
    """Helper to get the actual source node object from a connection object."""
    return workflow.get_node_by_id(connection.source_node_id)

def get_target_node_from_connection(workflow: N8nWorkflow, connection: N8nConnection) -> Optional[N8nNode]:
    """Helper to get the actual target node object from a connection object."""
    return workflow.get_node_by_id(connection.target_node_id)

def get_dangling_nodes(
    workflow: N8nWorkflow,
    input_dangling_exclude_types: Optional[List[str]] = None,
    output_dangling_exclude_types: Optional[List[str]] = None
) -> Dict[str, List[N8nNode]]:
    """
    Identifies nodes with no incoming connections (excluding specified types like 'start' nodes)
    and nodes with no outgoing connections (excluding specified types).

    Args:
        workflow: The N8nWorkflow object to analyze.
        input_dangling_exclude_types: List of node types to exclude from input dangling check
                                      (e.g., trigger nodes). Defaults to common triggers.
        output_dangling_exclude_types: List of node types to exclude from output dangling check
                                       (e.g., terminal logging/response nodes). Defaults to common terminals.

    Returns:
        A dictionary with keys 'inputs_dangling' and 'outputs_dangling',
        each containing a list of N8nNode objects.
    """
    if input_dangling_exclude_types is None:
        input_dangling_exclude_types = [
            "n8n-nodes-base.start",
            "n8n-nodes-base.manualTrigger",
            "n8n-nodes-base.webhook",
            "n8n-nodes-base.cron",
            # Add other common trigger node types
        ]

    if output_dangling_exclude_types is None:
        output_dangling_exclude_types = [
            "n8n-nodes-base.logMessage",
            "n8n-nodes-base.respondToWebhook",
            # Add other common terminal/response node types
        ]

    inputs_dangling: List[N8nNode] = []
    outputs_dangling: List[N8nNode] = []

    all_target_node_ids = {conn.target_node_id for conn in workflow.connections}
    all_source_node_ids = {conn.source_node_id for conn in workflow.connections}

    for node in workflow.nodes:
        # Check for dangling inputs
        if node.id not in all_target_node_ids and node.type not in input_dangling_exclude_types:
            inputs_dangling.append(node)

        # Check for dangling outputs
        if node.id not in all_source_node_ids and node.type not in output_dangling_exclude_types:
            outputs_dangling.append(node)

    return {"inputs_dangling": inputs_dangling, "outputs_dangling": outputs_dangling}


class WorkflowAnalysisEngine:
    """
    Main workflow analysis engine that integrates Phase 3 preprocessing
    pipeline with existing analysis capabilities.
    
    This class provides the unified interface for workflow analysis,
    combining structural analysis, feature extraction, and pattern mining.
    """
    
    def __init__(self, 
                 enable_preprocessing: bool = True,
                 enable_pattern_mining: bool = True,
                 mining_min_support: float = 0.1,
                 mining_min_confidence: float = 0.6):
        """
        Initialize the workflow analysis engine.
        
        Args:
            enable_preprocessing: Whether to enable Phase 3 preprocessing pipeline
            enable_pattern_mining: Whether to enable pattern mining capabilities
            mining_min_support: Minimum support for pattern mining
            mining_min_confidence: Minimum confidence for pattern mining
        """
        self.enable_preprocessing = enable_preprocessing
        self.enable_pattern_mining = enable_pattern_mining
        
        # Initialize preprocessing pipeline if enabled
        if self.enable_preprocessing:
            self.preprocessing_pipeline = PreprocessingPipeline()
            logger.info("Preprocessing pipeline initialized")
        
        # Initialize mining pipeline if enabled
        if self.enable_pattern_mining:
            self.mining_pipeline = OptimizedMiningPipeline(
                min_support=mining_min_support,
                min_confidence=mining_min_confidence
            )
            logger.info("Pattern mining pipeline initialized")
        
        logger.info("WorkflowAnalysisEngine initialized")
    
    def analyze_workflow(self, workflow: N8nWorkflow, 
                        include_preprocessing: bool = True,
                        include_structural_analysis: bool = True) -> Dict[str, Any]:
        """
        Comprehensive workflow analysis combining all capabilities.
        
        Args:
            workflow: N8nWorkflow to analyze
            include_preprocessing: Whether to include Phase 3 preprocessing
            include_structural_analysis: Whether to include structural analysis
            
        Returns:
            Dict containing all analysis results
        """
        logger.info(f"Analyzing workflow: {workflow.name}")
        
        results = {
            'workflow_id': workflow.id or workflow.name,
            'workflow_name': workflow.name,
            'analysis_timestamp': logger.info.__module__,  # Will be updated
            'analysis_components': []
        }
        
        try:
            # Structural Analysis (existing functionality)
            if include_structural_analysis:
                structural_results = self._perform_structural_analysis(workflow)
                results['structural_analysis'] = structural_results
                results['analysis_components'].append('structural')
            
            # Phase 3 Preprocessing (new functionality)
            if include_preprocessing and self.enable_preprocessing:
                preprocessing_results = self._perform_preprocessing_analysis(workflow)
                results['preprocessing_analysis'] = preprocessing_results
                results['analysis_components'].append('preprocessing')
            
            logger.info(f"Workflow analysis complete: {workflow.name}")
            return results
            
        except Exception as e:
            logger.error(f"Workflow analysis failed for {workflow.name}: {str(e)}")
            results['error'] = str(e)
            return results
    
    def analyze_workflow_batch(self, 
                             workflows: Generator[N8nWorkflow, None, None],
                             include_pattern_mining: bool = True,
                             **kwargs) -> Dict[str, Any]:
        """
        Batch analysis of multiple workflows with pattern mining.
        
        Args:
            workflows: Generator of N8nWorkflow objects
            include_pattern_mining: Whether to perform pattern mining on the batch
            **kwargs: Additional analysis parameters
            
        Returns:
            Dict containing batch analysis results
        """
        logger.info("Starting batch workflow analysis")
        
        batch_results = {
            'total_workflows': 0,
            'successfully_analyzed': 0,
            'failed_analyses': 0,
            'individual_results': [],
            'batch_patterns': None,
            'batch_stats': {}
        }
        
        # Store transactions for pattern mining
        transactions = []
        
        try:
            for workflow in workflows:
                batch_results['total_workflows'] += 1
                
                try:
                    # Analyze individual workflow
                    workflow_result = self.analyze_workflow(workflow, **kwargs)
                    batch_results['individual_results'].append(workflow_result)
                    batch_results['successfully_analyzed'] += 1
                    
                    # Collect transactions for pattern mining
                    if (include_pattern_mining and 
                        self.enable_pattern_mining and 
                        'preprocessing_analysis' in workflow_result):
                        
                        preprocessing_data = workflow_result['preprocessing_analysis']
                        if 'mining_transaction' in preprocessing_data:
                            transactions.append(preprocessing_data['mining_transaction'])
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze workflow {workflow.name}: {str(e)}")
                    batch_results['failed_analyses'] += 1
                    continue
            
            # Perform batch pattern mining
            if include_pattern_mining and transactions and self.enable_pattern_mining:
                logger.info(f"Mining patterns from {len(transactions)} transactions")
                pattern_results = self.mining_pipeline.mine_patterns(transactions)
                batch_results['batch_patterns'] = pattern_results.to_dict()
            
            # Calculate batch statistics
            batch_results['batch_stats'] = self._calculate_batch_stats(batch_results)
            
            logger.info(f"Batch analysis complete: {batch_results['successfully_analyzed']}/{batch_results['total_workflows']} workflows")
            return batch_results
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {str(e)}")
            batch_results['error'] = str(e)
            return batch_results
    
    def preprocess_for_pattern_mining(self,
                                    workflows: Generator[N8nWorkflow, None, None],
                                    **kwargs) -> Generator[List[str], None, None]:
        """
        Simplified interface for pattern mining preprocessing.
        
        This method provides the interface defined in the creative phase decisions
        for seamless integration with existing WorkflowAnalysisEngine.
        
        Args:
            workflows: Generator of workflows to process
            **kwargs: Additional preprocessing parameters
            
        Yields:
            List[str]: Transaction data for each workflow
        """
        if not self.enable_preprocessing:
            logger.warning("Preprocessing not enabled - cannot perform pattern mining preprocessing")
            return
        
        logger.info("Starting pattern mining preprocessing")
        
        for transaction in self.preprocessing_pipeline.preprocess_for_pattern_mining(workflows, **kwargs):
            yield transaction
    
    def _perform_structural_analysis(self, workflow: N8nWorkflow) -> Dict[str, Any]:
        """Perform structural analysis using existing functions."""
        try:
            # Use existing analysis functions
            dangling_nodes = get_dangling_nodes(workflow)
            
            # Basic structural metrics
            structural_results = {
                'node_count': len(workflow.nodes),
                'connection_count': len(workflow.connections),
                'dangling_nodes': {
                    'inputs_dangling': [node.id for node in dangling_nodes['inputs_dangling']],
                    'outputs_dangling': [node.id for node in dangling_nodes['outputs_dangling']]
                },
                'node_types': list(set(node.type for node in workflow.nodes)),
                'unique_node_types_count': len(set(node.type for node in workflow.nodes))
            }
            
            return structural_results
            
        except Exception as e:
            logger.error(f"Structural analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _perform_preprocessing_analysis(self, workflow: N8nWorkflow) -> Dict[str, Any]:
        """Perform Phase 3 preprocessing analysis."""
        try:
            # Process single workflow through preprocessing pipeline
            processed_workflows = list(self.preprocessing_pipeline.preprocess_workflows([workflow]))
            
            if not processed_workflows:
                return {'error': 'No workflows processed'}
            
            processed = processed_workflows[0]
            
            # Convert ProcessedWorkflow to dictionary
            return {
                'workflow_id': processed.workflow_id,
                'feature_count': processed.feature_count,
                'node_features_count': len(processed.node_features),
                'connection_features_count': len(processed.connection_features),
                'workflow_features': processed.workflow_features,
                'mining_transaction': processed.mining_transaction,
                'mining_transaction_length': len(processed.mining_transaction)
            }
            
        except Exception as e:
            logger.error(f"Preprocessing analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_batch_stats(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics for batch analysis."""
        stats = {
            'success_rate': 0.0,
            'average_features_per_workflow': 0.0,
            'average_transaction_length': 0.0,
            'common_node_types': [],
            'total_patterns_found': 0
        }
        
        try:
            # Success rate
            if batch_results['total_workflows'] > 0:
                stats['success_rate'] = batch_results['successfully_analyzed'] / batch_results['total_workflows']
            
            # Feature statistics
            feature_counts = []
            transaction_lengths = []
            all_node_types = []
            
            for result in batch_results['individual_results']:
                if 'preprocessing_analysis' in result:
                    preprocessing_data = result['preprocessing_analysis']
                    
                    if 'feature_count' in preprocessing_data:
                        feature_counts.append(preprocessing_data['feature_count'])
                    
                    if 'mining_transaction_length' in preprocessing_data:
                        transaction_lengths.append(preprocessing_data['mining_transaction_length'])
                
                if 'structural_analysis' in result:
                    structural_data = result['structural_analysis']
                    if 'node_types' in structural_data:
                        all_node_types.extend(structural_data['node_types'])
            
            # Calculate averages
            if feature_counts:
                stats['average_features_per_workflow'] = sum(feature_counts) / len(feature_counts)
            
            if transaction_lengths:
                stats['average_transaction_length'] = sum(transaction_lengths) / len(transaction_lengths)
            
            # Common node types
            if all_node_types:
                from collections import Counter
                type_counts = Counter(all_node_types)
                stats['common_node_types'] = type_counts.most_common(5)
            
            # Pattern statistics
            if batch_results['batch_patterns'] and 'stats' in batch_results['batch_patterns']:
                pattern_stats = batch_results['batch_patterns']['stats']
                stats['total_patterns_found'] = pattern_stats.get('total_rules', 0)
            
        except Exception as e:
            logger.warning(f"Failed to calculate batch stats: {str(e)}")
            stats['calculation_error'] = str(e)
        
        return stats
    
    def get_analysis_capabilities(self) -> Dict[str, Any]:
        """
        Get information about analysis capabilities.
        
        Returns:
            Dict with capability information
        """
        return {
            'preprocessing_enabled': self.enable_preprocessing,
            'pattern_mining_enabled': self.enable_pattern_mining,
            'structural_analysis_enabled': True,
            'batch_analysis_enabled': True,
            'supported_analysis_types': [
                'structural_analysis',
                'preprocessing_analysis' if self.enable_preprocessing else None,
                'pattern_mining' if self.enable_pattern_mining else None
            ],
            'preprocessing_pipeline_stats': (
                self.preprocessing_pipeline.get_preprocessing_stats() 
                if self.enable_preprocessing else None
            )
        }
