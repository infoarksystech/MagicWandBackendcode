# Example for remixing an image via Ideogram Remix API (stubbed)
import base64
import io
import json
import os
from PIL import Image
import uuid

from PIL import UnidentifiedImageError
from dotenv import load_dotenv
from openai import OpenAI
import requests
import json
import os
import time
import requests
import base64


# Load API key
load_dotenv()
IDEOGRAM_KEY = os.getenv("IDEOGRAM_KEY")
STABILITY_KEY = os.getenv("STABILITY_KEY")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
SEGMENT_API=os.getenv("SEGMENT_API")

#------------------------------------------------IDEOGRAM-AI -------------------------------------------------
def generate_ideogram_image(
    prompt: str,
    aspect_ratio: str = "",
    ref_image_url: str = "",
    model: str = "V_2",
    magic_prompt_option: str = "AUTO"
):
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
            "magic_prompt_option": magic_prompt_option,
            "style_reference_images": [ref_image_url] if ref_image_url else []
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


def generate_ideogram_3_image(
    prompt: str,
    negative_prompt: str = "",
    resolution: str = "1024x1024",
    rendering_speed: str = "DEFAULT",
    magic_prompt: str = "",
    style_codes=None,
    style_type: str = "",
    color_palette: dict = None
):
    print(">> Inside generate_ideogram_3_image")
    print(" - prompt:", prompt)

    api_key = SEGMENT_API  # Replace with your actual API key
    url = "https://api.segmind.com/v1/ideogram-3"

    try:
        data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "resolution": resolution,
            "rendering_speed": rendering_speed,
            "magic_prompt": magic_prompt,
            "style_codes": style_codes or [],
            "style_type": style_type,
        }

        # Optional color palette (either name or members)
        if color_palette:
            data["color_palette"] = color_palette

        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content, None
        else:
            return None, {"error": f"Segmind API error {response.status_code}: {response.text}"}
    except Exception as e:
        return None, {"error": f"Segmind exception: {str(e)}"}


def generate_gpt_image(
    prompt: str,
    size: str ="",
    quality: str="" ,
    moderation: str ="",
    background: str ="",
    output_compression: int = 100,
    output_format: str=""
):
    print(">> Inside generate_gpt_image_1")
    print(" - prompt:", prompt)

    api_key = SEGMENT_API  # Replace with your actual API key
    url = "https://api.segmind.com/v1/gpt-image-1.5"
    
    try:
        data = {
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "moderation": moderation,
            "background": background,
            "output_compression": output_compression,
            "output_format": output_format
        }
        
        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.content, None
        else:
            return None, {"error": f"Segmind API error {response.status_code}: {response.text}"}
    except Exception as e:
        return None, {"error": f"Segmind exception: {str(e)}"}


def generate_imagen_4_image(
    prompt: str,
    negative_prompt: str = "",
    aspect_ratio: str = ""
):
    print(">> Inside generate_imagen_4_image")
    print(" - prompt:", prompt)

    api_key = SEGMENT_API  # Replace with your actual API key
    url = "https://api.segmind.com/v1/imagen-4"

    try:
        data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "aspect_ratio": aspect_ratio
        }

        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content, None
        else:
            return None, {"error": f"Segmind API error {response.status_code}: {response.text}"}
    except Exception as e:
        return None, {"error": f"Segmind exception: {str(e)}"}



def generate_sdxl_dreamshaper_lightning(
    prompt: str,
    negative_prompt: str = "",
    samples: int = 1,
    scheduler: str = "DPM++ SDE",
    num_inference_steps: int = 7,
    guidance_scale: float = 1,
    seed: int = 2644125604,
    img_width: int = 1024,
    img_height: int = 1024
):
    print(">> Inside generate_sdxl_dreamshaper_lightning")
    print(" - prompt:", prompt)

    api_key = SEGMENT_API  # Replace with your actual API key
    url = "https://api.segmind.com/v1/sdxl1.0-dreamshaper-lightning"

    try:
        data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "samples": samples,
            "scheduler": scheduler,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "seed": seed,
            "img_width": img_width,
            "img_height": img_height,
            "base64": False
        }

        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content, None
        else:
            return None, {"error": f"Segmind API error {response.status_code}: {response.text}"}
    except Exception as e:
        return None, {"error": f"Segmind exception: {str(e)}"}

import requests

