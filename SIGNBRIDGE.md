# SignBridge — Claude Code Build Spec

## Project Overview

SignBridge is a two-way real-time communication system for deaf and hard-of-hearing patients in emergency medical settings. It runs on a **Rubik Pi 3** (Ubuntu 24.04, Qualcomm QCS6490, 12 TOPS NPU, 128GB internal storage).

There are two independent communication directions running as separate threads in one Python process:

- **Patient → Doctor:** Webcam captures patient signing → MediaPipe detects landmarks → classifier maps to signs → GPT-4o elaborates into a sentence → ElevenLabs speaks to doctor
- **Doctor → Patient:** Wake word activates mic → Whisper transcribes speech → large text printed to monitor for patient to read

---

## Hardware

- Rubik Pi 3 (Ubuntu 24.04)
- USB Webcam 1080p (at `/dev/video0`)
- HC-SR501 PIR sensor on GPIO17
- Speaker or headphones via 3.5mm jack
- Monitor via HDMI for patient-facing text display

---

## Environment Setup

Before generating any code, create a `requirements.txt`:

```
mediapipe
opencv-python
scikit-learn
openai
elevenlabs
openai-whisper
sounddevice
numpy
pvporcupine
RPi.GPIO
flask
```

And an install script `setup.sh`:

```bash
#!/bin/bash
sudo apt update
sudo apt install python3-pip python3-opencv espeak-ng portaudio19-dev -y
pip3 install -r requirements.txt
```

---

## Project File Structure

```
signbridge/
├── setup.sh
├── requirements.txt
├── config.py                  # All API keys and constants
├── state.py                   # Shared state object + lock
├── main.py                    # Entry point — starts all threads
│
├── patient_to_doctor/
│   ├── gesture_collector.py   # MODULE 1 — collect training data
│   ├── train_classifier.py    # MODULE 2 — train Random Forest
│   ├── gesture_recognition.py # MODULE 3 — MediaPipe + classifier
│   ├── llm_elaboration.py     # MODULE 4 — GPT-4o elaboration
│   └── tts_output.py          # MODULE 5 — ElevenLabs + espeak-ng
│
├── doctor_to_patient/
│   ├── wake_word.py           # MODULE 6 — wake word detection
│   ├── transcription.py       # MODULE 7 — Whisper transcription
│   └── patient_display.py     # MODULE 8 — fullscreen text display
│
└── tests/
    ├── test_camera.py
    ├── test_pir.py
    ├── test_mediapipe.py
    ├── test_classifier.py
    ├── test_tts.py
    ├── test_llm.py
    ├── test_wakeword.py
    ├── test_whisper.py
    └── test_display.py
```

---

## config.py

Generate this file first. It contains all constants and API keys.

```python
# config.py

OPENAI_API_KEY = "YOUR_OPENAI_KEY"
ELEVENLABS_API_KEY = "YOUR_ELEVENLABS_KEY"
ELEVENLABS_VOICE = "Rachel"
PORCUPINE_ACCESS_KEY = "YOUR_PORCUPINE_KEY"  # from picovoice.ai — free tier

# Hardware
WEBCAM_INDEX = 0
PIR_GPIO_PIN = 17
SAMPLE_RATE = 16000

# Gesture recognition
CONFIDENCE_THRESHOLD = 0.75
BUFFER_MAX_SIGNS = 4
BUFFER_TIMEOUT_SECONDS = 3.0
IDLE_TIMEOUT_SECONDS = 60

# Wake word
WAKE_WORD = "SignBridge"   # keyword for porcupine
STOP_WORD = "done"         # doctor says this to stop mic

# Paths
MODEL_PATH = "patient_to_doctor/gesture_model.pkl"
TRAINING_DATA_PATH = "patient_to_doctor/training_data.csv"
WHISPER_MODEL_SIZE = "base"  # tiny/base/small — base is best balance on Rubik Pi

# Medical sign vocabulary to train on
SIGN_VOCABULARY = [
    "YES", "NO",
    "PAIN", "CHEST", "LEFT", "RIGHT",
    "HEADACHE", "DIZZY", "BLEEDING", "JOINT"
]
```

---

## state.py

Generate this file second. It is the single shared memory object between all threads.

```python
# state.py
import threading

state_lock = threading.Lock()

state = {
    # Patient -> Doctor
    "sign_buffer": [],          # list of recently detected signs
    "last_sign": None,          # last detected sign to avoid repeats
    "last_sign_time": 0.0,      # timestamp of last detected sign
    "last_elaboration": "",     # last sentence GPT-4o produced
    "is_speaking": False,       # True while ElevenLabs is playing audio

    # Doctor -> Patient
    "mic_active": False,        # True when wake word has been detected
    "doctor_transcript": "",    # latest Whisper transcription

    # System
    "pir_last_motion": 0.0,     # timestamp of last PIR trigger
    "system_active": True,      # False to shut everything down
}
```

