#!/usr/bin/env python3
# doctor_to_patient/transcription.py
"""
MODULE 7 — Transcription
Transcribes doctor speech to text using Whisper when mic is active.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import state

try:
    import whisper
    import sounddevice as sd
    import numpy as np
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("ERROR: Whisper or sounddevice not available")
    print("Install with: pip install openai-whisper sounddevice")


def transcription_loop():
    """
    Main transcription loop.
    Monitors state["mic_active"] and transcribes audio when active.
    """
    if not WHISPER_AVAILABLE:
        print("ERROR: Cannot start transcription - dependencies missing")
        return

    # Load Whisper model once at startup
    print(f"Loading Whisper {config.WHISPER_MODEL_SIZE} model...")
    model = whisper.load_model(config.WHISPER_MODEL_SIZE)
    print("Whisper model loaded")

    print("Transcription loop started. Waiting for mic activation...")

    while state.state["system_active"]:
        # Wait for mic to be activated
        if not state.state["mic_active"]:
            time.sleep(0.1)
            continue

        print("Mic active - recording and transcribing...")

        # Record and transcribe while mic is active
        while state.state["mic_active"] and state.state["system_active"]:
            try:
                # Record 4-second audio chunk
                duration = 4
                audio = sd.rec(
                    int(duration * config.SAMPLE_RATE),
                    samplerate=config.SAMPLE_RATE,
                    channels=1,
                    dtype='float32'
                )
                sd.wait()

                # Flatten audio (sounddevice returns 2D array)
                audio = audio.flatten()

                # Transcribe with Whisper
                result = model.transcribe(audio, fp16=False)
                text = result["text"].strip()

                # Update state if we got meaningful text
                if text:
                    with state.state_lock:
                        # Append to existing transcript or start new
                        if state.state["doctor_transcript"]:
                            state.state["doctor_transcript"] += " " + text
                        else:
                            state.state["doctor_transcript"] = text

                    print(f"Transcribed: {text}")

                # Check for stop word
                if config.STOP_WORD.lower() in text.lower():
                    print(f"Stop word '{config.STOP_WORD}' detected")
                    with state.state_lock:
                        state.state["mic_active"] = False
                    break

            except Exception as e:
                print(f"ERROR during transcription: {e}")
                time.sleep(0.5)

        print("Mic deactivated")


def main():
    """Standalone test mode - activates immediately (skipping wake word)"""
    print("SignBridge Transcription Test")
    print("="*50)

    # Mock state for testing
    state.state["system_active"] = True
    state.state["mic_active"] = True  # Activate immediately for testing
    state.state["doctor_transcript"] = ""

    print("Transcription active - speak into microphone")
    print(f"Say '{config.STOP_WORD}' to stop, or press Ctrl+C")

    try:
        transcription_loop()
    except KeyboardInterrupt:
        print("\nStopped by user")
        state.state["system_active"] = False

    print("\nFinal transcript:")
    print(f'"{state.state["doctor_transcript"]}"')
    print("="*50)

if __name__ == "__main__":
    main()
