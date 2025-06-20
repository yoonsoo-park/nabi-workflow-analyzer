"""
n8n Workflow Analysis Engine

This module provides comprehensive analysis capabilities for n8n workflows,
including structure analysis, pattern detection, validation, and quality assessment.
"""

from typing import Dict, List, Any, Optional
from ..core.models import N8nWorkflow
from .node_analyzer import (
    calculate_node_type_distribution,
    extract_parameter_keys_for_node,
    extract_all_parameter_keys_by_type,
    get_nodes_with_specific_parameter,
    get_nodes_with_specific_parameter_value
)
from .connection_analyzer import (
    get_common_node_type_pairs,
    get_all_node_io_degrees,
    identify_trigger_nodes,
    identify_potential_terminal_nodes,
    get_sequential_patterns,
    analyze_workflow_paths,
    detect_common_integration_patterns,
    get_connection_statistics
)
from .workflow_metadata import (
    extract_basic_metadata,
    extract_node_types_summary,
    count_nodes_with_parameters,
    validate_workflow_structure,
    assess_workflow_quality,
    extract_workflow_signatures,
    compare_workflow_similarity
)
from .workflow_metrics import (
    count_nodes,
    count_connections,
    count_unique_node_types,
    calculate_workflow_density,
    average_parameters_per_node,
    count_complex_node_types,
    calculate_all_complexity_metrics
)
from .error_analyzer import (
    detect_potential_errors,
    analyze_error_patterns
)


