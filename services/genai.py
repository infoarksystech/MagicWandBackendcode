import json
import os
import shutil
import uuid
from typing import Dict, List
import requests
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified
from fastapi import HTTPException
from app.models.models import AppSettings, ImageStyle, Prompt
import requests
from PIL import Image
import io
import re

from app.services.provider import generate_automatic_mask_image, generate_background_erased_image, generate_caricature_image, generate_flux_kontext_image, generate_gemini_image, generate_gpt_image, generate_ic_light_image, generate_ideogram_3_image, generate_ideogram_image, generate_ideogram_remix_image, generate_imagen_4_image, generate_openai_edit_image, generate_playground_v25_image, generate_sdxl_dreamshaper_lightning, generate_sdxl_yamers_realistic, generate_skin_contrast_upscale_image, generate_stability_creative_upscaled_image, generate_stability_fast_upscaled_image, generate_stability_remove_background, generate_stability_replace_background_and_relight, generate_stability_search_and_recolor, generate_stability_search_and_replace, generate_stability_sketch_image, generate_stability_ultra_image, generate_text_overlay_image,generate_replace_background_image,generate_3d_image,generate_segmindai_upscaled_image

# Load API key
load_dotenv()
IDEOGRAM_KEY = os.getenv("IDEOGRAM_KEY")
STABILITY_KEY = os.getenv("STABILITY_KEY")
if not IDEOGRAM_KEY:
    raise ValueError("Missing API key! Set IDEOGRAM_KEY in the .env file.")

# Setup image folder
IMAGE_FOLDER = "assets/prompt_images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)


# ✅ Get metadata from product_metadata table
def get_metadata_value(db, product_id: int, key: str) -> str:
    result = db.execute(
        text("SELECT meta_value FROM product_metadata WHERE product_id = :pid AND meta_key = :key"),
        {"pid": product_id, "key": key}
    ).fetchone()
    return result[0] if result else ""


# ✅ Download and save image
def download_and_save_image(prompt_id: int, image_url: str, output_format: str = ""):
    print(f"[INFO] Downloading image for prompt_id: {prompt_id}, URL: {image_url}")
    print("pra@1")
    try:
        response = requests.get(image_url, stream=True)
        print(f"[DEBUG] Response status code: {response.status_code}")
        print("pra@2")
        if response.status_code != 200:
            print(f"[ERROR] Failed to download image, status: {response.status_code}")
            return None, "Failed to download image"
        print("pra@3")
        os.makedirs(IMAGE_FOLDER, exist_ok=True)
        random_str = uuid.uuid4().hex[:8]
        file_name = f"{prompt_id}_{random_str}.{output_format}"
        file_path = os.path.join(IMAGE_FOLDER, file_name)
        print(f"[INFO] Saving image to: {file_path}")
        print("pra@4")
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print("pra@5")
        return f"/{IMAGE_FOLDER}/{file_name}", None
        
    except Exception as e:
        print("pra@6")
        print(f"[EXCEPTION] Error downloading/saving image: {str(e)}")
        return None, str(e)


def save_image(prompt_id: int, image_data: bytes, seed: int, output_format: str = "jpeg"):
    try:
        os.makedirs(IMAGE_FOLDER, exist_ok=True)
        file_name = f"{prompt_id}_{seed}.{output_format}"
        file_path = os.path.join(IMAGE_FOLDER, file_name)
        print(f"[INFO] Saving binary image to: {file_path}")

        with open(file_path, "wb") as f:
            f.write(image_data)

        return f"/{IMAGE_FOLDER}/{file_name}"
    except Exception as e:
        print(f"[EXCEPTION] Error saving image: {str(e)}")
        return None

def get_public_image_url(local_path: str) -> str:
    # Example placeholder function — you must replace this
    # with real upload logic (e.g., S3, Cloudinary, etc.)
    if local_path.startswith("http"):
        return local_path  # Already a URL
    # For now, just return None if not a URL (to avoid crashing)
    return None

