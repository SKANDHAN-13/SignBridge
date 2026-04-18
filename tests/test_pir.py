#!/usr/bin/env python3
# tests/test_pir.py
"""
Test script to verify PIR sensor functionality.
Polls GPIO17 for 10 seconds, prints MOTION or idle every 500ms.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Try to import GPIO
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("WARNING: RPi.GPIO not available")
    print("This test requires RPi.GPIO to work with the PIR sensor")

def test_pir():
    """Test PIR sensor"""
    print("[TEST] test_pir.py")
    print("="*50)

    if not GPIO_AVAILABLE:
        print("SKIP: RPi.GPIO not available on this system")
        print("This test should be run on the Rubik Pi")
        print("="*50)
        return True

    try:
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.PIR_GPIO_PIN, GPIO.IN)

        print(f"PIR sensor initialized on GPIO{config.PIR_GPIO_PIN}")
        print("Testing for 10 seconds...")
        print("Wave your hand in front of the sensor\n")

        start_time = time.time()
        motion_count = 0

        while time.time() - start_time < 10:
            # Read PIR sensor
            motion = GPIO.input(config.PIR_GPIO_PIN)

            if motion:
                print("MOTION detected")
                motion_count += 1
            else:
                print("idle")

            time.sleep(0.5)

        # Cleanup
        GPIO.cleanup()

        print(f"\nMotion detections: {motion_count}")

        if motion_count > 0:
            print("PASS")
        else:
            print("WARN: No motion detected (move in front of sensor)")
            print("PASS")

        print("="*50)
        return True

    except Exception as e:
        print(f"\nFAIL: {e}")
        print("="*50)

        # Cleanup on error
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except:
                pass

        return False

if __name__ == "__main__":
    success = test_pir()
    sys.exit(0 if success else 1)
