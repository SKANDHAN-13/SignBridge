#!/usr/bin/env python3
# tests/test_tts.py
"""
Test script to verify TTS (Text-To-Speech) functionality.
Calls speak() with three test sentences. Verifies audio plays without error.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import TTS module
from patient_to_doctor import tts_output

def test_tts():
    """Test TTS functionality"""
    print("[TEST] test_tts.py")
    print("="*50)

    # Test sentences
    test_sentences = [
        "Testing text to speech, sentence one.",
        "This is the second test sentence.",
        "Final test sentence, number three."
    ]

    print(f"Testing TTS with {len(test_sentences)} sentences...")

    try:
        for i, sentence in enumerate(test_sentences, 1):
            print(f"\n[{i}/{len(test_sentences)}] Speaking: \"{sentence}\"")
            tts_output.speak(sentence)
            print("✓ Completed")

        print("\nPASS")
        print("="*50)
        return True

    except Exception as e:
        print(f"\nFAIL: TTS error: {e}")
        print("="*50)
        return False

if __name__ == "__main__":
    success = test_tts()
    sys.exit(0 if success else 1)
