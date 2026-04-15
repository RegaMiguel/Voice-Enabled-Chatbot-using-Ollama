import pyttsx3
import subprocess
import sounddevice as sd
from faster_whisper import WhisperModel
from scipy.io.wavfile import write


model = WhisperModel("base", device = "cpu", compute_type = "int8")

def record_audio(filename = "input.wav", duration = 5, fs = 16000):
    print("Listening.....")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels = 1)
    sd.wait()
    write(filename, fs, recording)

def transcribe_audio(filename = "input.wav"):
    segments, _ = model.transcribe(filename)
    return " ".join([seg.text for seg in segments])

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def ask_llm(prompt):
    result = subprocess.run(
        ["D:\\Microsoft VS Code Projects\\Ollama\\ollama.exe", "run", "mistral"], # Redirect to ollama.exe
        input = prompt.encode(),
        stdout= subprocess.PIPE
    )
    return result.stdout.decode()

while True:
    record_audio()

    user_input = transcribe_audio()
    print("You: ", user_input)

    if user_input.strip() == "":
        continue

    response = ask_llm(user_input)

    print("Model: ", response)

    speak(response)