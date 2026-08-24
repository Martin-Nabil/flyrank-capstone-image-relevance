import os
import base64
import requests
from pydantic import BaseModel, ValidationError, field_validator
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = "http://localhost:11434/api/generate"
VISION_MODEL = os.environ.get("VISION_MODEL", "moondream")

class ImageTags(BaseModel):
    tags: list[str]
    caption: str
    primary_subject: str
    confidence: float

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0 and 1")
        return v

def encode_image(filepath):
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def ask(image_b64, question):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": VISION_MODEL,
            "prompt": question,
            "images": [image_b64],
            "stream": False,
            "options": {"num_predict": 60, "temperature": 0.1},
        },
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    answer = result.get("response", "").strip()
    tokens = result.get("eval_count", 0) + result.get("prompt_eval_count", 0)
    return answer, tokens

KNOWN_ANIMALS = ["fox", "wolf", "dog", "bear", "deer"]

def first_sentence(text):
    for sep in [".", "\n"]:
        if sep in text:
            return text.split(sep)[0].strip() + "."
    return text.strip()

def tag_image(filepath):
    image_b64 = encode_image(filepath)
    total_tokens = 0

    animal_answer, t1 = ask(image_b64, "What animal is this?")
    total_tokens += t1
    animal_summary = first_sentence(animal_answer)

    action_answer, t2 = ask(image_b64, "What is the animal doing?")
    total_tokens += t2
    action_summary = first_sentence(action_answer)

    raw_combined = f"animal: {animal_answer} | action: {action_answer}"

    combined_lower = (animal_summary + " " + action_summary).lower()
    primary_subject = next((a for a in KNOWN_ANIMALS if a in combined_lower), None)

    if primary_subject is None:
        return None, raw_combined, total_tokens

    tags = [primary_subject, "animal", "wildlife"]
    caption = f"{animal_summary} {action_summary}".strip()
    confidence = 0.85

    try:
        validated = ImageTags(
            tags=tags,
            caption=caption,
            primary_subject=primary_subject,
            confidence=confidence,
        )
        return validated, raw_combined, total_tokens
    except ValidationError:
        return None, raw_combined, total_tokens