def generate_sdxl_yamers_realistic(
    prompt: str,
    negative_prompt: str = "",
    samples: int = 1,
    scheduler: str = "DPM++ 2M Karras",
    num_inference_steps: int = 30,
    guidance_scale: float = 7,
    seed: int = 565481734,
    img_width: int = 896,
    img_height: int = 1152
):
    print(">> Inside generate_sdxl_yamers_realistic")
    print(" - prompt:", prompt)

    api_key = SEGMENT_API  # Replace with your actual API key
    url = "https://api.segmind.com/v1/sdxl1.0-yamers-realistic"

    try:
        data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "samples": samples,
            "scheduler": scheduler,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "seed": seed,
            "img_width": img_width,
            "img_height": img_height,
            "base64": False
        }

        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content, None
        else:
            return None, {"error": f"Segmind API error {response.status_code}: {response.text}"}
    except Exception as e:
        return None, {"error": f"Segmind exception: {str(e)}"}

def generate_playground_v25_image(
    prompt: str,
    negative_prompt: str = "",
    samples: int = 1,
    num_inference_steps: int = 25,
    guidance_scale: float = 3,
    seed: int = 36446545871
):
    print(">> Inside generate_playground_v25_image")
    print(" - prompt:", prompt)

    api_key = SEGMENT_API  # Use your actual SEGMENT_API key
    url = "https://api.segmind.com/v1/playground-v2.5"

    try:
        data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "samples": samples,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "seed": seed,
            "base64": False
        }

        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content, None
        else:
            return None, {"error": f"Segmind API error {response.status_code}: {response.text}"}
    except Exception as e:
        return None, {"error": f"Segmind exception: {str(e)}"}

        

def generate_ideogram_remix_image(prompt: str, ref_image_path: str, aspect_ratio: str = ""):
    url = "https://api.ideogram.ai/remix"
    headers = {
        "Api-Key": IDEOGRAM_KEY  # Do NOT include Content-Type
    }

    # JSON string for the image_request
    image_request_payload = json.dumps({
        "prompt": prompt,
        "aspect_ratio": aspect_ratio
    })

    # Prepare the multipart form-data
    with open(ref_image_path, 'rb') as img_file:
        files = {
            "image_file": (os.path.basename(ref_image_path), img_file, "image/jpeg"),
            "image_request": (None, image_request_payload)
        }

        print("Sending request to Ideogram API...")
        print("URL:", url)
        print("Headers:", headers)
        print("Files keys:", files.keys())

        response = requests.post(url, headers=headers, files=files)

        print("Response status code:", response.status_code)
        print("Response content:", response.text)

        if response.status_code != 200:
            return None, None, response.json()

        try:
            data = response.json()
            print("Parsed JSON response:", data)
            image_url = data["data"][0]["url"]
            remix_prompt = data["data"][0].get("magic_prompt", prompt)
            return image_url, remix_prompt, None
        except (KeyError, IndexError) as e:
            print("Error parsing response:", e)
            return None, None, {"error": "Invalid remix response", "data": data}


#-----------------------------------------------------STABILITY-AI -----------------------------------------------

def generate_stability_ultra_image(
    prompt: str,
    negative_prompt: str = "",
    aspect_ratio: str = "",
    seed: int = 0,
    style_preset: str = "None",
    output_format: str = "jpeg"
):
    url = "https://api.stability.ai/v2beta/stable-image/generate/ultra"

    # Prepare multipart/form-data fields
    files = {
        "prompt": (None, prompt),
        "negative_prompt": (None, negative_prompt),
        "aspect_ratio": (None, aspect_ratio),
        "seed": (None, str(seed)),  # Make sure seed is string
        "output_format": (None, output_format)
    }

    if style_preset and style_preset != "None":
        files["style_preset"] = (None, style_preset)

    headers = {
        "Authorization": f"Bearer {STABILITY_KEY}",
        "Accept": "image/*"
        # Do NOT set 'Content-Type'; requests will handle it
    }

    response = requests.post(url, headers=headers, files=files)

    if response.status_code != 200:
        return None, None, {"error": "Failed to generate image", "response": response.text}

    # Check NSFW filter
    finish_reason = response.headers.get("finish-reason")
    if finish_reason == 'CONTENT_FILTERED':
        return None, None, {"error": "NSFW content filtered"}

    image_data = response.content
    seed_used = response.headers.get("seed")

    return image_data, seed_used, None

