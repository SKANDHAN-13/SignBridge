#!/usr/bin/env python3
# patient_to_doctor/gesture_recognition.py
"""
MODULE 3 — Gesture Recognition
Real-time gesture recognition using MediaPipe + trained classifier.
Core of patient → doctor direction.
"""

import cv2
import mediapipe as mp
import pickle
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class GestureRecognizer:
    """Real-time gesture recognition using MediaPipe and trained classifier"""

    def __init__(self):
        """Initialize gesture recognizer"""
        # Load trained model
        if not os.path.exists(config.MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {config.MODEL_PATH}. Run train_classifier.py first.")

        with open(config.MODEL_PATH, 'rb') as f:
            self.clf = pickle.load(f)

        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Debounce tracking
        self.last_sign = None

        print(f"GestureRecognizer initialized with model from {config.MODEL_PATH}")

    def extract_landmarks(self, hand_landmarks):
        """Extract 63-value vector from MediaPipe hand landmarks (21 landmarks × x,y,z)"""
        landmarks = []
        for landmark in hand_landmarks.landmark:
            landmarks.extend([landmark.x, landmark.y, landmark.z])
        return landmarks

    def get_sign(self, frame):
        """
        Process frame and return detected sign with confidence.

        Args:
            frame: BGR image from camera

        Returns:
            tuple: (sign_label, confidence) or (None, 0.0) if no confident detection
        """
        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        # Check if hand is detected
        if not results.multi_hand_landmarks:
            # Reset debounce when no hand detected
            self.last_sign = None
            return None, 0.0

        # Process first detected hand
        hand_landmarks = results.multi_hand_landmarks[0]

        # Extract features
        landmarks = self.extract_landmarks(hand_landmarks)

        # Classify
        prediction = self.clf.predict([landmarks])[0]
        probabilities = self.clf.predict_proba([landmarks])[0]
        confidence = max(probabilities)

        # Check confidence threshold
        if confidence < config.CONFIDENCE_THRESHOLD:
            return None, confidence

        # Debounce: don't return same sign twice in a row
        if prediction == self.last_sign:
            return None, confidence

        # Update last sign
        self.last_sign = prediction

        return prediction, confidence

    def release(self):
        """Release resources"""
        if self.hands:
            self.hands.close()


def main():
    """Standalone test mode - prints detected signs in real-time"""
    print("SignBridge Gesture Recognition")
    print("="*50)
    print("Starting real-time gesture detection...")
    print("Press Ctrl+C or ESC to exit")

    # Initialize recognizer
    try:
        recognizer = GestureRecognizer()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return

    # Open webcam
    cap = cv2.VideoCapture(config.WEBCAM_INDEX)
    if not cap.isOpened():
        print(f"ERROR: Cannot open camera at index {config.WEBCAM_INDEX}")
        return

    # Initialize MediaPipe drawing utilities for visualization
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands_viz = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Cannot read from camera")
                break

            # Flip for mirror effect
            frame = cv2.flip(frame, 1)

            # Get sign detection
            sign, confidence = recognizer.get_sign(frame)

            # Draw hand landmarks for visualization
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands_viz.process(frame_rgb)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )

            # Display detection on frame
            if sign:
                text = f"{sign}: {confidence*100:.1f}%"
                cv2.putText(frame, text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                print(f"Detected: {sign} (confidence: {confidence*100:.1f}%)")

            # Show frame
            cv2.imshow('Gesture Recognition', frame)

            # Check for exit
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

    except KeyboardInterrupt:
        print("\nStopped by user")

    finally:
        # Cleanup
        recognizer.release()
        hands_viz.close()
        cap.release()
        cv2.destroyAllWindows()

    print("="*50)

if __name__ == "__main__":
    main()
