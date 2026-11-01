import os
from typing import Dict, List
import uuid
from fastapi import HTTPException
import requests
from dotenv import load_dotenv
from sqlalchemy.orm.attributes import flag_modified
from app.models.models import Prompt

# Load API Keys from .env
load_dotenv()
IDEOGRAM_KEY = os.getenv("IDEOGRAM_KEY")

if not IDEOGRAM_KEY:
    raise ValueError("Missing API key! Set IDEOGRAM_KEY in the .env file.")

IMAGE_FOLDER = "assets/prompt_images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ✅ Function to call Ideogram API and get image URL
def generate_ideogram_image(prompt: str, aspect_ratio: str = "ASPECT_1_1", model: str = "V_2", magic_prompt_option: str = "AUTO"):
    url = "https://api.ideogram.ai/generate"
    headers = {
        "Api-Key": IDEOGRAM_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "image_request": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "model": model,
            "magic_prompt_option": magic_prompt_option
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        return None, None, response.json()

    data = response.json()

    try:
        image_url = data["data"][0]["url"]
        magic_prompt = data["data"][0].get("magic_prompt", prompt)
    except (KeyError, IndexError):
        return None, None, {"error": "No valid image URL or magic_prompt", "response": data}

    return image_url, magic_prompt, None


# ✅ Function to download and save image locally
def download_and_save_image(prompt_id: int, image_url: str, output_format: str = "jpg"):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code != 200:
            return None, "Failed to download image"

        random_str = uuid.uuid4().hex[:8]
        file_name = f"{prompt_id}_{random_str}.{output_format}"  # 👈 Changed from user_id to prompt_id
        file_path = os.path.join(IMAGE_FOLDER, file_name)

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        return f"/{IMAGE_FOLDER}/{file_name}", None

    except Exception as e:
        return None, str(e)


# ✅ Main function to generate, download, and store the image
def generate_and_store_image(prompt_id: int, prompt: str, aspect_ratio: str = "ASPECT_1_1"):
    image_url, magic_prompt, error = generate_ideogram_image(prompt, aspect_ratio)
    if error:
        return {"error": error}

    saved_path, error = download_and_save_image(prompt_id, image_url)
    if error:
        return {"error": error}

    return {
        "image_path": saved_path,
        "magic_prompt": magic_prompt,
    }

    
def generate_images_from_prompt_record(
    db: requests.Session,
    user_id: int,
    prompt_record: Prompt,
    aspect_ratio: str = None
) -> List[Dict[str, str]]:  # Return full info per image

    try:
        # Parse prompt list from string or keep as list
        if isinstance(prompt_record.prompt, str):
            if prompt_record.prompt.strip().startswith("["):
                prompt_list = eval(prompt_record.prompt)
            else:
                prompt_list = [p.strip() for p in prompt_record.prompt.split(",")]
        elif isinstance(prompt_record.prompt, list):
            prompt_list = prompt_record.prompt
        else:
            raise ValueError("Invalid prompt format.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse prompt list: {e}")

    if not isinstance(prompt_record.image_urls, list):
        prompt_record.image_urls = []

    image_results = []

    for idx, single_prompt in enumerate(prompt_list, start=1):
        result = generate_and_store_image(prompt_record.id, single_prompt.strip(), aspect_ratio)

        if "error" in result:
            continue

        image_path = result["image_path"]
        magic_prompt = result.get("magic_prompt", None)

        # Append image path if not already in list
        if image_path not in prompt_record.image_urls:
            prompt_record.image_urls.append(image_path)

        # Set magic_prompt only if not already set
        if not prompt_record.magic_prompt and magic_prompt:
            prompt_record.magic_prompt = magic_prompt

        image_results.append({
            "prompt": single_prompt,
            "image_url": image_path
        })

    # ✅ Make sure SQLAlchemy detects change
    flag_modified(prompt_record, "image_urls")

    # ✅ Save all changes once
    db.commit()

    return image_results
