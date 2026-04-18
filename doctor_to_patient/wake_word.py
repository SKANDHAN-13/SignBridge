#!/usr/bin/env python3
# doctor_to_patient/wake_word.py
"""
MODULE 6 — Wake Word Detection
Always-on lightweight wake word detection.
Activates doctor mic when "SignBridge" is heard.
"""

import sys
import os
import time
import struct

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import state

# Try to import pvporcupine
try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    print("WARNING: pvporcupine not available, using Whisper fallback")

# Try to import Whisper for fallback
try:
    import whisper
    import sounddevice as sd
    import numpy as np
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Try to import pyaudio for porcupine
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


def wake_word_loop_porcupine():
    """Wake word detection using pvporcupine (preferred method)"""
    print("Starting wake word detection with Porcupine...")

    # Initialize porcupine
    porcupine = None
    pa = None
    audio_stream = None

    try:
        # Use built-in "computer" keyword as proxy for "SignBridge"
        # In production, you can create custom wake word at picovoice.ai
        porcupine = pvporcupine.create(
            access_key=config.PORCUPINE_ACCESS_KEY,
            keywords=["computer"]  # Using built-in keyword
        )

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print(f"Listening for wake word (say 'computer' as proxy for '{config.WAKE_WORD}')...")

        while state.state["system_active"]:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("WAKE WORD DETECTED")
                with state.state_lock:
                    state.state["mic_active"] = True

                # Wait for mic to be deactivated
                while state.state["mic_active"] and state.state["system_active"]:
                    time.sleep(0.1)

    except Exception as e:
        print(f"ERROR in Porcupine wake word detection: {e}")

    finally:
        if audio_stream:
            audio_stream.close()
        if pa:
            pa.terminate()
        if porcupine:
            porcupine.delete()


def wake_word_loop_whisper():
    """Wake word detection using Whisper fallback (slower but works without API key)"""
    print("Starting wake word detection with Whisper fallback...")

    # Load Whisper model (use tiny for speed)
    print("Loading Whisper tiny model for wake word detection...")
    model = whisper.load_model("tiny")

    print(f"Listening for wake word '{config.WAKE_WORD}' or stop word '{config.STOP_WORD}'...")

    while state.state["system_active"]:
        try:
            # Record 2-second audio chunk
            duration = 2
            audio = sd.rec(
                int(duration * config.SAMPLE_RATE),
                samplerate=config.SAMPLE_RATE,
                channels=1,
                dtype='float32'
            )
            sd.wait()

            # Flatten audio
            audio = audio.flatten()

            # Transcribe
            result = model.transcribe(audio, fp16=False)
            text = result["text"].strip().lower()

            if not text:
                continue

            # Check for wake word
            if config.WAKE_WORD.lower() in text or "signbridge" in text or "sign bridge" in text:
                print("WAKE WORD DETECTED")
                with state.state_lock:
                    state.state["mic_active"] = True

            # Check for stop word
            if state.state["mic_active"] and (config.STOP_WORD.lower() in text or "done" in text):
                print("MIC DEACTIVATED")
                with state.state_lock:
                    state.state["mic_active"] = False

        except Exception as e:
            print(f"ERROR in Whisper wake word detection: {e}")
            time.sleep(0.5)


def wake_word_loop():
    """
    Main wake word detection loop.
    Tries Porcupine first, falls back to Whisper if unavailable.
    """
    # Check if Porcupine is available and configured
    if PORCUPINE_AVAILABLE and PYAUDIO_AVAILABLE:
        if config.PORCUPINE_ACCESS_KEY != "YOUR_PORCUPINE_KEY":
            wake_word_loop_porcupine()
            return

    # Fall back to Whisper
    if WHISPER_AVAILABLE:
        wake_word_loop_whisper()
    else:
        print("ERROR: No wake word detection method available")
        print("Install pvporcupine or whisper: pip install pvporcupine openai-whisper")


def main():
    """Standalone test mode"""
    print("SignBridge Wake Word Detection Test")
    print("="*50)

    # Mock state for testing
    state.state["system_active"] = True
    state.state["mic_active"] = False

    try:
        wake_word_loop()
    except KeyboardInterrupt:
        print("\nStopped by user")
        state.state["system_active"] = False

    print("="*50)

if __name__ == "__main__":
    main()