def generate_stability_sketch_image(
    image_path: str,
    prompt: str,
    negative_prompt: str = "",
    control_strength: float = 0.45,
    seed: int = 0,
    output_format: str = "jpeg"
):
    print(">> Inside generate_stability_sketch_image")
    print(" - image_path:", image_path)
    print(" - prompt:", prompt)

    host = "https://api.stability.ai/v2beta/stable-image/control/sketch"

    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {STABILITY_KEY}"
    }

    if not os.path.isfile(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return None, None, f"Image file not found: {image_path}"

    # Resize and compress image to be under 10MB
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")  # Ensure compatibility
            img.thumbnail((1024, 1024))  # Resize to max 1024x1024

            image_io = io.BytesIO()
            img.save(image_io, format="JPEG", quality=85)  # Compress

            image_io.seek(0)  # Reset pointer to start
    except Exception as e:
        print(f"[ERROR] Failed to process image: {e}")
        return None, None, f"Image processing error: {e}"

    params = {
        "prompt": str(prompt),
        "negative_prompt": str(negative_prompt),
        "control_strength": float(control_strength),
        "seed": int(seed),
        "output_format": str(output_format)
    }

    try:
        files = {
            "image": ("image.jpeg", image_io, "image/jpeg")
        }

        response = requests.post(host, headers=headers, data=params, files=files)

        if not response.ok:
            print(f"[ERROR] HTTP {response.status_code}: {response.text}")
            return None, None, f"HTTP {response.status_code}: {response.text}"

        if response.headers.get("finish-reason") == "CONTENT_FILTERED":
            print("[WARNING] NSFW content filtered.")
            return None, None, "Generation failed due to NSFW classifier"

        image_data = response.content
        seed_used = response.headers.get("seed", "")

        print("[SUCCESS] Image generated with seed:", seed_used)
        return image_data, seed_used, None

    except Exception as e:
        print(f"[ERROR] Error during request: {e}")
        return None, None, f"Error during request: {str(e)}"
    

def generate_stability_creative_upscaled_image(ref_image_path: str, prompt: str, negative_prompt: str = "", seed: int = 0, creativity: float = 0.3, output_format: str = "jpeg"):


    host = "https://api.stability.ai/v2beta/stable-image/upscale/creative"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {STABILITY_KEY}"  # ensure STABILITY_KEY is defined in your env
    }

    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": seed,
        "creativity": creativity,
        "output_format": output_format
    }

    files = {
        "image": open(ref_image_path, "rb")
    }

    # Step 1: Submit upscale request
    response = requests.post(host, headers=headers, files=files, data=params)
    if not response.ok:
        return None, None, f"Failed to submit: {response.text}"

    response_data = response.json()
    generation_id = response_data.get("id")
    if not generation_id:
        return None, None, "No generation ID returned"

    # Step 2: Poll for results
    start = time.time()
    timeout = 300
    while True:
        time.sleep(10)
        poll_response = requests.get(
            f"https://api.stability.ai/v2beta/results/{generation_id}",
            headers={**headers, "Accept": "*/*"}
        )
        if poll_response.status_code != 202:
            break
        if time.time() - start > timeout:
            return None, None, "Upscaling timeout exceeded"

    if not poll_response.ok:
        return None, None, f"Polling error: {poll_response.text}"

    if poll_response.headers.get("finish-reason") == "CONTENT_FILTERED":
        return None, None, "Image flagged as NSFW"

    # Save the result
    output_image_data = poll_response.content
    return output_image_data, prompt, None

def generate_stability_fast_upscaled_image(
    image_path: str,
    output_format: str = "jpeg"
):
    import requests
    import os

    host = "https://api.stability.ai/v2beta/stable-image/upscale/fast"
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {STABILITY_KEY}"  # Your API key must be set globally
    }

    # Prepare files and parameters
    params = {
        "output_format": output_format
    }
    files = {
        "image": open(image_path, "rb")
    }

    print(f"Sending Fast Upscaler request to {host}...")

    response = requests.post(
        host,
        headers=headers,
        files=files,
        data=params
    )

    if not response.ok:
        return None, None, f"HTTP {response.status_code}: {response.text}"

    finish_reason = response.headers.get("finish-reason")
    seed = response.headers.get("seed", "0")

    if finish_reason == 'CONTENT_FILTERED':
        return None, None, "Image flagged as NSFW"

    return response.content, seed, None