---

## MODULE 1 — gesture_collector.py

**Purpose:** Collect training data for the gesture classifier. Run this standalone before training.

**What it does:**
- Opens webcam
- Loops through each sign in `SIGN_VOCABULARY`
- For each sign, waits for user to press SPACE then records 50 landmark samples
- Saves all samples to `training_data.csv`
- Each row is 63 values (21 landmarks × x,y,z) + label

**Standalone test:**
```bash
python3 patient_to_doctor/gesture_collector.py
```

**Expected result:** `training_data.csv` created with rows of landmark data labeled by sign.

**Requirements:**
- OpenCV webcam feed showing live hand landmarks overlaid
- Terminal prompt tells user which sign to perform next
- Press SPACE to begin recording each sign
- Press Q to skip a sign
- Shows live count "PAIN: 23/50" on screen while collecting
- Saves progress incrementally so partial runs are not lost

---

## MODULE 2 — train_classifier.py

**Purpose:** Train a Random Forest classifier on the collected data.

**What it does:**
- Loads `training_data.csv`
- Splits into train/test sets
- Trains `RandomForestClassifier(n_estimators=200)`
- Prints accuracy report per sign class
- Saves model to `gesture_model.pkl`

**Standalone test:**
```bash
python3 patient_to_doctor/train_classifier.py
```

**Expected result:**
```
Training on 1500 samples across 10 classes...
Overall accuracy: 94.3%
YES: 97%  NO: 96%  PAIN: 93%  CHEST: 91% ...
Model saved to patient_to_doctor/gesture_model.pkl
```

**Requirements:**
- Print per-class accuracy so weak signs can be identified
- If any class is below 80%, print a warning: "WARNING: DIZZY accuracy low — collect more samples"
- Model must be saved with pickle

---

## MODULE 3 — gesture_recognition.py

**Purpose:** Real-time gesture recognition using MediaPipe + trained classifier. Core of patient → doctor direction.

**What it does:**
- Loads `gesture_model.pkl`
- Opens webcam
- Runs MediaPipe Hands on each frame
- Extracts 63-value landmark vector
- Classifies with confidence threshold from config
- Returns detected sign only if confidence >= `CONFIDENCE_THRESHOLD`
- Exposes a `GestureRecognizer` class with a `get_sign()` method

**Class interface:**
```python
class GestureRecognizer:
    def __init__(self): ...
    def get_sign(self, frame) -> tuple[str | None, float]: ...
        # Returns (sign_label, confidence) or (None, 0.0)
    def release(self): ...
```

**Standalone test:**
```bash
python3 patient_to_doctor/gesture_recognition.py
```

**Expected result:** Terminal prints detected sign + confidence in real time as user signs in front of camera. Runs until Ctrl+C.

**Requirements:**
- Same sign must not be returned twice in a row — debounce repeated detections
- Must use confidence threshold from config
- Must not crash if no hand is detected in frame

---

## MODULE 4 — llm_elaboration.py

**Purpose:** Take a buffer of detected signs and ask GPT-4o to form a coherent medical sentence.

**What it does:**
- Takes a list of sign strings e.g. `["PAIN", "CHEST", "LEFT"]`
- Sends to GPT-4o with a medical interpreter system prompt
- Returns elaborated sentence string
- Falls back to simple concatenation if offline or API fails

**System prompt to use:**
```
You are a medical interpreter assistant in an emergency room.
A deaf patient is communicating via ASL signs.
You receive a sequence of signed words and must construct a single
clear natural sentence that accurately represents what the patient
is trying to communicate.
Keep it to 1-2 sentences maximum.
Do not diagnose. Do not add information not implied by the signs.
Use calm clinical language appropriate for medical staff.
```

**Function interface:**
```python
def elaborate(sign_buffer: list[str]) -> str:
    # Returns elaborated sentence or fallback string
```

**Standalone test:**
```bash
python3 patient_to_doctor/llm_elaboration.py
```

**Expected result:** Prints elaborated sentences for several hardcoded test buffers:
```
Input: ['PAIN', 'CHEST', 'LEFT', 'SEVERE']
Output: "The patient is reporting severe pain on the left side of their chest."

Input: ['DIZZY', 'HEADACHE']
Output: "The patient is experiencing dizziness and a headache."

Input: ['BLEEDING', 'RIGHT', 'ARM']
Output: "The patient appears to have bleeding on their right arm."
```

