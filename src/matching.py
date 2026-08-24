import json
from src.db import get_db
from src.embeddings import cosine_similarity

SIMILARITY_THRESHOLD = 0.55
MIN_CONFIDENCE = 0.6

def rank_images_for_post(post_embedding, all_images):
    """Returns images sorted by similarity score, descending."""
    ranked = []
    for img in all_images:
        img_vec = json.loads(img["embedding"]) if isinstance(img["embedding"], str) else img["embedding"]
        score = cosine_similarity(post_embedding, img_vec)
        ranked.append({**img, "similarity_score": score})

    ranked.sort(key=lambda x: x["similarity_score"], reverse=True)
    return ranked

def apply_mismatch_guard(post, candidate_image):
    """Returns (approved: bool, reason: str or None)."""
    post_subject = (post.get("primary_subject") or "").lower().strip()
    image_subject = (candidate_image.get("primary_subject") or "").lower().strip()

    if post_subject and image_subject and post_subject != image_subject:
        return False, f"Animal category mismatch: expected {post_subject}, detected {image_subject}"

    if candidate_image["confidence"] is not None and candidate_image["confidence"] < MIN_CONFIDENCE:
        return False, f"Image confidence too low ({candidate_image['confidence']:.2f} < {MIN_CONFIDENCE})"

    if candidate_image["similarity_score"] < SIMILARITY_THRESHOLD:
        return False, f"Similarity below threshold ({candidate_image['similarity_score']:.2f} < {SIMILARITY_THRESHOLD})"

    return True, None

def suggest_image_for_post(post_id):
    """Full pipeline: rank candidates, apply the guard, return the best result."""
    conn = get_db()

    post = conn.execute("SELECT * FROM posts WHERE id = %s", (post_id,)).fetchone()
    if post is None:
        conn.close()
        raise ValueError(f"Post {post_id} not found")

    images = conn.execute(
        "SELECT * FROM images WHERE embedding IS NOT NULL AND needs_review = false"
    ).fetchall()

    post_embedding = json.loads(post["embedding"]) if isinstance(post["embedding"], str) else post["embedding"]
    ranked = rank_images_for_post(post_embedding, images)

    results = []
    for candidate in ranked[:5]:
        approved, reason = apply_mismatch_guard(post, candidate)
        results.append({
            "image_id": candidate["id"],
            "filename": candidate["filename"],
            "similarity_score": round(candidate["similarity_score"], 4),
            "approved": approved,
            "reason": reason,
        })

    best_approved = next((r for r in results if r["approved"]), None)

    conn.close()

    if best_approved:
        return {"status": "match_found", "suggestion": best_approved, "all_candidates": results}
    else:
        top_reason = results[0]["reason"] if results else "No candidate images available"
        return {"status": "no_confident_match", "reason": top_reason, "all_candidates": results}