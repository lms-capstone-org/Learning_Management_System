import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys

def initialize_firebase():
    """Initializes Firebase App if it hasn't been initialized yet."""
    
    # 1. Get the directory where THIS file (database.py) lives
    # This will result in: .../backend/core
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Build the full path to the config file
    cred_path = os.path.join(current_dir, "firebase_config.json")

    print(f"🔍 Looking for Firebase Config at: {cred_path}")

    if not firebase_admin._apps:
        if os.path.exists(cred_path):
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("🔥 Firebase Initialized Successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Firebase: {e}")
                sys.exit(1) # Stop the app if credentials are bad
        else:
            print(f"❌ CRITICAL ERROR: Config file not found at: {cred_path}")
            print("   -> Make sure 'firebase_config.json' is inside the 'backend/core' folder.")
            sys.exit(1) # Stop the app so you see the error immediately
    
    return firestore.client()

# Create the shared DB instance
db = initialize_firebase()