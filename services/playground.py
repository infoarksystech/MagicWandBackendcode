import os
import uuid
import requests
from sqlalchemy.orm import Session
from app.models.models import Playground
from app.services.provider import (
    generate_ideogram_image,
    generate_playground_v25_image,
    generate_sdxl_dreamshaper_lightning,
    generate_sdxl_yamers_realistic,
    generate_stability_ultra_image,
    generate_gpt_image,
    generate_imagen_4_image
)
from app.schemas.playground import ImageGenerationRequest

IMAGE_FOLDER = "assets/playground"

class PlaygroundService:
    @staticmethod
    async def generate_image(data: ImageGenerationRequest, db: Session):
        provider = data.provider.strip().lower()
        prompt = data.prompt
        output_format = data.output_format.strip().lower()
        aspect_ratio = data.aspect_ratio
        style_preset = data.style_preset
        seed = data.seed
        error = None
        local_url = None

        print("[DEBUG] Provider received:", provider)

        if provider == "ideogram-generate":
            image_url, magic_prompt, error = generate_ideogram_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio
            )
            if image_url:
                try:
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        os.makedirs(IMAGE_FOLDER, exist_ok=True)
                        file_name = f"{uuid.uuid4().hex[:8]}.{output_format}"
                        file_path = os.path.join(IMAGE_FOLDER, file_name)
                        with open(file_path, "wb") as f:
                            f.write(response.content)
                        local_url = f"/{IMAGE_FOLDER}/{file_name}"

                        db.add(Playground(
                            prompt=prompt,
                            provider=provider,
                            aspect_ratio=aspect_ratio,
                            output_format=output_format,
                            image_url=local_url
                        ))
                        db.commit()
                        return local_url, magic_prompt, error
                    else:
                        return None, None, {"error": "Failed to download image from Ideogram"}
                except Exception as e:
                    return None, None, {"error": str(e)}

        elif provider == "stability-ai-ultra":
            image_data, seed_used, error = generate_stability_ultra_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                seed=seed,
                style_preset=style_preset,
                output_format=output_format
            )
            if image_data:
                os.makedirs(IMAGE_FOLDER, exist_ok=True)
                file_name = f"{uuid.uuid4().hex[:8]}.{output_format}"
                file_path = os.path.join(IMAGE_FOLDER, file_name)
                with open(file_path, "wb") as f:
                    f.write(image_data)
                local_url = f"/{IMAGE_FOLDER}/{file_name}"

                db.add(Playground(
                    prompt=prompt,
                    provider=provider,
                    aspect_ratio=aspect_ratio,
                    output_format=output_format,
                    seed=seed_used,
                    image_url=local_url
                ))
                db.commit()
                return local_url, prompt, error

        elif provider == "gpt-image":
            print("[DEBUG] Entering gpt-image block")
            image_data, error = generate_gpt_image(
                prompt=prompt,
                output_format=output_format
            )
            print(f"-----------{prompt}")
            print(f"-----------{output_format}")
            if image_data:
                os.makedirs(IMAGE_FOLDER, exist_ok=True)
                file_name = f"{uuid.uuid4().hex[:8]}.{output_format}"
                file_path = os.path.join(IMAGE_FOLDER, file_name)
                with open(file_path, "wb") as f:
                    f.write(image_data)
                local_url = f"/{IMAGE_FOLDER}/{file_name}"
                print(f"-----------{local_url}")
                db.add(Playground(
                    prompt=prompt,
                    provider=provider,
                    output_format=output_format,
                    image_url=local_url
                ))
                print(f"-----------save on db")
                db.commit()
                return local_url, prompt, error
            else:
                print("[ERROR] GPT image generation failed:", error)  # ✅ Add this

        elif provider == "imagen":
            print("[DEBUG] Entering imagen block")
            image_data, error = generate_imagen_4_image(
                prompt=prompt,
                negative_prompt="",
                aspect_ratio=aspect_ratio
            )
            if image_data:
                os.makedirs(IMAGE_FOLDER, exist_ok=True)
                file_name = f"{uuid.uuid4().hex[:8]}.{output_format}"
                file_path = os.path.join(IMAGE_FOLDER, file_name)
                with open(file_path, "wb") as f:
                    f.write(image_data)
                local_url = f"/{IMAGE_FOLDER}/{file_name}"

                db.add(Playground(
                    prompt=prompt,
                    provider=provider,
                    output_format=output_format,
                    aspect_ratio=aspect_ratio,
                    image_url=local_url
                ))
                db.commit()
                return local_url, prompt, error
        elif provider == "dreamshaper":
            image_data, error = generate_sdxl_dreamshaper_lightning(
                prompt=prompt,
                negative_prompt="",
                samples=1,
                scheduler="DPM++ SDE",
                num_inference_steps=7,
                guidance_scale=1,
                seed=seed,
                img_width=1024,
                img_height=1024
            )
            if image_data:
                os.makedirs(IMAGE_FOLDER, exist_ok=True)
                file_name = f"{uuid.uuid4().hex[:8]}.{output_format}"
                file_path = os.path.join(IMAGE_FOLDER, file_name)
                with open(file_path, "wb") as f:
                    f.write(image_data)
                local_url = f"/{IMAGE_FOLDER}/{file_name}"

                db.add(Playground(
                    prompt=prompt,
                    provider=provider,
                    output_format=output_format,
                    image_url=local_url
                ))
                db.commit()
                return local_url, prompt, error
            else:
                print("[ERROR] Dreamshaper generation failed:", error)

        elif provider == "yamers-generate":
            image_data, error = generate_sdxl_yamers_realistic(
                prompt=prompt,
                negative_prompt="",
                samples=1,
                scheduler="DPM++ 2M Karras",
                num_inference_steps=30,
                guidance_scale=7,
                seed=seed,
                img_width=896,
                img_height=1152
            )
            if image_data:
                os.makedirs(IMAGE_FOLDER, exist_ok=True)
                file_name = f"{uuid.uuid4().hex[:8]}.{output_format}"
                file_path = os.path.join(IMAGE_FOLDER, file_name)
                with open(file_path, "wb") as f:
                    f.write(image_data)
                local_url = f"/{IMAGE_FOLDER}/{file_name}"

                db.add(Playground(
                    prompt=prompt,
                    provider=provider,
                    output_format=output_format,
                    image_url=local_url
                ))
                db.commit()
                return local_url, prompt, error
            else:
                print("[ERROR] Yamers generation failed:", error)

        elif provider == "playground":
            image_data, error = generate_playground_v25_image(
                prompt=prompt,
                negative_prompt="",
                samples=1,
                num_inference_steps=25,
                guidance_scale=3,
                seed=seed
            )
            if image_data:
                os.makedirs(IMAGE_FOLDER, exist_ok=True)
                file_name = f"{uuid.uuid4().hex[:8]}.{output_format}"
                file_path = os.path.join(IMAGE_FOLDER, file_name)
                with open(file_path, "wb") as f:
                    f.write(image_data)
                local_url = f"/{IMAGE_FOLDER}/{file_name}"

                db.add(Playground(
                    prompt=prompt,
                    provider=provider,
                    output_format=output_format,
                    image_url=local_url
                ))
                db.commit()
                return local_url, prompt, error
         
            else:
                print("[ERROR]  imagen image generation failed:", error)  # ✅ Add this

        # Fallback if no provider matched
        print("[ERROR] Unsupported provider or image generation failed")
        return None, None, {"error": "Unsupported provider or generation failed"}