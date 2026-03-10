# backend/community/router.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from firebase_admin import firestore
from datetime import datetime
from core.database import db
from core.security import get_current_user

router = APIRouter()


class PostCreate(BaseModel):
    content: str


class CommentCreate(BaseModel):
    content: str


@router.post("/")
async def create_post(post: PostCreate, user: dict = Depends(get_current_user)):
    """Creates a new community post."""
    try:
        # Fetch the user's username from Firestore
        user_doc = db.collection("users").document(user["uid"]).get()
        username = user_doc.to_dict().get("username", "Unknown User") if user_doc.exists else "Unknown User"

        doc_ref = db.collection("community_posts").document()
        post_data = {
            "id": doc_ref.id,
            "author_id": user["uid"],
            "author_username": username,
            "content": post.content,
            "created_at": firestore.SERVER_TIMESTAMP,
            "comments": []
        }

        doc_ref.set(post_data)
        return {"message": "Post created successfully", "post_id": doc_ref.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_posts(user: dict = Depends(get_current_user)):
    """Fetches all posts ordered by newest first."""
    try:
        docs = db.collection("community_posts").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        posts = []
        for doc in docs:
            data = doc.to_dict()
            # Convert timestamp to string for the frontend
            if "created_at" in data and data["created_at"] is not None:
                data["created_at"] = data["created_at"].isoformat()
            posts.append(data)
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{post_id}/comments")
async def add_comment(post_id: str, comment: CommentCreate, user: dict = Depends(get_current_user)):
    """Adds a comment to an existing post."""
    try:
        user_doc = db.collection("users").document(user["uid"]).get()
        username = user_doc.to_dict().get("username", "Unknown User") if user_doc.exists else "Unknown User"

        post_ref = db.collection("community_posts").document(post_id)
        if not post_ref.get().exists:
            raise HTTPException(status_code=404, detail="Post not found")

        new_comment = {
            "author_id": user["uid"],
            "author_username": username,
            "content": comment.content,
            "created_at": datetime.utcnow().isoformat()
        }

        # Atomically add the comment to the array
        post_ref.update({
            "comments": firestore.ArrayUnion([new_comment])
        })

        return {"message": "Comment added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))