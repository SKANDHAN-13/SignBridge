#!/usr/bin/env python3
# tests/test_display.py
"""
Test script to verify patient display functionality.
Opens patient display, cycles through 3 test messages every 2 seconds automatically.
"""

import sys
import os
import threading
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import state
from doctor_to_patient import patient_display

def test_display():
    """Test patient display with automated message cycling"""
    print("[TEST] test_display.py")
    print("="*50)

    # Reset state
    state.state["system_active"] = True
    state.state["doctor_transcript"] = ""

    # Test messages
    test_messages = [
        "Test message one: Can you hear me?",
        "Test message two: Please point to where it hurts.",
        "Test message three: We will help you right away."
    ]

    def message_cycler():
        """Automatically cycle through test messages"""
        print("\nDisplay opened. Cycling through test messages...")

        for i, message in enumerate(test_messages, 1):
            print(f"\n[{i}/{len(test_messages)}] Displaying: \"{message}\"")

            with state.state_lock:
                state.state["doctor_transcript"] = message

            time.sleep(2)

        time.sleep(1)

        print("\nTest complete. Press ESC in display window to exit...")

        # Keep running until user exits
        while state.state["system_active"]:
            time.sleep(0.5)

    # Start message cycler thread
    cycler_thread = threading.Thread(target=message_cycler, daemon=True)
    cycler_thread.start()

    # Run display (must be on main thread)
    try:
        patient_display.run_display()
    except KeyboardInterrupt:
        print("\nInterrupted by user")

    state.state["system_active"] = False

    print("\nPASS")
    print("="*50)
    return True

if __name__ == "__main__":
    success = test_display()
    sys.exit(0 if success else 1)
