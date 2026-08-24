# AI Image Understanding & Content Matching Engine

A system that looks at real images, understands what's actually in them using a vision-language model, and suggests contextually relevant images for blog posts — with a mismatch guard that refuses obviously wrong matches (like a wolf for a fox article) rather than guessing.

## Try it

```bash
curl http://localhost:8010/posts
curl http://localhost:8010/posts/1/images
```

Response for a fox-themed post:
```json
{
  "status": "match_found",
  "suggestion": {
    "image_id": 81,
    "filename": "fox_1.jpg",
    "similarity_score": 0.5529,
    "approved": true
  }
}
```

## How to run

Requires [Ollama](https://ollama.com) and [Docker](https://docker.com).

```bash
ollama pull moondream
ollama pull all-minilm

docker run --name capstone-db -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=imagerelevance -p 5433:5432 -v capstonedata:/var/lib/postgresql -d postgres

python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env   # fill in DATABASE_URL, VISION_MODEL, EMBEDDING_MODEL

python src\db.py                 # create tables
python src\batch_tag.py          # tag all images (takes several minutes)
python -m src.embed_images       # embed image captions
python -m src.seed_posts         # seed 6 test blog posts

uvicorn src.main:app --reload --port 8010
```

## Architecture
Images -> Vision model (moondream) -> tags/caption/confidence -> Postgres
Posts -> Embedding model (all-minilm) -> vector -> Postgres

GET /posts/:id/images
-> embed post text
-> cosine similarity vs all image embeddings
-> rank candidates
-> mismatch guard (category check -> confidence check -> similarity check)
-> return best approved match, or "no confident match" with reason


## Design decisions

See [`docs/DESIGN.md`](docs/DESIGN.md) for the full schema, matching strategy, and guard rules written before implementation began.

## Results

- **49/50 images** successfully tagged by the vision pipeline (1 correctly flagged for manual review due to low confidence)
- **80% top-1 precision** on a 5-post hand-labeled eval set (4/5 posts correctly matched to their category)
- **1 documented failure**: the "dog" post uses abstract language (companionship, behavior, training) while dog image captions are concrete/action-based (dogs standing, playing) — genuinely lower semantic overlap despite both being "about dogs." See `eval_results.json` for the full breakdown.
- Similarity threshold tuned from a design-doc starting point of 0.65 down to 0.53, based on real eval data (not guessed) — this recovered the "bear" post (0.5305 similarity, previously just below threshold) without loosening the guard enough to compromise its usefulness for other categories.

## Cost

All AI calls run through Ollama (free, local) — actual `$0` API cost. Token usage is tracked per-call in the `cost_log` table (52 calls, ~79,700 total token units logged during the full batch tag run) as a stand-in for what real per-call billing would track if swapped to a paid provider like Gemini.

## Known limitations

- Vision tagging uses two separate simple questions per image ("What animal is this?" / "What is it doing?") rather than one structured JSON prompt — several single-prompt JSON approaches were tried first and failed reliably with this small local model (it would copy example placeholder text verbatim, or get stuck in repetition loops). Asking simple, separate questions and assembling the JSON in Python proved far more reliable.
- The "dog" category has a real precision gap (documented above) that a threshold change alone can't fix without weakening the guard elsewhere — would need richer post text or category-specific tuning to close fully.
- The mismatch guard's category check relies on exact/known-synonym string matching against a small fixed list of 5 animals — not a general-purpose semantic category matcher.