#!/usr/bin/env python3
# patient_to_doctor/llm_elaboration.py
"""
MODULE 4 — LLM Elaboration
Takes a buffer of detected signs and asks GPT-4o to form a coherent medical sentence.
Falls back to simple concatenation if offline or API fails.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("WARNING: OpenAI library not available, will use fallback mode")

# System prompt for medical interpretation
SYSTEM_PROMPT = """You are a medical interpreter assistant in an emergency room.
A deaf patient is communicating via ASL signs.
You receive a sequence of signed words and must construct a single
clear natural sentence that accurately represents what the patient
is trying to communicate.
Keep it to 1-2 sentences maximum.
Do not diagnose. Do not add information not implied by the signs.
Use calm clinical language appropriate for medical staff."""

# Global OpenAI client
openai_client = None


def init_openai():
    """Initialize OpenAI client"""
    global openai_client

    if not OPENAI_AVAILABLE:
        return False

    if config.OPENAI_API_KEY == "YOUR_OPENAI_KEY":
        print("WARNING: OpenAI API key not configured, using fallback mode")
        return False

    try:
        openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        return True
    except Exception as e:
        print(f"WARNING: OpenAI initialization failed: {e}")
        return False


def elaborate_with_gpt(sign_buffer):
    """
    Use GPT-4o to elaborate sign buffer into a coherent sentence.

    Args:
        sign_buffer (list[str]): List of detected signs

    Returns:
        str: Elaborated sentence or None if failed
    """
    global openai_client

    if openai_client is None:
        if not init_openai():
            return None

    try:
        # Create user message
        user_message = f"Signs: {', '.join(sign_buffer)}"

        # Call GPT-4o
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=80
        )

        # Extract response
        elaboration = response.choices[0].message.content.strip()
        return elaboration

    except Exception as e:
        print(f"WARNING: GPT-4o elaboration failed: {e}")
        return None


def fallback_elaboration(sign_buffer):
    """
    Simple fallback: concatenate signs into a sentence.

    Args:
        sign_buffer (list[str]): List of detected signs

    Returns:
        str: Simple concatenated sentence
    """
    signs_lower = [sign.lower() for sign in sign_buffer]
    return f"Patient signed: {' '.join(signs_lower)}"


def elaborate(sign_buffer):
    """
    Elaborate a buffer of signs into a coherent sentence.
    Uses GPT-4o if available, falls back to simple concatenation.

    Args:
        sign_buffer (list[str]): List of detected signs

    Returns:
        str: Elaborated sentence (never None, never raises exception)
    """
    if not sign_buffer:
        return ""

    # Try GPT-4o first
    result = elaborate_with_gpt(sign_buffer)

    if result:
        return result

    # Fall back to simple concatenation
    return fallback_elaboration(sign_buffer)


def main():
    """Standalone test mode - tests elaboration with hardcoded sign buffers"""
    print("SignBridge LLM Elaboration Test")
    print("="*50)

    # Initialize OpenAI
    if init_openai():
        print("OpenAI initialized successfully")
    else:
        print("Using fallback mode (simple concatenation)")

    # Test cases
    test_buffers = [
        ["PAIN", "CHEST", "LEFT"],
        ["DIZZY", "HEADACHE"],
        ["BLEEDING", "RIGHT", "ARM"],
        ["YES"],
        ["NO", "PAIN"]
    ]

    print(f"\nTesting {len(test_buffers)} sign buffers...\n")

    for i, buffer in enumerate(test_buffers, 1):
        print(f"[{i}/{len(test_buffers)}]")
        print(f"Input: {buffer}")

        result = elaborate(buffer)

        print(f"Output: \"{result}\"")
        print()

    print("="*50)
    print("LLM Elaboration Test Complete!")

if __name__ == "__main__":
    main()
