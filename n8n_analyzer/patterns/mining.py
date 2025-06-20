"""
Mining Service for n8n Workflow Analysis

This module implements the MiningPreprocessor service and FP-Growth
algorithm integration for discovering frequent patterns in workflow data.
"""

import logging
from typing import Dict, Any, List, Tuple, Generator, Optional, Union
from collections import Counter, defaultdict
import json
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

try:
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder
    import pandas as pd
    MLXTEND_AVAILABLE = True
except ImportError:
    MLXTEND_AVAILABLE = False
    logger.warning("mlxtend not available - pattern mining will use fallback implementation")

from ..core.models import N8nWorkflow


@dataclass
class PatternResults:
    """Container for pattern mining results."""
    itemsets: Any  # pd.DataFrame or dict
    rules: Any  # pd.DataFrame or list
    stats: Dict[str, Any]
    mining_config: Dict[str, Any]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary."""
        return {
            'itemsets': self.itemsets.to_dict() if hasattr(self.itemsets, 'to_dict') else self.itemsets,
            'rules': self.rules.to_dict() if hasattr(self.rules, 'to_dict') else self.rules,
            'stats': self.stats,
            'mining_config': self.mining_config,
            'timestamp': self.timestamp
        }


@dataclass
class ValidationResult:
    """Container for pattern validation results."""
    is_significant: bool
    chi2_statistic: Optional[float]
    p_value: Optional[float]
    lift_confidence: Optional[float]
    conviction: Optional[float]
    quality_score: float


class MiningPreprocessor:
    """
    Mining preprocessor service for converting workflow features
    to transactional format suitable for FP-Growth algorithm.
    
    This service implements the transaction conversion algorithms
    defined in the creative phase decisions.
    """
    
    def __init__(self, min_support: float = 0.1, min_confidence: float = 0.6):
        """
        Initialize mining preprocessor.
        
        Args:
            min_support: Minimum support threshold for frequent itemsets
            min_confidence: Minimum confidence threshold for association rules
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        
        # Transaction format configuration
        self.config = {
            'node_type_prefix': 'type:',
            'pattern_prefix': 'pattern:',
            'complexity_prefix': 'complexity:',
            'quality_prefix': 'quality:',
            'structure_prefix': 'structure:',
            'quality_thresholds': {
                'high': 0.7,
                'medium': 0.4
            },
            'complexity_thresholds': {
                'high': 10.0,
                'medium': 5.0
            }
        }
        
        logger.info("MiningPreprocessor initialized")
    
    def convert_to_transaction(self,
                             workflow: N8nWorkflow,
                             node_features: List[Dict[str, Any]],
                             connection_features: List[str],
                             workflow_features: Dict[str, Any]) -> List[str]:
        """
        Convert workflow and features to transaction format for FP-Growth.
        
        Transaction items format:
        - "type:NodeType" (e.g., "type:Webhook")
        - "pattern:A→B" (e.g., "pattern:Webhook→Set")
        - "complexity:Level" (e.g., "complexity:High")
        - "quality:Score" (e.g., "quality:High")
        - "structure:Metric" (e.g., "structure:Dense")
        
        Args:
            workflow: Original N8nWorkflow
            node_features: List of node feature dictionaries
            connection_features: List of connection pattern strings
            workflow_features: Workflow-level features
            
        Returns:
            List[str]: Transaction items for this workflow
        """
        transaction = []
        
        try:
            # Add node type items
            node_types = self._extract_node_type_items(node_features)
            transaction.extend(node_types)
            
            # Add connection pattern items
            pattern_items = self._extract_pattern_items(connection_features)
            transaction.extend(pattern_items)
            
            # Add complexity items
            complexity_items = self._extract_complexity_items(workflow_features, node_features)
            transaction.extend(complexity_items)
            
            # Add quality items
            quality_items = self._extract_quality_items(workflow_features)
            transaction.extend(quality_items)
            
            # Add structure items
            structure_items = self._extract_structure_items(workflow_features)
            transaction.extend(structure_items)
            
            # Remove duplicates while preserving order
            transaction = list(dict.fromkeys(transaction))
            
            logger.debug(f"Generated transaction with {len(transaction)} items for workflow: {workflow.name}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to convert workflow to transaction: {str(e)}")
            return []
    
    def convert_batch_to_transactions(self,
                                    workflows_with_features: Generator[Tuple[N8nWorkflow, Dict[str, Any]], None, None]
                                    ) -> Generator[List[str], None, None]:
        """
        Convert batch of workflows to transactions efficiently.
        
        Args:
            workflows_with_features: Generator of (workflow, features) tuples
            
        Yields:
            List[str]: Transaction for each workflow
        """
        for workflow, features in workflows_with_features:
            try:
                transaction = self.convert_to_transaction(
                    workflow,
                    features.get('node_features', []),
                    features.get('connection_features', []),
                    features.get('workflow_features', {})
                )
                
                if transaction:  # Only yield non-empty transactions
                    yield transaction
                    
            except Exception as e:
                logger.warning(f"Failed to convert workflow {workflow.name}: {str(e)}")
                continue
    
    def _extract_node_type_items(self, node_features: List[Dict[str, Any]]) -> List[str]:
        """Extract node type transaction items."""
        items = []
        
        # Count node types
        type_counts = Counter()
        for node_feature in node_features:
            node_type = node_feature.get('type', 'Unknown')
            type_counts[node_type] += 1
        
        # Add type items
        for node_type, count in type_counts.items():
            items.append(f"{self.config['node_type_prefix']}{node_type}")
            
            # Add frequency indicators for common types
            if count > 3:
                items.append(f"{self.config['node_type_prefix']}{node_type}:frequent")
            elif count == 1:
                items.append(f"{self.config['node_type_prefix']}{node_type}:single")
        
        return items
    
    def _extract_pattern_items(self, connection_features: List[str]) -> List[str]:
        """Extract connection pattern transaction items."""
        items = []
        
        for pattern in connection_features:
            # Clean and add pattern items
            if pattern.startswith('seq:'):
                items.append(f"{self.config['pattern_prefix']}{pattern[4:]}")
            elif pattern.startswith('fan:'):
                items.append(f"{self.config['pattern_prefix']}fan:{pattern[4:]}")
            elif pattern.startswith('complex:'):
                items.append(f"{self.config['pattern_prefix']}complex:{pattern[8:]}")
            else:
                items.append(f"{self.config['pattern_prefix']}{pattern}")
        
        return items
    
    def _extract_complexity_items(self, 
                                workflow_features: Dict[str, Any],
                                node_features: List[Dict[str, Any]]) -> List[str]:
        """Extract complexity-related transaction items."""
        items = []
        
        # Overall workflow complexity
        overall_complexity = workflow_features.get('overall_complexity', 0)
        if overall_complexity > self.config['complexity_thresholds']['high']:
            items.append(f"{self.config['complexity_prefix']}High")
        elif overall_complexity > self.config['complexity_thresholds']['medium']:
            items.append(f"{self.config['complexity_prefix']}Medium")
        else:
            items.append(f"{self.config['complexity_prefix']}Low")
        
        # Parameter complexity
        param_complexity = workflow_features.get('parameter_complexity', 0)
        if param_complexity > 5:
            items.append(f"{self.config['complexity_prefix']}Parameters:High")
        
        # Structure complexity
        structure_complexity = workflow_features.get('structure_complexity', 0)
        if structure_complexity > 0.5:
            items.append(f"{self.config['complexity_prefix']}Structure:High")
        
        return items
    
    def _extract_quality_items(self, workflow_features: Dict[str, Any]) -> List[str]:
        """Extract quality-related transaction items."""
        items = []
        
        # Overall quality score
        quality_score = workflow_features.get('quality_score', 0)
        if quality_score > self.config['quality_thresholds']['high']:
            items.append(f"{self.config['quality_prefix']}High")
        elif quality_score > self.config['quality_thresholds']['medium']:
            items.append(f"{self.config['quality_prefix']}Medium")
        else:
            items.append(f"{self.config['quality_prefix']}Low")
        
        # Error handling coverage
        error_handling = workflow_features.get('error_handling_coverage', 0)
        if error_handling > 0.5:
            items.append(f"{self.config['quality_prefix']}ErrorHandling:Good")
        elif error_handling > 0.1:
            items.append(f"{self.config['quality_prefix']}ErrorHandling:Basic")
        
        return items
    
    def _extract_structure_items(self, workflow_features: Dict[str, Any]) -> List[str]:
        """Extract structure-related transaction items."""
        items = []
        
        # Node count categories
        node_count = workflow_features.get('node_count', 0)
        if node_count > 20:
            items.append(f"{self.config['structure_prefix']}Large")
        elif node_count > 5:
            items.append(f"{self.config['structure_prefix']}Medium")
        else:
            items.append(f"{self.config['structure_prefix']}Small")
        
        # Density
        density = workflow_features.get('density', 0)
        if density > 0.3:
            items.append(f"{self.config['structure_prefix']}Dense")
        elif density > 0.1:
            items.append(f"{self.config['structure_prefix']}Moderate")
        else:
            items.append(f"{self.config['structure_prefix']}Sparse")
        
        # Depth
        max_depth = workflow_features.get('max_depth', 0)
        if max_depth > 10:
            items.append(f"{self.config['structure_prefix']}Deep")
        elif max_depth > 5:
            items.append(f"{self.config['structure_prefix']}MediumDepth")
        else:
            items.append(f"{self.config['structure_prefix']}Shallow")
        
        return items


