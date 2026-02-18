import time
import requests
from openai import AzureOpenAI
from firebase_admin import firestore
from core.config import settings
from core.database import db 

def run_ai_pipeline(video_id, blob_url, video_name):
    print(f"🚀 Starting AI Pipeline for: {video_name}")
    
    # Reference to the Firestore document
    doc_ref = db.collection("videos").document(video_id)
    
    # Update status to indicate transcription started
    doc_ref.update({"status": "transcribing"})

    try:
        # --- STEP 1: TRANSCRIPTION (Azure Speech) ---
        url = f"{settings.AZURE_SPEECH_ENDPOINT.rstrip('/')}/speechtotext/v3.1/transcriptions"
        headers = {
            "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY, 
            "Content-Type": "application/json"
        }
        
        body = {
            "displayName": video_name,
            "locale": "en-US",
            "contentUrls": [blob_url],
            "properties": {
                "punctuationMode": "DictatedAndAutomatic",
                "profanityFilterMode": "Masked"
            }
        }

        r = requests.post(url, headers=headers, json=body)
        if r.status_code >= 400:
            raise Exception(f"Speech Service rejected request: {r.text}")

        transcription_url = r.json()["self"]

        # Polling Loop
        transcript_text = ""
        while True:
            time.sleep(5) # Wait 5 seconds between checks
            r = requests.get(transcription_url, headers={"Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY})
            status = r.json()["status"]
            
            if status == "Succeeded":
                files_url = r.json()["links"]["files"]
                files_r = requests.get(files_url, headers={"Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY})
                for f in files_r.json()["values"]:
                    if f["kind"] == "Transcription":
                        content = requests.get(f["links"]["contentUrl"]).json()
                        for phrase in content.get("recognizedPhrases", []):
                            if "nBest" in phrase and len(phrase["nBest"]) > 0:
                                transcript_text += phrase["nBest"][0]["display"] + " "
                break
            elif status == "Failed":
                raise Exception("Azure Speech Analysis Failed")

        # Handle empty video / silent video
        if len(transcript_text) < 5:
            doc_ref.update({"status": "completed", "summary": "No speech detected in this video."})
            print(f"⚠️ No speech detected for {video_name}")
            return

        # --- STEP 2: SUMMARIZATION (Azure OpenAI) ---
        doc_ref.update({"status": "summarizing"})
        
        client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )

        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an expert tutor. Summarize this educational transcript into clear bullet points."},
                {"role": "user", "content": transcript_text[:12000]} # Limit char count for token safety
            ]
        )
        summary_text = response.choices[0].message.content

        # --- STEP 3: SAVE RESULTS ---
        doc_ref.update({
            "status": "completed",
            "transcript": transcript_text,
            "summary": summary_text
        })
        print(f"🎉 Pipeline Finished for {video_name}")

    except Exception as e:
        print(f"❌ Pipeline Error: {str(e)}")
        doc_ref.update({
            "status": "failed", 
            "summary": "AI Processing Failed. Please contact support.",
            "error": str(e)
        })