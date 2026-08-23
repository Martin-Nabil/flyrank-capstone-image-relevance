# Design Doc — AI Image Understanding & Content Matching Engine

## 1. Image metadata schema

Each processed image produces this structured output from the vision model:

```json
{
  "tags": ["fox", "red fox", "wildlife", "forest"],
  "caption": "A red fox standing alert in a snowy forest clearing.",
  "primary_subject": "fox",
  "confidence": 0.91
}
```

- `tags`: array of strings, general descriptive keywords
- `caption`: one sentence, natural language description
- `primary_subject`: single word/short phrase — the main subject, used by the mismatch guard for category comparison
- `confidence`: float 0-1, the vision model's self-reported confidence

**Low-confidence rule:** if `confidence < 0.6`, the image is flagged for manual review rather than auto-accepted into the matching pool.

## 2. Matching strategy

1. Each image's `caption` is embedded into a vector (via the embedding model).
2. Each blog post's full text is embedded into a vector.
3. For a given post, we compute cosine similarity between the post's vector and every image's vector.
4. Images are ranked by similarity score, descending.
5. The top-ranked image(s) pass through the **mismatch guard** before being suggested.

## 3. Mismatch guard rules

An image is REJECTED as a suggestion if any of:
- `primary_subject` of the image doesn't semantically match the post's detected primary subject (checked via a small controlled category list for the ~50-image dataset, e.g. fox/wolf/dog/bear/deer — exact string or known-synonym match required)
- Cosine similarity score is below a fixed threshold (starting point: 0.65 — will be tuned during Phase 3 using the eval set)
- Image's `confidence` score is below 0.6 (never suggest a low-confidence tag as a match, regardless of similarity)

If every candidate image is rejected, the system returns "no confident match" with the specific reason(s) the top candidate failed.

## 4. Database design

**images**
- id (PK)
- filename
- source_url
- tags (JSON array)
- caption (text)
- primary_subject (text)
- confidence (float)
- embedding (vector/JSON array)
- created_at

**posts**
- id (PK)
- title
- body (text)
- primary_subject (text, optional — for guard comparison)
- embedding (vector/JSON array)
- created_at

**suggestions**
- id (PK)
- post_id (FK → posts)
- image_id (FK → images)
- similarity_score (float)
- status (pending / approved / rejected)
- rejection_reason (text, nullable)
- created_at

**cost_log**
- id (PK)
- call_type (vision / embedding)
- model (text)
- tokens_or_units (int)
- cost_usd (float, 0 for local Ollama calls)
- created_at

**Indexes:** `suggestions.post_id`, `suggestions.image_id`, `suggestions.status` — for fast lookups when querying a post's suggestions or filtering the review queue.

## 5. Dataset plan

~50 images across 5 categories (matching the brief's example): red fox, wolf, dog, bear, deer. Sourced from Unsplash/Pexels (free-to-use, license-checked). Roughly 10 images per category, giving enough volume to demonstrate real ranking behavior while staying small enough to verify by eye.

A small hand-labeled eval set (post → correct image ID) will be built from a subset of these, used to measure top-1 precision in Phase 4.