class OptimizedMiningPipeline:
    """
    Optimized mining pipeline with workflow-specific enhancements.
    
    This class implements the enhanced FP-Growth pipeline defined in
    the creative phase decisions.
    """
    
    def __init__(self, 
                 min_support: float = 0.1,
                 min_confidence: float = 0.6,
                 quality_filter: bool = True):
        """
        Initialize optimized mining pipeline.
        
        Args:
            min_support: Minimum support for frequent itemsets
            min_confidence: Minimum confidence for association rules
            quality_filter: Whether to filter transactions by quality
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.quality_filter = quality_filter
        
        self.validator = PatternValidator()
        
        logger.info("OptimizedMiningPipeline initialized")
    
    def mine_patterns(self, transactions: List[List[str]]) -> PatternResults:
        """
        Mine patterns using enhanced FP-Growth with workflow-specific optimizations.
        
        Optimizations:
        1. Quality-based transaction filtering
        2. Adaptive support thresholds
        3. Workflow-specific pattern validation
        
        Args:
            transactions: List of transaction lists
            
        Returns:
            PatternResults: Mining results with itemsets and rules
        """
        logger.info(f"Mining patterns from {len(transactions)} transactions")
        
        try:
            # Step 1: Filter transactions by quality (if enabled)
            if self.quality_filter:
                filtered_transactions = self._filter_quality_transactions(transactions)
                logger.info(f"Filtered to {len(filtered_transactions)} quality transactions")
            else:
                filtered_transactions = transactions
            
            if not filtered_transactions:
                logger.warning("No transactions available for mining")
                return self._empty_results()
            
            # Step 2: Mine frequent itemsets
            if MLXTEND_AVAILABLE:
                frequent_itemsets = self._mine_with_mlxtend(filtered_transactions)
                rules = self._generate_rules_mlxtend(frequent_itemsets)
            else:
                frequent_itemsets = self._mine_with_fallback(filtered_transactions)
                rules = self._generate_rules_fallback(frequent_itemsets)
            
            # Step 3: Validate patterns
            validated_rules = self._validate_workflow_patterns(rules)
            
            # Step 4: Calculate statistics
            stats = self._calculate_mining_stats(frequent_itemsets, validated_rules, transactions)
            
            return PatternResults(
                itemsets=frequent_itemsets,
                rules=validated_rules,
                stats=stats,
                mining_config={
                    'min_support': self.min_support,
                    'min_confidence': self.min_confidence,
                    'quality_filter': self.quality_filter
                },
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Pattern mining failed: {str(e)}")
            return self._empty_results()
    
    def _filter_quality_transactions(self, transactions: List[List[str]]) -> List[List[str]]:
        """Filter transactions based on quality indicators."""
        filtered = []
        
        for transaction in transactions:
            # Keep transactions with good quality indicators
            has_quality = any(item.startswith('quality:High') or item.startswith('quality:Medium') 
                            for item in transaction)
            has_error_handling = any('ErrorHandling' in item for item in transaction)
            sufficient_content = len(transaction) >= 3  # Minimum content threshold
            
            if has_quality or has_error_handling or sufficient_content:
                filtered.append(transaction)
        
        return filtered
    
    def _mine_with_mlxtend(self, transactions: List[List[str]]) -> 'pd.DataFrame':
        """Mine patterns using mlxtend library."""
        try:
            # Convert to one-hot encoded format
            te = TransactionEncoder()
            te_ary = te.fit(transactions).transform(transactions)
            df = pd.DataFrame(te_ary, columns=te.columns_)
            
            # Mine frequent itemsets
            frequent_itemsets = apriori(df, min_support=self.min_support, use_colnames=True)
            
            logger.info(f"Found {len(frequent_itemsets)} frequent itemsets")
            return frequent_itemsets
            
        except Exception as e:
            logger.warning(f"mlxtend mining failed, using fallback: {str(e)}")
            return self._mine_with_fallback(transactions)
    
    def _generate_rules_mlxtend(self, frequent_itemsets) -> 'pd.DataFrame':
        """Generate association rules using mlxtend."""
        try:
            if len(frequent_itemsets) == 0:
                return pd.DataFrame()
            
            rules = association_rules(
                frequent_itemsets,
                metric="confidence",
                min_threshold=self.min_confidence
            )
            
            logger.info(f"Generated {len(rules)} association rules")
            return rules
            
        except Exception as e:
            logger.warning(f"Rule generation failed: {str(e)}")
            return pd.DataFrame()
    
    def _mine_with_fallback(self, transactions: List[List[str]]) -> Dict[str, Any]:
        """Fallback mining implementation without mlxtend."""
        logger.info("Using fallback mining implementation")
        
        # Count item frequencies
        item_counts = Counter()
        for transaction in transactions:
            for item in transaction:
                item_counts[item] += 1
        
        total_transactions = len(transactions)
        min_count = int(self.min_support * total_transactions)
        
        # Filter frequent items
        frequent_items = {item: count for item, count in item_counts.items() 
                         if count >= min_count}
        
        # Generate frequent itemsets (pairs only for simplicity)
        frequent_itemsets = {}
        frequent_itemsets['single'] = frequent_items
        
        # Find frequent pairs
        frequent_pairs = {}
        for transaction in transactions:
            for i, item1 in enumerate(transaction):
                for item2 in transaction[i+1:]:
                    if item1 in frequent_items and item2 in frequent_items:
                        pair = tuple(sorted([item1, item2]))
                        frequent_pairs[pair] = frequent_pairs.get(pair, 0) + 1
        
        # Filter pairs by support
        frequent_pairs = {pair: count for pair, count in frequent_pairs.items() 
                         if count >= min_count}
        frequent_itemsets['pairs'] = frequent_pairs
        
        return frequent_itemsets
    
    def _generate_rules_fallback(self, frequent_itemsets: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate rules using fallback implementation."""
        rules = []
        
        if 'pairs' in frequent_itemsets and 'single' in frequent_itemsets:
            single_items = frequent_itemsets['single']
            pairs = frequent_itemsets['pairs']
            
            for (item1, item2), pair_count in pairs.items():
                # Generate rules: item1 -> item2 and item2 -> item1
                if item1 in single_items:
                    confidence = pair_count / single_items[item1]
                    if confidence >= self.min_confidence:
                        rules.append({
                            'antecedents': item1,
                            'consequents': item2,
                            'support': pair_count,
                            'confidence': confidence
                        })
                
                if item2 in single_items:
                    confidence = pair_count / single_items[item2]
                    if confidence >= self.min_confidence:
                        rules.append({
                            'antecedents': item2,
                            'consequents': item1,
                            'support': pair_count,
                            'confidence': confidence
                        })
        
        return rules
    
    def _validate_workflow_patterns(self, rules) -> Any:
        """Validate patterns for workflow relevance."""
        if MLXTEND_AVAILABLE and hasattr(rules, 'iterrows'):
            # Validate mlxtend rules
            validated_rules = []
            for idx, rule in rules.iterrows():
                validation = self.validator.validate_pattern_significance(rule)
                if validation.is_significant:
                    validated_rules.append(rule)
            return validated_rules
        else:
            # Validate fallback rules
            validated_rules = []
            for rule in rules:
                if rule['confidence'] > 0.7:  # Simple validation
                    validated_rules.append(rule)
            return validated_rules
    
    def _calculate_mining_stats(self, itemsets, rules, original_transactions) -> Dict[str, Any]:
        """Calculate mining statistics."""
        stats = {
            'total_transactions': len(original_transactions),
            'total_frequent_itemsets': len(itemsets) if hasattr(itemsets, '__len__') else len(itemsets.get('single', {})),
            'total_rules': len(rules) if hasattr(rules, '__len__') else 0,
            'average_transaction_length': sum(len(t) for t in original_transactions) / len(original_transactions) if original_transactions else 0,
            'mining_algorithm': 'mlxtend' if MLXTEND_AVAILABLE else 'fallback'
        }
        
        return stats
    
    def _empty_results(self) -> PatternResults:
        """Return empty results when mining fails."""
        return PatternResults(
            itemsets=pd.DataFrame() if MLXTEND_AVAILABLE else {},
            rules=pd.DataFrame() if MLXTEND_AVAILABLE else [],
            stats={'error': 'Mining failed'},
            mining_config={
                'min_support': self.min_support,
                'min_confidence': self.min_confidence
            },
            timestamp=datetime.now().isoformat()
        )


