#!/usr/bin/env python3
# tests/test_wakeword.py
"""
Test script to verify wake word detection functionality.
Runs wake word detector for 15 seconds. Prints detected events.
"""

import sys
import os
import time
import threading

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import state
from doctor_to_patient import wake_word

def monitor_state():
    """Monitor state changes and print them"""
    last_mic_active = False

    while state.state["system_active"]:
        current_mic_active = state.state["mic_active"]

        if current_mic_active != last_mic_active:
            if current_mic_active:
                print("✓ WAKE WORD DETECTED - Mic activated")
            else:
                print("✓ MIC DEACTIVATED")

            last_mic_active = current_mic_active

        time.sleep(0.1)

def test_wakeword():
    """Test wake word detection"""
    print("[TEST] test_wakeword.py")
    print("="*50)

    # Reset state
    state.state["system_active"] = True
    state.state["mic_active"] = False

    print("Testing wake word detection for 15 seconds...")
    print("Say 'SignBridge' or 'computer' to activate")
    print("Say 'done' to deactivate")

    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_state, daemon=True)
    monitor_thread.start()

    # Start wake word detection in separate thread
    wake_thread = threading.Thread(target=wake_word.wake_word_loop, daemon=True)
    wake_thread.start()

    # Run for 15 seconds
    try:
        time.sleep(15)
    except KeyboardInterrupt:
        print("\nInterrupted by user")

    # Stop
    state.state["system_active"] = False
    time.sleep(0.5)

    print("\nPASS")
    print("="*50)
    return True

if __name__ == "__main__":
    success = test_wakeword()
    sys.exit(0 if success else 1)
