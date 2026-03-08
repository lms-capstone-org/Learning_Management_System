import json
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
from pinecone import Pinecone
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- INITIALIZE PINECONE ---
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
pinecone_index = pc.Index(settings.PINECONE_INDEX_NAME)
from ai_features.ai_quiz.quiz_generator import generate_quiz

# --- INITIALIZE AZURE CLIENTS (AAD AUTH) ---
# We use DefaultAzureCredential so we don't need the Storage Key
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url=settings.AZURE_STORAGE_ACCOUNT_URL,
    credential=credential
)
openai_client = AzureOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,  # or your version
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
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

def ingest_to_pinecone(transcript_text, course_id, module_id):
    """
    Chunks the transcript text, creates embeddings, and upserts to Pinecone.
    Uses 'course_id' as the namespace.
    """
    print(f"🌲 Step 5: Ingesting into Pinecone (Namespace: {course_id})...")
    
    try:
        # 1. Chunk the text
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(transcript_text)

        # 2. Initialize OpenAI Client for Embeddings
        client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )

        vectors = []

        # 3. Process Chunks
        for i, chunk in enumerate(chunks):
            # Generate Embedding
            response = client.embeddings.create(
                input=chunk,
                model=settings.AZURE_DEPLOYMENT_NAME_EMBEDDING # Ensure this is in your config/env
            )
            embedding = response.data[0].embedding
            
            # Create Unique Vector ID
            vector_id = f"{module_id}_{i}"

            # Prepare Metadata
            metadata = {
                "text": chunk,
                "module_id": module_id,
                "course_id": course_id,
                "chunk_index": i
            }

            vectors.append((vector_id, embedding, metadata))

        # 4. Upsert to Pinecone
        # Batching is automatic in some clients, but for safety with large transcripts:
        pinecone_index.upsert(vectors=vectors, namespace=course_id)
        
        print(f"✅ Upserted {len(vectors)} chunks to Pinecone.")
        return True

    except Exception as e:
        print(f"❌ Pinecone Ingestion Failed: {e}")
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
        "created_at": firestore.SERVER_TIMESTAMP,
        "is_vectorized": False 
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
        
                # --- STEP 4: QUIZ GENERATION ---
        print("📝 Step 4: Generating Quiz...")
        questions = generate_quiz(transcript_text)

        # --- STEP 5: VECTORIZE ---
        print("🌲 Step 5: Ingesting into Pinecone...")
        ingest_to_pinecone(transcript_text, course_id, module_id)

                # --- FINAL SAVE ---
        doc_ref.update({
            "status": "completed",
            "summary_markdown": summary_md,
            "questions": questions,
            "model_used": settings.AZURE_OPENAI_DEPLOYMENT,
            "quiz_generated_at": firestore.SERVER_TIMESTAMP,
            "is_vectorized": True
        })


        

      

        # --- STEP 4: SAVE FINAL RESULTS ---
        doc_ref.update({
    "status": "completed",
    "summary_markdown": summary_md,
    "questions": questions,
    "model_used": settings.AZURE_OPENAI_DEPLOYMENT,
    "quiz_generated_at": firestore.SERVER_TIMESTAMP
})
        db.collection("courses").document(course_id).collection("modules").document(module_id).update({
            "status": "completed"
        })

        print(f"🎉 AI Pipeline Finished for Module: {module_id}")

    except Exception as e:
        print(f"❌ Pipeline Error: {str(e)}")
        doc_ref.update({
            "status": "failed",
            "error": str(e)
        })

# ... (Previous code in services.py) ...

def generate_course_answer(course_id: str, question: str):
    """
    RAG Logic:
    1. Embeds the user question.
    2. Searches Pinecone ONLY within the 'course_id' namespace.
    3. Sends context + question to Azure OpenAI.
    """
    print(f"💬 Chatting with Course: {course_id}")

    try:
        # 1. Embed Question
        # Ensure you have AZURE_DEPLOYMENT_NAME_EMBEDDING in your settings
        emb_response = openai_client.embeddings.create(
            input=question,
            model=settings.AZURE_DEPLOYMENT_NAME_EMBEDDING
        )
        query_vector = emb_response.data[0].embedding

        # 2. Query Pinecone (Strict Namespace Isolation)
        # We request the top 5 most relevant chunks
        search_results = pinecone_index.query(
            vector=query_vector,
            namespace=course_id,  # <--- CRITICAL: This restricts search to this course only
            top_k=5,
            include_metadata=True
        )

        # 3. Construct Context
        context_texts = []
        for match in search_results.matches:
            # Only use matches with a decent similarity score (optional guardrail)
            if match.score > 0.70: 
                context_texts.append(match.metadata['text'])
        
        # If no relevant context found
        if not context_texts:
            return "I couldn't find any information in the course materials related to your question."

        full_context = "\n\n".join(context_texts)

        # 4. Generate Answer via GPT-4
        system_prompt = f"""You are an AI Tutor for the course ID '{course_id}'.
        Answer the student's question based ONLY on the context provided below.
        If the answer is not in the context, state that you don't know.
        
        Context from Course Materials:
        {full_context}
        """

        response = openai_client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.5 # Lower temperature for more factual answers
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ Chat Error: {e}")
        raise e
