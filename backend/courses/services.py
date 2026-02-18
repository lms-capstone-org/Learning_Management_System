import os
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from core.config import settings

# Initialize Azure Blob Client
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(settings.AZURE_STORAGE_ACCOUNT_URL, credential=credential)

def generate_read_sas(blob_path: str):
    """Generates a secure Read-Only link for the video."""
    try:
        now = datetime.utcnow()
        # Start 5 mins ago to prevent clock skew errors
        start_time = now - timedelta(minutes=5)
        expiry_time = now + timedelta(hours=24)

        delegation_key = blob_service_client.get_user_delegation_key(
            key_start_time=start_time,
            key_expiry_time=expiry_time
        )

        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=settings.BLOB_CONTAINER_NAME,
            blob_name=blob_path,
            user_delegation_key=delegation_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            start=start_time
        )
        return f"{settings.AZURE_STORAGE_ACCOUNT_URL}/{settings.BLOB_CONTAINER_NAME}/{blob_path}?{sas_token}"
    except Exception as e:
        print(f"❌ Error generating SAS: {e}")
        return None

def upload_blob(file_content, blob_path):
    """Uploads bytes to Azure Blob Storage."""
    blob_client = blob_service_client.get_blob_client(
        container=settings.BLOB_CONTAINER_NAME, 
        blob=blob_path
    )
    blob_client.upload_blob(file_content, overwrite=True)