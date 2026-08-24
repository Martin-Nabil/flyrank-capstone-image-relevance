import os
import json
import re
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

PROMPT = 'What animal is in this image and what is it doing? Respond with exactly one JSON object like this example, with your own real values: {"tags": ["fox", "snow", "resting"], "caption": "A fox resting on a snowy rock.", "primary_subject": "fox", "confidence": 0.8}'

def encode_image(filepath):
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def extract_json(raw_text):
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")

    json_str = match.group()
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

    return json.loads(json_str)

def tag_image(filepath):
    image_b64 = encode_image(filepath)

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": VISION_MODEL,
            "prompt": PROMPT,
            "images": [image_b64],
            "stream": False,
            "options": {
                "num_predict": 200,
                "temperature": 0.1,
            },
        },
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    raw_text = result.get("response", "")
    tokens_used = result.get("eval_count", 0) + result.get("prompt_eval_count", 0)

    try:
        parsed = extract_json(raw_text)
        validated = ImageTags(**parsed)
        return validated, raw_text, tokens_used
    except (ValueError, ValidationError, json.JSONDecodeError):
        return None, raw_text, tokens_used