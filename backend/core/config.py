import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Azure Speech & OpenAI
    AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SPEECH_ENDPOINT = os.getenv("AZURE_SPEECH_ENDPOINT")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
    AZURE_DEPLOYMENT_NAME_EMBEDDING = os.getenv("AZURE_DEPLOYMENT_NAME_EMBEDDING")

    # Azure Storage
    AZURE_STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
    BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
    
    #Pinecone
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

settings = Settings()