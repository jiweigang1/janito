#!/usr/bin/env python3
"""
Test to verify that the loop protection decorator returns errors properly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from janito.tools.loop_protection_decorator import protect_against_loops


class TestTool:
    """Test tool to verify error return behavior."""
    
    @protect_against_loops(max_calls=3, time_window=5.0)
    def run(self, path: str) -> str:
        """Test method that should return an error when loop protection is triggered."""
        return f"Processing {path}"


def test_error_return():
    """Test that the decorator raises RuntimeError when limits are exceeded."""
    tool = TestTool()
    
    print("Testing loop protection error return behavior:")
    print("=" * 50)
    
    try:
        # First two calls should work fine
        result1 = tool.run("file1.txt")
        print(f"Call 1: {result1}")
        
        result2 = tool.run("file2.txt")
        print(f"Call 2: {result2}")
        
        # Third call should still work (limit is 3)
        result3 = tool.run("file3.txt")
        print(f"Call 3: {result3}")
        
        # Fourth call should trigger loop protection
        print("\nAttempting call 4 (should trigger loop protection):")
        result4 = tool.run("file4.txt")
        print(f"Call 4: {result4}")
        print("ERROR: Loop protection did not trigger as expected!")
        
    except RuntimeError as e:
        print(f"SUCCESS: Loop protection triggered as expected: {e}")
        return True
    except Exception as e:
        print(f"ERROR: Unexpected exception: {e}")
        return False
    
    return False


if __name__ == "__main__":
    success = test_error_return()
    sys.exit(0 if success else 1)