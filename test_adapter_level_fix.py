#!/usr/bin/env python3
"""
Test script to verify the adapter-level argument normalization fix.
"""

import os
import tempfile
from janito.tools.adapters.local.read_files import ReadFilesTool
from janito.tools.tools_adapter import ToolsAdapterBase


def test_adapter_level_fix():
    """Test the adapter-level argument normalization."""
    
    # Create test files
    test_file1 = "test1.txt"
    test_file2 = "test2.txt"
    
    try:
        with open(test_file1, 'w') as f:
            f.write("Content of test1.txt")
        with open(test_file2, 'w') as f:
            f.write("Content of test2.txt")
        
        print("Created test files: test1.txt, test2.txt")
        
        # Create adapter
        adapter = ToolsAdapterBase()
        adapter.add_tool(ReadFilesTool)
        
        # Test with string input through adapter
        print("\nTesting string input through adapter...")
        try:
            result = adapter.execute_by_name("read_files", arguments="test1.txt")
            print("✅ Success with string through adapter:")
            print(result)
        except Exception as e:
            print(f"❌ Error with string through adapter: {e}")
            import traceback
            traceback.print_exc()
        
        # Test with list input through adapter
        print("\nTesting list input through adapter...")
        try:
            result = adapter.execute_by_name("read_files", arguments=["test1.txt", "test2.txt"])
            print("✅ Success with list through adapter:")
            print(result)
        except Exception as e:
            print(f"❌ Error with list through adapter: {e}")
            import traceback
            traceback.print_exc()
            
    finally:
        # Clean up
        for f in [test_file1, test_file2]:
            if os.path.exists(f):
                os.remove(f)


if __name__ == "__main__":
    test_adapter_level_fix()