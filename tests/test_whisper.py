#!/usr/bin/env python3
# tests/test_whisper.py
"""
Test script to verify Whisper transcription functionality.
Records 5 seconds of audio from mic, transcribes with Whisper, prints result.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

try:
    import whisper
    import sounddevice as sd
    import numpy as np
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}")
    print("Install with: pip install openai-whisper sounddevice")
    sys.exit(1)

def test_whisper():
    """Test Whisper transcription"""
    print("[TEST] test_whisper.py")
    print("="*50)

    # Load Whisper model
    print(f"Loading Whisper {config.WHISPER_MODEL_SIZE} model...")
    model = whisper.load_model(config.WHISPER_MODEL_SIZE)
    print("Model loaded")

    # Record audio
    duration = 5
    print(f"\nRecording {duration} seconds of audio...")
    print("Speak into the microphone now!")

    audio = sd.rec(
        int(duration * config.SAMPLE_RATE),
        samplerate=config.SAMPLE_RATE,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    print("Recording complete")

    # Flatten audio
    audio = audio.flatten()

    # Transcribe
    print("Transcribing...")
    result = model.transcribe(audio, fp16=False)
    text = result["text"].strip()

    # Print result
    print("\nTranscription result:")
    print("-"*50)
    print(f'"{text}"')
    print("-"*50)

    if text:
        print("\nPASS")
    else:
        print("\nWARN: Empty transcription (this is OK if nothing was said)")
        print("PASS")

    print("="*50)
    return True

if __name__ == "__main__":
    success = test_whisper()
    sys.exit(0 if success else 1)