def generate_stability_search_and_recolor(
    image_path: str,
    prompt: str,
    select_prompt: str,
    negative_prompt: str = "",
    grow_mask: int = 3,
    seed: int = 0,
    output_format: str = "webp"
):
    import requests
    import os

    host = "https://api.stability.ai/v2beta/stable-image/edit/search-and-recolor"
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {STABILITY_KEY}"  # Your API key must be set globally
    }

    # Prepare request data
    params = {
        "prompt": prompt,
        "select_prompt": select_prompt,
        "negative_prompt": negative_prompt,
        "grow_mask": grow_mask,
        "seed": seed,
        "mode": "search",
        "output_format": output_format
    }
    files = {
        "image": open(image_path, "rb")
    }

    print(f"Sending Search-and-Recolor request to {host}...")

    response = requests.post(
        host,
        headers=headers,
        files=files,
        data=params
    )

    if not response.ok:
        return None, None, f"HTTP {response.status_code}: {response.text}"

    finish_reason = response.headers.get("finish-reason")
    seed = response.headers.get("seed", "0")

    if finish_reason == "CONTENT_FILTERED":
        return None, None, "Image flagged as NSFW"

    return response.content, seed, None

def generate_stability_search_and_replace(
    image_path: str,
    prompt: str,
    search_prompt: str,
    negative_prompt: str = "",
    seed: int = 0,
    output_format: str = "jpeg"
):
    import requests
    import os

    host = "https://api.stability.ai/v2beta/stable-image/edit/search-and-replace"
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {STABILITY_KEY}"  # Your API key must be set globally
    }

    # Prepare request data
    params = {
        "prompt": prompt,
        "search_prompt": search_prompt,
        "negative_prompt": negative_prompt,
        "seed": seed,
        "mode": "search",
        "output_format": output_format
    }
    files = {
        "image": open(image_path, "rb")
    }

    print(f"Sending Search-and-Replace request to {host}...")

    response = requests.post(
        host,
        headers=headers,
        files=files,
        data=params
    )

    if not response.ok:
        return None, None, f"HTTP {response.status_code}: {response.text}"

    finish_reason = response.headers.get("finish-reason")
    seed = response.headers.get("seed", "0")

    if finish_reason == "CONTENT_FILTERED":
        return None, None, "Image flagged as NSFW"

    return response.content, seed, None


def generate_stability_remove_background(
    image_path: str,
    output_format: str = "png"
):
    import requests
    import os

    host = "https://api.stability.ai/v2beta/stable-image/edit/remove-background"
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {STABILITY_KEY}"  # Ensure STABILITY_KEY is globally set
    }

    params = {
        "output_format": output_format
    }
    files = {
        "image": open(image_path, "rb")
    }

    print(f"Sending Remove Background request to {host}...")

    response = requests.post(
        host,
        headers=headers,
        files=files,
        data=params
    )

    if not response.ok:
        return None, None, f"HTTP {response.status_code}: {response.text}"

    finish_reason = response.headers.get("finish-reason")
    seed = response.headers.get("seed", "0")

    if finish_reason == "CONTENT_FILTERED":
        return None, None, "Image flagged as NSFW"

    return response.content, seed, None

