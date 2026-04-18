#!/usr/bin/env python3
# doctor_to_patient/patient_display.py
"""
MODULE 8 — Patient Display
Fullscreen display showing doctor's transcribed words in large text for patient to read.
"""

import sys
import os
import tkinter as tk
from tkinter import font as tkfont

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import state


class PatientDisplay:
    """Fullscreen display for showing doctor's transcription to patient"""

    def __init__(self, root):
        """Initialize patient display"""
        self.root = root
        self.root.title("SignBridge Patient Display")

        # Configure fullscreen
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')

        # Bind ESC key to exit
        self.root.bind('<Escape>', self.exit_fullscreen)

        # Create text widget
        self.text_widget = tk.Label(
            self.root,
            text="",
            font=("Arial", 64, "bold"),
            bg="black",
            fg="white",
            wraplength=self.root.winfo_screenwidth() - 100,  # Word wrap with margin
            justify="center",
            anchor="center"
        )
        self.text_widget.pack(expand=True, fill='both')

        # Track last displayed text to avoid unnecessary updates
        self.last_text = ""

        # Start update loop
        self.update_display()

    def update_display(self):
        """Poll state and update display when transcript changes"""
        try:
            # Get current transcript
            with state.state_lock:
                current_text = state.state["doctor_transcript"]

            # Update display if text changed
            if current_text != self.last_text:
                self.text_widget.config(text=current_text)
                self.last_text = current_text

            # Schedule next update
            if state.state["system_active"]:
                self.root.after(100, self.update_display)
            else:
                self.root.quit()

        except Exception as e:
            print(f"ERROR in display update: {e}")
            self.root.after(100, self.update_display)

    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        print("Exiting patient display...")
        state.state["system_active"] = False
        self.root.quit()


def run_display():
    """
    Run patient display.
    This should be called from the main thread (tkinter requirement).
    """
    root = tk.Tk()
    display = PatientDisplay(root)
    root.mainloop()


def main():
    """Standalone test mode - accepts typed input and displays it"""
    import threading

    print("SignBridge Patient Display Test")
    print("="*50)

    # Mock state for testing
    state.state["system_active"] = True
    state.state["doctor_transcript"] = "Ready to display text"

    def input_simulator():
        """Simulate input for testing"""
        print("\nDisplay opened in fullscreen mode")
        print("Type text to display (or press Ctrl+C to exit):")

        try:
            while state.state["system_active"]:
                text = input("> ")
                with state.state_lock:
                    state.state["doctor_transcript"] = text
        except (KeyboardInterrupt, EOFError):
            print("\nStopping...")
            state.state["system_active"] = False

    # Start input thread
    input_thread = threading.Thread(target=input_simulator, daemon=True)
    input_thread.start()

    # Run display (must be on main thread)
    run_display()

    print("="*50)

if __name__ == "__main__":
    main()
