import json
from typing import List
from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import uuid
import shutil
from PIL import Image
#from app.services.projects import create_projectc
from app.services.overlay import  fill_photo_frame_with_design,overlay_design_on_multiple_canvases,overlay_design_on_plates,overlay_multiple_designs_on_circles,frame_overlay_multiple_designs,fill_photo_frame_with_split_design_using_metadata,overlay_design_on_rounded_clock , coffee_mug_overlay  # type: ignore
from app.db.database import get_db
from app.models.models import Product, ProductMetadata,Gallery
import asyncio
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)  # Tune according to your server capacity
import time
import logging

executor = ThreadPoolExecutor()

router = APIRouter()

TEMP_OUTPUT_DIR = "outputs"
ASSETS_ROOT_DIR = os.path.join(os.path.dirname(__file__), "../../assets")
ASSETS_OUTPUT_DIR = os.path.join(ASSETS_ROOT_DIR, "output")

os.makedirs(TEMP_OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_OUTPUT_DIR, exist_ok=True)



def process_overlay(
    product_id: int,
    design_image_urls: List[str],
    db: Session
):
    try:
        design_image_paths = []
        for design_image_url in design_image_urls:
            if not design_image_url.startswith("/assets/"):
                raise HTTPException(status_code=400, detail="Invalid design_image_url path. Must start with /assets/")
            design_image_path = os.path.join(ASSETS_ROOT_DIR, design_image_url.replace("/assets/", ""))
            if not os.path.exists(design_image_path):
                raise HTTPException(status_code=400, detail=f"Design image not found at path: {design_image_url}")
            design_image_paths.append(design_image_path)

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        metadata_entries = db.query(ProductMetadata).filter(ProductMetadata.product_id == product_id).all()
        metadata_dict = {entry.meta_key: entry.meta_value for entry in metadata_entries}

        base_images_raw = metadata_dict.get("base-image")
        if not base_images_raw:
            raise HTTPException(status_code=400, detail="Product base-image is missing.")

        base_image_paths = json.loads(base_images_raw) if base_images_raw.strip().startswith("[") else [base_images_raw]
        base_image_paths = [path for path in base_image_paths if os.path.exists(path)]

        if not base_image_paths:
            raise HTTPException(status_code=400, detail="No valid base image paths found.")

        # Load common metadata
        dpi = int(metadata_dict.get("dpi", 300))
        is_cylindrical = metadata_dict.get("is_cylindrical", "false").lower() == "true"
        required_width = metadata_dict.get("required_width")
        required_height = metadata_dict.get("required_height")
        product_type = metadata_dict.get("product_type", "other").lower()
        clock_hand = None
        clock_hand_raw = metadata_dict.get("clock_hand")
        if clock_hand_raw:
            try:
                parsed = json.loads(clock_hand_raw)
                if isinstance(parsed, list) and parsed:
                    clock_hand = parsed[0]
                elif isinstance(parsed, str):
                    clock_hand = parsed
            except json.JSONDecodeError:
                clock_hand = clock_hand_raw

        frame_data_raw = metadata_dict.get("frame_data")
        frame_data = json.loads(frame_data_raw) if frame_data_raw else []

        required_resolution = None
        if required_width and required_height:
            required_resolution = {
                "width": int(required_width),
                "height": int(required_height)
            }

        # Validate design image (first one only)
        warnings = []
        with Image.open(design_image_paths[0]) as pil_img:
            actual_dpi = pil_img.info.get('dpi', (72, 72))[0]
            actual_width, actual_height = pil_img.size
            actual_aspect = actual_width / actual_height

        if actual_dpi < dpi:
            warnings.append(f"Design image DPI ({actual_dpi}) does not match required DPI ({dpi}).")
        if required_resolution:
            req_w = required_resolution["width"]
            req_h = required_resolution["height"]
            if actual_width < req_w or actual_height < req_h:
                warnings.append(f"Design image resolution ({actual_width}x{actual_height}) is lower than required ({req_w}x{req_h}).")
            expected_aspect = req_w / req_h
            if abs(actual_aspect - expected_aspect) >= 0.01:
                warnings.append(f"Aspect ratio mismatch: actual {actual_aspect:.2f}, expected {expected_aspect:.2f}")

        overlay_results = []

        for idx, base_path in enumerate(base_image_paths):
            # Frame data is now mapped by index, not by image_filename
            matching_frame_data = []
            if isinstance(frame_data, list) and idx < len(frame_data):
                matching_frame_data = frame_data[idx].get("frames", [])
            

            temp_output_filename = f"overlay_{uuid.uuid4()}.png"
            temp_output_path = os.path.join(TEMP_OUTPUT_DIR, temp_output_filename)
            print("🟢 START")

            if product_type == "photo_frame":
                result_path = fill_photo_frame_with_design(base_path, design_image_paths[0], temp_output_path)
            elif product_type == "split_frame":
                result_path = fill_photo_frame_with_split_design_using_metadata(base_path, design_image_paths[0], temp_output_path, matching_frame_data)
            elif product_type == "multiple_plate":
                result_path = overlay_multiple_designs_on_circles(base_path, design_image_paths, temp_output_path, matching_frame_data)
            elif product_type == "circular_plate":
                result_path = overlay_design_on_plates(base_path, design_image_paths[0], temp_output_path)
            elif product_type == "coffee_mug":
                result_path = coffee_mug_overlay(base_path, design_image_paths[0], temp_output_path, frame_data)
            elif product_type == "multiple_frame":
                result_path = frame_overlay_multiple_designs(base_path, design_image_paths, temp_output_path, matching_frame_data)
            elif product_type == "rounded_clock":
                result_path = overlay_design_on_rounded_clock(base_path, design_image_paths[0], clock_hand, temp_output_path, frame_data[0])
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported product type: {product_type}")

            if not result_path:
                raise HTTPException(status_code=500, detail="Overlay generation failed.")

            final_output_filename = f"overlay_{uuid.uuid4()}.png"
            final_output_path = os.path.join(ASSETS_OUTPUT_DIR, final_output_filename)
            shutil.move(result_path, final_output_path)

            image_link = f"/assets/output/{final_output_filename}"
            overlay_results.append(image_link)

        return {
            "overlay_image_urls": overlay_results,
            "warnings": warnings
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


def process_overlay1(
    product_id: int,
    design_image_urls: List[str],
    db: Session
):
    try:
        design_image_paths = []
        for design_image_url in design_image_urls:
            if not design_image_url.startswith("/assets/"):
                raise HTTPException(status_code=400, detail="Invalid design_image_url path. Must start with /assets/---"+design_image_url)
            design_image_path = os.path.join(ASSETS_ROOT_DIR, design_image_url.replace("/assets/", ""))
            if not os.path.exists(design_image_path):
                raise HTTPException(status_code=400, detail=f"Design image not found at path: {design_image_url}")
            design_image_paths.append(design_image_path)

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        metadata_entries = db.query(ProductMetadata).filter(ProductMetadata.product_id == product_id).all()
        metadata_dict = {entry.meta_key: entry.meta_value for entry in metadata_entries}

        product_image_path = metadata_dict.get("base-image")
        if not product_image_path or not os.path.exists(product_image_path):
            raise HTTPException(status_code=400, detail="Product base-image is missing or invalid path."+product_image_path)

        try:
            dpi = int(metadata_dict.get("dpi", 300))
            is_cylindrical = metadata_dict.get("is_cylindrical", "false").lower() == "true"
            required_width = metadata_dict.get("required_width")
            required_height = metadata_dict.get("required_height")
            product_type = metadata_dict.get("product_type", "other").lower()
            frame_data_raw = metadata_dict.get("frame_data")
            frame_data = json.loads(frame_data_raw) if frame_data_raw else None
            clock_hand = metadata_dict.get("clock_hand", None)

            required_resolution = None
            if required_width and required_height:
                required_resolution = {
                    "width": int(required_width),
                    "height": int(required_height)
                }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid metadata values: {e}")

        warnings = []
        with Image.open(design_image_paths[0]) as pil_img:
            actual_dpi = pil_img.info.get('dpi', (72, 72))[0]
            actual_width, actual_height = pil_img.size
            actual_aspect = actual_width / actual_height

        if actual_dpi < dpi:
            warnings.append(f"Design image DPI ({actual_dpi}) does not match required DPI ({dpi}).")
        if required_resolution:
            req_w = required_resolution["width"]
            req_h = required_resolution["height"]
            if actual_width < req_w or actual_height < req_h:
                warnings.append(f"Design image resolution ({actual_width}x{actual_height}) is lower than the required resolution ({req_w}x{req_h}).")
            expected_aspect = req_w / req_h
            if abs(actual_aspect - expected_aspect) >= 0.01:
                warnings.append(f"Design image aspect ratio ({actual_aspect:.2f}) does not match the required aspect ratio ({expected_aspect:.2f}).")

        temp_output_filename = f"overlay_{uuid.uuid4()}.png"
        temp_output_path = os.path.join(TEMP_OUTPUT_DIR, temp_output_filename)

        if product_type == "photo_frame":
            result_path = fill_photo_frame_with_design(product_image_path, design_image_paths[0], temp_output_path)
        elif product_type == "split_frame":
            result_path = fill_photo_frame_with_split_design_using_metadata(product_image_path, design_image_paths[0], temp_output_path, frame_data["frames"])
        elif product_type == "multiple_plate":
            result_path = overlay_multiple_designs_on_circles(product_image_path, design_image_paths, temp_output_path, frame_data["frames"])
        elif product_type == "circular_plate":
            result_path = overlay_design_on_plates(product_image_path, design_image_paths[0], temp_output_path)
        elif product_type == "multiple_canvases":
            result_path = overlay_design_on_multiple_canvases(product_image_path, design_image_paths[0], temp_output_path)
        elif product_type == "coffee_mug":
            result_path = coffee_mug_overlay(product_image_path, design_image_paths[0], temp_output_path, frame_data)
        elif product_type == "rounded_clock":
            result_path = overlay_design_on_rounded_clock(product_image_path, design_image_paths[0],clock_hand, temp_output_path, frame_data["frames"])
        else:
            raise HTTPException(status_code=400, detail="Unsupported product type.")

        if not result_path:
            raise HTTPException(status_code=500, detail="Overlay generation failed.")

        final_output_filename = f"overlay_{uuid.uuid4()}.png"
        final_output_path = os.path.join(ASSETS_OUTPUT_DIR, final_output_filename)
        shutil.move(result_path, final_output_path)

        image_link = f"/assets/output/{final_output_filename}"
        response_content = {"overlay_image_url": image_link}
        if warnings:
            response_content["warnings"] = warnings

        return response_content

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.post("/test-overlay")
async def test_overlay_api(
    product_id: int = Form(...),
    design_image_urls: str = Form(...),
    db: Session = Depends(get_db)
):
    design_image_urls_list = json.loads(design_image_urls)
    result = process_overlay(product_id, design_image_urls_list, db)
    return JSONResponse(content=result)



@router.post("/test-overlay-async")
async def test_overlay_api_async(
    product_id: int = Form(...),
    design_image_urls: str = Form(...)
):
    start = time.time()
    try:
        design_image_urls_lists = json.loads(design_image_urls)

        if not isinstance(design_image_urls_lists, list) or not all(isinstance(item, list) for item in design_image_urls_lists):
            raise HTTPException(status_code=400, detail="design_image_urls must be a JSON array of arrays.")

        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, process_overlay_threadsafe, product_id, urls)
            for urls in design_image_urls_lists
        ]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start
        return JSONResponse(content={"results": results, "total_time_sec": round(total_time, 2)})

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for design_image_urls")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")



