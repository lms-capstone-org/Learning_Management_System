# backend/core/security.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
import firebase_admin

# This tells FastAPI to expect a "Bearer" token in the Header
security_scheme = HTTPBearer()

def get_current_user(cred: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """
    Validates the Firebase ID Token sent by the Frontend.
    Returns the User Dictionary (uid, email, etc.) if valid.
    """
    token = cred.credentials
    try:
        # Verify the token with Firebase Auth
        decoded_token = auth.verify_id_token(token)
        
        # Return the user data to the endpoint
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "role": decoded_token.get("role", "student") # specific to your schema
        }
        
    except firebase_admin.auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please login again."
        )
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )