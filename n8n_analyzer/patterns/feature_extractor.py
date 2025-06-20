"""
Feature Extraction Service for n8n Workflow Analysis

This module implements multi-level feature extraction from n8n workflows:
- Node-level features: type, parameters, complexity, position
- Connection-level features: patterns, sequences, fan-in/fan-out
- Workflow-level features: structure metrics, quality scores
"""

import logging
import hashlib
from typing import Dict, Any, List, Generator, Tuple, Set
from collections import Counter, defaultdict
import math

from ..core.models import N8nWorkflow, N8nNode, N8nConnection


# Configure logging
logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Multi-level feature extraction service for n8n workflows.
    
    This service implements the feature extraction algorithms defined in the
    creative phase decisions, extracting meaningful features at three levels:
    - Node level: Individual node characteristics
    - Connection level: Node interaction patterns
    - Workflow level: Overall workflow structure and quality
    """
    
    def __init__(self, cache_enabled: bool = True):
        """
        Initialize feature extractor with configuration.
        
        Args:
            cache_enabled: Whether to enable feature caching for performance
        """
        self.cache_enabled = cache_enabled
        self._feature_cache = {}
        
        # Configuration for feature extraction
        self.config = {
            'position_zones': 4,  # Number of position zones for spatial analysis
            'complexity_factors': {
                'parameter_weight': 1.0,
                'nesting_weight': 2.0,
                'connection_weight': 1.5
            },
            'pattern_min_length': 2,  # Minimum pattern length for connection analysis
            'quality_thresholds': {
                'high': 0.7,
                'medium': 0.4
            }
        }
        
        logger.info("FeatureExtractor initialized")
    
    def extract_node_features(self, workflow: N8nWorkflow) -> Generator[Dict[str, Any], None, None]:
        """
        Extract node-level features from workflow.
        
        Features extracted per node:
        - type: Primary node classification
        - param_count: Number of parameters
        - complexity: Calculated complexity score
        - position_zone: Spatial zone classification
        - parameter_signature: Hash of parameter structure
        
        Args:
            workflow: N8nWorkflow to analyze
            
        Yields:
            Dict[str, Any]: Node feature dictionary for each node
        """
        logger.debug(f"Extracting node features from workflow: {workflow.name}")
        
        # Calculate workflow bounds for position zones
        workflow_bounds = self._calculate_workflow_bounds(workflow)
        
        for node in workflow.nodes:
            try:
                features = {
                    'node_id': node.id,
                    'type': node.type,
                    'param_count': len(node.parameters),
                    'complexity': self._calculate_node_complexity(node),
                    'position_zone': self._get_position_zone(node.position, workflow_bounds),
                    'parameter_signature': self._create_parameter_signature(node.parameters),
                    'type_version': node.typeVersion,
                    'has_notes': bool(node.notes)
                }
                
                # Add parameter-specific features
                param_features = self._extract_parameter_features(node.parameters)
                features.update(param_features)
                
                yield features
                
            except Exception as e:
                logger.warning(f"Failed to extract features for node {node.id}: {str(e)}")
                continue
    
    def extract_connection_patterns(self, workflow: N8nWorkflow) -> List[str]:
        """
        Extract connection-level patterns from workflow.
        
        Patterns extracted:
        - Sequential patterns: A→B→C
        - Fan-out patterns: A→{B,C,D}
        - Fan-in patterns: {A,B,C}→D
        - Complex patterns: Multi-step sequences
        
        Args:
            workflow: N8nWorkflow to analyze
            
        Returns:
            List[str]: List of connection pattern strings
        """
        logger.debug(f"Extracting connection patterns from workflow: {workflow.name}")
        
        patterns = []
        
        try:
            # Build connection graph for pattern analysis
            connection_graph = self._build_connection_graph(workflow)
            
            # Extract sequential patterns
            sequential_patterns = self._extract_sequential_patterns(connection_graph, workflow)
            patterns.extend([f"seq:{pattern}" for pattern in sequential_patterns])
            
            # Extract fan patterns
            fan_patterns = self._extract_fan_patterns(connection_graph, workflow)
            patterns.extend([f"fan:{pattern}" for pattern in fan_patterns])
            
            # Extract complex patterns
            complex_patterns = self._extract_complex_patterns(connection_graph, workflow)
            patterns.extend([f"complex:{pattern}" for pattern in complex_patterns])
            
            # Add connection statistics as patterns
            conn_stats = self._get_connection_statistics(workflow)
            patterns.extend([f"stat:{k}:{v}" for k, v in conn_stats.items()])
            
        except Exception as e:
            logger.warning(f"Failed to extract connection patterns: {str(e)}")
        
        return patterns
    
    def extract_workflow_features(self, workflow: N8nWorkflow) -> Dict[str, Any]:
        """
        Extract workflow-level features.
        
        Features extracted:
        - Structure metrics: node count, density, depth, branching factor
        - Quality metrics: error handling coverage, validation score
        - Complexity metrics: overall workflow complexity
        - Type distribution: node type frequencies
        
        Args:
            workflow: N8nWorkflow to analyze
            
        Returns:
            Dict[str, Any]: Workflow-level features
        """
        logger.debug(f"Extracting workflow features from workflow: {workflow.name}")
        
        try:
            features = {
                # Basic structure metrics
                'node_count': len(workflow.nodes),
                'connection_count': len(workflow.connections),
                'unique_node_types': len(set(node.type for node in workflow.nodes)),
                
                # Calculated structure metrics
                'density': self._calculate_density(workflow),
                'max_depth': self._calculate_max_depth(workflow),
                'avg_degree': self._calculate_average_degree(workflow),
                'branching_factor': self._calculate_branching_factor(workflow),
                
                # Quality assessment
                'quality_score': self._assess_quality(workflow),
                'error_handling_coverage': self._assess_error_handling(workflow),
                'validation_score': self._assess_validation_quality(workflow),
                
                # Complexity metrics
                'overall_complexity': self._calculate_overall_complexity(workflow),
                'parameter_complexity': self._calculate_parameter_complexity(workflow),
                'structure_complexity': self._calculate_structure_complexity(workflow),
                
                # Type distribution
                'node_type_distribution': self._get_node_type_distribution(workflow),
                'dominant_node_type': self._get_dominant_node_type(workflow),
                'type_diversity': self._calculate_type_diversity(workflow)
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to extract workflow features: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_node_complexity(self, node: N8nNode) -> float:
        """Calculate complexity score for a node."""
        param_complexity = len(node.parameters) * self.config['complexity_factors']['parameter_weight']
        
        # Calculate parameter nesting complexity
        nesting_complexity = self._calculate_parameter_nesting(node.parameters)
        nesting_score = nesting_complexity * self.config['complexity_factors']['nesting_weight']
        
        return param_complexity + nesting_score
    
    def _calculate_parameter_nesting(self, parameters: Dict[str, Any]) -> int:
        """Calculate parameter nesting depth."""
        def get_nesting_depth(obj, current_depth=0):
            if isinstance(obj, dict):
                if not obj:
                    return current_depth
                return max(get_nesting_depth(v, current_depth + 1) for v in obj.values())
            elif isinstance(obj, list):
                if not obj:
                    return current_depth
                return max(get_nesting_depth(item, current_depth + 1) for item in obj)
            else:
                return current_depth
        
        return get_nesting_depth(parameters)
    
    def _get_position_zone(self, position: Tuple[int, int], workflow_bounds: Dict[str, int]) -> int:
        """Classify node position into spatial zones."""
        x, y = position
        
        # Normalize position to workflow bounds
        width = workflow_bounds['max_x'] - workflow_bounds['min_x'] or 1
        height = workflow_bounds['max_y'] - workflow_bounds['min_y'] or 1
        
        norm_x = (x - workflow_bounds['min_x']) / width
        norm_y = (y - workflow_bounds['min_y']) / height
        
        # Divide into quadrants (can be extended to more zones)
        if norm_x < 0.5 and norm_y < 0.5:
            return 0  # Top-left
        elif norm_x >= 0.5 and norm_y < 0.5:
            return 1  # Top-right
        elif norm_x < 0.5 and norm_y >= 0.5:
            return 2  # Bottom-left
        else:
            return 3  # Bottom-right
    
    def _calculate_workflow_bounds(self, workflow: N8nWorkflow) -> Dict[str, int]:
        """Calculate workflow spatial bounds."""
        if not workflow.nodes:
            return {'min_x': 0, 'max_x': 1, 'min_y': 0, 'max_y': 1}
        
        positions = [node.position for node in workflow.nodes]
        x_coords = [pos[0] for pos in positions]
        y_coords = [pos[1] for pos in positions]
        
        return {
            'min_x': min(x_coords),
            'max_x': max(x_coords),
            'min_y': min(y_coords),
            'max_y': max(y_coords)
        }
    
    def _create_parameter_signature(self, parameters: Dict[str, Any]) -> str:
        """Create hash signature of parameter structure."""
        # Create a structure signature (keys and types, not values)
        def get_structure(obj):
            if isinstance(obj, dict):
                return {k: get_structure(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [get_structure(item) for item in obj[:3]]  # Sample first 3 items
            else:
                return type(obj).__name__
        
        structure = get_structure(parameters)
        signature_str = str(sorted(str(structure).encode()))
        return hashlib.md5(signature_str.encode()).hexdigest()[:8]
    
    def _extract_parameter_features(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameter-specific features."""
        features = {}
        
        # Parameter type analysis
        param_types = []
        for value in parameters.values():
            param_types.append(type(value).__name__)
        
        type_counter = Counter(param_types)
        features['param_type_diversity'] = len(type_counter)
        features['dominant_param_type'] = type_counter.most_common(1)[0][0] if type_counter else 'none'
        
        # Boolean parameters count
        features['boolean_param_count'] = sum(1 for v in parameters.values() if isinstance(v, bool))
        
        # String parameters count
        features['string_param_count'] = sum(1 for v in parameters.values() if isinstance(v, str))
        
        return features
    
    def _build_connection_graph(self, workflow: N8nWorkflow) -> Dict[str, List[str]]:
        """Build connection graph for pattern analysis."""
        graph = defaultdict(list)
        
        for connection in workflow.connections:
            source_id = connection.source_node_id
            target_id = connection.target_node_id
            graph[source_id].append(target_id)
        
        return dict(graph)
    
    def _extract_sequential_patterns(self, graph: Dict[str, List[str]], workflow: N8nWorkflow) -> List[str]:
        """Extract sequential connection patterns."""
        patterns = []
        
        # Find chains of connections
        visited = set()
        
        for start_node in graph:
            if start_node in visited:
                continue
                
            # Find path from this node
            path = self._find_longest_path(graph, start_node, visited)
            
            if len(path) >= self.config['pattern_min_length']:
                # Convert node IDs to types for pattern
                node_types = []
                for node_id in path:
                    node_type = next((node.type for node in workflow.nodes if node.id == node_id), 'Unknown')
                    node_types.append(node_type)
                
                pattern = '→'.join(node_types)
                patterns.append(pattern)
        
        return patterns
    
    def _find_longest_path(self, graph: Dict[str, List[str]], start: str, visited: Set[str]) -> List[str]:
        """Find longest path from start node."""
        path = [start]
        visited.add(start)
        
        if start in graph:
            for neighbor in graph[start]:
                if neighbor not in visited:
                    sub_path = self._find_longest_path(graph, neighbor, visited.copy())
                    if len(sub_path) > 1:  # Found a continuation
                        path.extend(sub_path[1:])  # Skip the first node (duplicate)
                        break
        
        return path
    
    def _extract_fan_patterns(self, graph: Dict[str, List[str]], workflow: N8nWorkflow) -> List[str]:
        """Extract fan-out and fan-in patterns."""
        patterns = []
        
        # Fan-out patterns (one node connects to many)
        for node_id, targets in graph.items():
            if len(targets) > 2:  # Fan-out to 3+ nodes
                node_type = next((node.type for node in workflow.nodes if node.id == node_id), 'Unknown')
                target_types = []
                for target_id in targets:
                    target_type = next((node.type for node in workflow.nodes if node.id == target_id), 'Unknown')
                    target_types.append(target_type)
                
                pattern = f"{node_type}→{{{','.join(target_types)}}}"
                patterns.append(pattern)
        
        # Fan-in patterns (many nodes connect to one)
        target_counts = defaultdict(list)
        for source, targets in graph.items():
            for target in targets:
                target_counts[target].append(source)
        
        for target_id, sources in target_counts.items():
            if len(sources) > 2:  # Fan-in from 3+ nodes
                target_type = next((node.type for node in workflow.nodes if node.id == target_id), 'Unknown')
                source_types = []
                for source_id in sources:
                    source_type = next((node.type for node in workflow.nodes if node.id == source_id), 'Unknown')
                    source_types.append(source_type)
                
                pattern = f"{{{','.join(source_types)}}}→{target_type}"
                patterns.append(pattern)
        
        return patterns
    
    def _extract_complex_patterns(self, graph: Dict[str, List[str]], workflow: N8nWorkflow) -> List[str]:
        """Extract complex multi-step patterns."""
        patterns = []
        
        # Look for common integration patterns
        node_types = {node.id: node.type for node in workflow.nodes}
        
        # Webhook → Processing → Response pattern
        for node_id, targets in graph.items():
            node_type = node_types.get(node_id, '')
            
            if 'webhook' in node_type.lower():
                # Check for webhook → processing → response chains
                for target_id in targets:
                    target_type = node_types.get(target_id, '')
                    if target_id in graph:
                        for final_target_id in graph[target_id]:
                            final_type = node_types.get(final_target_id, '')
                            if 'respond' in final_type.lower() or 'return' in final_type.lower():
                                pattern = f"webhook-process-response:{node_type}→{target_type}→{final_type}"
                                patterns.append(pattern)
        
        return patterns
    
    def _get_connection_statistics(self, workflow: N8nWorkflow) -> Dict[str, Any]:
        """Get connection statistics as features."""
        if not workflow.connections:
            return {}
        
        # Calculate connection statistics
        connection_counts = defaultdict(int)
        for connection in workflow.connections:
            connection_counts[connection.source_node_id] += 1
        
        stats = {}
        if connection_counts:
            stats['max_fan_out'] = max(connection_counts.values())
            stats['avg_fan_out'] = sum(connection_counts.values()) / len(connection_counts)
        
        return stats
    
    def _calculate_density(self, workflow: N8nWorkflow) -> float:
        """Calculate workflow density (connections / possible connections)."""
        num_nodes = len(workflow.nodes)
        if num_nodes <= 1:
            return 0.0
        
        max_connections = num_nodes * (num_nodes - 1)
        actual_connections = len(workflow.connections)
        
        return actual_connections / max_connections if max_connections > 0 else 0.0
    
    def _calculate_max_depth(self, workflow: N8nWorkflow) -> int:
        """Calculate maximum depth of workflow."""
        graph = self._build_connection_graph(workflow)
        
        # Find all starting nodes (no incoming connections)
        all_targets = set()
        for targets in graph.values():
            all_targets.update(targets)
        
        start_nodes = [node_id for node_id in [node.id for node in workflow.nodes] 
                      if node_id not in all_targets]
        
        if not start_nodes:
            return 0
        
        max_depth = 0
        for start in start_nodes:
            depth = self._get_node_depth(graph, start, set())
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _get_node_depth(self, graph: Dict[str, List[str]], node: str, visited: Set[str]) -> int:
        """Calculate depth from a specific node."""
        if node in visited:
            return 0
        
        visited.add(node)
        
        if node not in graph:
            return 1
        
        max_child_depth = 0
        for child in graph[node]:
            child_depth = self._get_node_depth(graph, child, visited.copy())
            max_child_depth = max(max_child_depth, child_depth)
        
        return 1 + max_child_depth
    
    def _calculate_average_degree(self, workflow: N8nWorkflow) -> float:
        """Calculate average node degree."""
        if not workflow.nodes:
            return 0.0
        
        # Count connections per node
        degree_count = defaultdict(int)
        for connection in workflow.connections:
            degree_count[connection.source_node_id] += 1
            degree_count[connection.target_node_id] += 1
        
        total_degree = sum(degree_count.values())
        return total_degree / len(workflow.nodes)
    
    def _calculate_branching_factor(self, workflow: N8nWorkflow) -> float:
        """Calculate average branching factor."""
        graph = self._build_connection_graph(workflow)
        
        if not graph:
            return 0.0
        
        branching_factors = [len(targets) for targets in graph.values()]
        return sum(branching_factors) / len(branching_factors) if branching_factors else 0.0
    
    def _assess_quality(self, workflow: N8nWorkflow) -> float:
        """Assess overall workflow quality."""
        quality_score = 0.0
        max_score = 0.0
        
        # Factor 1: Error handling presence (0.3 weight)
        error_handling_score = self._assess_error_handling(workflow)
        quality_score += error_handling_score * 0.3
        max_score += 0.3
        
        # Factor 2: Node naming quality (0.2 weight)
        naming_score = self._assess_naming_quality(workflow)
        quality_score += naming_score * 0.2
        max_score += 0.2
        
        # Factor 3: Structure quality (0.3 weight)
        structure_score = self._assess_structure_quality(workflow)
        quality_score += structure_score * 0.3
        max_score += 0.3
        
        # Factor 4: Parameter completeness (0.2 weight)
        param_score = self._assess_parameter_completeness(workflow)
        quality_score += param_score * 0.2
        max_score += 0.2
        
        return quality_score / max_score if max_score > 0 else 0.0
    
    def _assess_error_handling(self, workflow: N8nWorkflow) -> float:
        """Assess error handling coverage."""
        total_nodes = len(workflow.nodes)
        if total_nodes == 0:
            return 0.0
        
        # Count nodes with error handling
        error_handling_nodes = 0
        for node in workflow.nodes:
            # Check if node has error handling configuration
            if 'onError' in node.parameters or 'continueOnFail' in node.parameters:
                error_handling_nodes += 1
            
            # Check for explicit error handling node types
            if 'error' in node.type.lower() or 'catch' in node.type.lower():
                error_handling_nodes += 1
        
        return error_handling_nodes / total_nodes
    
    def _assess_validation_quality(self, workflow: N8nWorkflow) -> float:
        """Assess validation quality."""
        # This is a placeholder for more sophisticated validation assessment
        # Could check for data validation nodes, schema validation, etc.
        validation_nodes = sum(1 for node in workflow.nodes 
                             if 'validate' in node.type.lower() or 'check' in node.type.lower())
        
        return min(validation_nodes / len(workflow.nodes), 1.0) if workflow.nodes else 0.0
    
    def _assess_naming_quality(self, workflow: N8nWorkflow) -> float:
        """Assess node naming quality."""
        if not workflow.nodes:
            return 0.0
        
        good_names = 0
        for node in workflow.nodes:
            # Consider name good if it's different from the default type name
            # and has reasonable length
            if (node.name != node.type and 
                len(node.name) > 3 and 
                not node.name.startswith('Node')):
                good_names += 1
        
        return good_names / len(workflow.nodes)
    
    def _assess_structure_quality(self, workflow: N8nWorkflow) -> float:
        """Assess workflow structure quality."""
        # Penalize overly complex or overly simple structures
        node_count = len(workflow.nodes)
        
        if node_count == 0:
            return 0.0
        elif node_count == 1:
            return 0.3  # Very simple
        elif 2 <= node_count <= 20:
            return 1.0  # Good complexity
        elif 21 <= node_count <= 50:
            return 0.7  # Getting complex
        else:
            return 0.4  # Very complex
    
    def _assess_parameter_completeness(self, workflow: N8nWorkflow) -> float:
        """Assess parameter completeness."""
        if not workflow.nodes:
            return 0.0
        
        nodes_with_params = sum(1 for node in workflow.nodes if node.parameters)
        return nodes_with_params / len(workflow.nodes)
    
    def _calculate_overall_complexity(self, workflow: N8nWorkflow) -> float:
        """Calculate overall workflow complexity."""
        if not workflow.nodes:
            return 0.0
        
        # Combine multiple complexity factors
        node_complexity = sum(self._calculate_node_complexity(node) for node in workflow.nodes)
        structure_complexity = self._calculate_structure_complexity(workflow)
        
        return (node_complexity + structure_complexity) / len(workflow.nodes)
    
    def _calculate_parameter_complexity(self, workflow: N8nWorkflow) -> float:
        """Calculate parameter complexity across workflow."""
        if not workflow.nodes:
            return 0.0
        
        total_params = sum(len(node.parameters) for node in workflow.nodes)
        total_nesting = sum(self._calculate_parameter_nesting(node.parameters) for node in workflow.nodes)
        
        return (total_params + total_nesting) / len(workflow.nodes)
    
    def _calculate_structure_complexity(self, workflow: N8nWorkflow) -> float:
        """Calculate structural complexity."""
        density = self._calculate_density(workflow)
        max_depth = self._calculate_max_depth(workflow)
        branching_factor = self._calculate_branching_factor(workflow)
        
        # Combine factors with weights
        return (density * 0.4 + (max_depth / 10) * 0.3 + (branching_factor / 5) * 0.3)
    
    def _get_node_type_distribution(self, workflow: N8nWorkflow) -> Dict[str, int]:
        """Get node type distribution."""
        type_counts = Counter(node.type for node in workflow.nodes)
        return dict(type_counts)
    
    def _get_dominant_node_type(self, workflow: N8nWorkflow) -> str:
        """Get most common node type."""
        if not workflow.nodes:
            return 'none'
        
        type_counts = Counter(node.type for node in workflow.nodes)
        return type_counts.most_common(1)[0][0]
    
    def _calculate_type_diversity(self, workflow: N8nWorkflow) -> float:
        """Calculate type diversity using Shannon entropy."""
        if not workflow.nodes:
            return 0.0
        
        type_counts = Counter(node.type for node in workflow.nodes)
        total_nodes = len(workflow.nodes)
        
        # Calculate Shannon entropy
        entropy = 0.0
        for count in type_counts.values():
            probability = count / total_nodes
            entropy -= probability * math.log2(probability)
        
        return entropy 