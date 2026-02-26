from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

from core.database import db

security_scheme = HTTPBearer()


def get_current_user(cred: HTTPAuthorizationCredentials = Depends(security_scheme)):
    token = cred.credentials
    try:
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        uid = decoded_token["uid"]

        # Default role if nothing is configured
        role = "student"

        # 1) Try to read the authoritative role from Firestore (admin panel updates this)
        try:
            doc = db.collection("users").document(uid).get()
            if doc.exists:
                data = doc.to_dict() or {}
                if data.get("role"):
                    role = data["role"]
        except Exception:
            # If Firestore is temporarily unavailable, fall back to token claims
            pass

        # 2) If Firestore had no role field, fall back to custom claims (older tokens)
        if role == "student":
            role = decoded_token.get("role", "student")

        return {
            "uid": uid,
            "email": decoded_token.get("email"),
            "role": role,
        }

    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.")
    except auth.RevokedIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked.")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")


# Reusable role checkers — use these as dependencies in your routes
def require_admin(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


def require_instructor(user: dict = Depends(get_current_user)):
    if user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Instructor access required.")
    return user


def require_student(user: dict = Depends(get_current_user)):
    if user["role"] != "student":
        raise HTTPException(status_code=403, detail="Access denied.")
    return user

def require_auth(user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin","instructor","student"] :
        raise HTTPException(status_code=403, detail="Access denied.")
    return user


def require_instructor_or_admin(user: dict = Depends(get_current_user)):
    if user["role"] not in ["instructor", "admin"]:
        raise HTTPException(status_code=403, detail="Instructor or Admin access required.")
    return user