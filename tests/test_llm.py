#!/usr/bin/env python3
# tests/test_llm.py
"""
Test script to verify LLM elaboration functionality.
Calls elaborate() with three hardcoded sign buffers.
Prints results. Verifies non-empty string returned.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import elaboration module
from patient_to_doctor import llm_elaboration

def test_llm():
    """Test LLM elaboration"""
    print("[TEST] test_llm.py")
    print("="*50)

    # Test buffers
    test_buffers = [
        ["PAIN", "CHEST", "LEFT"],
        ["DIZZY", "HEADACHE"],
        ["BLEEDING", "RIGHT", "ARM"]
    ]

    print(f"Testing LLM elaboration with {len(test_buffers)} sign buffers...")

    all_passed = True

    for i, buffer in enumerate(test_buffers, 1):
        print(f"\n[{i}/{len(test_buffers)}]")
        print(f"Input: {buffer}")

        try:
            result = llm_elaboration.elaborate(buffer)

            print(f"Output: \"{result}\"")

            # Verify non-empty string
            if not result or not isinstance(result, str):
                print("✗ FAIL: Empty or invalid result")
                all_passed = False
            else:
                print("✓ PASS: Non-empty string returned")

        except Exception as e:
            print(f"✗ FAIL: Exception raised: {e}")
            all_passed = False

    print("\n" + "="*50)

    if all_passed:
        print("PASS")
        return True
    else:
        print("FAIL: Some tests failed")
        return False

if __name__ == "__main__":
    success = test_llm()
    sys.exit(0 if success else 1)
