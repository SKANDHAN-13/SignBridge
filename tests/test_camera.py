#!/usr/bin/env python3
# tests/test_camera.py
"""
Test script to verify webcam functionality.
Opens webcam, displays live feed for 5 seconds, prints resolution.
"""

import cv2
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def test_camera():
    """Test webcam capture and display"""
    print("[TEST] test_camera.py")
    print("="*50)

    # Try to open webcam
    cap = cv2.VideoCapture(config.WEBCAM_INDEX)

    if not cap.isOpened():
        print(f"FAIL: Cannot open camera at index {config.WEBCAM_INDEX}")
        return False

    print(f"Camera opened at /dev/video{config.WEBCAM_INDEX}")

    # Get resolution
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Resolution: {width}x{height}")

    # Display feed for 5 seconds
    print("Displaying feed for 5 seconds...")
    start_time = time.time()

    while time.time() - start_time < 5:
        ret, frame = cap.read()

        if not ret:
            print("FAIL: Cannot read frame from camera")
            cap.release()
            cv2.destroyAllWindows()
            return False

        # Display frame
        cv2.imshow('Camera Test', frame)

        # Check for ESC key to exit early
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

    print("PASS")
    print("="*50)
    return True

if __name__ == "__main__":
    success = test_camera()
    sys.exit(0 if success else 1)
