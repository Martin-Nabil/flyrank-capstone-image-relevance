import os
import time
import json
from src.db import get_db
from src.vision import tag_image

MAX_RETRIES = 3
LOW_CONFIDENCE_THRESHOLD = 0.6
IMAGES_DIR = "images"

def log_cost(conn, call_type, model, units):
    conn.execute(
        "INSERT INTO cost_log (call_type, model, units, cost_usd) VALUES (%s, %s, %s, %s)",
        (call_type, model, units, 0.0)
    )

def upsert_image_record(conn, filename, category, source_url):
    row = conn.execute(
        "SELECT id FROM images WHERE filename = %s", (filename,)
    ).fetchone()
    if row:
        return row["id"]
    row = conn.execute(
        "INSERT INTO images (filename, category, source_url) VALUES (%s, %s, %s) RETURNING id",
        (filename, category, source_url)
    ).fetchone()
    return row["id"]

def process_image(conn, filepath, filename, category, source_url):
    image_id = upsert_image_record(conn, filename, category, source_url)
    conn.commit()

    attempts = 0
    result = None
    raw = None

    while attempts < MAX_RETRIES:
        attempts += 1
        result, raw, tokens = tag_image(filepath)
        log_cost(conn, "vision", os.environ.get("VISION_MODEL", "moondream"), tokens)
        conn.commit()

        if result is not None:
            break

        print(f"  Attempt {attempts}/{MAX_RETRIES} failed for {filename}, raw: {raw[:80]}")
        time.sleep(1)

    if result is None:
        print(f"  FAILED after {MAX_RETRIES} attempts: {filename} -- flagging for review")
        conn.execute(
            "UPDATE images SET needs_review = true, processed_at = now() WHERE id = %s",
            (image_id,)
        )
        conn.commit()
        return False

    needs_review = result.confidence < LOW_CONFIDENCE_THRESHOLD

    conn.execute(
        """UPDATE images SET
            tags = %s, caption = %s, primary_subject = %s,
            confidence = %s, needs_review = %s, processed_at = now()
           WHERE id = %s""",
        (json.dumps(result.tags), result.caption, result.primary_subject,
         result.confidence, needs_review, image_id)
    )
    conn.commit()

    flag = " [LOW CONFIDENCE - FLAGGED]" if needs_review else ""
    print(f"  OK: {filename} -> {result.primary_subject} (conf={result.confidence}){flag}")
    return True

def run_batch():
    conn = get_db()
    total = 0
    succeeded = 0

    for category in sorted(os.listdir(IMAGES_DIR)):
        category_path = os.path.join(IMAGES_DIR, category)
        if not os.path.isdir(category_path):
            continue

        for filename in sorted(os.listdir(category_path)):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            filepath = os.path.join(category_path, filename)
            print(f"Processing {filename}...")
            total += 1

            if process_image(conn, filepath, filename, category, source_url=None):
                succeeded += 1

    conn.close()
    print(f"\nDone. {succeeded}/{total} images tagged successfully.")

if __name__ == "__main__":
    run_batch()