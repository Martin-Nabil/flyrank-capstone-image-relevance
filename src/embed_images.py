import json
from src.db import get_db
from src.embeddings import embed_text

def run():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, caption FROM images WHERE caption IS NOT NULL AND needs_review = false"
    ).fetchall()

    print(f"Embedding {len(rows)} images...")
    for row in rows:
        vec = embed_text(row["caption"])
        conn.execute(
            "UPDATE images SET embedding = %s WHERE id = %s",
            (json.dumps(vec), row["id"])
        )
        conn.commit()
        print(f"  Embedded image {row['id']}")

    conn.close()
    print("Done.")

if __name__ == "__main__":
    run()