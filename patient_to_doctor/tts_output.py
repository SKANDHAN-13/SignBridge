#!/usr/bin/env python3
# patient_to_doctor/tts_output.py
"""
MODULE 5 — TTS Output
Speaks text aloud through speaker or headphones.
Uses ElevenLabs if online, falls back to espeak-ng if offline.
"""

import subprocess
import sys
import os
import tempfile
import socket

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Initialize pygame for audio playback
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("WARNING: pygame not available, will use subprocess for all TTS")

# Try to import ElevenLabs
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import save
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

# Global TTS mode
TTS_MODE = None
elevenlabs_client = None


def check_internet():
    """Check if internet connection is available"""
    try:
        # Try to connect to Google DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


def init_tts():
    """Initialize TTS system and determine mode"""
    global TTS_MODE, elevenlabs_client

    # Check if we should use ElevenLabs
    if ELEVENLABS_AVAILABLE and config.ELEVENLABS_API_KEY != "YOUR_ELEVENLABS_KEY":
        if check_internet():
            try:
                elevenlabs_client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
                TTS_MODE = "elevenlabs"
                print("TTS: ElevenLabs (online)")
                return
            except Exception as e:
                print(f"WARNING: ElevenLabs initialization failed: {e}")

    # Fall back to espeak-ng
    TTS_MODE = "espeak"
    print("TTS: espeak-ng (offline)")


def speak_with_elevenlabs(text):
    """Speak using ElevenLabs API"""
    try:
        # Generate audio
        audio = elevenlabs_client.generate(
            text=text,
            voice=config.ELEVENLABS_VOICE,
            model="eleven_monolingual_v1"
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            temp_file = f.name
            save(audio, temp_file)

        # Play audio using pygame if available
        if PYGAME_AVAILABLE:
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            # Block until playback finishes
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        else:
            # Fall back to mpg123 or similar
            subprocess.run(['mpg123', '-q', temp_file], check=False)

        # Clean up temp file
        os.unlink(temp_file)

        return True

    except Exception as e:
        print(f"WARNING: ElevenLabs TTS failed: {e}")
        return False


def speak_with_espeak(text):
    """Speak using espeak-ng (offline fallback)"""
    try:
        # Use espeak-ng with blocking call
        subprocess.run(
            ['espeak-ng', text],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: espeak-ng failed: {e}")
        return False
    except FileNotFoundError:
        print("ERROR: espeak-ng not installed. Run: sudo apt install espeak-ng")
        return False


def speak(text):
    """
    Speak text aloud. Blocks until audio finishes playing.

    Args:
        text (str): Text to speak
    """
    global TTS_MODE, elevenlabs_client

    if not text or not text.strip():
        return

    # Initialize if not already done
    if TTS_MODE is None:
        init_tts()

    # Try primary mode first
    if TTS_MODE == "elevenlabs":
        success = speak_with_elevenlabs(text)
        if success:
            return
        # Fall back to espeak on failure
        print("Falling back to espeak-ng...")
        TTS_MODE = "espeak"  # Switch permanently to fallback

    # Use espeak
    speak_with_espeak(text)


def main():
    """Standalone test mode - speaks three test sentences"""
    print("SignBridge TTS Output Test")
    print("="*50)

    # Initialize TTS
    init_tts()

    # Test sentences
    test_sentences = [
        "SignBridge is ready. Please sign to communicate.",
        "The patient is reporting pain on the left side of their chest.",
        "The patient confirms yes."
    ]

    print(f"\nSpeaking {len(test_sentences)} test sentences...")

    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n[{i}/{len(test_sentences)}] Speaking: \"{sentence}\"")
        speak(sentence)
        print("Done")

    print("\n" + "="*50)
    print("TTS Test Complete!")

if __name__ == "__main__":
    main()
