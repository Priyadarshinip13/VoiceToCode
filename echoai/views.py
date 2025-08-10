from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import whisper
import tempfile
import os
import uuid
from elevenlabs import ElevenLabs
import google.generativeai as genai

# 🔹 Set Gemini API Key
genai.configure(api_key="AIzaSyD6xOl2X1Gqdcqk75CejQSJlORQfm4Ug38")

# 🔹 ElevenLabs API Key
ELEVEN_API_KEY = "sk_f35dac392830ae99fe8d0ea9d77cd9be3e6521b518906ffd"
tts_client = ElevenLabs(api_key=ELEVEN_API_KEY)

@csrf_exempt
def index_view(request):
    if request.method == 'POST':
        print("📡 POST received")

        # 1️⃣ Handle Text Input
        user_text = request.POST.get('text')
        
        # 2️⃣ Handle Voice Input
        if not user_text:
            audio_file = request.FILES.get('audio')
            if not audio_file:
                return HttpResponse("No input provided", status=400)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
                for chunk in audio_file.chunks():
                    temp.write(chunk)
                temp_path = temp.name

            print("🧠 Transcribing:", temp_path)
            model = whisper.load_model("base")
            result = model.transcribe(temp_path, fp16=False)
            user_text = result.get('text', '').strip()

        print("Input text:", user_text)

        if not user_text:
            return HttpResponse("Couldn't understand input", status=400)

        # 🤖 Generate code using Gemini
        prompt = (
            f"Write a user specified programming language code for this: {user_text}. "
            f"After that, explain should be simple (10 line points explanation, each line ≤ 7 words) "
            f"with clean code explained line-by-line in a human-friendly way. "
            f"Use 'Explanation:' before the explanation section."
        )
        gemini_model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
        response = gemini_model.generate_content(prompt)

        bot_reply = response.text.strip()
        print("🤖 Gemini says:\n", bot_reply)

        # Extract explanation (optional: refine later)
        explanation_start = bot_reply.rfind("\n\n")
        explanation = bot_reply[explanation_start:].strip() if explanation_start != -1 else bot_reply

        # 🎧 Speak explanation with ElevenLabs
        audio_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
        audio_stream = tts_client.text_to_speech.convert(
        voice_id="yM93hbw8Qtvdma2wCnJG",  # Replace with your actual Voice ID
        model_id="eleven_multilingual_v2",
        text=explanation
        )

        with open(audio_path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        print("🔊 Voice saved:", audio_path)
        audio_url = f"/audio/{os.path.basename(audio_path)}"

        return JsonResponse({
            "transcript": user_text,
            "code": bot_reply,
            "audio_url": audio_url
        })

    return render(request, 'index.html')


@csrf_exempt
def run_code_view(request):
    if request.method == 'POST':
        try:
            code = request.POST.get("code", "")
            local_vars = {}

            # ⚠️ Be cautious! `exec()` can be dangerous.
            exec(code, {}, local_vars)

            # Capture output if any
            output = ""
            if "_result" in local_vars:
                output = str(local_vars["_result"])
            else:
                output = "✅ Code executed successfully."

            return JsonResponse({"output": output})

        except Exception as e:
            return JsonResponse({"output": f"❌ Error: {str(e)}"})

    return JsonResponse({"output": "❌ Invalid request method"})
