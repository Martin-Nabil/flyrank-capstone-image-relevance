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