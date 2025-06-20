"""
Preprocessing Pipeline for n8n Workflow Analysis

This module provides the main preprocessing pipeline that orchestrates
feature extraction, data staging, and mining preprocessing for workflow analysis.
"""

import logging
from typing import Generator, Dict, Any, Optional, List
from ..core.models import N8nWorkflow
from ..patterns.feature_extractor import FeatureExtractor
from ..patterns.data_staging import DataStaging
from ..patterns.mining import MiningPreprocessor


# Configure logging
logger = logging.getLogger(__name__)


class ProcessedWorkflow:
    """
    Container for processed workflow data including extracted features
    and preprocessed mining data.
    """
    def __init__(self, 
                 original_workflow: N8nWorkflow,
                 node_features: List[Dict[str, Any]],
                 connection_features: List[str],
                 workflow_features: Dict[str, Any],
                 mining_transaction: List[str]):
        self.original_workflow = original_workflow
        self.node_features = node_features
        self.connection_features = connection_features
        self.workflow_features = workflow_features
        self.mining_transaction = mining_transaction
        
    @property
    def workflow_id(self) -> str:
        """Get workflow identifier"""
        return self.original_workflow.id or self.original_workflow.name
        
    @property
    def feature_count(self) -> int:
        """Get total feature count"""
        return len(self.node_features) + len(self.connection_features) + len(self.workflow_features)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'workflow_id': self.workflow_id,
            'workflow_name': self.original_workflow.name,
            'node_features': self.node_features,
            'connection_features': self.connection_features,
            'workflow_features': self.workflow_features,
            'mining_transaction': self.mining_transaction,
            'feature_count': self.feature_count
        }


