# SignBridge

A two-way real-time communication system for deaf and hard-of-hearing patients in emergency medical settings.

## Overview

SignBridge runs on a Rubik Pi 3 and provides bidirectional communication:

- **Patient → Doctor:** Webcam captures patient signing → MediaPipe detects landmarks → classifier maps to signs → GPT-4o elaborates into a sentence → ElevenLabs speaks to doctor
- **Doctor → Patient:** Wake word activates mic → Whisper transcribes speech → large text printed to monitor for patient to read

## Hardware Requirements

- Rubik Pi 3 (Ubuntu 24.04)
- USB Webcam 1080p
- HC-SR501 PIR sensor on GPIO17
- Speaker or headphones via 3.5mm jack
- Monitor via HDMI for patient-facing text display

## Installation

### Development on macOS

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install macOS-compatible dependencies:**
   ```bash
   pip install -r requirements-macos.txt
   ```

   Note: `RPi.GPIO` and `pygame` are excluded on macOS (only needed on Rubik Pi)

3. **Configure API keys in `config.py`:**
   - `OPENAI_API_KEY` - Get from https://platform.openai.com/
   - `ELEVENLABS_API_KEY` - Get from https://elevenlabs.io/
   - `PORCUPINE_ACCESS_KEY` - Get from https://picovoice.ai/ (free tier)

### Deployment on Rubik Pi (Ubuntu 24.04)

1. **Install system dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-opencv espeak-ng portaudio19-dev -y
   ```

2. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

   Or use the provided setup script:
   ```bash
   ./setup.sh
   ```

3. **Configure API keys** as above

## Setup Workflow

### 1. Collect Training Data

```bash
python3 patient_to_doctor/gesture_collector.py
```

This will guide you through collecting 50 samples of each sign in the vocabulary. Press SPACE to start recording each sign, Q to skip.

### 2. Train the Classifier

```bash
python3 patient_to_doctor/train_classifier.py
```

This trains a Random Forest classifier on the collected data and saves it to `gesture_model.pkl`.

### 3. Run the System

```bash
python3 main.py
```

## Testing

Each module has an independent test script:

```bash
# Hardware tests
python3 tests/test_camera.py       # Test webcam
python3 tests/test_pir.py          # Test PIR sensor
python3 tests/test_mediapipe.py    # Test hand detection

# Patient → Doctor pipeline
python3 tests/test_classifier.py   # Test gesture classifier
python3 tests/test_llm.py          # Test GPT-4o elaboration
python3 tests/test_tts.py          # Test text-to-speech

# Doctor → Patient pipeline
python3 tests/test_wakeword.py     # Test wake word detection
python3 tests/test_whisper.py      # Test speech transcription
python3 tests/test_display.py      # Test patient display
```

## Usage

### Patient Communication (Sign → Speech)

1. Patient signs to the camera
2. System detects and buffers signs
3. After 3 second pause, GPT-4o elaborates the signs into a coherent sentence
4. ElevenLabs speaks the sentence to the doctor

### Doctor Communication (Speech → Text)

1. Doctor says the wake word ("SignBridge" or "computer")
2. Mic activates (indicated by terminal message)
3. Doctor speaks their message
4. Text appears in large font on patient display
5. Doctor says "done" to deactivate mic

### Exit

Press ESC in the display window or Ctrl+C in terminal.

## Project Structure

```
signbridge/
├── config.py                  # Configuration and API keys
├── state.py                   # Shared state between threads
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
├── setup.sh                   # Installation script
│
├── patient_to_doctor/
│   ├── gesture_collector.py   # Collect training data
│   ├── train_classifier.py    # Train Random Forest classifier
│   ├── gesture_recognition.py # Real-time gesture recognition
│   ├── llm_elaboration.py     # GPT-4o elaboration
│   └── tts_output.py          # Text-to-speech output
│
├── doctor_to_patient/
│   ├── wake_word.py           # Wake word detection
│   ├── transcription.py       # Whisper transcription
│   └── patient_display.py     # Fullscreen text display
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

## Sign Vocabulary

Default vocabulary (configurable in `config.py`):
- YES, NO
- PAIN, CHEST, LEFT, RIGHT
- HEADACHE, DIZZY, BLEEDING, JOINT

## Offline Mode

SignBridge works without internet:
- TTS falls back to espeak-ng
- LLM elaboration falls back to simple concatenation
- Wake word detection uses Whisper fallback

## Troubleshooting

### Gesture model not found
Run `train_classifier.py` after collecting training data with `gesture_collector.py`

### Camera not opening
Check webcam index in `config.py` (default: 0)

### No audio output
- Check speaker/headphone connection
- Install espeak-ng: `sudo apt install espeak-ng`

### Wake word not working
- Install pvporcupine and configure API key, OR
- System will automatically fall back to Whisper-based detection

### GPIO errors on non-Raspberry Pi systems
PIR sensor is optional and will be skipped if RPi.GPIO is not available

## Performance Notes

- Whisper "base" model recommended for Rubik Pi (good accuracy/speed balance)
- All models load once at startup for efficiency
- Use `fp16=False` for CPU inference
- Gesture recognition runs at ~20-30 FPS

## License

Built for StarkHacks 2026
