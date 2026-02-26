from firebase_admin import firestore
from core.database import db

class UserService:

    @staticmethod
    def get_profile(uid: str):
        doc = db.collection("users").document(uid).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data["uid"] = uid
        return data

    @staticmethod
    def update_profile(uid: str, updates: dict):
        updates["updated_at"] = firestore.SERVER_TIMESTAMP
        db.collection("users").document(uid).update(updates)
        return UserService.get_profile(uid)

    @staticmethod
    def ensure_user_exists(uid: str, email: str):
        """
        Called on every login.
        Creates Firestore doc if it doesn't exist.
        If it exists, just updates last_login.
        """
        doc_ref = db.collection("users").document(uid)
        doc = doc_ref.get()

        if not doc.exists:
            # First time login — create the document
            doc_ref.set({
                "email": email,
                "role": "student",
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_login": firestore.SERVER_TIMESTAMP,
            })
        else:
            # Existing user — just update last_login
            doc_ref.update({
                "last_login": firestore.SERVER_TIMESTAMP,
            })
            
        return UserService.get_profile(uid)