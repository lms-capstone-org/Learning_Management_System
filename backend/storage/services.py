"""
Azure Blob Storage services
"""
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from core.config import settings
from core.exceptions import StorageException


def generate_upload_sas(blob_path: str, expiry_hours: int = 1) -> str:
    """
    Generate a SAS URL for uploading a file to Azure Blob Storage.

    Args:
        blob_path: Path in blob storage
        expiry_hours: SAS token expiry in hours

    Returns:
        SAS URL for upload
    """
    try:
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            settings.AZURE_STORAGE_ACCOUNT_URL,
            credential=credential
        )

        now = datetime.utcnow()
        start_time = now - timedelta(minutes=5)  # Prevent clock skew
        expiry_time = now + timedelta(hours=expiry_hours)

        # Get user delegation key
        delegation_key = blob_service_client.get_user_delegation_key(
            key_start_time=start_time,
            key_expiry_time=expiry_time
        )

        # Generate SAS token with write permission
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=settings.BLOB_CONTAINER_NAME,
            blob_name=blob_path,
            user_delegation_key=delegation_key,
            permission=BlobSasPermissions(write=True, create=True),
            expiry=expiry_time,
            start=start_time
        )

        sas_url = f"{settings.AZURE_STORAGE_ACCOUNT_URL}/{settings.BLOB_CONTAINER_NAME}/{blob_path}?{sas_token}"
        return sas_url

    except Exception as e:
        raise StorageException(f"SAS generation failed: {str(e)}")


def generate_download_sas(blob_path: str, expiry_hours: int = 24) -> str:
    """
    Generate a read-only SAS URL for downloading a file.
    (This already exists in courses/services.py but duplicated here for clarity)

    Args:
        blob_path: Path in blob storage
        expiry_hours: SAS token expiry in hours

    Returns:
        Read-only SAS URL
    """
    try:
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            settings.AZURE_STORAGE_ACCOUNT_URL,
            credential=credential
        )

        now = datetime.utcnow()
        start_time = now - timedelta(minutes=5)
        expiry_time = now + timedelta(hours=expiry_hours)

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

        sas_url = f"{settings.AZURE_STORAGE_ACCOUNT_URL}/{settings.BLOB_CONTAINER_NAME}/{blob_path}?{sas_token}"
        return sas_url

    except Exception as e:
        raise StorageException(f"SAS generation failed: {str(e)}")