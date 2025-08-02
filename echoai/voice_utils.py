import whisper
from TTS.api import TTS
import os

model = whisper.load_model("base")

def transcribe_audio(path):
    result = model.transcribe(path)
    return result["text"]

tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)

def generate_voice_reply(text):
    output_path = f"echoai/static/audio/reply.wav"
    tts.tts_to_file(text=text, file_path=output_path)
    return "/static/audio/reply.wav"
