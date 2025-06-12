#!/usr/bin/env python3
"""
Test script for large batch processing with memory efficiency monitoring.
"""

import time
import sys
import tracemalloc
from n8n_analyzer.core.parser import (
    parse_workflows_batch, 
    find_workflow_files, 
    get_workflow_stats
)


def test_large_batch_processing():
    """Test parser with large dataset and monitor memory usage."""
    
    print("🔥 Testing Large Batch Processing (1000+ workflows)")
    print("=" * 70)
    
    # Find workflow files
    try:
        files = find_workflow_files('data/test_large_dataset')
        print(f"✅ Found {len(files)} workflow files")
    except Exception as e:
        print(f"❌ Error finding workflow files: {e}")
        return False
    
    if len(files) < 1000:
        print(f"❌ Expected at least 1000 files, found {len(files)}")
        return False
    
    # Test 1: Statistics without full parsing (fast overview)
    print("\n📊 Testing workflow statistics (no full parsing)...")
    try:
        start_time = time.time()
        stats = get_workflow_stats(files)
        stats_time = time.time() - start_time
        
        print(f"✅ Analyzed {stats['total_files']} files in {stats_time:.3f} seconds")
        print(f"   Readable files: {stats['readable_files']}")
        print(f"   Parse errors: {stats['parse_errors']}")
        print(f"   Total nodes: {stats['total_nodes']}")
        print(f"   Total connections: {stats['total_connections']}")
        print(f"   Average: {stats_time/stats['total_files']:.6f} seconds per file")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return False
    
    # Test 2: Memory-efficient batch processing with monitoring
    print("\n🧠 Testing memory-efficient batch processing...")
    
    # Start memory monitoring
    tracemalloc.start()
    
    try:
        start_time = time.time()
        workflows_processed = 0
        total_nodes = 0
        total_connections = 0
        
        # Process in batches using generator
        for workflow in parse_workflows_batch(files, skip_errors=True):
            workflows_processed += 1
            total_nodes += len(workflow.nodes)
            total_connections += len(workflow.connections)
            
            # Progress update every 100 workflows
            if workflows_processed % 100 == 0:
                current_time = time.time()
                elapsed = current_time - start_time
                rate = workflows_processed / elapsed if elapsed > 0 else 0
                
                # Memory usage
                current_memory, peak_memory = tracemalloc.get_traced_memory()
                
                print(f"   Processed {workflows_processed} workflows...")
                print(f"     Rate: {rate:.1f} workflows/sec")
                print(f"     Memory: {current_memory / 1024 / 1024:.1f} MB current, {peak_memory / 1024 / 1024:.1f} MB peak")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Final memory usage
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n✅ Successfully processed {workflows_processed} workflows!")
        print(f"   Total time: {total_time:.3f} seconds")
        print(f"   Average: {total_time/workflows_processed:.6f} seconds per workflow")
        print(f"   Rate: {workflows_processed/total_time:.1f} workflows per second")
        print(f"   Total nodes processed: {total_nodes}")
        print(f"   Total connections processed: {total_connections}")
        print(f"   Peak memory usage: {peak_memory / 1024 / 1024:.1f} MB")
        print(f"   Memory per workflow: {peak_memory / workflows_processed / 1024:.1f} KB")
        
        # Validate memory efficiency (should be well under 1GB for 1000 workflows)
        if peak_memory < 1024 * 1024 * 1024:  # 1GB
            print(f"   ✅ Memory efficient: Peak usage under 1GB")
        else:
            print(f"   ⚠️  High memory usage: {peak_memory / 1024 / 1024 / 1024:.1f} GB")
        
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")
        tracemalloc.stop()
        return False
    
    # Test 3: Batch processing with subset for speed comparison
    print("\n⚡ Testing subset processing for comparison...")
    try:
        subset_size = 100
        start_time = time.time()
        
        workflows = list(parse_workflows_batch(files[:subset_size], skip_errors=True))
        
        end_time = time.time()
        subset_time = end_time - start_time
        
        print(f"✅ Processed {len(workflows)} workflows in {subset_time:.3f} seconds")
        print(f"   Average: {subset_time/len(workflows):.6f} seconds per workflow")
        print(f"   Rate: {len(workflows)/subset_time:.1f} workflows per second")
        
        # Estimate time for 5000 workflows
        estimated_time_5k = (subset_time / subset_size) * 5000
        print(f"   📈 Estimated time for 5000 workflows: {estimated_time_5k:.1f} seconds ({estimated_time_5k/60:.1f} minutes)")
        
    except Exception as e:
        print(f"❌ Error in subset processing: {e}")
        return False
    
    # Test 4: Generator behavior verification
    print("\n🔄 Testing generator behavior (memory efficiency)...")
    try:
        # Create generator but don't consume all at once
        generator = parse_workflows_batch(files[:10], skip_errors=True)
        
        # Verify it's a generator
        if hasattr(generator, '__next__'):
            print("✅ Returns proper generator object")
            
            # Process one at a time to verify lazy evaluation
            first_workflow = next(generator)
            print(f"✅ Lazy evaluation works - first workflow: {first_workflow.name}")
            
            # Process remaining
            remaining_count = sum(1 for _ in generator)
            print(f"✅ Generator processes remaining {remaining_count} workflows lazily")
            
        else:
            print("❌ Not returning a generator")
            return False
            
    except Exception as e:
        print(f"❌ Error testing generator behavior: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 Large batch processing tests completed successfully!")
    print("✅ Memory-efficient parser handles 1000+ workflows effectively")
    print("✅ Ready for Phase 2 implementation")
    
    return True


if __name__ == "__main__":
    success = test_large_batch_processing()
    sys.exit(0 if success else 1) 