**Requirements:**
- Must handle offline gracefully — fallback returns `"Patient signed: pain chest left"`
- Temperature must be 0.3 for consistent medical language
- Max tokens 80 — keep responses short
- Must not throw exceptions — always return a string

---

## MODULE 5 — tts_output.py

**Purpose:** Speak text aloud through speaker or headphones.

**What it does:**
- Checks internet connectivity at startup
- If online: uses ElevenLabs with Rachel voice
- If offline: uses espeak-ng subprocess
- Exposes a `speak(text)` function
- Blocks until audio finishes playing

**Function interface:**
```python
def speak(text: str) -> None:
    # Speaks text, blocks until done
```

**Standalone test:**
```bash
python3 patient_to_doctor/tts_output.py
```

**Expected result:** Speaks three test sentences aloud through the audio output device.

**Requirements:**
- Must not crash if ElevenLabs fails mid-session — fall back to espeak-ng silently
- Must block until audio finishes so elaboration and speaking do not overlap
- Print which TTS mode is active at startup: `TTS: ElevenLabs (online)` or `TTS: espeak-ng (offline)`
- Use pygame for audio playback of ElevenLabs mp3

---

## MODULE 6 — wake_word.py

**Purpose:** Always-on lightweight wake word detection. Activates doctor mic when "SignBridge" is heard.

**What it does:**
- Runs pvporcupine with the built-in "computer" keyword as a proxy (or custom keyword if available)
- When wake word detected: sets `state["mic_active"] = True`
- When stop word detected via Whisper short listen: sets `state["mic_active"] = False`
- Runs as a daemon thread

**Note to Claude Code:** pvporcupine requires a free access key from picovoice.ai. If unavailable, implement a simple energy-threshold + keyword spotter using Whisper on 2-second audio chunks as fallback. The fallback listens continuously in short bursts and checks if the transcript contains "SignBridge" or "done".

**Standalone test:**
```bash
python3 doctor_to_patient/wake_word.py
```

**Expected result:** Terminal prints `WAKE WORD DETECTED` when "SignBridge" is spoken, `MIC DEACTIVATED` when "done" is spoken.

---

## MODULE 7 — transcription.py

**Purpose:** Transcribe doctor speech to text using Whisper when mic is active.

**What it does:**
- Monitors `state["mic_active"]`
- While active: records audio in 4-second chunks using sounddevice
- Passes each chunk to Whisper base model for transcription
- Updates `state["doctor_transcript"]` with latest text
- Stops when `state["mic_active"]` becomes False

**Function interface:**
```python
def transcription_loop() -> None:
    # Runs forever, checks state["mic_active"]
    # Updates state["doctor_transcript"] when active
```

**Standalone test:**
```bash
python3 doctor_to_patient/transcription.py
```

**Expected result:** When run standalone, activates immediately (skipping wake word) and prints transcriptions to terminal as doctor speaks. Stops on Ctrl+C.

**Requirements:**
- Use `whisper.load_model("base")` — load once at startup, not per chunk
- Audio chunks must be float32 numpy arrays
- Must handle silence gracefully — empty transcription should not overwrite last real transcript
- fp16=False for CPU inference on Rubik Pi

---

## MODULE 8 — patient_display.py

**Purpose:** Fullscreen display showing doctor's transcribed words in large text for patient to read.

**What it does:**
- Opens a fullscreen tkinter window with black background
- Monitors `state["doctor_transcript"]` in a polling loop
- Updates displayed text whenever transcript changes
- Text is white, very large (font size 64), centered, word-wrapped

**Standalone test:**
```bash
python3 doctor_to_patient/patient_display.py
```

**Expected result:** Fullscreen black window opens. Terminal accepts typed input. Whatever is typed appears on screen in giant white text simulating what Whisper would send.

**Requirements:**
- Must be fullscreen
- Font size 64 minimum
- White text on black background — high contrast for easy reading
- Word wrap at screen width
- Must update smoothly without flicker
- Press Escape to exit during testing

---

## main.py

**Purpose:** Entry point. Starts all threads and coordinates the full system.

**Thread structure:**
```
main.py
├── pir_thread         — polls GPIO17, updates state["pir_last_motion"]
├── gesture_thread     — runs GestureRecognizer, feeds sign_buffer
├── elaboration_thread — watches sign_buffer, calls elaborate(), calls speak()
├── wake_word_thread   — always-on wake word detection
├── transcription_thread — Whisper transcription when mic active
└── display_thread     — tkinter patient display (must be main thread or separate process)
```