class WorkflowAnalysisEngine:
    """
    Comprehensive workflow analysis engine that integrates all analysis capabilities.
    This is the main interface for Phase 2 workflow analysis functionality.
    """
    
    def __init__(self):
        """Initialize the analysis engine."""
        self.analysis_cache = {}
    
    def analyze_single_workflow(self, workflow: N8nWorkflow, 
                               include_patterns: bool = True,
                               include_validation: bool = True,
                               include_quality: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a single workflow.
        
        Args:
            workflow: The N8nWorkflow to analyze
            include_patterns: Whether to include pattern analysis
            include_validation: Whether to include validation
            include_quality: Whether to include quality assessment
        
        Returns:
            Dict containing comprehensive analysis results
        """
        analysis_result = {
            'workflow_info': {
                'name': workflow.name,
                'id': workflow.id,
                'file_path': workflow.file_path
            },
            'basic_metadata': extract_basic_metadata(workflow),
            'structure_analysis': self._analyze_structure(workflow),
            'complexity_metrics': calculate_all_complexity_metrics(workflow),
            'node_analysis': self._analyze_nodes(workflow),
            'connection_analysis': self._analyze_connections(workflow)
        }
        
        if include_patterns:
            analysis_result['pattern_analysis'] = self._analyze_patterns(workflow)
        
        if include_validation:
            analysis_result['validation'] = validate_workflow_structure(workflow).get_summary()
        
        if include_quality:
            analysis_result['quality_assessment'] = assess_workflow_quality(workflow)
        
        # Add error detection
        analysis_result['error_analysis'] = detect_potential_errors(workflow)
        
        return analysis_result
    
    def _analyze_structure(self, workflow: N8nWorkflow) -> Dict[str, Any]:
        """Analyze workflow structure."""
        return {
            'node_count': count_nodes(workflow),
            'connection_count': count_connections(workflow),
            'unique_node_types': count_unique_node_types(workflow),
            'density': calculate_workflow_density(workflow),
            'trigger_nodes': [node.id for node in identify_trigger_nodes(workflow)],
            'terminal_nodes': [node.id for node in identify_potential_terminal_nodes(workflow)],
            'node_degrees': get_all_node_io_degrees(workflow)
        }
    
    def _analyze_nodes(self, workflow: N8nWorkflow) -> Dict[str, Any]:
        """Analyze workflow nodes."""
        return {
            'node_type_distribution': calculate_node_type_distribution(workflow),
            'parameter_analysis': {
                'parameter_keys_by_type': extract_all_parameter_keys_by_type(workflow),
                'parameter_statistics': count_nodes_with_parameters(workflow),
                'avg_parameters_per_node': average_parameters_per_node(workflow)
            },
            'complex_node_count': count_complex_node_types(workflow),
            'node_types_summary': extract_node_types_summary(workflow)
        }
    
    def _analyze_connections(self, workflow: N8nWorkflow) -> Dict[str, Any]:
        """Analyze workflow connections."""
        return {
            'connection_statistics': get_connection_statistics(workflow),
            'common_node_pairs': get_common_node_type_pairs(workflow),
            'path_analysis': analyze_workflow_paths(workflow)
        }
    
    def _analyze_patterns(self, workflow: N8nWorkflow) -> Dict[str, Any]:
        """Analyze workflow patterns."""
        return {
            'sequential_patterns': get_sequential_patterns(workflow),
            'integration_patterns': detect_common_integration_patterns(workflow),
            'workflow_signature': extract_workflow_signatures(workflow)
        }
    
    def analyze_workflow_batch(self, workflows: List[N8nWorkflow], 
                              compare_similarities: bool = False) -> Dict[str, Any]:
        """
        Analyze a batch of workflows and provide aggregate insights.
        
        Args:
            workflows: List of N8nWorkflow objects to analyze
            compare_similarities: Whether to perform similarity analysis
        
        Returns:
            Dict containing batch analysis results
        """
        if not workflows:
            return {'error': 'No workflows provided for analysis'}
        
        # Analyze each workflow
        individual_analyses = []
        for workflow in workflows:
            try:
                analysis = self.analyze_single_workflow(workflow)
                individual_analyses.append(analysis)
            except Exception as e:
                individual_analyses.append({
                    'error': f"Failed to analyze workflow {workflow.name}: {str(e)}",
                    'workflow_info': {
                        'name': workflow.name,
                        'id': workflow.id,
                        'file_path': workflow.file_path
                    }
                })
        
        # Aggregate analysis
        batch_result = {
            'summary': {
                'total_workflows': len(workflows),
                'successfully_analyzed': len([a for a in individual_analyses if 'error' not in a]),
                'failed_analyses': len([a for a in individual_analyses if 'error' in a])
            },
            'aggregate_metrics': self._calculate_aggregate_metrics(individual_analyses),
            'individual_analyses': individual_analyses
        }
        
        if compare_similarities and len(workflows) > 1:
            batch_result['similarity_analysis'] = self._analyze_similarities(workflows)
        
        return batch_result
    
    def _calculate_aggregate_metrics(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate metrics from individual analyses."""
        successful_analyses = [a for a in analyses if 'error' not in a]
        
        if not successful_analyses:
            return {'error': 'No successful analyses to aggregate'}
        
        # Aggregate basic metrics
        total_nodes = sum(a['structure_analysis']['node_count'] for a in successful_analyses)
        total_connections = sum(a['structure_analysis']['connection_count'] for a in successful_analyses)
        
        # Aggregate node types
        all_node_types = {}
        for analysis in successful_analyses:
            for node_type, count in analysis['node_analysis']['node_types_summary'].items():
                all_node_types[node_type] = all_node_types.get(node_type, 0) + count
        
        # Quality score aggregation
        quality_scores = []
        for analysis in successful_analyses:
            if 'quality_assessment' in analysis:
                quality_scores.append(analysis['quality_assessment']['overall_quality_score'])
        
        return {
            'total_nodes_across_workflows': total_nodes,
            'total_connections_across_workflows': total_connections,
            'average_nodes_per_workflow': total_nodes / len(successful_analyses),
            'average_connections_per_workflow': total_connections / len(successful_analyses),
            'most_common_node_types': sorted(all_node_types.items(), key=lambda x: x[1], reverse=True)[:10],
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'quality_score_distribution': {
                'min': min(quality_scores) if quality_scores else 0,
                'max': max(quality_scores) if quality_scores else 0,
                'scores': quality_scores
            }
        }
    
    def _analyze_similarities(self, workflows: List[N8nWorkflow]) -> Dict[str, Any]:
        """Analyze similarities between workflows."""
        similarities = []
        
        for i, workflow1 in enumerate(workflows):
            for j, workflow2 in enumerate(workflows[i+1:], i+1):
                try:
                    similarity = compare_workflow_similarity(workflow1, workflow2)
                    similarities.append({
                        'workflow1': {'name': workflow1.name, 'id': workflow1.id},
                        'workflow2': {'name': workflow2.name, 'id': workflow2.id},
                        'similarity_scores': similarity
                    })
                except Exception as e:
                    similarities.append({
                        'workflow1': {'name': workflow1.name, 'id': workflow1.id},
                        'workflow2': {'name': workflow2.name, 'id': workflow2.id},
                        'error': f"Similarity analysis failed: {str(e)}"
                    })
        
        # Find most similar pairs
        valid_similarities = [s for s in similarities if 'error' not in s]
        if valid_similarities:
            most_similar = max(valid_similarities, 
                             key=lambda x: x['similarity_scores']['overall_similarity'])
            least_similar = min(valid_similarities, 
                              key=lambda x: x['similarity_scores']['overall_similarity'])
        else:
            most_similar = None
            least_similar = None
        
        return {
            'total_comparisons': len(similarities),
            'successful_comparisons': len(valid_similarities),
            'most_similar_pair': most_similar,
            'least_similar_pair': least_similar,
            'all_similarities': similarities
        }

# Convenience functions for direct access to analysis capabilities
def quick_workflow_analysis(workflow: N8nWorkflow) -> Dict[str, Any]:
    """
    Quick analysis of a single workflow with essential metrics.
    
    Args:
        workflow: The N8nWorkflow to analyze
    
    Returns:
        Dict containing essential analysis results
    """
    engine = WorkflowAnalysisEngine()
    return engine.analyze_single_workflow(workflow, 
                                        include_patterns=False, 
                                        include_validation=True, 
                                        include_quality=True)

def comprehensive_workflow_analysis(workflow: N8nWorkflow) -> Dict[str, Any]:
    """
    Comprehensive analysis of a single workflow with all features.
    
    Args:
        workflow: The N8nWorkflow to analyze
    
    Returns:
        Dict containing comprehensive analysis results
    """
    engine = WorkflowAnalysisEngine()
    return engine.analyze_single_workflow(workflow, 
                                        include_patterns=True, 
                                        include_validation=True, 
                                        include_quality=True)
