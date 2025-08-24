import threading
import time
import queue
from vosk import Model, KaldiRecognizer
import pyaudio

# === SurgeCell Sim ===
def surgecell_monitor():
    while True:
        print("[SurgeCell] Monitoring load...")
        time.sleep(10)

# === Reflexive Loop ===
def reflexive_loop():
    while True:
        print("[Jarvis Prime] Reflexive loop active...")
        time.sleep(5)

# === Voice Listener ===
def voice_listener(command_queue):
    model = Model(lang="en-us")
    recognizer = KaldiRecognizer(model, 16000)
    mic = pyaudio.PyAudio()
    stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()
    print("[Jarvis Prime] Voice listener active...")

    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = recognizer.Result()
            text = eval(result).get('text', '')
            if text:
                command_queue.put(text)

# === Command Listener ===
def command_listener():
    command_queue = queue.Queue()

    # Start voice listener
    threading.Thread(target=voice_listener, args=(command_queue,), daemon=True).start()

    while True:
        if not command_queue.empty():
            user_input = command_queue.get()
            print(f"[Jarvis Prime] Heard command: '{user_input}'")

        user_input = input("[Jarvis Prime] Enter evolution command: ")
        if user_input.lower() == 'exit':
            print("[Jarvis Prime] Shutting down...")
            break
        else:
            print(f"[Jarvis Prime] Logged command: '{user_input}'")

if __name__ == '__main__':
    threading.Thread(target=reflexive_loop, daemon=True).start()
    threading.Thread(target=surgecell_monitor, daemon=True).start()
    command_listener()
