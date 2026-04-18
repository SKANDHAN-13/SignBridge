#!/usr/bin/env python3
# tests/test_classifier.py
"""
Test script to verify trained classifier works with live camera feed.
Loads gesture_model.pkl, runs 5 seconds of live classification,
prints sign + confidence for every detection.
"""

import cv2
import mediapipe as mp
import pickle
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def extract_landmarks(hand_landmarks):
    """Extract 63-value vector from MediaPipe hand landmarks"""
    landmarks = []
    for landmark in hand_landmarks.landmark:
        landmarks.extend([landmark.x, landmark.y, landmark.z])
    return landmarks

def test_classifier():
    """Test classifier with live camera feed"""
    print("[TEST] test_classifier.py")
    print("="*50)

    # Load trained model
    if not os.path.exists(config.MODEL_PATH):
        print(f"FAIL: Model not found at {config.MODEL_PATH}")
        print("Please run train_classifier.py first")
        return False

    with open(config.MODEL_PATH, 'rb') as f:
        clf = pickle.load(f)

    print(f"Model loaded from {config.MODEL_PATH}")

    # Initialize MediaPipe
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

    print("Testing live classification for 5 seconds...")
    print("Show hand signs to the camera")

    start_time = time.time()
    detection_count = 0

    while time.time() - start_time < 5:
        ret, frame = cap.read()
        if not ret:
            print("FAIL: Cannot read frame from camera")
            cap.release()
            cv2.destroyAllWindows()
            return False

        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        # Process hand landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )

                # Extract features
                landmarks = extract_landmarks(hand_landmarks)

                # Classify
                prediction = clf.predict([landmarks])[0]
                probabilities = clf.predict_proba([landmarks])[0]
                confidence = max(probabilities)

                # Display on frame
                text = f"{prediction}: {confidence*100:.1f}%"
                cv2.putText(frame, text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Print to terminal
                if confidence >= config.CONFIDENCE_THRESHOLD:
                    print(f"Detected: {prediction} (confidence: {confidence*100:.1f}%)")
                    detection_count += 1

        # Display frame
        cv2.imshow('Classifier Test', frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

    print(f"\nDetections above threshold: {detection_count}")

    if detection_count > 0:
        print("PASS")
    else:
        print("WARN: No confident detections (this is OK if no signs were shown)")
        print("PASS")

    print("="*50)
    return True

if __name__ == "__main__":
    success = test_classifier()
    sys.exit(0 if success else 1)
