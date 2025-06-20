"""
Data Staging Service for n8n Workflow Analysis

This module provides efficient intermediate data storage and retrieval
for the preprocessing pipeline, supporting memory-optimized processing
and batch operations for large-scale workflow analysis.
"""

import logging
import pickle
import json
import uuid
import tempfile
import os
from typing import Dict, Any, List, Optional, Generator, Union
from pathlib import Path
from datetime import datetime


# Configure logging
logger = logging.getLogger(__name__)


class StagingHandle:
    """
    Handle for staged data that provides access information and metadata.
    """
    def __init__(self, handle_id: str, storage_type: str, location: str, metadata: Dict[str, Any]):
        self.handle_id = handle_id
        self.storage_type = storage_type
        self.location = location
        self.metadata = metadata
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert handle to dictionary representation."""
        return {
            'handle_id': self.handle_id,
            'storage_type': self.storage_type,
            'location': self.location,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


class DataStaging:
    """
    Data staging service for efficient intermediate storage and retrieval.
    
    This service provides memory-optimized storage for preprocessed features
    and supports multiple storage strategies based on data size and access patterns.
    
    Storage strategies:
    - memory_optimized: In-memory storage with automatic disk overflow
    - disk_based: Direct disk storage for large datasets
    - hybrid: Intelligent switching between memory and disk
    """
    
    def __init__(self, 
                 storage_strategy: str = 'memory_optimized',
                 temp_dir: Optional[str] = None,
                 memory_limit: int = 1024 * 1024 * 100):  # 100MB default
        """
        Initialize data staging service.
        
        Args:
            storage_strategy: Storage strategy ('memory_optimized', 'disk_based', 'hybrid')
            temp_dir: Directory for temporary file storage
            memory_limit: Memory limit in bytes for memory_optimized strategy
        """
        self.storage_strategy = storage_strategy
        self.memory_limit = memory_limit
        
        # Setup temporary directory
        if temp_dir:
            self.temp_dir = Path(temp_dir)
            self.temp_dir.mkdir(exist_ok=True)
        else:
            self.temp_dir = Path(tempfile.gettempdir()) / 'n8n_analyzer_staging'
            self.temp_dir.mkdir(exist_ok=True)
        
        # Storage containers
        self._memory_storage: Dict[str, Any] = {}
        self._disk_storage: Dict[str, str] = {}  # handle_id -> file_path
        self._handle_registry: Dict[str, StagingHandle] = {}
        
        # Memory usage tracking
        self._memory_usage = 0
        
        logger.info(f"DataStaging initialized with strategy: {storage_strategy}")
    
    def stage_features(self, features: Dict[str, Any], 
                      handle_id: Optional[str] = None,
                      force_strategy: Optional[str] = None) -> StagingHandle:
        """
        Stage feature data for later retrieval.
        
        Args:
            features: Feature data to stage
            handle_id: Optional custom handle ID
            force_strategy: Force specific storage strategy
            
        Returns:
            StagingHandle: Handle for retrieving staged data
        """
        # Generate handle ID if not provided
        if not handle_id:
            handle_id = str(uuid.uuid4())
        
        # Determine storage strategy
        strategy = force_strategy or self._determine_storage_strategy(features)
        
        # Stage data based on strategy
        if strategy == 'memory':
            location = self._stage_to_memory(handle_id, features)
        else:  # disk
            location = self._stage_to_disk(handle_id, features)
        
        # Create handle
        metadata = {
            'data_size': self._estimate_data_size(features),
            'feature_types': list(features.keys()),
            'storage_strategy': strategy
        }
        
        handle = StagingHandle(handle_id, strategy, location, metadata)
        self._handle_registry[handle_id] = handle
        
        logger.debug(f"Staged features with handle: {handle_id} using {strategy} storage")
        return handle
    
    def retrieve_staged_data(self, handle: Union[StagingHandle, str]) -> Dict[str, Any]:
        """
        Retrieve staged feature data.
        
        Args:
            handle: StagingHandle or handle ID string
            
        Returns:
            Dict[str, Any]: Retrieved feature data
            
        Raises:
            KeyError: If handle not found
            FileNotFoundError: If disk file not found
        """
        # Get handle object
        if isinstance(handle, str):
            if handle not in self._handle_registry:
                raise KeyError(f"Handle not found: {handle}")
            handle = self._handle_registry[handle]
        
        # Retrieve data based on storage type
        if handle.storage_type == 'memory':
            return self._retrieve_from_memory(handle.handle_id)
        else:  # disk
            return self._retrieve_from_disk(handle.location)
    
    def stage_batch_features(self, 
                           feature_batch: Generator[Dict[str, Any], None, None],
                           batch_size: int = 100) -> List[StagingHandle]:
        """
        Stage a batch of feature data efficiently.
        
        Args:
            feature_batch: Generator of feature dictionaries
            batch_size: Number of features to batch together
            
        Returns:
            List[StagingHandle]: Handles for each staged batch
        """
        handles = []
        current_batch = []
        
        for features in feature_batch:
            current_batch.append(features)
            
            if len(current_batch) >= batch_size:
                # Stage current batch
                batch_data = {'batch': current_batch, 'size': len(current_batch)}
                handle = self.stage_features(batch_data)
                handles.append(handle)
                
                current_batch = []
        
        # Stage remaining features if any
        if current_batch:
            batch_data = {'batch': current_batch, 'size': len(current_batch)}
            handle = self.stage_features(batch_data)
            handles.append(handle)
        
        logger.info(f"Staged {len(handles)} batches of features")
        return handles
    
    def retrieve_batch_features(self, handles: List[StagingHandle]) -> Generator[Dict[str, Any], None, None]:
        """
        Retrieve batched feature data as a generator.
        
        Args:
            handles: List of batch handles
            
        Yields:
            Dict[str, Any]: Individual feature dictionaries
        """
        for handle in handles:
            try:
                batch_data = self.retrieve_staged_data(handle)
                
                # Yield individual features from batch
                for features in batch_data['batch']:
                    yield features
                    
            except Exception as e:
                logger.warning(f"Failed to retrieve batch {handle.handle_id}: {str(e)}")
                continue
    
    def cleanup_staging(self, handle: Union[StagingHandle, str, None] = None) -> None:
        """
        Clean up staged data.
        
        Args:
            handle: Specific handle to clean up, or None to clean up all
        """
        if handle is None:
            # Clean up all staged data
            for handle_id in list(self._handle_registry.keys()):
                self._cleanup_single_handle(handle_id)
        else:
            # Clean up specific handle
            if isinstance(handle, StagingHandle):
                handle_id = handle.handle_id
            else:
                handle_id = handle
            
            self._cleanup_single_handle(handle_id)
    
    def get_staging_stats(self) -> Dict[str, Any]:
        """
        Get statistics about staged data.
        
        Returns:
            Dict with staging statistics
        """
        memory_handles = sum(1 for h in self._handle_registry.values() if h.storage_type == 'memory')
        disk_handles = sum(1 for h in self._handle_registry.values() if h.storage_type == 'disk')
        
        return {
            'total_handles': len(self._handle_registry),
            'memory_handles': memory_handles,
            'disk_handles': disk_handles,
            'memory_usage_bytes': self._memory_usage,
            'storage_strategy': self.storage_strategy,
            'temp_dir': str(self.temp_dir)
        }
    
    def _determine_storage_strategy(self, features: Dict[str, Any]) -> str:
        """Determine optimal storage strategy for given features."""
        data_size = self._estimate_data_size(features)
        
        if self.storage_strategy == 'memory_optimized':
            # Use memory if under limit and space available
            if data_size < self.memory_limit and (self._memory_usage + data_size) < self.memory_limit:
                return 'memory'
            else:
                return 'disk'
        
        elif self.storage_strategy == 'disk_based':
            return 'disk'
        
        elif self.storage_strategy == 'hybrid':
            # Intelligent decision based on data characteristics
            if data_size < 1024 * 10:  # < 10KB, use memory
                return 'memory'
            else:
                return 'disk'
        
        else:
            return 'disk'  # Default fallback
    
    def _stage_to_memory(self, handle_id: str, features: Dict[str, Any]) -> str:
        """Stage data to memory storage."""
        self._memory_storage[handle_id] = features
        
        # Update memory usage
        data_size = self._estimate_data_size(features)
        self._memory_usage += data_size
        
        return f"memory://{handle_id}"
    
    def _stage_to_disk(self, handle_id: str, features: Dict[str, Any]) -> str:
        """Stage data to disk storage."""
        file_path = self.temp_dir / f"staging_{handle_id}.pkl"
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(features, f)
            
            self._disk_storage[handle_id] = str(file_path)
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to stage data to disk: {str(e)}")
            raise
    
    def _retrieve_from_memory(self, handle_id: str) -> Dict[str, Any]:
        """Retrieve data from memory storage."""
        if handle_id not in self._memory_storage:
            raise KeyError(f"Data not found in memory: {handle_id}")
        
        return self._memory_storage[handle_id]
    
    def _retrieve_from_disk(self, file_path: str) -> Dict[str, Any]:
        """Retrieve data from disk storage."""
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Staged file not found: {file_path}")
        except Exception as e:
            logger.error(f"Failed to retrieve data from disk: {str(e)}")
            raise
    
    def _estimate_data_size(self, data: Any) -> int:
        """Estimate data size in bytes."""
        try:
            # Use pickle to estimate size
            return len(pickle.dumps(data))
        except Exception:
            # Fallback estimation
            return len(str(data).encode('utf-8'))
    
    def _cleanup_single_handle(self, handle_id: str) -> None:
        """Clean up a single handle."""
        if handle_id not in self._handle_registry:
            return
        
        handle = self._handle_registry[handle_id]
        
        try:
            if handle.storage_type == 'memory':
                # Remove from memory
                if handle_id in self._memory_storage:
                    data_size = self._estimate_data_size(self._memory_storage[handle_id])
                    del self._memory_storage[handle_id]
                    self._memory_usage -= data_size
            
            else:  # disk
                # Remove file
                if handle_id in self._disk_storage:
                    file_path = self._disk_storage[handle_id]
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    del self._disk_storage[handle_id]
            
            # Remove handle
            del self._handle_registry[handle_id]
            
            logger.debug(f"Cleaned up staging handle: {handle_id}")
            
        except Exception as e:
            logger.warning(f"Error cleaning up handle {handle_id}: {str(e)}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.cleanup_staging()
        except Exception:
            pass  # Ignore cleanup errors during destruction 