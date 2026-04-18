#!/usr/bin/env python3
# main.py
"""
SignBridge Main Entry Point
Coordinates all threads for two-way communication system.
"""

import threading
import time
import cv2
import sys

import config
import state

# Import modules
from patient_to_doctor import gesture_recognition, llm_elaboration, tts_output
from doctor_to_patient import wake_word, transcription, patient_display

# Try to import GPIO
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("WARNING: RPi.GPIO not available, PIR sensor will be disabled")


def pir_thread_func():
    """PIR motion sensor thread - polls GPIO17"""
    if not GPIO_AVAILABLE:
        print("PIR thread: GPIO not available, thread exiting")
        return

    try:
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.PIR_GPIO_PIN, GPIO.IN)
        print(f"PIR sensor initialized on GPIO{config.PIR_GPIO_PIN}")

        while state.state["system_active"]:
            try:
                # Read PIR sensor
                if GPIO.input(config.PIR_GPIO_PIN):
                    with state.state_lock:
                        state.state["pir_last_motion"] = time.time()

                time.sleep(0.5)

            except Exception as e:
                print(f"ERROR in PIR thread: {e}")
                time.sleep(1)

    finally:
        if GPIO_AVAILABLE:
            GPIO.cleanup()


def gesture_thread_func():
    """Gesture recognition thread - runs GestureRecognizer, feeds sign_buffer"""
    try:
        # Initialize gesture recognizer
        recognizer = gesture_recognition.GestureRecognizer()

        # Open webcam
        cap = cv2.VideoCapture(config.WEBCAM_INDEX)
        if not cap.isOpened():
            print(f"ERROR: Cannot open webcam at index {config.WEBCAM_INDEX}")
            return

        print("Gesture recognition started")

        while state.state["system_active"]:
            try:
                ret, frame = cap.read()
                if not ret:
                    print("WARNING: Cannot read from webcam")
                    time.sleep(0.1)
                    continue

                # Flip for mirror effect
                frame = cv2.flip(frame, 1)

                # Get sign detection
                sign, confidence = recognizer.get_sign(frame)

                if sign:
                    with state.state_lock:
                        # Add to sign buffer
                        state.state["sign_buffer"].append(sign)

                        # Limit buffer size
                        if len(state.state["sign_buffer"]) > config.BUFFER_MAX_SIGNS:
                            state.state["sign_buffer"].pop(0)

                        # Update timing
                        state.state["last_sign"] = sign
                        state.state["last_sign_time"] = time.time()

                    print(f"Sign detected: {sign} ({confidence*100:.1f}%)")

            except Exception as e:
                print(f"ERROR in gesture thread: {e}")
                time.sleep(0.5)

    finally:
        recognizer.release()
        cap.release()


def elaboration_thread_func():
    """Elaboration thread - watches sign_buffer, calls elaborate(), calls speak()"""
    print("Elaboration thread started")

    while state.state["system_active"]:
        try:
            # Check if we have signs in buffer
            with state.state_lock:
                sign_buffer = state.state["sign_buffer"].copy()
                last_sign_time = state.state["last_sign_time"]
                is_speaking = state.state["is_speaking"]

            # Wait if no signs or already speaking
            if not sign_buffer or is_speaking:
                time.sleep(0.1)
                continue

            # Check if enough time has passed since last sign (buffer timeout)
            time_since_last_sign = time.time() - last_sign_time
            if time_since_last_sign < config.BUFFER_TIMEOUT_SECONDS:
                time.sleep(0.1)
                continue

            # We have signs and timeout reached - elaborate and speak
            print(f"Elaborating signs: {sign_buffer}")

            # Mark as speaking
            with state.state_lock:
                state.state["is_speaking"] = True

            # Elaborate
            elaboration = llm_elaboration.elaborate(sign_buffer)
            print(f"Elaboration: \"{elaboration}\"")

            # Store elaboration
            with state.state_lock:
                state.state["last_elaboration"] = elaboration

            # Speak
            if elaboration:
                tts_output.speak(elaboration)

            # Clear buffer and reset speaking flag
            with state.state_lock:
                state.state["sign_buffer"] = []
                state.state["is_speaking"] = False

        except Exception as e:
            print(f"ERROR in elaboration thread: {e}")
            with state.state_lock:
                state.state["is_speaking"] = False
            time.sleep(1)


def main():
    """Main entry point"""
    print("="*50)
    print("SignBridge Starting...")
    print("="*50)

    # Reset state
    state.state["system_active"] = True

    try:
        # Initialize TTS
        print("\nInitializing TTS...")
        tts_output.init_tts()

        # Start all daemon threads
        print("\nStarting threads...")

        threads = []

        # PIR thread
        if GPIO_AVAILABLE:
            pir_thread = threading.Thread(target=pir_thread_func, daemon=True, name="PIR")
            pir_thread.start()
            threads.append(pir_thread)

        # Gesture recognition thread
        gesture_thread = threading.Thread(target=gesture_thread_func, daemon=True, name="Gesture")
        gesture_thread.start()
        threads.append(gesture_thread)

        # Elaboration thread
        elaboration_thread = threading.Thread(target=elaboration_thread_func, daemon=True, name="Elaboration")
        elaboration_thread.start()
        threads.append(elaboration_thread)

        # Wake word thread
        wake_thread = threading.Thread(target=wake_word.wake_word_loop, daemon=True, name="WakeWord")
        wake_thread.start()
        threads.append(wake_thread)

        # Transcription thread
        trans_thread = threading.Thread(target=transcription.transcription_loop, daemon=True, name="Transcription")
        trans_thread.start()
        threads.append(trans_thread)

        # Give threads time to initialize
        time.sleep(2)

        print("\n✓ All threads started")

        # Speak startup message
        print("\nSpeaking startup message...")
        tts_output.speak("SignBridge is ready. Please sign to communicate.")

        print("\n" + "="*50)
        print("SignBridge Running")
        print("="*50)
        print("\nPatient → Doctor:")
        print("  - Show hand signs to camera")
        print("  - System will elaborate and speak to doctor")
        print("\nDoctor → Patient:")
        print("  - Say wake word to activate mic")
        print("  - Speak your message")
        print("  - Say 'done' to deactivate mic")
        print("  - Text appears on patient display")
        print("\nPress ESC in display window to exit")
        print("="*50 + "\n")

        # Run patient display on main thread (tkinter requirement)
        patient_display.run_display()

    except KeyboardInterrupt:
        print("\n\nShutdown requested...")

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Shutdown
        print("\nShutting down SignBridge...")
        state.state["system_active"] = False

        # Give threads time to exit
        time.sleep(1)

        print("SignBridge stopped")
        print("="*50)


if __name__ == "__main__":
    main()