def generate_stability_replace_background_and_relight(
    subject_image_path: str,
    background_prompt: str,
    background_reference: str = "",
    foreground_prompt: str = "",
    negative_prompt: str = "",
    preserve_original_subject: float = 0.6,
    original_background_depth: float = 0.5,
    keep_original_background: bool = False,
    light_source_strength: float = 0.3,
    light_reference: str = "",
    light_source_direction: str = "none",
    seed: int = 0,
    output_format: str = "jpeg"
):
    host = "https://api.stability.ai/v2beta/stable-image/edit/replace-background-and-relight"
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {STABILITY_KEY}"
    }
    print(f"subject_image_path-------->:{subject_image_path}")
    print(f"background prompt--------->:{background_prompt}")
    print(f"background_reference--------->:{background_reference}")
    print(f"light_reference--------->:{light_reference}")
    try:
        files = {
            "subject_image": open(subject_image_path, "rb")
        }

        # Optional: Attach background or light reference if local file exists
        if background_reference and os.path.exists(background_reference):
            files["background_reference"] = open(background_reference, "rb")

        if light_reference and os.path.exists(light_reference):
            files["light_reference"] = open(light_reference, "rb")

            

        # Prepare form data
        params = {
            "background_prompt": background_prompt,
            "foreground_prompt": foreground_prompt,
            "negative_prompt": negative_prompt,
            "preserve_original_subject": preserve_original_subject,
            "original_background_depth": original_background_depth,
            "keep_original_background": str(keep_original_background).lower(),
            "light_source_direction": light_source_direction if light_source_direction in ["left", "right", "above", "below"] else None,
            "light_source_strength": light_source_strength if light_source_direction in ["left", "right", "above", "below"] else None,
            "seed": seed,
            "output_format": output_format
        }

        # Remove unset fields
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.post(host, headers=headers, files=files, data=params)

        if not response.ok:
            return None, None, f"HTTP {response.status_code}: {response.text}"

        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            try:
                json_response = response.json()
                return None, None, f"API returned JSON instead of image: {json_response}"
            except Exception:
                return None, None, f"Unexpected content-type: {content_type} | Response: {response.text}"


        # Validate image data in memory
        try:
            Image.open(io.BytesIO(response.content)).verify()
        except Exception as e:
            return None, None, f"Invalid image returned from API: {e}"

        finish_reason = response.headers.get("finish-reason")
        response_seed = response.headers.get("seed", str(seed))

        if finish_reason == "CONTENT_FILTERED":
            return None, None, "Image flagged as NSFW"

        return response.content, response_seed, None

    except Exception as e:
        return None, None, f"[ERROR] Exception occurred: {str(e)}"
    



#------------------------------------------------------ GEMINI-AI ------------------------------------------------

