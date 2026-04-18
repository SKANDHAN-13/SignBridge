#!/usr/bin/env python3
# tests/test_mediapipe.py
"""
Test script to verify MediaPipe Hands functionality.
Opens webcam, runs MediaPipe Hands, draws landmarks on feed for 10 seconds.
Prints landmark count per frame.
"""

import cv2
import mediapipe as mp
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def test_mediapipe():
    """Test MediaPipe hand detection"""
    print("[TEST] test_mediapipe.py")
    print("="*50)

    # Initialize MediaPipe Hands
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # Open webcam
    cap = cv2.VideoCapture(config.WEBCAM_INDEX)

    if not cap.isOpened():
        print(f"FAIL: Cannot open camera at index {config.WEBCAM_INDEX}")
        return False

    print(f"Camera opened at /dev/video{config.WEBCAM_INDEX}")
    print("Testing MediaPipe Hands for 10 seconds...")
    print("Show your hand to the camera")

    start_time = time.time()
    frame_count = 0
    hand_detected_count = 0
    fps_list = []

    while time.time() - start_time < 10:
        loop_start = time.time()

        ret, frame = cap.read()
        if not ret:
            print("FAIL: Cannot read frame from camera")
            cap.release()
            cv2.destroyAllWindows()
            return False

        # Flip frame for mirror effect
        frame = cv2.flip(frame, 1)

        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        # Draw hand landmarks
        if results.multi_hand_landmarks:
            hand_detected_count += 1
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )
                # Count landmarks
                landmark_count = len(hand_landmarks.landmark)
                cv2.putText(frame, f"Landmarks: {landmark_count}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                print(f"Hand detected: {landmark_count} landmarks per frame")

        # Display frame
        cv2.imshow('MediaPipe Test', frame)

        frame_count += 1

        # Calculate FPS
        loop_time = time.time() - loop_start
        if loop_time > 0:
            fps_list.append(1.0 / loop_time)

        # Check for ESC key to exit early
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

    # Calculate average FPS
    avg_fps = sum(fps_list) / len(fps_list) if fps_list else 0

    print(f"\nFrames processed: {frame_count}")
    print(f"Hands detected: {hand_detected_count} frames")
    print(f"Average FPS: {avg_fps:.1f}")

    if hand_detected_count > 0:
        print("PASS")
    else:
        print("WARN: No hands detected during test (show hand to camera next time)")
        print("PASS")

    print("="*50)
    return True

if __name__ == "__main__":
    success = test_mediapipe()
    sys.exit(0 if success else 1)
