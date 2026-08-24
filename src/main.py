from fastapi import FastAPI, HTTPException
from src.db import get_db
from src.matching import suggest_image_for_post

app = FastAPI(title="AI Image Understanding & Content Matching Engine")

@app.get("/")
def root():
    return {"name": "Image Relevance Engine", "version": "1.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/posts/{post_id}/images")
def get_images_for_post(post_id: int):
    conn = get_db()
    post = conn.execute("SELECT id FROM posts WHERE id = %s", (post_id,)).fetchone()
    conn.close()

    if post is None:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    return suggest_image_for_post(post_id)

@app.get("/posts")
def list_posts():
    conn = get_db()
    rows = conn.execute("SELECT id, title, primary_subject FROM posts ORDER BY id").fetchall()
    conn.close()
    return rows

@app.post("/posts/{post_id}/suggestions", status_code=201)
def create_suggestion(post_id: int):
    """Run matching for a post and save the result as a pending suggestion."""
    conn = get_db()
    post = conn.execute("SELECT id FROM posts WHERE id = %s", (post_id,)).fetchone()
    if post is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    result = suggest_image_for_post(post_id)

    if result["status"] != "match_found":
        conn.close()
        return {"status": "no_confident_match", "reason": result["reason"]}

    suggestion = result["suggestion"]
    row = conn.execute(
        """INSERT INTO suggestions (post_id, image_id, similarity_score, status)
           VALUES (%s, %s, %s, 'pending') RETURNING id""",
        (post_id, suggestion["image_id"], suggestion["similarity_score"])
    ).fetchone()
    conn.commit()
    conn.close()

    return {"suggestion_id": row["id"], "status": "pending", "image_id": suggestion["image_id"]}

@app.get("/suggestions")
def list_suggestions(status: str | None = None):
    conn = get_db()
    if status:
        rows = conn.execute(
            """SELECT s.*, p.title AS post_title, i.filename AS image_filename
               FROM suggestions s
               JOIN posts p ON p.id = s.post_id
               JOIN images i ON i.id = s.image_id
               WHERE s.status = %s ORDER BY s.created_at DESC""",
            (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT s.*, p.title AS post_title, i.filename AS image_filename
               FROM suggestions s
               JOIN posts p ON p.id = s.post_id
               JOIN images i ON i.id = s.image_id
               ORDER BY s.created_at DESC"""
        ).fetchall()
    conn.close()
    return rows

@app.post("/suggestions/{suggestion_id}/approve")
def approve_suggestion(suggestion_id: int):
    conn = get_db()
    row = conn.execute("SELECT id FROM suggestions WHERE id = %s", (suggestion_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Suggestion {suggestion_id} not found")

    conn.execute("UPDATE suggestions SET status = 'approved' WHERE id = %s", (suggestion_id,))
    conn.commit()
    conn.close()
    return {"suggestion_id": suggestion_id, "status": "approved"}

@app.post("/suggestions/{suggestion_id}/reject")
def reject_suggestion(suggestion_id: int, reason: str | None = None):
    conn = get_db()
    row = conn.execute("SELECT id FROM suggestions WHERE id = %s", (suggestion_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Suggestion {suggestion_id} not found")

    conn.execute(
        "UPDATE suggestions SET status = 'rejected', rejection_reason = %s WHERE id = %s",
        (reason, suggestion_id)
    )
    conn.commit()
    conn.close()
    return {"suggestion_id": suggestion_id, "status": "rejected"}