def generate_gemini_image(prompt: str, aspect_ratio: str = "1:1", output_format: str = "jpeg"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        return None, None, f"Failed to generate image, status code: {response.status_code}, response: {response.text}"

    try:
        data = response.json()
        print(f"[DEBUG] Gemini API response JSON: {json.dumps(data, indent=2)}")

        # Example: data["candidates"][0]["image"]["imageBytes"] might contain base64 image string
        candidates = data.get("candidates", [])
        if not candidates:
            return None, None, "No candidates found in Gemini API response."

        candidate = candidates[0]

        # Try to get base64 image bytes
        image_bytes_base64 = candidate.get("image", {}).get("imageBytes")

        if image_bytes_base64:
            # Decode base64 to bytes
            import base64
            image_data = base64.b64decode(image_bytes_base64)
            # Save image data to a temp file or return image data directly
            # For now, we can save this to a file and return the path
            # But your download_and_save_image expects a URL, so consider saving here directly
            temp_file_path = f"/tmp/{uuid.uuid4().hex}.{output_format}"
            with open(temp_file_path, "wb") as f:
                f.write(image_data)
            return temp_file_path, prompt, None

        # Or if an URL is given directly (less common)
        image_url = candidate.get("output") or candidate.get("imageUrl") or None
        if image_url:
            return image_url, prompt, None

        return None, None, "No image data found in Gemini response."

    except Exception as e:
        return None, None, f"Error parsing Gemini response: {str(e)}"
    
#------------------------------------------------ Segmind-AI ---------------------------------------------------------


def generate_openai_edit_image(reference_image: str, prompt: str, output_format: str = "jpeg"):
    print(">> Inside generate_openai_edit_image (via FILE)")
    print(" - prompt:", prompt)
    print(" - image URL:", reference_image)

    api_key = SEGMENT_API  # Replace this with your actual key
    url = "https://api.segmind.com/v1/gpt-image-1-edit"

    data = {
        "image_urls": [reference_image],  # Use public URL
        "prompt": prompt,
        "size": "auto",
        "quality": "auto",
        "background": "opaque",
        "output_compression": 100,
        "output_format": output_format,
        "moderation": "auto"
    }

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            print("[INFO] Image generated successfully.")
            return response.content, None
        else:
            error_msg = f"Segmind API error {response.status_code}: {response.text}"
            print(f"[ERROR] {error_msg}")
            return None, error_msg

    except Exception as e:
        error_msg = f"Segmind exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return None, error_msg




def generate_caricature_image(
    reference_image: str,  # Should be a public image URL
    output_format: str = "png"
):
    print(">> Inside generate_caricature_image")
    print(" - image URL:", reference_image)

    api_key = SEGMENT_API  # Make sure SEGMENT_API is set in your environment or config
    url = "https://api.segmind.com/v1/caricature-style"

    try:
        data = {
            "image": reference_image,
            "size": "1024x1024",
            "quality": "low",
            "background": "opaque",
            "output_compression": 100,
            "output_format": output_format
        }

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            print("[INFO] Caricature image generated successfully.")
            return response.content, None
        else:
            error_msg = f"Segmind API error {response.status_code}: {response.text}"
            print(f"[ERROR] {error_msg}")
            return None, error_msg

    except Exception as e:
        error_msg = f"Segmind caricature exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return None, error_msg


 #--------------------------------

def generate_flux_kontext_image(
    reference_image: str,  # local file path now
    prompt: str,
    aspect_ratio:str="1:1",
    output_format: str = "png"
):
    print(">> Inside generate_flux_kontext_image (using file)")
    print(" - prompt:", prompt)
    print(" - local image:", reference_image)

    api_key = SEGMENT_API
    url = "https://api.segmind.com/v1/flux-kontext-max"

    try:
        data = {
            "prompt": prompt,
            "seed": 30699,
            "aspect_ratio":aspect_ratio,
            "output_format":output_format
        }

        headers = {
            "x-api-key": api_key
        }

        files = {
            "input_image": open(reference_image, "rb")
        }

        response = requests.post(url, data=data, files=files, headers=headers)

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                image_base64 = response.json().get("image")
                if image_base64:
                    return base64.b64decode(image_base64), None
                else:
                    return None, "No image key found in JSON response"
            elif "image" in content_type or "octet-stream" in content_type:
                return response.content, None
            else:
                return None, f"Unexpected content type: {content_type}"
        else:
            return None, f"Segmind API error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Segmind exception: {str(e)}"
       

def image_url_to_base64(image_url):
    response = requests.get(image_url)
    image_data = response.content
    return base64.b64encode(image_data).decode("utf-8")

def generate_background_erased_image(
    reference_image: str,
    return_mask: bool = True,
    invert_mask: bool = False,
    grow_mask: int = 0
):
    print(">> Inside generate_background_erased_image")
    print(" - reference_image:", reference_image)

    api_key = SEGMENT_API
    url = "https://api.segmind.com/v1/background-eraser"

    try:
        base64_image = image_url_to_base64(reference_image)

        data = {
            "image": base64_image,
            "return_mask": return_mask,
            "invert_mask": invert_mask,
            "grow_mask": grow_mask,
            "base64": False
        }

        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content, None
        else:
            return None, f"Segmind API error {response.status_code}: {response.text}"

    except Exception as e:
        return None, f"Segmind exception: {str(e)}"    


def generate_automatic_mask_image(
    reference_image: str,
    prompt: str = "",
    threshold: float = 0.2,
    invert_mask: bool = False,
    return_mask: bool = True,
    return_alpha: bool = False,
    grow_mask: int = 10,
    seed: int = 468685
):
    print(">> Inside generate_automatic_mask_image")
    print(" - prompt:", prompt)
    print(" - reference_image:", reference_image)

    api_key = SEGMENT_API
    url = "https://api.segmind.com/v1/automatic-mask-generator"

    try:
        base64_image = image_url_to_base64(reference_image)

        data = {
            "prompt": prompt,
            "image": base64_image,
            "threshold": threshold,
            "invert_mask": invert_mask,
            "return_mask": return_mask,
            "return_alpha": return_alpha,
            "grow_mask": grow_mask,
            "seed": seed,
            "base64": False
        }

        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content, None
        else:
            return None, f"Segmind API error {response.status_code}: {response.text}"

    except Exception as e:
        return None, f"Segmind exception: {str(e)}"       



def generate_text_overlay_image(
    reference_image: str,
    text: str,
    font: str ,
    font_size: int ,
    color: str ,
    outline_color: str ,
    outline_size: int ,
    align: str ,
    blend_mode: str ,
    image_format: str ,
    image_quality: int ,
    margin_x: int ,
    margin_y: int ,
    linespace: int ,
    graphspace: int ,
    wrap: int ,
    text_underlay: bool = False
):
    print(">> Inside generate_text_overlay_image")
    print(" - reference_image:", reference_image)
    print(" - text:", text)

    api_key = SEGMENT_API
    url = "https://api.segmind.com/v1/text-overlay"

    try:
        data = {
            "align": align,
            "base64": False,
            "blend_mode": blend_mode,
            "color": color,
            "font": font,
            "font_size": font_size,
            "graphspace": graphspace,
            "image": reference_image,  # public URL
            "image_format": image_format,
            "image_quality": image_quality,
            "linespace": linespace,
            "margin_x": margin_x,
            "margin_y": margin_y,
            "outline_color": outline_color,
            "outline_size": outline_size,
            "text": text,
            "text_underlay": text_underlay,
            "wrap": wrap
        }

        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content, None
        else:
            return None, f"Segmind API error {response.status_code}: {response.text}"

    except Exception as e:
        return None, f"Segmind exception: {str(e)}"            


def generate_skin_contrast_upscale_image(
    reference_image: str,
    image_format: str ,
    image_quality: int = 85
):
    print(">> Inside generate_skin_contrast_upscale_image")
    print(" - reference_image:", reference_image)

    api_key = SEGMENT_API # Replace with your actual API key
    url = "https://api.segmind.com/v1/skin-contrast-upscaler"

    try:
        base64_image = image_url_to_base64(reference_image)

        data = {
            "image": base64_image,
            "image_format": image_format,
            "image_quality": image_quality,
            "base64": False
        }

        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content, None
        else:
            return None, f"Segmind API error {response.status_code}: {response.text}"

    except Exception as e:
        return None, f"Segmind exception: {str(e)}"
    


def generate_ic_light_image(
    reference_image: str,
    prompt: str,
    output_format: str = "webp",
    width: int = 512,
    height: int = 640,
    cfg: int = 2,
    seed: int = 42,
    steps: int = 25,
    light_source: str = "None",
    highres_scale: float = 1.5,
    lowres_denoise: float = 0.9,
    highres_denoise: float = 0.5,
    output_quality: int = 80,
    appended_prompt: str = "best quality",
    negative_prompt: str = "lowres, bad anatomy, bad hands, cropped, worst quality",
    number_of_images: int = 1
):
    print(">> Inside generate_ic_light_image")
    print(" - subject_image_url:", reference_image)
    print(" - prompt:", prompt)

    api_key = "SG_b3d52a27414bf84a"  # Replace with your API key
    url = "https://api.segmind.com/v1/ic-light"

    try:
        data = {
            "subject_image": reference_image,
            "prompt": prompt,
            "output_format": output_format,
            "width": width,
            "height": height,
            "cfg": cfg,
            "seed": seed,
            "steps": steps,
            "light_source": light_source,
            "highres_scale": highres_scale,
            "lowres_denoise": lowres_denoise,
            "highres_denoise": highres_denoise,
            "output_quality": output_quality,
            "appended_prompt": appended_prompt,
            "negative_prompt": negative_prompt,
            "number_of_images": number_of_images
        }

        headers = {"x-api-key": api_key}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content, None
        else:
            return None, f"Segmind API error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Segmind exception: {str(e)}"


def generate_replace_background_image(
    prompt: str,
    image_url: str,
    rendering_speed: str = "DEFAULT",
    magic_prompt: str = "AUTO",
    style_codes: list = None,
    style_reference_images: list = None
):
    print(">> Inside generate_replace_background_image")
    print(" - prompt:", prompt)
    print(" - image_url:", image_url)

    api_key = SEGMENT_API
    url = "https://api.segmind.com/v1/ideogram-3-replace-background"

    try:
        data = {
            "prompt": prompt,
            "image": image_url,
            "rendering_speed": rendering_speed,
            "magic_prompt": magic_prompt,
            "style_codes": style_codes or [],
            "style_reference_images": style_reference_images or []
        }

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=data)
        print("Segmind Response Status:", response.status_code)
        print("Segmind Content-Type:", response.headers.get("Content-Type"))
        
        # ✅ Case 1: success with binary image
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "").lower()

            # API returned an image file (PNG/JPEG)
            if "image" in content_type:
                return response.content, None

            # API returned JSON (rare fallback case)
            try:
                result = response.json()
                if "image_base64" in result:
                    import base64
                    return base64.b64decode(result["image_base64"]), None
                elif "image_url" in result:
                    image_data = requests.get(result["image_url"]).content
                    return image_data, None
                else:
                    return None, {"error": "Unexpected JSON response format."}
            except Exception:
                print("[DEBUG] Unexpected non-JSON response:", response.text[:300])
                return None, {"error": "Segmind returned unknown data format."}

        else:
            return None, {"error": f"Segmind API error {response.status_code}: {response.text}"}

    except Exception as e:
        return None, {"error": f"Segmind exception: {str(e)}"}

    

