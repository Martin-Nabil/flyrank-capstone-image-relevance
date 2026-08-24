import json
from src.db import get_db
from src.embeddings import embed_text

POSTS = [
    {
        "title": "The secret life of red foxes",
        "body": "Red foxes, or Vulpes vulpes, are among the most adaptable wild canines in the northern hemisphere. Known for their striking russet coats and bushy tails, these clever animals thrive in forests, grasslands, and even urban edges. This wild fox species is famous for its resourcefulness when hunting small prey.",
        "primary_subject": "fox",
    },
    {
        "title": "Gray wolves: pack hunters of the wilderness",
        "body": "The gray wolf is a powerful pack predator found across remote wilderness areas. Wolves communicate through howls and body language, coordinating complex hunts as a family unit. Their presence in an ecosystem often signals a healthy, balanced food web.",
        "primary_subject": "wolf",
    },
    {
        "title": "Man's best friend: understanding dog behavior",
        "body": "Dogs have been companions to humans for thousands of years. From loyal guard dogs to playful family pets, canine behavior is shaped by both instinct and training. Understanding a dog's body language can deepen the human-canine bond.",
        "primary_subject": "dog",
    },
    {
        "title": "Bears in the wild: giants of the forest",
        "body": "Bears are among the largest land mammals, ranging from black bears to massive grizzlies. These powerful animals are surprisingly agile climbers and swimmers, and their diet varies widely depending on season and habitat.",
        "primary_subject": "bear",
    },
    {
        "title": "The graceful deer of the northern woods",
        "body": "Deer are gentle herbivores known for their alertness and speed. Found throughout forests and meadows, these animals play a key role in shaping plant growth through their grazing habits. Their antlers are a striking seasonal feature of many species.",
        "primary_subject": "deer",
    },
    {
        "title": "Best hiking trails for beginners this fall",
        "body": "Autumn is the perfect season to explore local hiking trails. Cooler temperatures and colorful foliage make for a scenic outing. Whether you're a beginner or an experienced hiker, there's a trail suited to every skill level this season.",
        "primary_subject": None,
    },
]

def run():
    conn = get_db()
    for post in POSTS:
        full_text = post["title"] + ". " + post["body"]
        vec = embed_text(full_text)
        conn.execute(
            "INSERT INTO posts (title, body, primary_subject, embedding) VALUES (%s, %s, %s, %s)",
            (post["title"], post["body"], post["primary_subject"], json.dumps(vec))
        )
        conn.commit()
        print(f"Seeded post: {post['title']}")

    conn.close()
    print("Done.")

if __name__ == "__main__":
    run()