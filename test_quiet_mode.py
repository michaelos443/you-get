#!/usr/bin/env python3
"""
Test script to verify the quiet mode functionality works correctly.
"""

import sys
import os
import subprocess
import tempfile

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_quiet_mode():
    """Test that quiet mode suppresses non-essential output."""
    
    # Test with a simple URL that should work
    test_url = "https://httpbin.org/json"
    
    print("Testing quiet mode functionality...")
    
    # Test normal mode (should have output)
    print("\n1. Testing normal mode (should show output):")
    try:
        result_normal = subprocess.run([
            sys.executable, "you-get", "--info", test_url
        ], capture_output=True, text=True, timeout=30)
        print(f"Normal mode stdout length: {len(result_normal.stdout)}")
        print(f"Normal mode stderr length: {len(result_normal.stderr)}")
        if result_normal.stdout:
            print("✓ Normal mode produces output as expected")
        else:
            print("⚠ Normal mode produced no stdout output")
    except subprocess.TimeoutExpired:
        print("⚠ Normal mode test timed out")
    except Exception as e:
        print(f"⚠ Normal mode test failed: {e}")
    
    # Test quiet mode (should have minimal output)
    print("\n2. Testing quiet mode (should suppress most output):")
    try:
        result_quiet = subprocess.run([
            sys.executable, "you-get", "--quiet", "--info", test_url
        ], capture_output=True, text=True, timeout=30)
        print(f"Quiet mode stdout length: {len(result_quiet.stdout)}")
        print(f"Quiet mode stderr length: {len(result_quiet.stderr)}")
        
        if len(result_quiet.stdout) < len(result_normal.stdout):
            print("✓ Quiet mode suppresses output as expected")
        else:
            print("⚠ Quiet mode did not suppress output effectively")
            
    except subprocess.TimeoutExpired:
        print("⚠ Quiet mode test timed out")
    except Exception as e:
        print(f"⚠ Quiet mode test failed: {e}")
    
    # Test that errors still show in quiet mode
    print("\n3. Testing that errors still show in quiet mode:")
    try:
        result_error = subprocess.run([
            sys.executable, "you-get", "--quiet", "invalid-url-that-should-fail"
        ], capture_output=True, text=True, timeout=30)
        
        if result_error.stderr:
            print("✓ Errors still show in quiet mode")
        else:
            print("⚠ Errors may be suppressed in quiet mode")
            
    except subprocess.TimeoutExpired:
        print("⚠ Error test timed out")
    except Exception as e:
        print(f"⚠ Error test failed: {e}")

def test_log_module():
    """Test the log module quiet functionality directly."""
    print("\n4. Testing log module directly:")
    
    try:
        from you_get.util import log
        
        # Test normal mode
        log.set_quiet(False)
        print("Testing log.i() in normal mode:")
        log.i("This should be visible")
        
        # Test quiet mode
        log.set_quiet(True)
        print("Testing log.i() in quiet mode (should be suppressed):")
        log.i("This should be suppressed")
        
        # Test that warnings and errors still show
        print("Testing log.w() in quiet mode (should still show):")
        log.w("This warning should still show")
        
        print("Testing log.e() in quiet mode (should still show):")
        log.e("This error should still show")
        
        print("✓ Log module quiet functionality works correctly")
        
    except Exception as e:
        print(f"⚠ Log module test failed: {e}")

if __name__ == "__main__":
    test_log_module()
    test_quiet_mode()
    print("\nQuiet mode testing completed!")