class PreprocessingPipeline:
    """
    Main orchestrator for preprocessing workflow data.
    
    This class coordinates feature extraction, data staging, and mining preprocessing
    using a modular service-based architecture with generator-based processing
    for memory efficiency.
    
    Architecture follows the Hybrid Service-Generator pattern:
    - Service classes for modularity and testability
    - Generator-based processing for memory efficiency
    - Dependency injection for flexibility
    """
    
    def __init__(self, 
                 feature_extractor: Optional[FeatureExtractor] = None,
                 data_staging: Optional[DataStaging] = None,
                 mining_preprocessor: Optional[MiningPreprocessor] = None):
        """
        Initialize preprocessing pipeline with service dependencies.
        
        Args:
            feature_extractor: Service for multi-level feature extraction
            data_staging: Service for efficient data storage and retrieval
            mining_preprocessor: Service for FP-Growth data preparation
        """
        # Dependency injection with default implementations
        self.feature_extractor = feature_extractor or FeatureExtractor()
        self.data_staging = data_staging or DataStaging()
        self.mining_preprocessor = mining_preprocessor or MiningPreprocessor()
        
        # Pipeline configuration
        self.config = {
            'batch_size': 100,  # Process workflows in batches
            'cache_features': True,  # Enable feature caching
            'validate_features': True,  # Enable feature validation
            'memory_limit': '2GB'  # Memory usage limit
        }
        
        logger.info("PreprocessingPipeline initialized with services")
    
    def preprocess_workflows(self, 
                           workflows: Generator[N8nWorkflow, None, None],
                           feature_levels: List[str] = None,
                           staging_strategy: str = 'memory_optimized',
                           mining_format: str = 'fp_growth'
                           ) -> Generator[ProcessedWorkflow, None, None]:
        """
        Main preprocessing pipeline that processes workflows through all stages.
        
        This is the primary interface for workflow preprocessing, implementing
        the generator-based processing pattern for memory efficiency.
        
        Args:
            workflows: Generator of N8nWorkflow objects to process
            feature_levels: List of feature levels to extract ['node', 'connection', 'workflow']
            staging_strategy: Data staging strategy ('memory_optimized', 'disk_based')
            mining_format: Output format for mining algorithms ('fp_growth', 'apriori')
            
        Yields:
            ProcessedWorkflow: Workflow with extracted features and mining data
            
        Raises:
            PreprocessingError: If preprocessing fails for a workflow
        """
        # Set default feature levels
        if feature_levels is None:
            feature_levels = ['node', 'connection', 'workflow']
            
        logger.info(f"Starting preprocessing pipeline with levels: {feature_levels}")
        
        # Process workflows using generator pattern
        for workflow in workflows:
            try:
                # Process single workflow through all stages
                processed = self._process_single_workflow(
                    workflow, feature_levels, staging_strategy, mining_format
                )
                
                # Validate processed workflow
                if self.config['validate_features']:
                    self._validate_processed_workflow(processed)
                
                logger.debug(f"Successfully processed workflow: {workflow.name}")
                yield processed
                
            except Exception as e:
                logger.error(f"Failed to process workflow {workflow.name}: {str(e)}")
                # Continue processing other workflows
                continue
    
    def _process_single_workflow(self,
                                workflow: N8nWorkflow,
                                feature_levels: List[str],
                                staging_strategy: str,
                                mining_format: str) -> ProcessedWorkflow:
        """
        Process a single workflow through all preprocessing stages.
        
        Args:
            workflow: N8nWorkflow to process
            feature_levels: Feature levels to extract
            staging_strategy: Data staging strategy
            mining_format: Mining format
            
        Returns:
            ProcessedWorkflow: Fully processed workflow
        """
        # Stage 1: Feature Extraction
        node_features = []
        connection_features = []
        workflow_features = {}
        
        if 'node' in feature_levels:
            node_features = list(self.feature_extractor.extract_node_features(workflow))
            
        if 'connection' in feature_levels:
            connection_features = self.feature_extractor.extract_connection_patterns(workflow)
            
        if 'workflow' in feature_levels:
            workflow_features = self.feature_extractor.extract_workflow_features(workflow)
        
        # Stage 2: Data Staging (if configured)
        if staging_strategy != 'none':
            staging_handle = self.data_staging.stage_features({
                'node_features': node_features,
                'connection_features': connection_features,
                'workflow_features': workflow_features
            })
            logger.debug(f"Features staged with handle: {staging_handle}")
        
        # Stage 3: Mining Preprocessing
        mining_transaction = self.mining_preprocessor.convert_to_transaction(
            workflow, node_features, connection_features, workflow_features
        )
        
        # Create processed workflow container
        processed = ProcessedWorkflow(
            original_workflow=workflow,
            node_features=node_features,
            connection_features=connection_features,
            workflow_features=workflow_features,
            mining_transaction=mining_transaction
        )
        
        return processed
    
    def _validate_processed_workflow(self, processed: ProcessedWorkflow) -> None:
        """
        Validate processed workflow data quality.
        
        Args:
            processed: ProcessedWorkflow to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # Basic validation checks
        if not processed.mining_transaction:
            raise ValueError(f"Empty mining transaction for workflow: {processed.workflow_id}")
            
        if processed.feature_count == 0:
            logger.warning(f"No features extracted for workflow: {processed.workflow_id}")
            
        # Validate feature data types
        if not isinstance(processed.node_features, list):
            raise TypeError("Node features must be a list")
            
        if not isinstance(processed.connection_features, list):
            raise TypeError("Connection features must be a list")
            
        if not isinstance(processed.workflow_features, dict):
            raise TypeError("Workflow features must be a dictionary")
    
    def preprocess_for_pattern_mining(self,
                                    workflows: Generator[N8nWorkflow, None, None],
                                    **kwargs) -> Generator[List[str], None, None]:
        """
        Simplified interface for pattern mining preprocessing.
        
        This method provides a streamlined interface that outputs only
        the transactional data needed for FP-Growth algorithm.
        
        Args:
            workflows: Generator of workflows to process
            **kwargs: Additional preprocessing parameters
            
        Yields:
            List[str]: Transaction data for each workflow
        """
        logger.info("Starting pattern mining preprocessing")
        
        for processed in self.preprocess_workflows(workflows, **kwargs):
            yield processed.mining_transaction
    
    def get_preprocessing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the preprocessing pipeline performance.
        
        Returns:
            Dict with preprocessing statistics
        """
        return {
            'pipeline_config': self.config,
            'feature_extractor_type': type(self.feature_extractor).__name__,
            'data_staging_type': type(self.data_staging).__name__,
            'mining_preprocessor_type': type(self.mining_preprocessor).__name__
        }


class PreprocessingError(Exception):
    """Custom exception for preprocessing pipeline errors."""
    def __init__(self, message: str, workflow_id: Optional[str] = None, stage: Optional[str] = None):
        self.workflow_id = workflow_id
        self.stage = stage
        
        error_msg = "Preprocessing error"
        if stage:
            error_msg += f" in stage '{stage}'"
        if workflow_id:
            error_msg += f" for workflow '{workflow_id}'"
        error_msg += f": {message}"
        
        super().__init__(error_msg) 