def process_overlay_threadsafe(product_id: int, design_image_urls: List[str]):
    from app.db.database import SessionLocal  # Import session factory
    db = SessionLocal()
    try:
        return process_overlay(product_id, design_image_urls, db)
    finally:
        db.close()


@router.post("/trigger-overlay-from-gallery")
async def trigger_overlay_from_gallery(
    product_id: int = Form(...),
    key: str = Form(...),
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    start = time.time()
    try:
        # Total number of matching entries (not currently returned but you could include if needed)
        total = db.query(Gallery).filter(Gallery.key.ilike(f"%{key}%")).count()
        if total == 0:
            raise HTTPException(status_code=404, detail="No gallery entries found for the given key.")

        # Fetch paginated image URLs with the matching key
        gallery_entries = (
            db.query(Gallery)
            .filter(Gallery.key.ilike(f"%{key}%"))
            .offset(offset)
            .limit(limit)
            .all()
        )

        if not gallery_entries:
            raise HTTPException(status_code=404, detail="No gallery entries found for the given key and pagination range")

        # Prepare input for async overlay processing
        design_image_urls_lists = [[entry.image_url] for entry in gallery_entries]
        gallery_ids = [entry.id for entry in gallery_entries]

        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, process_overlay_threadsafe, product_id, urls)
            for urls in design_image_urls_lists
        ]
        results = await asyncio.gather(*tasks)

        # Combine Gallery ID and overlay result
        combined_results = []
        for gallery_id, result in zip(gallery_ids, results):
            result["gallery_id"] = gallery_id
            combined_results.append(result)

        total_time = time.time() - start
        return JSONResponse(content={"results": combined_results, "total": total, "total_time_sec": round(total_time, 2)})

    except HTTPException as http_exc:
        raise http_exc  # Re-raise directly

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.post("/overlay-from-gallery-id")
async def overlay_from_gallery_id(
    product_id: int = Form(...),
    gallery_id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Fetch the gallery entry using the gallery ID
        gallery_entry = db.query(Gallery).filter(Gallery.id == gallery_id).first()
        if not gallery_entry:
            raise HTTPException(status_code=404, detail="Gallery entry not found.")

        image_url = gallery_entry.image_url
        if not image_url:
            raise HTTPException(status_code=400, detail="Gallery entry does not contain a valid image URL.")

        # Prepare input as a single-item list for design image
        design_image_urls = [image_url]

        # Call the existing overlay logic
        result = process_overlay(product_id, design_image_urls, db)

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