**Important:** tkinter must run on the main thread. Start all other threads as daemons first, then run the tkinter display loop on the main thread.

**Startup sequence:**
1. Print `SignBridge starting...`
2. Load gesture model
3. Load Whisper model
4. Check internet connectivity, print TTS mode
5. Start all daemon threads
6. Speak `"SignBridge is ready. Please sign to communicate."`
7. Start tkinter display on main thread

**Shutdown:** Ctrl+C sets `state["system_active"] = False`, all threads check this and exit cleanly.

---

## tests/

Generate each test file as a completely standalone script that can be run independently to verify each component works before integration.

### test_camera.py
Opens webcam, displays live feed for 5 seconds, prints resolution. Pass/fail.

### test_pir.py
Polls GPIO17 for 10 seconds, prints MOTION or idle every 500ms. Pass/fail.

### test_mediapipe.py
Opens webcam, runs MediaPipe Hands, draws landmarks on feed for 10 seconds. Prints landmark count per frame. Pass/fail.

### test_classifier.py
Loads `gesture_model.pkl`, runs 5 seconds of live classification, prints sign + confidence for every detection. Pass/fail.

### test_tts.py
Calls `speak()` with three test sentences. Verifies audio plays without error. Pass/fail.

### test_llm.py
Calls `elaborate()` with three hardcoded sign buffers. Prints results. Verifies non-empty string returned. Pass/fail.

### test_wakeword.py
Runs wake word detector for 15 seconds. Prints detected events. Pass/fail.

### test_whisper.py
Records 5 seconds of audio from mic, transcribes with Whisper, prints result. Pass/fail.

### test_display.py
Opens patient display, cycles through 3 test messages every 2 seconds automatically. Pass/fail.

---

## Build Order for Claude Code

Generate files in exactly this order. After each module, generate its corresponding test file and confirm it passes before moving on.

1. `config.py`
2. `state.py`
3. `patient_to_doctor/gesture_collector.py` → `tests/test_camera.py` → `tests/test_mediapipe.py`
4. `patient_to_doctor/train_classifier.py` → `tests/test_classifier.py`
5. `patient_to_doctor/gesture_recognition.py`
6. `patient_to_doctor/tts_output.py` → `tests/test_tts.py`
7. `patient_to_doctor/llm_elaboration.py` → `tests/test_llm.py`
8. `doctor_to_patient/wake_word.py` → `tests/test_wakeword.py`
9. `doctor_to_patient/transcription.py` → `tests/test_whisper.py`
10. `doctor_to_patient/patient_display.py` → `tests/test_display.py`
11. `main.py`
12. `setup.sh` + `requirements.txt`

---

## Testing Protocol

Run each test in isolation before integrating. Expected test output format:

```
[TEST] test_camera.py
Camera opened at /dev/video0
Resolution: 1920x1080
PASS

[TEST] test_mediapipe.py
Hand detected: 21 landmarks per frame
Average FPS: 24.3
PASS
```

Any FAIL should block progress on the next module until resolved.

---

## Key Constraints for Claude Code

- All code must run on **Ubuntu 24.04 on Rubik Pi 3 (ARM64)**
- Use `RPi.GPIO` for GPIO — if incompatible with Rubik Pi, fall back to `rubikpi_gpio` with identical pin layout
- All models load once at startup — never reload mid-session
- All threads must check `state["system_active"]` and exit cleanly when False
- No thread should crash the whole application — wrap all thread loops in try/except and log errors
- ElevenLabs and GPT-4o are optional enhancements — system must be fully functional without them using espeak-ng and simple sign concatenation
- `fp16=False` for all Whisper inference — Rubik Pi CPU does not support fp16
- Webcam index is `WEBCAM_INDEX` from config — never hardcode 0
- All file paths use `pathlib.Path` — never hardcode string paths
- Sign vocabulary comes from `config.SIGN_VOCABULARY` — never hardcode in modules

---

## Demo Sequence (for reference)

1. System boots → speaks *"SignBridge is ready. Please sign to communicate."*
2. Patient signs `PAIN` → `CHEST` → `LEFT`
3. After 3 second pause, GPT-4o elaborates → ElevenLabs speaks: *"The patient is reporting pain on the left side of their chest."*
4. Doctor says *"SignBridge"* → mic activates → terminal prints `MIC ACTIVE`
5. Doctor says *"Can you point to exactly where it hurts?"*
6. Words appear in giant text on patient monitor
7. Doctor says *"done"* → mic deactivates → terminal prints `MIC INACTIVE`
8. Patient signs `YES` → system speaks *"The patient confirms yes."*
