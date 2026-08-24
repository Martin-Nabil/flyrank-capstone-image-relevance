import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["PEXELS_API_KEY"]
HEADERS = {"Authorization": API_KEY}

CATEGORIES = {
    "fox": "red fox animal",
    "wolf": "wolf animal wildlife",
    "dog": "dog animal",
    "bear": "bear animal wildlife",
    "deer": "deer animal wildlife",
}

IMAGES_PER_CATEGORY = 10
OUTPUT_DIR = "images"

def fetch_category(category, query):
    print(f"Fetching {category}...")
    response = requests.get(
        "https://api.pexels.com/v1/search",
        headers=HEADERS,
        params={"query": query, "per_page": IMAGES_PER_CATEGORY},
    )
    response.raise_for_status()
    data = response.json()

    category_dir = os.path.join(OUTPUT_DIR, category)
    os.makedirs(category_dir, exist_ok=True)

    manifest = []
    for i, photo in enumerate(data["photos"]):
        img_url = photo["src"]["medium"]
        filename = f"{category}_{i+1}.jpg"
        filepath = os.path.join(category_dir, filename)

        img_response = requests.get(img_url)
        with open(filepath, "wb") as f:
            f.write(img_response.content)

        manifest.append({
            "filename": filename,
            "category": category,
            "source_url": photo["url"],
            "photographer": photo["photographer"],
            "pexels_id": photo["id"],
        })

        print(f"  Saved {filename}")

    return manifest

def main():
    all_manifest = []
    for category, query in CATEGORIES.items():
        entries = fetch_category(category, query)
        all_manifest.extend(entries)

    import json
    with open(os.path.join(OUTPUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(all_manifest, f, indent=2)

    print(f"\nDone. {len(all_manifest)} images saved. Manifest written to images/manifest.json")

if __name__ == "__main__":
    main()