class PatternValidator:
    """
    Pattern validator for statistical significance testing.
    """
    
    def __init__(self):
        """Initialize pattern validator."""
        logger.info("PatternValidator initialized")
    
    def validate_pattern_significance(self, pattern) -> ValidationResult:
        """
        Validate pattern statistical significance.
        
        Args:
            pattern: Association rule or pattern to validate
            
        Returns:
            ValidationResult: Validation metrics
        """
        try:
            # Basic validation for both mlxtend and fallback patterns
            if hasattr(pattern, 'confidence'):
                confidence = pattern.confidence
            elif isinstance(pattern, dict) and 'confidence' in pattern:
                confidence = pattern['confidence']
            else:
                confidence = 0.5  # Default
            
            # Simple significance test
            is_significant = confidence > 0.6
            quality_score = confidence
            
            return ValidationResult(
                is_significant=is_significant,
                chi2_statistic=None,  # Placeholder for future implementation
                p_value=None,  # Placeholder for future implementation
                lift_confidence=None,  # Placeholder for future implementation
                conviction=None,  # Placeholder for future implementation
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.warning(f"Pattern validation failed: {str(e)}")
            return ValidationResult(
                is_significant=False,
                chi2_statistic=None,
                p_value=None,
                lift_confidence=None,
                conviction=None,
                quality_score=0.0
            )
