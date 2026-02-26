from firebase_admin import auth, firestore
from core.database import db

VALID_ROLES = ["student", "instructor", "admin"]

class AdminService:

    @staticmethod
    def assign_role(uid: str, role: str):
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of {VALID_ROLES}")

        try:
            auth.get_user(uid)
        except auth.UserNotFoundError:
            raise ValueError("User not found in Firebase Auth")

        auth.set_custom_user_claims(uid, {"role": role})

        db.collection("users").document(uid).update({
            "role": role,
            "updated_at": firestore.SERVER_TIMESTAMP
        })

        return {"uid": uid, "role": role}

    @staticmethod
    def get_user(uid: str):
        doc = db.collection("users").document(uid).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data["uid"] = uid
        return data

    @staticmethod
    def list_users(limit: int = 20, cursor: str = None, role: str = None, search: str = None):
        
        # Firestore limitation: can't combine role filter + email search
        # without a composite index — so we handle them separately
        query = db.collection("users")

        if role and not search:
            query = query.where("role", "==", role)

        if search:
            end = search + "\uf8ff"
            query = query.where("email", ">=", search).where("email", "<=", end)

        if cursor:
            last_doc = db.collection("users").document(cursor).get()
            if last_doc.exists:
                query = query.start_after(last_doc)
            # if cursor doc doesn't exist, just ignore and fetch from beginning

        fetch_limit = limit * 5 if (role and search) else limit
        docs = query.limit(fetch_limit).stream()

        users = []
        last_uid = None

        for doc in docs:
            data = doc.to_dict()
            data["uid"] = doc.id
            # Post-filter by role if search is also active (Firestore limitation workaround)
            if role and search and data.get("role") != role:
                continue
            users.append(data)
            last_uid = doc.id

        trimmed = users[:limit]
        return {
            "users": trimmed,
            "next_cursor": last_uid if len(trimmed) == limit else None,
            "limit": limit
        }