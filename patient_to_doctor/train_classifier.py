#!/usr/bin/env python3
# patient_to_doctor/train_classifier.py
"""
MODULE 2 — Train Classifier
Trains a Random Forest classifier on collected gesture data.
Run this after collecting training data with gesture_collector.py
"""

import numpy as np
import pandas as pd
import pickle
import sys
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def load_training_data():
    """Load training data from CSV"""
    if not os.path.exists(config.TRAINING_DATA_PATH):
        print(f"ERROR: Training data not found at {config.TRAINING_DATA_PATH}")
        print("Please run gesture_collector.py first to collect training data")
        return None, None

    # Read CSV
    data = pd.read_csv(config.TRAINING_DATA_PATH, header=None)

    # Split features and labels
    X = data.iloc[:, :-1].values  # First 63 columns are landmarks
    y = data.iloc[:, -1].values    # Last column is label

    return X, y

def train_model(X, y):
    """Train Random Forest classifier"""
    # Split into train/test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training on {len(X_train)} samples across {len(np.unique(y))} classes...")
    print(f"Test set: {len(X_test)} samples")

    # Train Random Forest
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )

    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    overall_accuracy = accuracy_score(y_test, y_pred)

    print(f"\nOverall accuracy: {overall_accuracy*100:.1f}%")

    # Per-class accuracy
    print("\nPer-class accuracy:")
    print("-" * 50)

    # Get unique classes
    classes = np.unique(y)
    low_accuracy_classes = []

    for cls in classes:
        # Find indices where true label is this class
        mask = y_test == cls
        if mask.sum() == 0:
            continue

        class_accuracy = accuracy_score(y_test[mask], y_pred[mask])
        print(f"  {cls}: {class_accuracy*100:.0f}%")

        # Check for low accuracy
        if class_accuracy < 0.80:
            low_accuracy_classes.append((cls, class_accuracy))

    # Warnings for low accuracy classes
    if low_accuracy_classes:
        print("\n" + "!"*50)
        print("WARNINGS:")
        for cls, acc in low_accuracy_classes:
            print(f"  WARNING: {cls} accuracy low ({acc*100:.0f}%) — collect more samples")
        print("!"*50)

    # Detailed classification report
    print("\nDetailed Classification Report:")
    print("-" * 50)
    print(classification_report(y_test, y_pred))

    return clf, overall_accuracy

def save_model(clf):
    """Save trained model to pickle file"""
    model_dir = os.path.dirname(config.MODEL_PATH)
    if model_dir and not os.path.exists(model_dir):
        os.makedirs(model_dir)

    with open(config.MODEL_PATH, 'wb') as f:
        pickle.dump(clf, f)

    print(f"\nModel saved to {config.MODEL_PATH}")

def main():
    """Main training routine"""
    print("SignBridge Gesture Classifier Training")
    print("="*50)

    # Load data
    X, y = load_training_data()
    if X is None:
        return

    print(f"Loaded {len(X)} samples")
    print(f"Feature dimensions: {X.shape[1]}")
    print(f"Classes: {', '.join(np.unique(y))}")

    # Train model
    clf, accuracy = train_model(X, y)

    # Save model
    save_model(clf)

    print("\n" + "="*50)
    print("Training Complete!")
    print(f"Final model accuracy: {accuracy*100:.1f}%")
    print("\nNext step: Run gesture_recognition.py to test real-time recognition")
    print("="*50)

if __name__ == "__main__":
    main()