def generate_3d_image(
    image_url: str,
    seed: int = 42,
    steps: int = 30,
    num_chunks: int = 8000,
    max_facenum: int = 20000,
    guidance_scale: float = 7.5,
    generate_texture: bool = True,
    octree_resolution: int = 256,
    remove_background: bool = True
):
    print(">> Inside generate_hunyuan3d_image")
    print(" - image_url:", image_url)

    api_key = SEGMENT_API  # stored API key in your environment/config
    url = "https://api.segmind.com/v1/hunyuan3d-2.1"

    try:
        data = {
            "seed": seed,
            "image": image_url,
            "steps": steps,
            "num_chunks": num_chunks,
            "max_facenum": max_facenum,
            "guidance_scale": guidance_scale,
            "generate_texture": generate_texture,
            "octree_resolution": octree_resolution,
            "remove_background": remove_background
        }

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            # The Segmind Hunyuan3D API usually returns a download link (ZIP or GLB)
            result = response.json()
            if "zip_url" in result:
                image_data = requests.get(result["zip_url"]).content
                return image_data, None
            elif "result_url" in result:
                image_data = requests.get(result["result_url"]).content
                return image_data, None
            else:
                return None, {"error": "Unexpected API response format."}
        else:
            return None, {"error": f"Segmind API error {response.status_code}: {response.text}"}

    except Exception as e:
        return None, {"error": f"Segmind exception: {str(e)}"}

     
