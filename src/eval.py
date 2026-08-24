import json
from src.db import get_db
from src.matching import suggest_image_for_post

def run_eval():
    conn = get_db()
    posts = conn.execute(
        "SELECT id, title, primary_subject FROM posts WHERE primary_subject IS NOT NULL ORDER BY id"
    ).fetchall()
    conn.close()

    results = []
    for post in posts:
        result = suggest_image_for_post(post["id"])

        if result["status"] == "match_found":
            suggested_image_id = result["suggestion"]["image_id"]
            conn2 = get_db()
            img = conn2.execute(
                "SELECT primary_subject FROM images WHERE id = %s", (suggested_image_id,)
            ).fetchone()
            conn2.close()
            correct = img["primary_subject"] == post["primary_subject"]
        else:
            correct = False

        results.append({
            "post_id": post["id"],
            "post_title": post["title"],
            "expected_category": post["primary_subject"],
            "status": result["status"],
            "correct": correct,
        })

    total = len(results)
    num_correct = sum(1 for r in results if r["correct"])
    precision = num_correct / total if total > 0 else 0

    print(f"\nTop-1 Precision: {num_correct}/{total} ({precision*100:.0f}%)\n")
    for r in results:
        status_mark = "PASS" if r["correct"] else "FAIL"
        print(f"[{status_mark}] Post {r['post_id']} \"{r['post_title']}\" expected={r['expected_category']} status={r['status']}")

    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump({"precision": precision, "num_correct": num_correct, "total": total, "results": results}, f, indent=2)

    print("\nResults saved to eval_results.json")

if __name__ == "__main__":
    run_eval()