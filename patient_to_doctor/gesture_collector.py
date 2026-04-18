#!/usr/bin/env python3
# patient_to_doctor/gesture_collector.py
"""
MODULE 1 — Gesture Collector
Collects training data for the gesture classifier.
Run standalone before training the model.
"""

import cv2
import mediapipe as mp
import numpy as np
import csv
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def extract_landmarks(hand_landmarks):
    """Extract 63-value vector from MediaPipe hand landmarks (21 landmarks × x,y,z)"""
    landmarks = []
    for landmark in hand_landmarks.landmark:
        landmarks.extend([landmark.x, landmark.y, landmark.z])
    return landmarks

def load_existing_data():
    """Load existing training data if available"""
    data = {}
    if os.path.exists(config.TRAINING_DATA_PATH):
        with open(config.TRAINING_DATA_PATH, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 64:  # 63 landmarks + 1 label
                    label = row[-1]
                    if label not in data:
                        data[label] = []
                    data[label].append(row)
    return data

def save_data(data):
    """Save training data incrementally"""
    with open(config.TRAINING_DATA_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        for label in data:
            for row in data[label]:
                writer.writerow(row)

def collect_sign_data(sign_label, cap, samples_per_sign=50):
    """Collect samples for a specific sign"""
    print(f"\n{'='*50}")
    print(f"Ready to collect: {sign_label}")
    print(f"{'='*50}")
    print("Position your hand and press SPACE to start recording")
    print("Press Q to skip this sign")

    samples = []
    collecting = False

    while len(samples) < samples_per_sign:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read from webcam")
            break

        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        # Draw hand landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )

                # Collect sample if in collecting mode
                if collecting:
                    landmarks = extract_landmarks(hand_landmarks)
                    samples.append(landmarks + [sign_label])

        # Display status
        status = f"{sign_label}: {len(samples)}/{samples_per_sign}"
        if not collecting:
            status += " - Press SPACE to start"
        else:
            status += " - Recording..."

        cv2.putText(frame, status, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Gesture Collector', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            if not collecting and results.multi_hand_landmarks:
                collecting = True
                print(f"Recording {sign_label}...")
        elif key == ord('q'):
            print(f"Skipping {sign_label}")
            return []
        elif key == 27:  # ESC
            return None

    print(f"Completed {sign_label}: {len(samples)} samples collected")
    return samples

def main():
    """Main collection loop"""
    print("SignBridge Gesture Collector")
    print("="*50)

    # Load existing data
    existing_data = load_existing_data()
    print(f"Loaded existing data: {sum(len(v) for v in existing_data.values())} samples")

    # Open webcam
    cap = cv2.VideoCapture(config.WEBCAM_INDEX)
    if not cap.isOpened():
        print(f"Error: Cannot open webcam at index {config.WEBCAM_INDEX}")
        return

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print(f"\nWebcam opened at index {config.WEBCAM_INDEX}")
    print(f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"\nCollecting {len(config.SIGN_VOCABULARY)} signs: {', '.join(config.SIGN_VOCABULARY)}")
    print("\nControls:")
    print("  SPACE - Start recording current sign")
    print("  Q     - Skip current sign")
    print("  ESC   - Exit program")

    # Collect data for each sign
    all_data = existing_data

    for sign in config.SIGN_VOCABULARY:
        # Check if we already have enough samples
        if sign in all_data and len(all_data[sign]) >= 50:
            print(f"\n{sign}: Already have {len(all_data[sign])} samples, skipping...")
            continue

        samples = collect_sign_data(sign, cap)

        if samples is None:  # User pressed ESC
            print("\nCollection interrupted by user")
            break

        if samples:
            if sign not in all_data:
                all_data[sign] = []
            all_data[sign].extend(samples)

            # Save incrementally
            save_data(all_data)
            print(f"Progress saved to {config.TRAINING_DATA_PATH}")

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

    # Final summary
    print("\n" + "="*50)
    print("Collection Complete!")
    print("="*50)
    total_samples = sum(len(v) for v in all_data.values())
    print(f"Total samples collected: {total_samples}")
    for sign in config.SIGN_VOCABULARY:
        count = len(all_data.get(sign, []))
        print(f"  {sign}: {count} samples")
    print(f"\nData saved to: {config.TRAINING_DATA_PATH}")
    print("\nNext step: Run train_classifier.py to train the model")

if __name__ == "__main__":
    main()
