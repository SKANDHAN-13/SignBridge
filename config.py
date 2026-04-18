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
