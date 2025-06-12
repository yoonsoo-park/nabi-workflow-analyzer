#!/usr/bin/env python3
"""
Test script for the n8n workflow parser with real sample data.
"""

from n8n_analyzer.core.parser import (
    parse_workflows_batch, 
    find_workflow_files, 
    get_workflow_stats,
    parse_single_workflow
)
import time
import sys
from pathlib import Path


def test_parser_with_sample_data():
    """Test the parser with generated sample data."""
    
    print("🧪 Testing n8n Workflow Parser with Sample Data")
    print("=" * 60)
    
    # Find workflow files
    try:
        files = find_workflow_files('data/raw_workflows')
        print(f"✅ Found {len(files)} workflow files")
    except Exception as e:
        print(f"❌ Error finding workflow files: {e}")
        return False
    
    if not files:
        print("❌ No workflow files found. Run generate_sample_data.py first.")
        return False
    
    # Test statistics function
    print("\n📊 Testing workflow statistics...")
    try:
        stats = get_workflow_stats(files[:10])  # Test with first 10 files
        print(f"✅ Sample stats (first 10 files):")
        for key, value in stats.items():
            if key == 'workflow_names':
                print(f"   {key}: {len(value)} names")
            else:
                print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Error getting workflow stats: {e}")
        return False
    
    # Test single workflow parsing
    print("\n🔍 Testing single workflow parsing...")
    try:
        workflow = parse_single_workflow(files[0])
        print(f"✅ Successfully parsed single workflow:")
        print(f"   Name: {workflow.name}")
        print(f"   ID: {workflow.id}")
        print(f"   Active: {workflow.active}")
        print(f"   Nodes: {len(workflow.nodes)}")
        print(f"   Connections: {len(workflow.connections)}")
        print(f"   Tags: {workflow.tags}")
        
        # Test node access
        if workflow.nodes:
            first_node = workflow.nodes[0]
            print(f"   First node: {first_node.name} ({first_node.type})")
            
            # Test get_node_by_id method
            found_node = workflow.get_node_by_id(first_node.id)
            if found_node:
                print(f"   ✅ get_node_by_id works correctly")
            else:
                print(f"   ❌ get_node_by_id failed")
                
    except Exception as e:
        print(f"❌ Error parsing single workflow: {e}")
        return False
    
    # Test memory-efficient batch parsing
    print("\n⚡ Testing memory-efficient batch parsing...")
    try:
        start_time = time.time()
        workflows = list(parse_workflows_batch(files[:5], skip_errors=True))
        end_time = time.time()
        
        print(f"✅ Parsed {len(workflows)} workflows in {end_time - start_time:.3f} seconds")
        
        for i, wf in enumerate(workflows):
            complexity = wf.tags.get('complexity', 'unknown')
            category = wf.tags.get('category', 'unknown')
            print(f"   {i+1}. {wf.name}")
            print(f"      Complexity: {complexity}, Category: {category}")
            print(f"      Nodes: {len(wf.nodes)}, Connections: {len(wf.connections)}")
            
    except Exception as e:
        print(f"❌ Error in batch parsing: {e}")
        return False
    
    # Test generator behavior (memory efficiency)
    print("\n🔄 Testing generator behavior...")
    try:
        generator = parse_workflows_batch(files[:3], skip_errors=True)
        
        # Verify it's actually a generator
        if hasattr(generator, '__next__'):
            print("✅ Returns proper generator object")
            
            # Test lazy evaluation
            first_workflow = next(generator)
            print(f"✅ Lazy evaluation works - got first workflow: {first_workflow.name}")
            
            # Get remaining workflows
            remaining = list(generator)
            print(f"✅ Generator completed - total workflows processed: {len(remaining) + 1}")
        else:
            print("❌ Not returning a generator")
            return False
            
    except Exception as e:
        print(f"❌ Error testing generator behavior: {e}")
        return False
    
    # Test error handling
    print("\n🛡️ Testing error handling...")
    try:
        # Test with non-existent file
        error_files = ["non_existent.json"] + files[:2]
        workflows_with_errors = list(parse_workflows_batch(error_files, skip_errors=True))
        
        # Should skip the non-existent file and parse the valid ones
        if len(workflows_with_errors) == 2:
            print("✅ Error handling works - skipped invalid file, parsed valid ones")
        else:
            print(f"❌ Expected 2 workflows, got {len(workflows_with_errors)}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing error handling: {e}")
        return False
    
    # Performance test with larger dataset
    print("\n🚀 Performance test with larger dataset...")
    try:
        test_size = min(20, len(files))
        start_time = time.time()
        
        # Test batch processing
        workflows = list(parse_workflows_batch(files[:test_size], skip_errors=True))
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Processed {len(workflows)} workflows in {total_time:.3f} seconds")
        print(f"   Average: {total_time/len(workflows):.4f} seconds per workflow")
        
        # Calculate total nodes and connections
        total_nodes = sum(len(wf.nodes) for wf in workflows)
        total_connections = sum(len(wf.connections) for wf in workflows)
        
        print(f"   Total nodes parsed: {total_nodes}")
        print(f"   Total connections parsed: {total_connections}")
        
    except Exception as e:
        print(f"❌ Error in performance test: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All parser tests completed successfully!")
    print("✅ Memory-efficient JSON parser is working correctly")
    return True


if __name__ == "__main__":
    success = test_parser_with_sample_data()
    sys.exit(0 if success else 1) 