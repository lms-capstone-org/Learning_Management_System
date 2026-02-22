import os
import time
import requests
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, UserDelegationKey
from openai import AzureOpenAI
from firebase_admin import firestore
from core.config import settings
from core.database import db

# --- INITIALIZE AZURE CLIENTS (AAD AUTH) ---
# We use DefaultAzureCredential so we don't need the Storage Key
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url=settings.AZURE_STORAGE_ACCOUNT_URL,
    credential=credential
)


def upload_transcript_to_blob(text_content, course_id, module_id):
    """
    Uploads the transcript text to Azure Blob Storage (videos container -> transcripts folder).
    Returns the direct URL (Frontend may need to generate a SAS for this later).
    """
    try:
        # Structure: transcripts/course_id/module_id.txt
        blob_path = f"transcripts/{course_id}/{module_id}.txt"

        blob_client = blob_service_client.get_blob_client(
            container=settings.BLOB_CONTAINER_NAME,
            blob=blob_path
        )

        # Upload text
        blob_client.upload_blob(text_content, overwrite=True)
        print(f"💾 Transcript saved to: {blob_path}")

        return blob_client.url, blob_path
    except Exception as e:
        print(f"❌ Failed to upload transcript to blob: {e}")
        raise e


def run_ai_pipeline(video_sas_url, course_id, module_id, video_name):
    print(f"🚀 Starting AI Pipeline for Module: {module_id}")

    # Use module_id as the Document ID in ai_assets
    doc_ref = db.collection("ai_assets").document(module_id)

    # Initialize Document
    doc_ref.set({
        "status": "transcribing",
        "linked_course_id": course_id,
        "linked_module_id": module_id,
        "created_at": firestore.SERVER_TIMESTAMP
    }, merge=True)

    try:
        # --- STEP 1: TRANSCRIPTION (Azure Speech REST API) ---
        # Note: We still use the Key for Speech because it's a specific Cognitive Service
        print("🎤 Step 1: Transcribing Video...")

        url = f"{settings.AZURE_SPEECH_ENDPOINT.rstrip('/')}/speechtotext/v3.1/transcriptions"
        headers = {
            "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
            "Content-Type": "application/json"
        }

        body = {
            "displayName": f"{course_id}_{module_id}",
            "locale": "en-US",
            "contentUrls": [video_sas_url],  # Speech Service downloads video from here
            "properties": {
                "punctuationMode": "DictatedAndAutomatic",
                "profanityFilterMode": "Masked"
            }
        }

        r = requests.post(url, headers=headers, json=body)
        if r.status_code >= 400:
            raise Exception(f"Speech Service rejected request: {r.text}")

        transcription_job_url = r.json()["self"]

        # Polling Loop
        transcript_text = ""
        while True:
            time.sleep(5)
            r = requests.get(transcription_job_url, headers={"Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY})
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

        # Handle Silent Video
        if len(transcript_text) < 5:
            doc_ref.update({"status": "completed", "summary_markdown": "No speech detected in this video."})
            print(f"⚠️ No speech detected for {video_name}")
            return

        # --- STEP 2: UPLOAD TRANSCRIPT TO BLOB ---
        print("💾 Step 2: Uploading Transcript to Blob...")
        transcript_url, transcript_path = upload_transcript_to_blob(transcript_text, course_id, module_id)

        # Save URL and Path to Firestore
        doc_ref.update({
            "transcript_blob_url": transcript_url,
            "transcript_storage_path": transcript_path,  # Useful for generating SAS later
            "status": "summarizing"
        })

        # --- STEP 3: SUMMARIZATION (Azure OpenAI) ---
        print("🧠 Step 3: Generating Summary...")

        client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )

        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system",
                 "content": "You are an expert tutor. Create a concise markdown summary of this transcript."},
                {"role": "user", "content": transcript_text[:15000]}  # Truncate to save tokens
            ]
        )
        summary_md = response.choices[0].message.content

        # --- STEP 4: SAVE FINAL RESULTS ---
        doc_ref.update({
            "status": "completed",
            "summary_markdown": summary_md,
            "model_used": settings.AZURE_OPENAI_DEPLOYMENT
        })
        print(f"🎉 AI Pipeline Finished for Module: {module_id}")

    except Exception as e:
        print(f"❌ Pipeline Error: {str(e)}")
        doc_ref.update({
            "status": "failed",
            "error": str(e)
        })