def generate_clarityai_upscaled_image(
    image_url: str,
    scale_factor: int = 4,
    creativity: int = 4,
    resemblance: int = 3,
    dynamic: int = 4,
    fractality: int = 1,
    style: str = "portrait",
    prompt: str = ""
):
    print(">> Inside generate_clarityai_upscaled_image")
    print(" - image_url:", image_url)

    api_key = SEGMENT_API  # stored API key
    url = "https://api.segmind.com/v1/clarityai-creative-upscaler"

    try:
        data = {
            "image": image_url,
            "scale_factor": scale_factor,
            "creativity": creativity,
            "resemblance": resemblance,
            "dynamic": dynamic,
            "fractality": fractality,
            "style": style,
            "prompt": prompt
        }

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()

            # Handle image data or URL return
            if "image_base64" in result:
                import base64
                return base64.b64decode(result["image_base64"]), None
            elif "image_url" in result:
                image_data = requests.get(result["image_url"]).content
                return image_data, None
            else:
                return None, {"error": "Unexpected API response format."}

        else:
            return None, {"error": f"Segmind API error {response.status_code}: {response.text}"}

    except Exception as e:
        return None, {"error": f"Segmind exception: {str(e)}"}

def generate_segmindai_upscaled_image(
    image_url: str,
    scale_factor: int = 4,
    creativity: int = 4,
    resemblance: int = 3,
    dynamic: int = 4,
    fractality: int = 1,
    style: str = "portrait",
    prompt: str = ""
):
    print(">> Inside generate_clarityai_upscaled_image")
    print(" - image_url:", image_url)

    api_key = SEGMENT_API  # stored API key
    url = "https://api.segmind.com/v1/clarityai-creative-upscaler"

    try:
        data = {
            "image": image_url,
            "scale_factor": scale_factor,
            "creativity": creativity,
            "resemblance": resemblance,
            "dynamic": dynamic,
            "fractality": fractality,
            "style": style,
            "prompt": prompt
        }

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()

            # Handle image data or URL return
            if "image_base64" in result:
                import base64
                return base64.b64decode(result["image_base64"]), None
            elif "image_url" in result:
                image_data = requests.get(result["image_url"]).content
                return image_data, None
            else:
                return None, {"error": "Unexpected API response format."}

        else:
            return None, {"error": f"Segmind API error {response.status_code}: {response.text}"}

    except Exception as e:
        return None, {"error": f"Segmind exception: {str(e)}"}

