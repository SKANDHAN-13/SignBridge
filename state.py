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
