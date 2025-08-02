from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import whisper
import tempfile
import os
import uuid
import pyttsx3
import google.generativeai as genai

# Set Gemini API key
genai.configure(api_key="AIzaSyD6xOl2X1Gqdcqk75CejQSJlORQfm4Ug38")

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

        print("🗣️ Input text:", user_text)

        if not user_text:
            return HttpResponse("Couldn't understand input", status=400)

        # 🤖 Generate code using Gemini
        prompt = (f"Write Python code for this: {user_text}. After that, explain the code line-by-line in a human-friendly way. "
        f"Use 'Explanation:' before the explanation section."
        )
        gemini_model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
        response = gemini_model.generate_content(prompt)

        bot_reply = response.text.strip()
        print("🤖 Gemini says:\n", bot_reply)

        # Extract explanation (optional: refine later)
        explanation_start = bot_reply.rfind("\n\n")
        explanation = bot_reply[explanation_start:].strip() if explanation_start != -1 else bot_reply

        # 🎧 Speak explanation
        tts = pyttsx3.init()
        tts.setProperty('rate', 160)
        audio_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
        tts.save_to_file(explanation, audio_path)
        tts.runAndWait()
        print("🔊 Voice saved:", audio_path)

        audio_url = f"/audio/{os.path.basename(audio_path)}"

        return JsonResponse({
            "transcript": user_text,
            "code": bot_reply,
            "audio_url": audio_url
        })

    return render(request, 'index.html')

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def run_code_view(request):
    if request.method == 'POST':
        try:
            code = request.POST.get("code", "")
            local_vars = {}

            # ⚠️ Be cautious! `exec()` is risky.
            exec(code, {}, local_vars)

            # Capture output if any (basic)
            output = ""
            if "_result" in local_vars:
                output = str(local_vars["_result"])
            else:
                output = "✅ Code executed successfully."

            return JsonResponse({"output": output})

        except Exception as e:
            return JsonResponse({"output": f"❌ Error: {str(e)}"})

    return JsonResponse({"output": "❌ Invalid request method"})