def generate_images_from_prompt_record(
    db,
    user_id: int,
    aspect_ratio:str,
    prompt_record,
    no_of_images: int = 1,
    user_params_dict=None
):
    results = []
    print(f"[INFO] Starting image generation for user_id: {user_id}")
    
    if not prompt_record or not prompt_record.prompt:
        print("[ERROR] Invalid prompt record.")
        return [{"error": "Invalid prompt record"}]

    # Prepare full prompt
    if isinstance(prompt_record.prompt, list):
        if not prompt_record.prompt:
            return [{"error": "Prompt list is empty"}]
        full_prompt = " ".join(prompt_record.prompt).strip()
    else:
        full_prompt = str(prompt_record.prompt).strip()

    if not full_prompt:
        return [{"error": "Prompt is empty"}]

    print(f"[DEBUG] Full prompt: {full_prompt}")

    # Extract provider and options from user_params_dict and DB
    provider=None
    image_style_name = user_params_dict.get("imageStyle") or None
    print(f" image_style_name: {image_style_name}")

    if image_style_name:
        style_record = db.query(ImageStyle).filter_by(style_name=image_style_name).first()
        print(f" style_record: {style_record}")
        
        if not style_record:
            raise ValueError(f"Image style '{image_style_name}' not found in database.")
        
        try:
            endpoint_data = json.loads(style_record.endpoint)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse endpoint JSON: {style_record.endpoint}")
            print(f"[ERROR] JSONDecodeError: {e}")
            return [{"error": "Invalid endpoint format in image style configuration"}]

        
        
        # Extract values from the endpoint JSON
        provider = endpoint_data.get("provider", "")
        seed = endpoint_data.get("seed", "0")
        output_format=endpoint_data.get("output_format", "")
        resolution = endpoint_data.get("resolution", "")
        grow_mask = endpoint_data.get("grow_mask", "")
        negative_prompt = endpoint_data.get("negative_prompt", "")
        foreground_prompt = endpoint_data.get("foreground_prompt", "")
        preserve_original_subject = endpoint_data.get("preserve_original_subject", "")
        original_background_depth = endpoint_data.get("original_background_depth", "")
        keep_original_background = endpoint_data.get("keep_original_background", "")
        light_source_strength = endpoint_data.get("light_source_strength", "")
        light_source_direction = endpoint_data.get("light_source_direction", "")
        style_preset = endpoint_data.get("style_preset", "")
        control_strength = endpoint_data.get("control_strength", "")
        fidelity = endpoint_data.get("fidelity", "")
        change_strength = endpoint_data.get("change_strength", "")
        composition_fidelity = endpoint_data.get("composition_fidelity", "")
        style_strength = endpoint_data.get("style_strength", "")
        creativity = endpoint_data.get("creativity", "")
        left = endpoint_data.get("left", "")
        right = endpoint_data.get("right", "")
        up = endpoint_data.get("up", "")
        down = endpoint_data.get("down", "")
        ref_images_path = endpoint_data.get("ref_image", "")
        ref_images_url = get_public_image_url(ref_images_path)
        size=endpoint_data.get("size", "")
        quality=endpoint_data.get("quality", "")
        moderation=endpoint_data.get("moderation", "")
        background=endpoint_data.get("background", "")

    
        # Handle aspect ratio format
        standard_aspect_ratio = parse_aspect_ratio(aspect_ratio)
        model_aspect_ratio = map_aspect_ratio_for_provider(standard_aspect_ratio, provider)  
        print(f"aspect ratio: {model_aspect_ratio}")
    # Generate images
    for _ in range(no_of_images):
        print(f"[INFO] Generating image using provider: {provider} for style: {image_style_name}")
        image_url = magic_prompt = error = None

        if provider == "ideogram-generate":
            image_url, magic_prompt, error = generate_ideogram_image(full_prompt, model_aspect_ratio,ref_images_url)
            print(f"[DEBUG] Ideogram result => URL: {image_url}, Error: {error}")

            if error:
                results.append({"error": error})
                continue

            saved_path, error = download_and_save_image(prompt_record.id, image_url, output_format)
            print(f"[DEBUG] Saved path: {saved_path}, Error: {error}")

            if error:
                results.append({"error": error})
                continue

            results.append({
                "image_path": saved_path,
                "prompt": magic_prompt
            })

        elif provider == "stability-ai-ultra":
            image_data, seed, error = generate_stability_ultra_image(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                aspect_ratio=model_aspect_ratio,
                seed=seed,
                style_preset=style_preset,
                output_format=output_format
            )
            print(f"[DEBUG] Stability result => Seed: {seed}, Error: {error}")

            if error or not image_data:
                results.append({"error": error or "Image generation failed"})
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}_{seed}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"
            results.append({
                "image_path": remix_url,
                "prompt": full_prompt,
            })

        elif provider == "gemini-generate":
            image_url, used_prompt, error = generate_gemini_image(
                full_prompt,
                model_aspect_ratio,
                output_format
            )
            print(f"[DEBUG] Gemini result => URL: {image_url}, Error: {error}")

            if error or not image_url:
                error_msg = error or "Image URL not returned (possible model issue)."
                results.append({"error": error_msg})
                continue

            saved_path, error = download_and_save_image(prompt_record.id, image_url, output_format)
            print(f"[DEBUG] Saved path: {saved_path}, Error: {error}")

            if error:
                results.append({"error": error})
                continue

            results.append({
                "image_path": saved_path,
                "prompt": used_prompt
            })
        elif provider == "gpt-image":
            image_data, error = generate_gpt_image(
                prompt=full_prompt,
                output_format=output_format,
                size=size,
                quality=quality,
                moderation=moderation,
                background=background

            )
            if error:
                print(f"[ERROR] GPT-Image-1 Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            print(f"image path :-----------{file_name}")
            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"
            results.append({
                "image_path": remix_url,
                "prompt": full_prompt,
            })

        elif provider == "imagen":
            image_data, error = generate_imagen_4_image(
                prompt=full_prompt ,
                negative_prompt=negative_prompt,
                aspect_ratio=model_aspect_ratio
            )

            if error:
                print(f"[ERROR] Imagen-4 Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            print(f"file_name:----------{file_name}")
            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"
            results.append({
                "image_path": remix_url,
                "prompt": full_prompt,
            })

        elif provider == "dreamshaper":
            image_data, error = generate_sdxl_dreamshaper_lightning(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                samples=1,
                scheduler="DPM++ SDE",
                num_inference_steps=7,
                guidance_scale=1,
                seed=seed,
                img_width=1024,
                img_height=1024
            )


            if error:
                print(f"[ERROR] SDXL Dreamshaper Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            print(f"file_name:----------{file_name}")
            with open(abs_path, "wb") as f:
                f.write(image_data)
        
            remix_url = f"/{IMAGE_FOLDER}/{file_name}"
            results.append({
                "image_path": remix_url,
                "prompt": full_prompt,
            })

        elif provider == "yamers":
            image_data, error = generate_sdxl_yamers_realistic(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                samples=1,
                scheduler="DPM++ 2M Karras",
                num_inference_steps=30,
                guidance_scale=7,
                seed=seed,
                img_width=896,
                img_height=1152
            )

            if error:
                print(f"[ERROR] Yamers Realistic Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            print(f"file_name:----------{file_name}")
            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"
            results.append({
                "image_path": remix_url,
                "prompt": full_prompt,
            })


        elif provider == "playground":
            image_data, error = generate_playground_v25_image(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                samples=1,
                num_inference_steps=25,
                guidance_scale=3,
                seed=seed
            )

            if error:
                print(f"[ERROR] Playground-v2.5 Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            print(f"file_name:----------{file_name}")
            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"
            results.append({
                "image_path": remix_url,
                "prompt": full_prompt,
            })

        elif provider == "segmind-ideogram":
            image_data, error = generate_ideogram_3_image(
                prompt=full_prompt,
                negative_prompt='',
                resolution="1024x1024",
                rendering_speed="DEFAULT",
                magic_prompt="",
                style_codes=[],
                style_type=""
            )

            print(f"aspect ratio:----------{aspect_ratio}")

            if error:
                print(f"[ERROR] Ideogram-3 Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            print(f"file_name:----------{file_name}")
            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"
            results.append({
                "image_path": remix_url,
                "prompt": full_prompt,
            })
        
        
     
        else:
            print(f"[ERROR] Unsupported provider: {provider}")
            results.append({"error": f"Unsupported provider: {provider}"})

    print(f"[INFO] Completed image generation. Total results: {len(results)}")
    return results
   
def remix_images_from_reference(
    db: requests.Session,
    user_id: int,
    aspect_ratio:str,
    prompt_record: Prompt,
    ref_image_url: str,
    no_of_images: int = 1,
    user_params_dict=None  # ✅ Add this
):
    results = []
    model_aspect_ratio = None  # ensure it exists
    # Step 1: Get the image style from user_params_dict
    image_style_name = user_params_dict.get("imageStyle") if user_params_dict else None
    print(f" image_style_name: {image_style_name}")
    print("user_params_dict:", user_params_dict if user_params_dict else {})

    if image_style_name:
        style_record = db.query(ImageStyle).filter_by(style_name=image_style_name).first()
        print(f" style_record: {style_record}")
        
        if not style_record:
            raise ValueError(f"Image style '{image_style_name}' not found in database.")
        
        # Parse the JSON string in the endpoint field
        endpoint_data = json.loads(style_record.endpoint)  # Parse endpoint into a Python dictionary
        print(f"Parsed endpoint data: {endpoint_data}")
        
        # Extract values from the endpoint JSON
        provider = endpoint_data.get("provider", "")
        seed = endpoint_data.get("seed", "")
        output_format=endpoint_data.get("output_format", "")
        resolution = endpoint_data.get("resolution", "")
        grow_mask = endpoint_data.get("grow_mask", "")
        negative_prompt = endpoint_data.get("negative_prompt", "")
        foreground_prompt = endpoint_data.get("foreground_prompt", "")
        preserve_original_subject = endpoint_data.get("preserve_original_subject", "")
        original_background_depth = endpoint_data.get("original_background_depth", "")
        keep_original_background = endpoint_data.get("keep_original_background", "")
        light_source_strength = endpoint_data.get("light_source_strength", "")
        light_source_direction = endpoint_data.get("light_source_direction", "")
        style_preset = endpoint_data.get("style_preset", "")
        control_strength = endpoint_data.get("control_strength", "")
        fidelity = endpoint_data.get("fidelity", "")
        change_strength = endpoint_data.get("change_strength", "")
        composition_fidelity = endpoint_data.get("composition_fidelity", "")
        style_strength = endpoint_data.get("style_strength", "")
        creativity = endpoint_data.get("creativity", "")
        left = endpoint_data.get("left", "")
        right = endpoint_data.get("right", "")
        up = endpoint_data.get("up", "")
        down = endpoint_data.get("down", "")
        threshold = endpoint_data.get("threshold", "")
        invert_mask = endpoint_data.get("invert_mask", False)
        return_mask = endpoint_data.get("return_mask", True)
        return_alpha = endpoint_data.get("return_alpha", False)
        font = endpoint_data.get("font", "")
        font_size = endpoint_data.get("font_size", "")
        color = endpoint_data.get("color", "")
        outline_color = endpoint_data.get("outline_color", "")
        outline_size = endpoint_data.get("outline_size", "")
        align = endpoint_data.get("align", "")
        blend_mode = endpoint_data.get("blend_mode", "")
        image_format = endpoint_data.get("image_format", "")
        image_quality = endpoint_data.get("image_quality", "")
        margin_x = endpoint_data.get("margin_x", "")
        margin_y = endpoint_data.get("margin_y", "")
        linespace = endpoint_data.get("linespace", "")
        graphspace = endpoint_data.get("graphspace", "")
        wrap = endpoint_data.get("wrap", "")
        text_underlay = endpoint_data.get("text_underlay", True)
        light_source = endpoint_data.get("light_source", "None")
        highres_scale = endpoint_data.get("highres_scale", "")
        lowres_denoise = endpoint_data.get("lowres_denoise", "")
        highres_denoise = endpoint_data.get("highres_denoise", "")
        output_quality = endpoint_data.get("output_quality", "")
        appended_prompt = endpoint_data.get("appended_prompt", "")
        overlay_image = endpoint_data.get("overlay_image", None)
        rescale_factor = endpoint_data.get("rescale_factor", "")
        resize_method = endpoint_data.get("resize_method", "")
        bg_remove_model = endpoint_data.get("bg_remove_model", "")
        mirror = endpoint_data.get("mirror", "")
        opacity = endpoint_data.get("opacity", "")
        x_percent = endpoint_data.get("x_percent", "")
        y_percent = endpoint_data.get("y_percent", "")
        rotation = endpoint_data.get("rotation", "")
        original_aspect_ratio = endpoint_data.get("aspect_ratio", "")
    else:
        # fallback if no style is selected
        provider_setting = db.query(AppSettings).filter_by(app_key="provider").first()
        provider = provider_setting.app_value if provider_setting else "ideogram-remix"

    # Handle aspect ratio format
        standard_aspect_ratio = parse_aspect_ratio(aspect_ratio)
        model_aspect_ratio = map_aspect_ratio_for_provider(standard_aspect_ratio, provider)
        print(f"aspect ratio: {model_aspect_ratio}")   

    if not isinstance(prompt_record.image_urls, list):
        prompt_record.image_urls = []
    select_prompt = user_params_dict.get("otherKeywords", "")
    select_background = user_params_dict.get("background", "")


    for _ in range(no_of_images):
        remix_url = remix_prompt = error = None

        if provider == "stabilityai-sketch":
            local_image_path = ref_image_url
            if ref_image_url.startswith("http"):
                local_image_path = download_image_to_temp_file(ref_image_url)
                if not local_image_path:
                    continue

            image_data, remix_prompt, error = generate_stability_sketch_image(
                image_path=local_image_path,
                prompt=prompt_record.prompt
            )

            if error:
                print(f"[ERROR] Sketch Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"
    
        elif provider == "openai-edit":
            subject_image_path = ref_image_url
            if subject_image_path.startswith("http"):
                subject_image_path = download_image_to_temp_file(subject_image_path)
                if not subject_image_path:
                    print(f"[ERROR] Could not download image: {ref_image_url}")
                    continue
                 
            image_data, error = generate_openai_edit_image(
                reference_image="https://magicwandapi.arksys.in/"+ subject_image_path,
                prompt=prompt_record.prompt,
                output_format=output_format
            )

            if error:
                print(f"[ERROR] OpenAI Remix Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.png"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"


        elif provider == "caricature-style":
            subject_image_path = ref_image_url
            if subject_image_path.startswith("http"):
                subject_image_path = download_image_to_temp_file(subject_image_path)
                if not subject_image_path:
                    print(f"[ERROR] Could not download image: {ref_image_url}")
                    continue

            image_data, error = generate_caricature_image(

                reference_image="https://magicwandapi.arksys.in/"+ subject_image_path,      #subject_image_path,
                output_format=output_format
            )

            if error:
                print(f"[ERROR] Caricature API Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"

        elif provider == "flux-kontext-max":
            subject_image_path = ref_image_url
            if subject_image_path.startswith("http"):
                subject_image_path = download_image_to_temp_file(subject_image_path)
                if not subject_image_path:
                    print(f"[ERROR] Could not download image: {ref_image_url}")
                    continue

            image_data, error = generate_flux_kontext_image(
                reference_image=subject_image_path,  # local file path now
                prompt=prompt_record.prompt,
                aspect_ratio=original_aspect_ratio,
                output_format=output_format
            )
            print(f"original_aspect_ratio: {original_aspect_ratio}")
            if error:
                print(f"[ERROR] Flux Kontext API Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"

        elif provider == "keep-original":
            subject_image_path = ref_image_url

            if subject_image_path.startswith("http"):
                subject_image_path = download_image_to_temp_file(subject_image_path)
                if not subject_image_path:
                    print(f"[ERROR] Could not download image: {ref_image_url}")
                    continue

            # Instead of generating a new image, just copy the reference image
            try:
                with open(subject_image_path, "rb") as f:
                    image_data = f.read()
            except Exception as e:
                print(f"[ERROR] Could not read reference image: {e}")
                continue

            # Save it with a new name to simulate “generated” image
            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.{output_format}"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"

            results.append({
                "image_path": remix_url,
                "source": "keep-original"
            })    
            
        elif provider == "background-eraser":
            subject_image_path = ref_image_url if isinstance(ref_image_url, list) else [ref_image_url]
            

            image_data, error = generate_background_erased_image(
                reference_image="https://magicwandapi.arksys.in/"+ subject_image_path,
                return_mask=return_mask,
                invert_mask=invert_mask,
                grow_mask=grow_mask
            )

            if error:
                print(f"[ERROR] Background Eraser Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.png"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"

        
        elif provider == "text-overlay":

            # ✅ Always normalize to string
            if isinstance(ref_image_url, list):
                subject_image_path = ref_image_url[0]
            else:
                subject_image_path = ref_image_url

            reference_image = f"https://magicwandapi.arksys.in/{subject_image_path.lstrip('/')}"

            # --------------------------------------------------
            # ✅ Overlay config (defaults + user OR fallback)
            # --------------------------------------------------
            overlay_config = {
                "align": user_params_dict.get("text") or "center",
                "blend_mode": "normal",
                "color": user_params_dict.get("textColor") or "#ffffff",
                "font": user_params_dict.get("textStyle") or "JosefinSans-Bold",
                "font_size": (
                    int(user_params_dict.get("background"))
                    if user_params_dict
                    and user_params_dict.get("background")
                    and str(user_params_dict.get("background")).isdigit()
                    else 120
                ),

                "image_format": "jpeg",
                "image_quality": 90,
                "margin_x": 40,
                "margin_y": 40,
                "wrap": 10,

                # visibility & layering
                "text_underlay": False,
                "outline_color": "#000000",
                "outline_size": 2,
                "linespace": 10,
                "graphspace": 0
            }

            # --------------------------------------------------
            # ✅ Text priority: subject → prompt
            # --------------------------------------------------
            text_value = (
                user_params_dict.get("subject")
                if user_params_dict
                else None
            ) or prompt_record.prompt

            # --------------------------------------------------
            # ✅ Generate image
            # --------------------------------------------------
            image_data, error = generate_text_overlay_image(
                reference_image=reference_image,
                text=text_value,
                **overlay_config
            )

            if error:
                print(f"[ERROR] Text Overlay Error: {error}")
                continue

            # --------------------------------------------------
            # ✅ Save image
            # --------------------------------------------------
            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.jpg"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"

            results.append({
                "image_path": remix_url,
                "prompt": text_value,
                "applied_overlay": overlay_config
            })



        elif provider == "relighting":
            subject_image_path = ref_image_url if isinstance(ref_image_url, list) else [ref_image_url]
            remote_url = None

            
            image_data, error = generate_ic_light_image(
                reference_image="https://magicwandapi.arksys.in/"+ subject_image_path,
                prompt=prompt_record.prompt
            )

            if error:
                print(f"[ERROR] IC Light Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.jpg"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"
    
        elif provider == "skin-contrast":
            if isinstance(ref_image_url, list):
                subject_image_path = ref_image_url[0]  # take the first one
            else:
                subject_image_path = ref_image_url
           
            image_data, error = generate_skin_contrast_upscale_image(
                reference_image="https://magicwandapi.arksys.in/"+ subject_image_path,
                #"https://magicwandapi.arksys.in/{}",
                image_format=output_format,
                image_quality=85
            )

            if error:
                print(f"[ERROR] Skin Contrast Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.jpg"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"  

            results.append({
                "image_path": remix_url,
                "source": "skin-contrast"
            })

        elif provider == "segmind-ideogram-replace-bg":
            subject_image_path = ref_image_url if isinstance(ref_image_url, list) else [ref_image_url]

            image_data, error = generate_replace_background_image(
                image_url="https://magicwandapi.arksys.in/"+ subject_image_path,
                prompt=prompt_record.prompt,
                rendering_speed="DEFAULT",
                magic_prompt="AUTO",
                style_codes=[],
                style_reference_images=[]
            )

            if error:
                print(f"[ERROR] Ideogram Replace Background Error: {error}")
                continue

            random_str = uuid.uuid4().hex[:8]
            file_name = f"{random_str}.png"
            abs_path = os.path.join(IMAGE_FOLDER, file_name)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "wb") as f:
                f.write(image_data)

            remix_url = f"/{IMAGE_FOLDER}/{file_name}"
            results.append({
                "image_path": remix_url,
                "prompt": prompt_record.prompt
            })
     
                                      
        else:  # default: ideogram-remix
            remix_url, remix_prompt, error = generate_ideogram_remix_image(
                prompt=prompt_record.prompt,
                ref_image_path=ref_image_url,
                aspect_ratio=aspect_ratio
            )
            print(" - image_path1:", ref_image_url)
            print(" - prompt1:", prompt_record.prompt)
            if error:
                print(f"[ERROR] Ideogram Error: {error}")
                continue

            saved_path, error = download_and_save_image(prompt_record.id, remix_url)
            if error:
                print(f"[ERROR] Save Error: {error}")
                continue

            remix_url = saved_path

        # Avoid duplicate image URLs
        if remix_url and remix_url not in prompt_record.image_urls:
            prompt_record.image_urls.append(remix_url)

        # Save magic prompt if not already stored
        if not prompt_record.magic_prompt and remix_prompt:
            prompt_record.magic_prompt = remix_prompt

        results.append({
            "prompt": prompt_record.prompt,
            "image_path": remix_url,
            "ref_image":ref_image_url
        })

    flag_modified(prompt_record, "image_urls")
    db.commit()

    print(f"[INFO] remix_images_from_reference generated {len(results)} image(s)")
    return results



def parse_aspect_ratio(raw_ratio: str) -> str:
    raw_ratio = (raw_ratio or "").strip()

    match_aspect = re.match(r"^ASPECT_(\d+)_(\d+)$", raw_ratio)
    if match_aspect:
        return f"{match_aspect.group(1)}:{match_aspect.group(2)}"

    match_comma = re.match(r"^(\d+)\s*,\s*(\d+)$", raw_ratio)
    if match_comma:
        return f"{match_comma.group(1)}:{match_comma.group(2)}"

    if re.match(r"^\d+:\d+$", raw_ratio):
        return raw_ratio

    return raw_ratio  # returns string (never None!)

def map_aspect_ratio_for_provider(aspect_ratio: str, provider: str) -> str:
    parts = aspect_ratio.split(":")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        return aspect_ratio  # returns string, same as input

    width, height = parts

    if provider in ["ideogram-generate", "ideogram-remix"]:
        return f"ASPECT_{width}_{height}"
    elif provider in ["gemini-generate", "flux-kontext-max","stability-ai-ultra","imagen"]:
     if width and height:
        return f"{width}:{height}"
     else:
        return None
    else:
        return f"{width}:{height}"



def ensure_absolute_url(url: str, base_url="http://localhost:8000"):
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"{base_url}/{url.lstrip('/')}"

def download_image_to_temp_file(url: str) -> str:
    try:
        response = requests.get(url)
        if response.status_code == 200:
            temp_path = f"/tmp/{uuid.uuid4()}.jpg"
            with open(temp_path, "wb") as f:
                f.write(response.content)
            print(f"[INFO] Image downloaded to: {temp_path}")
            return temp_path
        else:
            print(f"[ERROR] Failed to download image: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Exception during image download: {e}")
        return None    


def download_openai_image_to_temp_file(url):
    try:
        response = requests.get(url)
        if response.status_code != 200 or 'image' not in response.headers.get('Content-Type', ''):
            print(f"[ERROR] Invalid image content from: {url}")
            return None

        file_ext = url.split(".")[-1].split("?")[0]
        file_name = f"{uuid.uuid4().hex[:8]}.{file_ext}"
        temp_path = os.path.join("assets", "prompt_images", file_name)

        os.makedirs(os.path.dirname(temp_path), exist_ok=True)

        with open(temp_path, "wb") as f:
            f.write(response.content)

        # Verify image validity
        with Image.open(temp_path) as img:
            img.verify()

        return temp_path

    except Exception as e:
        print(f"[ERROR] Failed to download image: {e}")
        return None

    
    

