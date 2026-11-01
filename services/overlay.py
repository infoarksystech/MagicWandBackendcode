import os
import cv2
import numpy as npi
import json
import numpy as np
from PIL import Image, ImageDraw,ImageFilter
# import torch
import logging
import time
# from PIL import Image
# import os

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load YOLOv5 model once
#model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

# def generate_overlay(product_image_path: str, design_image_path: str, is_cylindrical: bool, dpi: int,
#                      required_resolution: dict = None, output_path: str = 'final_overlay.png') -> str:
#     if not os.path.exists(product_image_path):
#         raise FileNotFoundError(f"Product image not found: {product_image_path}")
#     if not os.path.exists(design_image_path):
#         raise FileNotFoundError(f"Design image not found: {design_image_path}")

#     product_img = cv2.imread(product_image_path)
#     design_img = cv2.imread(design_image_path, cv2.IMREAD_UNCHANGED)

#     # Validate design image DPI
#     with Image.open(design_image_path) as pil_img:
#         design_dpi = pil_img.info.get('dpi', (72, 72))[0]
#     if design_dpi < dpi:
#         raise ValueError(f"Design DPI ({design_dpi}) below required {dpi}")

#     design_height_px, design_width_px = design_img.shape[:2]

#     if required_resolution:
#         req_w, req_h = required_resolution.get("width"), required_resolution.get("height")
#         if req_w is None or req_h is None:
#             raise ValueError("Required resolution must specify both width and height.")
#         if design_width_px < req_w or design_height_px < req_h:
#             raise ValueError("Design resolution too low.")
#         actual_aspect = design_width_px / design_height_px
#         required_aspect = req_w / req_h
#         if abs(actual_aspect - required_aspect) >= 0.01:
#             raise ValueError("Aspect ratio mismatch.")

#     # Background removal on design image
#     if design_img.shape[2] == 4:
#         design_rgb = design_img[:, :, :3]
#         design_alpha = design_img[:, :, 3]
#     else:
#         design_rgb = design_img
#         design_alpha = np.ones(design_rgb.shape[:2], dtype=np.uint8) * 255

#     hsv = cv2.cvtColor(design_rgb, cv2.COLOR_BGR2HSV)
#     bg_mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))
#     fg_mask = cv2.bitwise_not(bg_mask)
#     fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
#     design_alpha = cv2.bitwise_and(design_alpha, fg_mask)

#     # Determine the printing area
#     if not is_cylindrical:
#         # Attempt to detect a photo frame by finding a large, white, quadrilateral region.
#         hsv_product = cv2.cvtColor(product_img, cv2.COLOR_BGR2HSV)
#         white_mask = cv2.inRange(hsv_product, np.array([0, 0, 200]), np.array([180, 50, 255]))
#         contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#         photo_frame_box = None
#         max_area = 0
#         img_area = product_img.shape[0] * product_img.shape[1]
#         for cnt in contours:
#             area = cv2.contourArea(cnt)
#             # Skip too-small regions (e.g., less than 5% of the image area)
#             if area < 0.05 * img_area:
#                 continue
#             approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
#             if len(approx) == 4:
#                 if area > max_area:
#                     max_area = area
#                     x, y, w, h = cv2.boundingRect(approx)
#                     photo_frame_box = (x, y, x + w, y + h)

#         if photo_frame_box is not None:
#             logging.info("Photo frame detected. Using the detected blank area for overlay.")
#             px1, py1, px2, py2 = photo_frame_box
#             printing_area_width = px2 - px1
#             printing_area_height = py2 - py1
#         else:
#             # Fallback to YOLO-based product detection
#             results = model(product_img)
#             detections = results.xyxy[0].cpu().numpy()
#             if len(detections) == 0:
#                 raise RuntimeError("No object detected in product image.")
#             x1, y1, x2, y2 = map(int, sorted(detections, key=lambda x: (x[2]-x[0])*(x[3]-x[1]), reverse=True)[0][:4])
#             box_width, box_height = x2 - x1, y2 - y1
#             printing_area_width = int(box_width * 0.6)
#             px1 = x1 + (box_width - printing_area_width) // 2
#             px2 = px1 + printing_area_width
#             py1, py2 = y1, y2
#             printing_area_height = py2 - py1
#     else:
#         # For cylindrical objects, continue with the original YOLO detection.
#         results = model(product_img)
#         detections = results.xyxy[0].cpu().numpy()
#         if len(detections) == 0:
#             raise RuntimeError("No object detected in product image.")
#         x1, y1, x2, y2 = map(int, sorted(detections, key=lambda x: (x[2]-x[0])*(x[3]-x[1]), reverse=True)[0][:4])
#         box_width, box_height = x2 - x1, y2 - y1

#         # Identify the best slice using brightness for cylindrical warping
#         gray_roi = cv2.cvtColor(product_img[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY) / 255.0
#         num_slices = 10
#         slice_width = box_width // num_slices
#         brightness = [np.mean(gray_roi[:, i*slice_width:(i+1)*slice_width]) for i in range(num_slices)]
#         max_i = int(np.argmax(brightness))
#         sx1 = max_i * slice_width
#         sx2 = sx1 + slice_width
#         expand_px = int(slice_width * 0.5)
#         px1 = max(x1 + sx1 - expand_px, x1)
#         px2 = min(x1 + sx2 + expand_px, x2)
#         min_width = int(box_width * 0.6)
#         if px2 - px1 < min_width:
#             cx = (px1 + px2) // 2
#             px1 = max(cx - min_width // 2, x1)
#             px2 = min(cx + min_width // 2, x2)
#         py1, py2 = y1, y2
#         printing_area_width = px2 - px1
#         printing_area_height = py2 - py1

#     # Resize and warp design image to fit within the determined printing area.
#     # Updated to make the design image 80% of the printing area's dimensions.
#     design_width = int(printing_area_width * 1.0)
#     design_height = int(printing_area_height * 1.0)
#     # crop_x = max(0, (design_width - printing_area_width) // 2)
#     # crop_y = max(0, (design_height - printing_area_height) // 2)
#     # crop_w = min(printing_area_width, design_width)
#     # crop_h = min(printing_area_height, design_height)

#     # resized_design = design_rgb[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
#     # resized_alpha = design_alpha[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
#     resized_design = cv2.resize(design_rgb, (design_width, design_height))
#     resized_alpha = cv2.resize(design_alpha, (design_width, design_height))

#     offset_x = px1 + (printing_area_width - design_width) // 2
#     offset_y = py1 + (printing_area_height - design_height) // 2

#     def cylindrical_warp(image):
#         h, w = image.shape[:2]
#         warped = np.zeros_like(image)
#         for i in range(w):
#             offset = int(20 * np.sin(np.pi * i / w))
#             if offset == 0:
#                 warped[:, i] = image[:, i]
#             else:
#                 warped[offset:, i] = image[:h - offset, i]
#         return warped

#     if is_cylindrical:
#         resized_design = cylindrical_warp(resized_design)
#         resized_alpha = cylindrical_warp(resized_alpha)

#     # Composite the design image onto the product image using alpha blending.
#     product_img = product_img.astype(np.float32)
#     resized_design = resized_design.astype(np.float32)
#     resized_alpha = resized_alpha.astype(np.float32) / 255.0

#     for c in range(3):
#         product_img[offset_y:offset_y+design_height, offset_x:offset_x+design_width, c] = (
#             resized_alpha * resized_design[:, :, c] +
#             (1 - resized_alpha) * product_img[offset_y:offset_y+design_height, offset_x:offset_x+design_width, c]
#         )

#     final_image = np.clip(product_img, 0, 255).astype(np.uint8)
#     cv2.imwrite(output_path, final_image)

#     return output_path



def fill_photo_frame_with_design(frame_image_path, design_image_path, output_path):
    """
    Updated version of design overlay:
    - Improves mask normalization to avoid hazy overlay.
    - Uses proper contrast-preserving alpha mask.
    - Crops and warps the design image to fit the white area inside the frame.
    """

    try:
        # Load input images with alpha channel support
        frame_img = cv2.imread(frame_image_path, cv2.IMREAD_UNCHANGED)
        design_img = cv2.imread(design_image_path, cv2.IMREAD_UNCHANGED)

        if frame_img is None or design_img is None:
            raise ValueError("Could not load input images.")

        if frame_img.ndim != 3 or frame_img.shape[2] not in [3, 4]:
            raise ValueError("Invalid frame image: must have 3 (BGR) or 4 (BGRA) channels.")
        if design_img.ndim != 3 or design_img.shape[2] not in [3, 4]:
            raise ValueError("Invalid design image: must have 3 (BGR) or 4 (BGRA) channels.")

        # Split channels
        frame_bgr = frame_img[:, :, :3]
        frame_alpha = frame_img[:, :, 3] if frame_img.shape[2] == 4 else None

        # Detect white printable area via thresholding
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 195, 255, cv2.THRESH_BINARY)

        # Find largest 4-point contour
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest_contour = None
        max_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            epsilon = 0.01 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            if area > max_area and len(approx) == 4:
                largest_contour = approx
                max_area = area

        if largest_contour is None:
            print("❌ No suitable rectangular area found.")
            return False

        def order_points(pts):
            rect = np.zeros((4, 2), dtype="float32")
            s = pts.sum(axis=1)
            diff = np.diff(pts, axis=1)
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
            return rect

        fill_area_pts = order_points(largest_contour.reshape(4, 2))
        x, y, w, h = cv2.boundingRect(fill_area_pts.astype(np.int32))
        h = h - 2  # Optional: reduce printing height

        # Extract design and alpha
        design_bgr = design_img[:, :, :3]
        design_alpha = (
            design_img[:, :, 3] if design_img.shape[2] == 4
            else np.ones(design_img.shape[:2], dtype=np.uint8) * 255
        )

        # Maintain aspect ratio when resizing
        design_aspect = design_bgr.shape[0] / design_bgr.shape[1]
        if w >= h:
            target_width = w
            target_height = int(target_width * design_aspect)
            if target_height < h:
                target_height = h
                target_width = int(target_height / design_aspect)
        else:
            target_height = h
            target_width = int(target_height / design_aspect)
            if target_width < w:
                target_width = w
                target_height = int(target_width * design_aspect)

        design_resized = cv2.resize(design_bgr, (target_width, target_height))
        alpha_resized = cv2.resize(design_alpha, (target_width, target_height))

        # Center crop to match printing area
        start_x = max((target_width - w) // 2, 0)
        start_y = max((target_height - h) // 2, 0)
        cropped_design = design_resized[start_y:start_y+h, start_x:start_x+w]
        cropped_alpha = alpha_resized[start_y:start_y+h, start_x:start_x+w]

        # Warp design and alpha to fit the frame
        src_pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")
        M = cv2.getPerspectiveTransform(src_pts, fill_area_pts)

        warped_design = cv2.warpPerspective(cropped_design, M, (frame_bgr.shape[1], frame_bgr.shape[0]),
                                            borderMode=cv2.BORDER_TRANSPARENT)
        warped_alpha = cv2.warpPerspective(cropped_alpha, M, (frame_bgr.shape[1], frame_bgr.shape[0]),
                                           borderMode=cv2.BORDER_TRANSPARENT)

        # Prepare soft mask
        mask = warped_alpha.copy()
        cv2.drawContours(mask, [largest_contour], -1, 255, thickness=-1, lineType=cv2.LINE_AA)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        # Normalize alpha and enhance slightly
        alpha_mask = np.clip((mask.astype(np.float32) / 255.0) ** 0.95, 0.0, 1.0)
        alpha_mask_3ch = cv2.merge([alpha_mask] * 3)

        # Blend design with frame
        blended = alpha_mask_3ch * warped_design.astype(np.float32) + \
                  (1 - alpha_mask_3ch) * frame_bgr.astype(np.float32)
        blended = np.clip(blended, 0, 255).astype(np.uint8)

        # Restore original alpha channel if needed
        if frame_alpha is not None:
            result = cv2.merge([blended[:, :, 0], blended[:, :, 1], blended[:, :, 2], frame_alpha])
        else:
            result = blended

        cv2.imwrite(output_path, result)
        print(f"✅ Output saved at: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
        
def fill_photo_frame_with_design_using_metadata(frame_image_path, design_image_path, output_path, frame_data):
    try:
        frame_img = cv2.imread(frame_image_path, cv2.IMREAD_UNCHANGED)
        design_img = cv2.imread(design_image_path, cv2.IMREAD_UNCHANGED)

        if frame_img is None or design_img is None:
            raise ValueError("Could not load input images.")

        frame_bgr = frame_img[:, :, :3] if frame_img.shape[2] == 4 else frame_img.copy()
        design_bgr = design_img[:, :, :3]
        design_alpha = design_img[:, :, 3] if design_img.shape[2] == 4 else np.ones(design_img.shape[:2], dtype=np.uint8) * 255

        if frame_data["shape_type"] == "rectangle":
            corners = frame_data["corners"]

            if len(corners) == 2:
                # Convert diagonal points to 4 corners of rectangle
                x1, y1 = corners[0]["x"], corners[0]["y"]
                x2, y2 = corners[1]["x"], corners[1]["y"]
                corners = [
                    {"x": x1, "y": y1},  # top-left
                    {"x": x2, "y": y1},  # top-right
                    {"x": x2, "y": y2},  # bottom-right
                    {"x": x1, "y": y2},  # bottom-left
                ]
            elif len(corners) != 4:
                raise ValueError(f"Rectangle must have 4 corners. Got {len(corners)}: {corners}")

            # Source width and height from corners
            pts = np.array([[pt["x"], pt["y"]] for pt in corners], dtype="float32")
            w = int(np.linalg.norm(pts[0] - pts[1]))
            h = int(np.linalg.norm(pts[0] - pts[3]))
            fill_area_pts = pts

            # Smart resize logic (preserve design aspect ratio, ensure full coverage)
            design_h, design_w = design_bgr.shape[:2]
            design_aspect = design_h / design_w

            if w >= h:
                target_width = w
                target_height = int(target_width * design_aspect)
                if target_height < h:
                    target_height = h
                    target_width = int(target_height / design_aspect)
            else:
                target_height = h
                target_width = int(target_height / design_aspect)
                if target_width < w:
                    target_width = w
                    target_height = int(target_width * design_aspect)

            design_resized = cv2.resize(design_bgr, (target_width, target_height))
            alpha_resized = cv2.resize(design_alpha, (target_width, target_height))

            # Center crop to match the printable area (w, h)
            start_x = max((target_width - w) // 2, 0)
            start_y = max((target_height - h) // 2, 0)
            cropped_design = design_resized[start_y:start_y + h, start_x:start_x + w]
            cropped_alpha = alpha_resized[start_y:start_y + h, start_x:start_x + w]

            # Perspective warp to match the printable area
            src_pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")
            M = cv2.getPerspectiveTransform(src_pts, fill_area_pts)

            warped = cv2.warpPerspective(cropped_design, M, (frame_bgr.shape[1], frame_bgr.shape[0]),
                                         borderMode=cv2.BORDER_TRANSPARENT)
            warped_alpha = cv2.warpPerspective(cropped_alpha, M, (frame_bgr.shape[1], frame_bgr.shape[0]),
                                               borderMode=cv2.BORDER_TRANSPARENT)

            # Soft blending using alpha mask + blur
            mask = warped_alpha.copy()
            cv2.drawContours(mask, [np.int32(fill_area_pts)], -1, 240, thickness=-1, lineType=cv2.LINE_AA)
            mask = cv2.GaussianBlur(mask, (3, 3), 0)

            alpha_mask = mask.astype(np.float32) / 255.0
            alpha_mask_3ch = cv2.merge([alpha_mask] * 3)

            blended = alpha_mask_3ch * warped.astype(np.float32) + (1 - alpha_mask_3ch) * frame_bgr.astype(np.float32)
            result = np.clip(blended, 0, 255).astype(np.uint8)

        elif frame_data["shape_type"] == "circle":
            # (Unchanged logic for circle from earlier version — can also upgrade if you like)
            center_x = int(frame_data["corners"][0]["x"])
            center_y = int(frame_data["corners"][0]["y"])
            radius = int(frame_data["radius"])
            diameter = 2 * radius

            resized_design = cv2.resize(design_bgr, (diameter, diameter))
            resized_alpha = cv2.resize(design_alpha, (diameter, diameter))

            mask = np.zeros((diameter, diameter), dtype=np.float32)
            cv2.circle(mask, (radius, radius), radius, 1.0, -1)
            mask = cv2.GaussianBlur(mask, (31, 31), 0)
            mask_uint8 = (mask * 255).astype(np.uint8)

            x_start = center_x - radius
            y_start = center_y - radius
            x_end = center_x + radius
            y_end = center_y + radius

            roi = frame_bgr[y_start:y_end, x_start:x_end]
            design_roi = resized_design
            mask_roi = mask_uint8

            blended = blend_images_(roi, design_roi, mask=mask_roi, alpha=0.9)
            frame_bgr[y_start:y_end, x_start:x_end] = blended
            result = frame_bgr

        # Restore alpha if present
        if frame_img.shape[2] == 4:
            result = cv2.merge([result[:, :, 0], result[:, :, 1], result[:, :, 2], frame_img[:, :, 3]])

        cv2.imwrite(output_path, result)
        print(f"✅ Output saved at: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error: {e}")
        return False

ASSETS_ROOT_DIR = r"C:\Users\91890\Downloads\FastAPI-Ecommerce-API-main\FastAPI-Ecommerce-API-main\assets"

def resolve_asset_path(path):
    if path.startswith("/assets/"):
        return os.path.join(ASSETS_ROOT_DIR, path.replace("/assets/", "").replace("/", os.sep))
    return path

def blend_images_(background, overlay, mask=None, alpha=1.0):
    background = background.astype(np.float32)
    overlay = overlay.astype(np.float32)

    if mask is not None:
        if mask.ndim == 2:
            mask = cv2.merge([mask / 255.0] * 3)
        elif mask.ndim == 3:
            mask = mask.astype(np.float32) / 255.0
        blended = (1 - mask) * background + mask * overlay * alpha
    else:
        blended = (1 - alpha) * background + alpha * overlay

    return np.clip(blended, 0, 255).astype(np.uint8)

def center_crop_square(image):
    h, w = image.shape[:2]
    size = min(h, w)
    y = (h - size) // 2
    x = (w - size) // 2
    return image[y:y+size, x:x+size]

def create_soft_circle_mask(diameter, edge_fade=0.01):
    """
    Create a circular mask with soft edge blending.
    edge_fade defines the portion of the radius used for fading (0.05 = 5%)
    """
    radius = diameter // 2
    mask = np.zeros((diameter, diameter), dtype=np.float32)
    solid_radius = int(radius * (1 - edge_fade))

    # Inner solid circle
    cv2.circle(mask, (radius, radius), solid_radius, 1.0, -1)

    # Feathered edge
    blur_radius = radius - solid_radius
    if blur_radius > 0:
        blur_kernel = max(3, 2 * blur_radius + 1)  # odd number
        mask = cv2.GaussianBlur(mask, (blur_kernel, blur_kernel), blur_radius / 2)

    return (mask * 255).astype(np.uint8)

def overlay_multiple_designs_on_circles(
    frame_image_path,
    design_image_paths,
    output_path,
    frames_data,
    rim_inner_ratio=0.90,
    lab_effect_opacity=0.5
):
    try:
        import json
        import cv2
        import numpy as np
        import os

        # -------------------------------
        # Normalize frame data
        # -------------------------------
        if isinstance(frames_data, str):
            frames_data = json.loads(frames_data)

        normalized_frames = []
        for frame in frames_data:
            if isinstance(frame, str):
                frame = json.loads(frame)
            normalized_frames.append(frame)

        frames_data = normalized_frames

        # -------------------------------
        # Load base frame image
        # -------------------------------
        frame_img = cv2.imread(frame_image_path, cv2.IMREAD_UNCHANGED)
        if frame_img is None:
            raise ValueError("Could not load frame image")

        frame_bgr = frame_img[:, :, :3] if frame_img.shape[2] == 4 else frame_img.copy()
        original_alpha = frame_img[:, :, 3] if frame_img.shape[2] == 4 else None

        # -------------------------------
        # Utility: circle from points
        # -------------------------------
        def circle_from_points(points):
            xs = np.array([p["x"] for p in points])
            ys = np.array([p["y"] for p in points])
            cx = int(xs.mean())
            cy = int(ys.mean())
            r = int(np.mean(np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)))
            return cx, cy, r

        # -------------------------------
        # Process each plate
        # -------------------------------
        for idx, frame in enumerate(frames_data):
            if "coordinates" not in frame:
                continue

            points = frame["coordinates"].get("points", [])
            if len(points) < 10:
                continue

            center_x, center_y, radius = circle_from_points(points)
            # ✅ ADD: increase radius safely
            RADIUS_SCALE = 1.1  # tweak: 1.05–1.15
            radius = int(radius * RADIUS_SCALE)
            diameter = int(radius * 2)

            if diameter <= 0:
                continue

            # Resolve design image
            design_path = (
                design_image_paths[idx]
                if idx < len(design_image_paths)
                else design_image_paths[-1]
            )

            if not os.path.exists(design_path):
                continue

            design_img = cv2.imread(design_path, cv2.IMREAD_UNCHANGED)
            if design_img is None:
                continue

            design_bgr = design_img[:, :, :3]

            # Center-crop square
            h, w = design_bgr.shape[:2]
            side = min(h, w)
            start_x = (w - side) // 2
            start_y = (h - side) // 2
            design_bgr = design_bgr[start_y:start_y+side, start_x:start_x+side]

            resized_design = cv2.resize(design_bgr, (diameter, diameter))

            x1, y1 = center_x - radius, center_y - radius
            x2, y2 = center_x + radius, center_y + radius

            if x1 < 0 or y1 < 0 or x2 > frame_bgr.shape[1] or y2 > frame_bgr.shape[0]:
                continue

            roi = frame_bgr[y1:y2, x1:x2].astype(np.float32)

            # -------------------------------
            # Masks
            # -------------------------------
            yy, xx = np.ogrid[:diameter, :diameter]
            dist = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2)

            circle_mask = (dist <= radius).astype(np.float32)
            circle_mask = cv2.GaussianBlur(circle_mask, (0, 0), sigmaX=2)

            # Blend base
            blended = (
                resized_design.astype(np.float32) * circle_mask[:, :, None]
                + roi * (1 - circle_mask[:, :, None])
            )

            # -------------------------------
            # Rim lighting (unchanged)
            # -------------------------------
            inner_r = int(radius * rim_inner_ratio)
            rim_mask = ((dist <= radius) & (dist >= inner_r)).astype(np.float32)
            rim_mask = cv2.GaussianBlur(rim_mask, (0, 0), sigmaX=radius * 0.05)

            grad = np.linspace(1, 0, diameter)
            light_dir = (np.tile(grad, (diameter, 1)) +
                         np.tile(grad[:, None], (1, diameter))) / 2

            blended += (255 - blended) * rim_mask[:, :, None] * light_dir[:, :, None] * lab_effect_opacity
            blended *= (1 - rim_mask[:, :, None] * (1 - light_dir[:, :, None]) * lab_effect_opacity)

            frame_bgr[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)

        # -------------------------------
        # Restore alpha
        # -------------------------------
        if original_alpha is not None:
            frame_bgr = cv2.merge([
                frame_bgr[:, :, 0],
                frame_bgr[:, :, 1],
                frame_bgr[:, :, 2],
                original_alpha
            ])

        cv2.imwrite(output_path, frame_bgr)
        return output_path

    except Exception as e:
        print("❌ Error in overlay_multiple_designs_on_circles:", str(e))
        return False



def overlay_multiple_designs_on_circles1(frame_image_path, design_image_paths, output_path, frames_data,
                                        rim_inner_ratio=0.90, lab_effect_opacity=0.5):
    try:
        frame_img = cv2.imread(frame_image_path, cv2.IMREAD_UNCHANGED)
        if frame_img is None:
            raise ValueError("❌ Could not load frame image.")

        frame_bgr = frame_img[:, :, :3] if frame_img.shape[2] == 4 else frame_img.copy()
        original_alpha = frame_img[:, :, 3] if frame_img.shape[2] == 4 else None

        for idx, frame_data in enumerate(frames_data):
            if frame_data["shape_type"] != "circle":
                print(f"⏭️ Skipping non-circle frame: {frame_data['id']}")
                continue

            design_image_path = design_image_paths[idx] if idx < len(design_image_paths) else design_image_paths[-1]
            resolved_path = resolve_asset_path(design_image_path)

            if not os.path.exists(resolved_path):
                print(f"❌ Design image not found for frame {frame_data['id']}: {resolved_path}")
                continue

            design_img = cv2.imread(resolved_path, cv2.IMREAD_UNCHANGED)
            if design_img is None:
                print(f"❌ Could not load design image: {resolved_path}")
                continue

            design_bgr = design_img[:, :, :3]
            design_bgr_cropped = center_crop_square(design_bgr)

            center_x = int(frame_data["corners"][0]["x"])
            center_y = int(frame_data["corners"][0]["y"])
            radius = int(frame_data["radius"])
            diameter = 2 * radius

            resized_design = cv2.resize(design_bgr_cropped, (diameter, diameter))

            x_start = center_x - radius
            y_start = center_y - radius
            x_end = center_x + radius
            y_end = center_y + radius

            if x_start < 0 or y_start < 0 or x_end > frame_bgr.shape[1] or y_end > frame_bgr.shape[0]:
                print(f"⚠️ Skipping frame {frame_data['id']} — circle exceeds image bounds.")
                continue

            # Step 1: Circular mask
            # circle_mask = np.zeros((diameter, diameter), dtype=np.uint8)
            # cv2.circle(circle_mask, (radius, radius), radius, 255, -1)
            circle_mask = create_soft_circle_mask(diameter)

            # Step 2: Blend design into frame within the circle
            roi = frame_bgr[y_start:y_end, x_start:x_end]
            blended_design = blend_images_(roi, resized_design, circle_mask, alpha=1.0)

            # Step 3: Rim mask
            rim_mask = np.zeros((diameter, diameter), dtype=np.float32)
            outer_radius = radius
            inner_radius = int(radius * rim_inner_ratio)

            cv2.circle(rim_mask, (radius, radius), outer_radius, 1.0, -1)
            cv2.circle(rim_mask, (radius, radius), inner_radius, 0.0, -1)
            rim_mask = cv2.GaussianBlur(rim_mask, (0, 0), sigmaX=(outer_radius - inner_radius) * 0.5)

            # Step 4: Directional lighting mask (simulate top-left light)
            gradient = np.linspace(1.0, 0.0, diameter)
            x_grad = np.tile(gradient, (diameter, 1))
            y_grad = np.tile(gradient[:, None], (1, diameter))
            directional_light = (x_grad + y_grad) / 2.0

            # Step 5: Light & shadow masks
            light_mask = rim_mask * directional_light
            shadow_mask = rim_mask * (1.0 - directional_light)

            blended_design = blended_design.astype(np.float32)

            # ✅ Step 5.1: Very thin shiny highlight on top-left
            shiny_rim_mask = np.zeros((diameter, diameter), dtype=np.float32)
            highlight_inner = inner_radius
            highlight_outer = highlight_inner + 1  # very thin

            cv2.circle(shiny_rim_mask, (radius, radius), highlight_outer, 1.0, -1)
            cv2.circle(shiny_rim_mask, (radius, radius), highlight_inner, 0.0, -1)

            top_left_mask = np.zeros((diameter, diameter), dtype=np.float32)
            cv2.ellipse(top_left_mask, (radius, radius), (radius, radius), 0, 180, 270, 1.0, -1)
            shiny_rim_mask *= top_left_mask
            shiny_rim_mask *= directional_light
            shiny_rim_mask = cv2.GaussianBlur(shiny_rim_mask, (3, 3), sigmaX=0.8)

            shiny_highlight = np.full((diameter, diameter, 3), 255, dtype=np.float32)
            blended_design += (shiny_highlight - blended_design) * shiny_rim_mask[:, :, None] * 0.5

            # ✅ Step 5.2: Very thin shadow on bottom-right
            shadow_rim_mask = np.zeros((diameter, diameter), dtype=np.float32)
            shadow_inner = inner_radius
            shadow_outer = shadow_inner + 1

            cv2.circle(shadow_rim_mask, (radius, radius), shadow_outer, 1.0, -1)
            cv2.circle(shadow_rim_mask, (radius, radius), shadow_inner, 0.0, -1)

            bottom_right_mask = np.zeros((diameter, diameter), dtype=np.float32)
            cv2.ellipse(bottom_right_mask, (radius, radius), (radius, radius), 0, 0, 90, 1.0, -1)
            shadow_rim_mask *= bottom_right_mask
            shadow_rim_mask *= (1.0 - directional_light)
            shadow_rim_mask = cv2.GaussianBlur(shadow_rim_mask, (3, 3), sigmaX=0.8)

            blended_design *= (1.0 - shadow_rim_mask[:, :, None] * 0.5)

            # Step 6: Apply rim light & shadow masks
            shaded = blended_design.copy()
            shaded += (255 - shaded) * light_mask[:, :, None] * lab_effect_opacity
            shaded *= (1.0 - shadow_mask[:, :, None] * lab_effect_opacity)

            # Step 7: Mask final shaded result with circular area
            circle_mask_float = circle_mask.astype(np.float32) / 255.0
            shaded = shaded * circle_mask_float[:, :, None] + roi.astype(np.float32) * (1.0 - circle_mask_float[:, :, None])
            blended_final = np.clip(shaded, 0, 255).astype(np.uint8)

            # Step 8: Paste into original frame
            frame_bgr[y_start:y_end, x_start:x_end] = blended_final

        # Final alpha merge if original had transparency
        result = frame_bgr
        if original_alpha is not None:
            result = cv2.merge([result[:, :, 0], result[:, :, 1], result[:, :, 2], original_alpha])

        cv2.imwrite(output_path, result)
        print(f"✅ Output saved at: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Error in overlay_multiple_designs_on_circles: {e}")
        return False

# def blend_images(background, overlay, mask=None, alpha=1.0):
#     background = background.astype(np.float32)
#     overlay = overlay.astype(np.float32)

#     if mask is not None:
#         if mask.ndim == 2:
#             mask = cv2.merge([mask / 255.0] * 3)
#         elif mask.ndim == 3:
#             mask = mask.astype(np.float32) / 255.0
#         blended = (1 - mask) * background + mask * overlay * alpha
#     else:
#         blended = (1 - alpha) * background + alpha * overlay

#     return np.clip(blended, 0, 255).astype(np.uint8)

# def center_crop_square(image):
#     h, w = image.shape[:2]
#     size = min(h, w)
#     y = (h - size) // 2
#     x = (w - size) // 2
#     return image[y:y+size, x:x+size]

# def create_soft_circle_mask(diameter, edge_fade=0.05):
#     """
#     Create a circular mask with soft edge blending.
#     edge_fade defines the portion of the radius used for fading (0.05 = 5%)
#     """
#     radius = diameter // 2
#     mask = np.zeros((diameter, diameter), dtype=np.float32)
#     solid_radius = int(radius * (1 - edge_fade))

#     # Inner solid circle
#     cv2.circle(mask, (radius, radius), solid_radius, 1.0, -1)

#     # Feathered edge
#     blur_radius = radius - solid_radius
#     if blur_radius > 0:
#         blur_kernel = max(3, 2 * blur_radius + 1)  # odd number
#         mask = cv2.GaussianBlur(mask, (blur_kernel, blur_kernel), blur_radius / 2)

#     return (mask * 255).astype(np.uint8)

# def overlay_multiple_designs_on_circles(frame_image_path, design_image_paths, output_path, frames_data):
#     try:
#         frame_img = cv2.imread(frame_image_path, cv2.IMREAD_UNCHANGED)
#         if frame_img is None:
#             raise ValueError("❌ Could not load frame image.")

#         frame_bgr = frame_img[:, :, :3] if frame_img.shape[2] == 4 else frame_img.copy()
#         original_alpha = frame_img[:, :, 3] if frame_img.shape[2] == 4 else None

#         for idx, frame_data in enumerate(frames_data):
#             if frame_data["shape_type"] != "circle":
#                 print(f"⏭️ Skipping non-circle frame: {frame_data['id']}")
#                 continue

#             design_image_path = design_image_paths[idx] if idx < len(design_image_paths) else design_image_paths[-1]
#             resolved_path = resolve_asset_path(design_image_path)
#             print(f"🔍 Frame {frame_data['id']} — design path: {design_image_path} → resolved: {resolved_path}")

#             if not os.path.exists(resolved_path):
#                 print(f"❌ Design image not found for frame {frame_data['id']}: {resolved_path}")
#                 continue

#             design_img = cv2.imread(resolved_path, cv2.IMREAD_UNCHANGED)
#             if design_img is None:
#                 print(f"❌ Could not load design image: {resolved_path}")
#                 continue

#             design_bgr = design_img[:, :, :3]
#             design_alpha = design_img[:, :, 3] if design_img.shape[2] == 4 else np.ones(design_img.shape[:2], dtype=np.uint8) * 255

#             design_bgr_cropped = center_crop_square(design_bgr)

#             center_x = int(frame_data["corners"][0]["x"])
#             center_y = int(frame_data["corners"][0]["y"])
#             radius = int(frame_data["radius"])
#             diameter = 2 * radius

#             resized_design = cv2.resize(design_bgr_cropped, (diameter, diameter))

#             # Soft edge circular mask (only feathering on edge)
#             mask_uint8 = create_soft_circle_mask(diameter, edge_fade=0.0)

#             x_start = center_x - radius
#             y_start = center_y - radius
#             x_end = center_x + radius
#             y_end = center_y + radius

#             if x_start < 0 or y_start < 0 or x_end > frame_bgr.shape[1] or y_end > frame_bgr.shape[0]:
#                 print(f"⚠️ Skipping frame {frame_data['id']} — circle exceeds image bounds.")
#                 continue

#             roi = frame_bgr[y_start:y_end, x_start:x_end]
#             blended = blend_images(roi, resized_design, mask=mask_uint8, alpha=1.0)
#             frame_bgr[y_start:y_end, x_start:x_end] = blended

#         result = frame_bgr
#         if original_alpha is not None:
#             result = cv2.merge([result[:, :, 0], result[:, :, 1], result[:, :, 2], original_alpha])

#         cv2.imwrite(output_path, result)
#         print(f"✅ Output saved at: {output_path}")
#         return output_path

#     except Exception as e:
#         print(f"❌ Error in overlay_multiple_designs_on_circles: {e}")
#         return False
def overlay_design_on_plates(
    frame_image_path: str,
    design_image_paths: list,   # list of 3 design images
    frame_data: dict,           # parsed JSON (not string)
    output_path: str
):
    """
    Overlay multiple designs on plates defined by frame data polygons.
    """

    frame_img = cv2.imread(frame_image_path, cv2.IMREAD_COLOR)
    if frame_img is None:
        raise ValueError("Frame image not found")

    h, w = frame_img.shape[:2]

    frames = json.loads(frame_data["frames"])

    if len(frames) != len(design_image_paths):
        raise ValueError("Number of designs must match number of plates")

    for idx, frame in enumerate(frames):
        points = frame["coordinates"]["points"]

        # Convert points to numpy array
        polygon = np.array(
            [[int(p["x"]), int(p["y"])] for p in points],
            dtype=np.int32
        )

        # Create mask
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask, [polygon], 255)

        # Bounding box of polygon
        x, y, bw, bh = cv2.boundingRect(polygon)

        # Load design image
        design_img = cv2.imread(design_image_paths[idx], cv2.IMREAD_UNCHANGED)
        if design_img is None:
            raise ValueError(f"Design image not found: {design_image_paths[idx]}")

        # Resize design to bounding box
        design_resized = cv2.resize(design_img, (bw, bh), interpolation=cv2.INTER_LINEAR)

        # Extract alpha
        if design_resized.shape[2] == 4:
            design_rgb = design_resized[:, :, :3].astype(np.float32)
            alpha = design_resized[:, :, 3].astype(np.float32) / 255.0
        else:
            design_rgb = design_resized.astype(np.float32)
            alpha = np.ones((bh, bw), dtype=np.float32)

        # Apply global opacity
        opacity = float(frame_data.get("designOpacity", 1))
        alpha *= opacity

        # ROI
        roi = frame_img[y:y+bh, x:x+bw].astype(np.float32)

        # Mask crop
        mask_crop = mask[y:y+bh, x:x+bw] / 255.0

        # Combine alpha with polygon mask
        final_alpha = alpha * mask_crop

        # Alpha blend
        blended = (
            design_rgb * final_alpha[..., None] +
            roi * (1 - final_alpha[..., None])
        )

        frame_img[y:y+bh, x:x+bw] = np.clip(blended, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, frame_img)
    return output_path

def overlay_design_on_plates1(frame_image_path, design_image_path, output_path):
    """
    Detects white circular plates in an image and overlays a design on each plate with reduced brightness.
    """
    try:
        # Load images
        frame_img = cv2.imread(frame_image_path, cv2.IMREAD_UNCHANGED)
        design_img = cv2.imread(design_image_path, cv2.IMREAD_UNCHANGED)

        if frame_img is None or design_img is None:
            raise ValueError("Could not load input images.")

        frame_bgr = frame_img[:, :, :3] if frame_img.shape[2] == 4 else frame_img
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # Detect circles (plates)
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=100,
                                   param1=80, param2=40, minRadius=80, maxRadius=frame_bgr.shape[0] // 3)

        if circles is None:
            raise ValueError("No plates detected in the image.")

        circles = np.round(circles[0, :]).astype("int")  # Convert to integer values

        def adjust_brightness(image, factor=0.5):
            """Reduces brightness of the overlayed design."""
            return np.clip(image * factor, 0, 255).astype(np.uint8)

        def overlay_design_on_plate(center_x, center_y, radius):
            diameter = 2 * radius
            left, right = max(center_x - radius, 0), min(center_x + radius, frame_bgr.shape[1])
            top, bottom = max(center_y - radius, 0), min(center_y + radius, frame_bgr.shape[0])

            roi_w, roi_h = right - left, bottom - top
            diameter = min(roi_w, roi_h)

            # Resize and prepare design
            design_resized = cv2.resize(design_img, (diameter, diameter), interpolation=cv2.INTER_LINEAR)

            if design_resized.shape[2] == 4:
                design_rgb = design_resized[:, :, :3].astype(np.float32)
                design_alpha = design_resized[:, :, 3] / 255.0
            else:
                design_rgb = design_resized.astype(np.float32)
                design_alpha = np.ones((diameter, diameter), dtype=np.float32)

            # Get region of interest from frame
            roi = frame_bgr[top:bottom, left:right].astype(np.float32)

            # Direct alpha blending (no circular mask)
            final_alpha = design_alpha  # Use design's own alpha only

            overlay = design_rgb * final_alpha[..., None] + roi * (1 - final_alpha[..., None])
            blended = np.clip(overlay, 0, 255).astype(np.uint8)

            frame_bgr[top:bottom, left:right] = blended

        # Apply overlay on all detected plates
        for (x, y, r) in circles:
            overlay_design_on_plate(x, y, r)

        cv2.imwrite(output_path, frame_bgr)
        return output_path

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def fill_photo_frame_with_split_design_using_metadata(
    frame_image_path,
    design_image_path,
    output_path,
    frames_data
):
    try:
        frame_img = cv2.imread(frame_image_path, cv2.IMREAD_UNCHANGED)
        design_img = cv2.imread(design_image_path, cv2.IMREAD_UNCHANGED)

        if frame_img is None or design_img is None:
            raise ValueError("Could not load input images.")

        frame_bgr = frame_img[:, :, :3] if frame_img.shape[2] == 4 else frame_img.copy()
        frame_h, frame_w = frame_bgr.shape[:2]

        design_bgr = design_img[:, :, :3]
        design_alpha = (
            design_img[:, :, 3]
            if design_img.shape[2] == 4
            else np.ones(design_img.shape[:2], dtype=np.uint8) * 255
        )

        design_h, design_w = design_bgr.shape[:2]

        # ------------------------------
        # Step 1: Calculate frame widths
        # ------------------------------
        frame_widths = []

        for frame_data in frames_data:
            corners = frame_data.get("corners", [])

            if len(corners) == 2:
                x1, y1 = corners[0]["x"], corners[0]["y"]
                x2, y2 = corners[1]["x"], corners[1]["y"]
                corners = [
                    {"x": x1, "y": y1},
                    {"x": x2, "y": y1},
                    {"x": x2, "y": y2},
                    {"x": x1, "y": y2},
                ]

            if len(corners) != 4:
                frame_widths.append(0)
                continue

            width = np.linalg.norm(
                np.array([corners[0]["x"], corners[0]["y"]]) -
                np.array([corners[1]["x"], corners[1]["y"]])
            )
            frame_widths.append(width)

        total_width = sum(frame_widths)
        if total_width == 0:
            raise ValueError("Invalid frame widths: total width is zero.")

        split_ratios = [w / total_width for w in frame_widths]
        current_x = 0

        # ------------------------------
        # Step 2: Overlay each split
        # ------------------------------
        for i, frame_data in enumerate(frames_data):
            if frame_data.get("shape_type") != "rectangle":
                continue

            corners = frame_data.get("corners", [])
            if len(corners) == 2:
                x1, y1 = corners[0]["x"], corners[0]["y"]
                x2, y2 = corners[1]["x"], corners[1]["y"]
                corners = [
                    {"x": x1, "y": y1},
                    {"x": x2, "y": y1},
                    {"x": x2, "y": y2},
                    {"x": x1, "y": y2},
                ]

            if len(corners) != 4 or split_ratios[i] == 0:
                continue

            dst_pts = np.array([[p["x"], p["y"]] for p in corners], dtype="float32")

            width_top = np.linalg.norm(dst_pts[0] - dst_pts[1])
            width_bottom = np.linalg.norm(dst_pts[3] - dst_pts[2])
            height_left = np.linalg.norm(dst_pts[0] - dst_pts[3])
            height_right = np.linalg.norm(dst_pts[1] - dst_pts[2])

            w = int(max(width_top, width_bottom))
            h = int(max(height_left, height_right))

            if w == 0 or h == 0:
                continue

            slice_width = int(split_ratios[i] * design_w)
            end_x = min(current_x + slice_width, design_w)

            if end_x <= current_x:
                continue

            design_part = design_bgr[:, current_x:end_x]
            alpha_part = design_alpha[:, current_x:end_x]
            current_x = end_x

            part_h, part_w = design_part.shape[:2]
            aspect = part_h / part_w

            if w >= h:
                target_w = w
                target_h = int(target_w * aspect)
                if target_h < h:
                    target_h = h
                    target_w = int(target_h / aspect)
            else:
                target_h = h
                target_w = int(target_h / aspect)
                if target_w < w:
                    target_w = w
                    target_h = int(target_w * aspect)

            design_resized = cv2.resize(design_part, (target_w, target_h))
            alpha_resized = cv2.resize(alpha_part, (target_w, target_h))

            x_crop = max((target_w - w) // 2, 0)
            y_crop = max((target_h - h) // 2, 0)

            cropped_design = design_resized[y_crop:y_crop + h, x_crop:x_crop + w]
            cropped_alpha = alpha_resized[y_crop:y_crop + h, x_crop:x_crop + w]

            src_pts = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype="float32")
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)

            warped_design = cv2.warpPerspective(cropped_design, M, (frame_w, frame_h))
            warped_alpha = cv2.warpPerspective(cropped_alpha, M, (frame_w, frame_h))

            alpha_mask = (warped_alpha.astype(np.float32) / 255.0)
            alpha_mask_3ch = cv2.merge([alpha_mask] * 3)

            frame_bgr = (
                alpha_mask_3ch * warped_design +
                (1 - alpha_mask_3ch) * frame_bgr
            ).astype(np.uint8)

        if frame_img.shape[2] == 4:
            result = cv2.merge([frame_bgr, frame_img[:, :, 3]])
        else:
            result = frame_bgr

        cv2.imwrite(output_path, result)
        return output_path

    except Exception as e:
        print(f"❌ Error: {e}")
        return False



def fill_photo_frame_with_split_design_using_metadata_bkp(frame_image_path, design_image_path, output_path, frames_data):
    try:
        frame_img = cv2.imread(frame_image_path, cv2.IMREAD_UNCHANGED)
        design_img = cv2.imread(design_image_path, cv2.IMREAD_UNCHANGED)

        if frame_img is None or design_img is None:
            raise ValueError("Could not load input images.")

        frame_bgr = frame_img[:, :, :3] if frame_img.shape[2] == 4 else frame_img.copy()
        frame_h, frame_w = frame_bgr.shape[:2]

        design_bgr = design_img[:, :, :3]
        design_alpha = (
            design_img[:, :, 3] if design_img.shape[2] == 4
            else np.ones(design_img.shape[:2], dtype=np.uint8) * 255
        )

        design_h, design_w = design_bgr.shape[:2]

        # Step 1: Calculate proportional widths
        frame_widths = []
        for frame_data in frames_data:
            corners = frame_data["corners"]
            if len(corners) == 2:
                x1, y1 = corners[0]["x"], corners[0]["y"]
                x2, y2 = corners[1]["x"], corners[1]["y"]
                corners = [
                    {"x": x1, "y": y1},
                    {"x": x2, "y": y1},
                    {"x": x2, "y": y2},
                    {"x": x1, "y": y2},
                ]
            if len(corners) != 4:
                frame_widths.append(0)
                continue
            width = np.linalg.norm(np.array([corners[0]["x"], corners[0]["y"]]) - np.array([corners[1]["x"], corners[1]["y"]]))
            frame_widths.append(width)

        total_width = sum(frame_widths)
        split_ratios = [w / total_width for w in frame_widths]

        current_x = 0  # starting slice from design image

        # Step 2: Overlay designs
        for i, frame_data in enumerate(frames_data):
            if frame_data["shape_type"] != "rectangle":
                print(f"Skipping non-rectangle shape at index {i}")
                continue

            corners = frame_data["corners"]
            if len(corners) == 2:
                x1, y1 = corners[0]["x"], corners[0]["y"]
                x2, y2 = corners[1]["x"], corners[1]["y"]
                corners = [
                    {"x": x1, "y": y1},
                    {"x": x2, "y": y1},
                    {"x": x2, "y": y2},
                    {"x": x1, "y": y2},
                ]
            if len(corners) != 4:
                continue

            dst_pts = np.array([[pt["x"], pt["y"]] for pt in corners], dtype="float32")

            width_top = np.linalg.norm(dst_pts[0] - dst_pts[1])
            width_bottom = np.linalg.norm(dst_pts[3] - dst_pts[2])
            height_left = np.linalg.norm(dst_pts[0] - dst_pts[3])
            height_right = np.linalg.norm(dst_pts[1] - dst_pts[2])
            w = int(max(width_top, width_bottom))
            h = int(max(height_left, height_right))

            if w == 0 or h == 0 or split_ratios[i] == 0:
                print(f"Skipping frame {i} due to invalid size or ratio.")
                continue

            slice_width = int(split_ratios[i] * design_w)
            end_x = min(current_x + slice_width, design_w)

            design_part = design_bgr[:, current_x:end_x]
            alpha_part = design_alpha[:, current_x:end_x]
            current_x = end_x

            # Resize to frame size
            resized_design = cv2.resize(design_part, (w, h))
            resized_alpha = cv2.resize(alpha_part, (w, h))

            # Warp to polygon
            src_pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)

            warped_design = cv2.warpPerspective(resized_design, M, (frame_w, frame_h))
            warped_alpha = cv2.warpPerspective(resized_alpha, M, (frame_w, frame_h))

            # Blend
            warped_alpha = cv2.GaussianBlur(warped_alpha, (3, 3), 0)
            alpha_mask = warped_alpha.astype(np.float32) / 255.0
            alpha_mask_3ch = cv2.merge([alpha_mask] * 3)

            frame_bgr = frame_bgr.astype(np.float32)
            warped_design = warped_design.astype(np.float32)
            blended = alpha_mask_3ch * warped_design + (1 - alpha_mask_3ch) * frame_bgr
            frame_bgr = np.clip(blended, 0, 255).astype(np.uint8)

        # Final merge
        if frame_img.shape[2] == 4:
            result = cv2.merge([frame_bgr[:, :, 0], frame_bgr[:, :, 1], frame_bgr[:, :, 2], frame_img[:, :, 3]])
        else:
            result = frame_bgr

        cv2.imwrite(output_path, result)
        print(f"✅ Output saved at: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
def overlay_design_on_rounded_clock(
    frame_image_path,
    design_image_path,
    clock_overlay_path,
    output_path,
    frame_block
):
    try:
        # ---------- Load base image ----------
        frame_img = cv2.imread(frame_image_path, cv2.IMREAD_UNCHANGED)
        if frame_img is None:
            raise ValueError("Could not load base frame image")

        frame_bgr = frame_img[:, :, :3].astype(np.float32)
        original_alpha = frame_img[:, :, 3] if frame_img.shape[2] == 4 else None
        h_img, w_img = frame_bgr.shape[:2]

        # ---------- Load design ----------
        design_img = cv2.imread(design_image_path, cv2.IMREAD_COLOR)
        if design_img is None:
            raise ValueError("Could not load design image")

        rotation_angle = float(frame_block.get("rotationAngle", 0))
        if rotation_angle != 0:
            center = (design_img.shape[1] // 2, design_img.shape[0] // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
            design_img = cv2.warpAffine(
                design_img, M_rot, (design_img.shape[1], design_img.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT
            )

        # ---------- Load clock overlay ----------
        overlay_img = cv2.imread(clock_overlay_path, cv2.IMREAD_UNCHANGED)

        design_opacity = float(frame_block.get("designOpacity", 1.0))
        raw_frames = frame_block.get("frames", [])
        if isinstance(raw_frames, str):
            raw_frames = json.loads(raw_frames)

        # ---------- Process each polygon frame ----------
        for frame_data in raw_frames:
            points = frame_data.get("coordinates", {}).get("points", [])
            if not points:
                continue

            poly_pts = np.array([[p["x"], p["y"]] for p in points], dtype=np.int32)

            # ---------- Bounding rectangle ----------
            x, y, w, h = cv2.boundingRect(poly_pts)
            if w <= 0 or h <= 0:
                continue

            # Resize design to bounding rectangle
            design_resized = cv2.resize(design_img, (w, h)).astype(np.float32)

            # Polygon mask inside bounding box
            mask = np.zeros((h, w), dtype=np.float32)
            poly_pts_shifted = poly_pts - np.array([x, y])
            cv2.fillPoly(mask, [poly_pts_shifted], 1.0)
            mask = mask * design_opacity

            # Blend the design into the polygon area
            roi = frame_bgr[y:y + h, x:x + w]
            for c in range(3):
                roi[:, :, c] = roi[:, :, c] * (1 - mask) + design_resized[:, :, c] * mask
            frame_bgr[y:y + h, x:x + w] = roi

            # ---------- Overlay clock ring ----------
            if overlay_img is not None:
                ring_resized = cv2.resize(overlay_img, (w, h))
                if ring_resized.shape[2] == 4:
                    alpha = ring_resized[:, :, 3] / 255.0
                    for c in range(3):
                        frame_bgr[y:y + h, x:x + w, c] = (
                            frame_bgr[y:y + h, x:x + w, c] * (1 - alpha) +
                            ring_resized[:, :, c] * alpha
                        )

        # ---------- Restore alpha ----------
        if original_alpha is not None:
            frame_bgr = cv2.merge([
                frame_bgr[:, :, 0].astype(np.uint8),
                frame_bgr[:, :, 1].astype(np.uint8),
                frame_bgr[:, :, 2].astype(np.uint8),
                original_alpha
            ])
        else:
            frame_bgr = frame_bgr.astype(np.uint8)

        cv2.imwrite(output_path, frame_bgr)
        return output_path

    except Exception as e:
        print(f"Rounded clock overlay error: {e}")
        return None

def overlay_design_on_rounded_clock1(frame_image_path, design_image_path, clock_overlay_path, output_path, frames):
    try:
        frame_img = cv2.imread(frame_image_path, cv2.IMREAD_UNCHANGED)
        if frame_img is None:
            raise ValueError("❌ Could not load base frame image.")

        frame_bgr = frame_img[:, :, :3] if frame_img.shape[2] == 4 else frame_img.copy()
        original_alpha = frame_img[:, :, 3] if frame_img.shape[2] == 4 else None

        # === Load and prepare design image ===
        resolved_design_path = resolve_asset_path(design_image_path)
        design_img = cv2.imread(resolved_design_path, cv2.IMREAD_UNCHANGED)
        if design_img is None:
            raise ValueError(f"❌ Could not load design image: {resolved_design_path}")
        design_bgr = design_img[:, :, :3]
        design_bgr_cropped = center_crop_square(design_bgr)

        # === Load clock overlay image ===
        resolved_overlay_path = resolve_asset_path(clock_overlay_path)
        overlay_img = cv2.imread(resolved_overlay_path, cv2.IMREAD_UNCHANGED)
        if overlay_img is None:
            raise ValueError(f"❌ Could not load overlay clock image: {resolved_overlay_path}")

        for frame_data in frames:
            corners = frame_data["corners"]
            if isinstance(corners, dict):
                center_x = int(corners["x"])
                center_y = int(corners["y"])
            elif isinstance(corners, list) and len(corners) > 0 and isinstance(corners[0], dict):
                center_x = int(corners[0]["x"])
                center_y = int(corners[0]["y"])
            else:
                print("⚠️ Skipping frame — Invalid 'corners' format.")
                continue

            radius = int(frame_data["radius"])
            diameter = 2 * radius

            # Resize design and clock overlay
            resized_design = cv2.resize(design_bgr_cropped, (diameter, diameter))
            resized_overlay = cv2.resize(overlay_img, (diameter, diameter))

            # Create circular mask
            mask = np.zeros((diameter, diameter), dtype=np.uint8)
            cv2.circle(mask, (radius, radius), radius, 255, -1)

            # Coordinates
            x_start = center_x - radius
            y_start = center_y - radius
            x_end = center_x + radius
            y_end = center_y + radius

            if x_start < 0 or y_start < 0 or x_end > frame_bgr.shape[1] or y_end > frame_bgr.shape[0]:
                print("⚠️ Skipping frame — exceeds image bounds.")
                continue

            # === Blend design inside circular area ===
            roi = frame_bgr[y_start:y_end, x_start:x_end]
            blended_design = blend_images_(roi, resized_design, mask=mask, alpha=1.0)
            frame_bgr[y_start:y_end, x_start:x_end] = blended_design

            # === Blend overlay inside circular area ===
            if resized_overlay.shape[2] == 4:
                overlay_bgr = resized_overlay[:, :, :3]
                overlay_alpha = resized_overlay[:, :, 3] / 255.0
                roi = frame_bgr[y_start:y_end, x_start:x_end]
                for c in range(3):
                    roi[:, :, c] = (1 - overlay_alpha) * roi[:, :, c] + overlay_alpha * overlay_bgr[:, :, c]
                frame_bgr[y_start:y_end, x_start:x_end] = roi
            else:
                print("⚠️ Overlay image has no alpha channel — skipping overlay.")

        # === Restore alpha channel if present ===
        result = frame_bgr
        if original_alpha is not None:
            result = cv2.merge([result[:, :, 0], result[:, :, 1], result[:, :, 2], original_alpha])

        cv2.imwrite(output_path, result)
        print(f"✅ Rounded clock image saved at: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Error in overlay_design_on_rounded_clock: {e}")
        return None

def overlay_design_on_multiple_canvases(room_image_path, design_image_path, output_path):
    """
    Overlays a design image split into multiple sections onto detected canvases in a room image.
    The design image is resized to match the total canvas size while maintaining aspect ratio.

    Parameters:
    - room_image_path: Path to the input image containing blank canvases.
    - design_image_path: Path to the design image to be split and overlaid.
    - output_path: Path to save the final image with the design applied.

    Returns:
    - Output image path if successful, otherwise False.
    """
    try:
        # Load images
        room_img = cv2.imread(room_image_path, cv2.IMREAD_UNCHANGED)
        design_img = cv2.imread(design_image_path, cv2.IMREAD_UNCHANGED)

        if room_img is None or design_img is None:
            raise ValueError("Could not load input images.")

        # Convert to grayscale and apply threshold to detect black canvases
        gray = cv2.cvtColor(room_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

        # Find contours of the canvases
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        canvas_contours = []

        for cnt in contours:
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            if len(approx) == 4:  # Ensure it's a quadrilateral
                canvas_contours.append(approx)

        # Debugging: Draw detected contours for verification
        debug_img = room_img.copy()
        cv2.drawContours(debug_img, canvas_contours, -1, (0, 0, 255), 3)  # Red contours
        cv2.imwrite("debug_canvases.jpg", debug_img)
        print("Saved debug image as 'debug_canvases.jpg' to check detected canvases.")

        # Ensure exactly 3 canvases are detected
        if len(canvas_contours) != 3:
            raise ValueError(f"Expected 3 canvases, but found {len(canvas_contours)}.")

        # Sort contours from left to right using bounding box x-coordinates
        canvas_contours = sorted(canvas_contours, key=lambda c: cv2.boundingRect(c)[0])

        # Determine total canvas size
        canvas_width = sum([cv2.boundingRect(c)[2] for c in canvas_contours])
        canvas_height = max([cv2.boundingRect(c)[3] for c in canvas_contours])

        # Resize the design image while maintaining aspect ratio
        design_h, design_w, _ = design_img.shape
        scale_factor = min(canvas_width / design_w, canvas_height / design_h)
        new_w = int(design_w * scale_factor)
        new_h = int(design_h * scale_factor)
        resized_design = cv2.resize(design_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Crop the resized design image to exactly match the total canvas size
        start_x = max((new_w - canvas_width) // 2, 0)
        start_y = max((new_h - canvas_height) // 2, 0)
        cropped_design = resized_design[start_y:start_y + canvas_height, start_x:start_x + canvas_width]

        # Split the cropped design image into 3 equal vertical sections
        section_width = cropped_design.shape[1] // 3
        design_sections = [cropped_design[:, i * section_width:(i + 1) * section_width] for i in range(3)]

        # Overlay each section onto detected canvases
        result = room_img.copy()
        for i in range(3):  # Ensure exactly 3 iterations
            x, y, w, h = cv2.boundingRect(canvas_contours[i])
            src_pts = np.array([[0, 0], [section_width - 1, 0], [section_width - 1, h - 1], [0, h - 1]], dtype=np.float32)
            dst_pts = np.array([pt[0] for pt in canvas_contours[i]], dtype=np.float32)

            # Compute transformation matrix
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)

            # Warp design section to fit the canvas
            warped = cv2.warpPerspective(design_sections[i], M, (result.shape[1], result.shape[0]))

            # Create mask and blend onto the original image
            mask = np.zeros_like(result, dtype=np.uint8)
            cv2.fillPoly(mask, [canvas_contours[i]], (255, 255, 255))
            result = np.where(mask == (255, 255, 255), warped, result)

        # Save and return the output path
        cv2.imwrite(output_path, result)
        return output_path

    except Exception as e:
        print(f"Error: {str(e)}")
        return False



#.........cofee_mug_overlay...................


def pil_to_cv2(pil_image):
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)

def cv2_to_pil(cv2_image):
    return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGRA2RGBA))

# --- Core Image Processing Functions from your app ---

def apply_cylindrical_warp(image, strength):
    if strength == 0:
        return image
    pil_image = cv2_to_pil(image)
    width, height = pil_image.size
    warped_image = Image.new('RGBA', (width, height))
    for y in range(height):
        for x in range(width):
            nx = (2 * x / width) - 1
            ny = (2 * y / height) - 1
            theta = nx * (np.pi / 2)
            h_factor = np.cos(theta)
            if abs(h_factor) < 1e-6: continue
            new_x = int((nx / h_factor + 1) * width / 2)
            if 0 <= new_x < width:
                pixel = pil_image.getpixel((new_x, y))
                warped_image.putpixel((x, y), pixel)
    return pil_to_cv2(warped_image)

def create_combined_mask(mask_shape, frames_data):
    if not frames_data:
        return None
    combined_mask = Image.new('L', mask_shape, 0)
    positive_shapes = [s for s in frames_data if not s.get('isNegative')]
    negative_shapes = [s for s in frames_data if s.get('isNegative')]
    if positive_shapes:
        positive_mask = Image.new('L', mask_shape, 0)
        draw_positive = ImageDraw.Draw(positive_mask)
        for shape_data in positive_shapes:
            if shape_data.get('is_closed'):
                draw_shape(draw_positive, shape_data, fill=255)
        combined_mask = positive_mask
    else:
        combined_mask = Image.new('L', mask_shape, 255)
    if negative_shapes:
        negative_mask = Image.new('L', mask_shape, 0)
        draw_negative = ImageDraw.Draw(negative_mask)
        for shape_data in negative_shapes:
            if shape_data.get('is_closed'):
                draw_shape(draw_negative, shape_data, fill=255)
        combined_mask = Image.fromarray(np.clip(np.array(combined_mask) - np.array(negative_mask), 0, 255).astype(np.uint8))
    return combined_mask

def draw_shape(draw_context, shape_data, fill):
    coords = shape_data.get('coordinates', {})
    points = coords.get('points', [])
    if len(points) < 2: return
    path = []
    for p in points:
        path.append((p['x'], p['y']))
    if len(path) > 2:
        draw_context.polygon(path, fill=fill, outline=fill)

def blend_images_numpy(base, design, mode, opacity):
    base_np = np.array(base.convert('RGBA'), dtype=float) / 255.0
    design_np = np.array(design.convert('RGBA'), dtype=float) / 255.0
    epsilon = 1e-6
    design_alpha = design_np[..., 3] * opacity
    base_rgb = base_np[..., :3]
    design_rgb = design_np[..., :3]

    if mode == 'multiply':
        blended_rgb = base_rgb * design_rgb
    elif mode == 'screen':
        blended_rgb = 1 - (1 - base_rgb) * (1 - design_rgb)
    elif mode == 'overlay':
        blended_rgb = np.where(base_rgb < 0.5, 2 * base_rgb * design_rgb, 1 - 2 * (1 - base_rgb) * (1 - design_rgb))
    else: # Fallback to normal
        blended_rgb = design_rgb

    final_alpha = design_alpha + base_np[..., 3] * (1 - design_alpha)
    final_alpha[final_alpha == 0] = epsilon
    final_rgb = (blended_rgb * design_alpha[..., None] + base_rgb * base_np[..., 3, None] * (1 - design_alpha[..., None])) / final_alpha[..., None]
    final_rgba = np.dstack((final_rgb, final_alpha))
    return Image.fromarray((np.clip(final_rgba, 0, 1) * 255).astype(np.uint8), 'RGBA')

def blend_images(base, design, mode, opacity):
    if base.mode != 'RGBA': base = base.convert('RGBA')
    if mode == 'normal':
        if opacity < 1.0:
            alpha = design.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            design.putalpha(alpha)
        return Image.alpha_composite(base, design)
    else:
        return blend_images_numpy(base, design, mode, opacity)
    

# --- Main Execution ---

def coffee_mug_overlay(product_image_path: str,
    design_image_path: str,
    output_image_path: str,
    frames_coordinates: list):
    start_time = time.time()
    # --- PARAMETERS ---
    # These values are taken from your session.
    # IMPORTANT: Replace 'path/to/your/product.jpg' and 'path/to/your/design.png'

    # for frame_info in frames_coordinates:
    #     warp_coords = json.loads(frame_info['warpCoords'])
    #     frames_data = json.loads(frame_info['frames'])
    #     rotation_angle = float(frame_info['rotationAngle'])
    #     design_opacity = float(frame_info['designOpacity'])
    #     blend_mode = frame_info['blendModeSelected']
    #     curvature_strength = float(frame_info['curvatureStrength'])
    #     mesh_rows = int(frame_info['meshRows'])
    #     mesh_cols = int(frame_info['meshCols'])
    #     original_mesh_coords = json.loads(frame_info['originalMeshCoords'])
    #     deformed_mesh_coords = json.loads(frame_info['deformedMeshCoords'])

    for frame_info in frames_coordinates:
        warp_coords = json.loads(frame_info.get('warpCoords', '[]'))
        frames_data = json.loads(frame_info.get('frames', '[]'))
        rotation_angle = float(frame_info.get('rotationAngle', 0))
        design_opacity = float(frame_info.get('designOpacity', 1))
        blend_mode = frame_info.get('blendModeSelected', 'normal')
        curvature_strength = float(frame_info.get('curvatureStrength', 0))
        mesh_rows = int(frame_info.get('meshRows', 0))
        mesh_cols = int(frame_info.get('meshCols', 0))
        original_mesh_coords = json.loads(frame_info.get('originalMeshCoords', '[]'))
        deformed_mesh_coords = json.loads(frame_info.get('deformedMeshCoords', '[]'))


    
    is_mesh_warp = True if mesh_rows > 0 and mesh_cols > 0 else False

    interpolation_method = cv2.INTER_LINEAR # Hardcoded warp quality

    # --- PROCESSING LOGIC ---
    try:
        base_img_pil = Image.open(product_image_path).convert('RGBA')
        design_img_pil = Image.open(design_image_path).convert('RGBA')
    except FileNotFoundError:
        print("ERROR: Could not find image files. Please update the 'product_image_path' and 'design_image_path' variables.")
        return

    if rotation_angle != 0:
        design_img_pil = design_img_pil.rotate(-rotation_angle, expand=True, resample=Image.BICUBIC)

    design_img_cv = pil_to_cv2(design_img_pil)
    h, w = base_img_pil.size[1], base_img_pil.size[0]

    warped_design_cv = np.zeros((h, w, 4), dtype=np.uint8)

    if is_mesh_warp:
        src_h, src_w = design_img_cv.shape[:2]
        original_mesh_pts = np.float32([[p['x'] * src_w, p['y'] * src_h] for p in original_mesh_coords])
        deformed_mesh_pts = np.float32([[p['x'], p['y']] for p in deformed_mesh_coords])

        for r in range(mesh_rows):
            for c in range(mesh_cols):
                idx_tl, idx_tr = r * (mesh_cols + 1) + c, r * (mesh_cols + 1) + (c + 1)
                idx_bl, idx_br = (r + 1) * (mesh_cols + 1) + c, (r + 1) * (mesh_cols + 1) + (c + 1)

                src_tl, src_tr, src_bl, src_br = original_mesh_pts[idx_tl], original_mesh_pts[idx_tr], original_mesh_pts[idx_bl], original_mesh_pts[idx_br]
                dst_tl, dst_tr, dst_bl, dst_br = deformed_mesh_pts[idx_tl], deformed_mesh_pts[idx_tr], deformed_mesh_pts[idx_bl], deformed_mesh_pts[idx_br]

                src_tri1, dst_tri1 = np.float32([src_tl, src_tr, src_br]), np.float32([dst_tl, dst_tr, dst_br])
                src_tri2, dst_tri2 = np.float32([src_tl, src_br, src_bl]), np.float32([dst_tl, dst_br, dst_bl])

                M1 = cv2.getAffineTransform(src_tri1, dst_tri1)
                temp_warped1 = cv2.warpAffine(design_img_cv, M1, (w, h), flags=interpolation_method, borderMode=cv2.BORDER_TRANSPARENT)
                mask1 = np.zeros((h, w), dtype=np.uint8)
                cv2.fillConvexPoly(mask1, np.int32(dst_tri1), 255)
                warped_design_cv = np.where(mask1[..., None] != 0, temp_warped1, warped_design_cv)

                M2 = cv2.getAffineTransform(src_tri2, dst_tri2)
                temp_warped2 = cv2.warpAffine(design_img_cv, M2, (w, h), flags=interpolation_method, borderMode=cv2.BORDER_TRANSPARENT)
                mask2 = np.zeros((h, w), dtype=np.uint8)
                cv2.fillConvexPoly(mask2, np.int32(dst_tri2), 255)
                warped_design_cv = np.where(mask2[..., None] != 0, temp_warped2, warped_design_cv)

    else:
        src_h, src_w = design_img_cv.shape[:2]
        src_pts = np.float32([[0, 0], [src_w, 0], [src_w, src_h], [0, src_h]])
        dst_pts = np.float32([[p['x'], p['y']] for p in warp_coords])
        if len(dst_pts) == 4:
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_design_cv = cv2.warpPerspective(design_img_cv, matrix, (w, h), flags=interpolation_method, borderMode=cv2.BORDER_TRANSPARENT)

    if curvature_strength > 0:
        warped_design_cv = apply_cylindrical_warp(warped_design_cv, curvature_strength)

    if frames_data:
        mask_pil = create_combined_mask((w, h), frames_data)
        if mask_pil:
            mask_cv = np.array(mask_pil)
            warped_design_cv[:, :, 3] = cv2.bitwise_and(warped_design_cv[:, :, 3], mask_cv)


    warped_design_pil = cv2_to_pil(warped_design_cv)
    # --- Slight blur at edges (alpha channel) ---
    r, g, b, a = warped_design_pil.split()
    a = a.filter(ImageFilter.GaussianBlur(radius=3))  # gentle edge blur
    warped_design_pil = Image.merge('RGBA', (r, g, b, a))

    final_image = blend_images(base_img_pil.copy(), warped_design_pil, blend_mode, design_opacity)

    final_image.save(output_image_path)
    elapsed_time = time.time() - start_time
    print(f"✅ Final image saved to {output_image_path} in {elapsed_time:.2f} seconds")

    return output_image_path


def pil_to_cv2(img):
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA)


def cv2_to_pil(img):
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA))


def apply_cylindrical_warp(image, strength):
    if strength <= 0:
        return image

    pil_img = cv2_to_pil(image)
    w, h = pil_img.size
    out = Image.new("RGBA", (w, h))

    for y in range(h):
        for x in range(w):
            nx = (2 * x / w) - 1
            theta = nx * (np.pi / 2)
            c = np.cos(theta)
            if abs(c) < 1e-6:
                continue
            sx = int((nx / c + 1) * w / 2)
            if 0 <= sx < w:
                out.putpixel((x, y), pil_img.getpixel((sx, y)))

    return pil_to_cv2(out)


def draw_shape(draw, shape, fill):
    pts = shape.get("coordinates", {}).get("points", [])
    if len(pts) < 3:
        return
    draw.polygon([(p["x"], p["y"]) for p in pts], fill=fill)


def create_mask(size, frames):
    if not frames:
        return None
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for f in frames:
        if f.get("is_closed"):
            draw_shape(draw, f, 255)
    return mask


def blend_images(base, overlay, mode, opacity):
    base = base.convert("RGBA")
    overlay = overlay.convert("RGBA")

    if opacity < 1:
        alpha = overlay.split()[3].point(lambda p: int(p * opacity))
        overlay.putalpha(alpha)

    return Image.alpha_composite(base, overlay)

def frame_overlay_multiple_designs(
    product_image_path: str,
    design_image_paths: list,
    output_image_path: str,
    frames_coordinates: str  # JSON string
):
    import time, json, cv2, numpy as np
    from PIL import Image, ImageFilter

    print("🟢 START frame_overlay_multiple_designs")
    start_time = time.time()

    # --- Open base image ---
    try:
        base_img_pil = Image.open(product_image_path).convert("RGBA")
        print(f"🟢 Loaded base image: {product_image_path}")
    except Exception as e:
        print(f"❌ Failed to open base image: {e}")
        return

    w, h = base_img_pil.size
    interpolation = cv2.INTER_LINEAR

    # --- Parse frames_coordinates string ---
    try:
        frames_coordinates_list = json.loads(frames_coordinates)
    except Exception as e:
        print(f"❌ Failed to parse frames_coordinates: {e}")
        return

    # --- Only first frame block ---
    frame_info = frames_coordinates_list[0]
    frames_data = json.loads(frame_info.get("frames", "[]"))
    print("🟢 Loaded frame_info[0] with frames count:", len(frames_data))

    # --- Loop over each frame inside frames_data ---
    for frame_idx, frame in enumerate(frames_data):
        if frame_idx >= len(design_image_paths):
            print("⚠️ No more designs left")
            break

        design_path = design_image_paths[frame_idx]
        print(f"\n🟢 Applying design {frame_idx+1} → frame {frame.get('id')} ({design_path})")

        try:
            design_img_pil = Image.open(design_path).convert("RGBA")
            print(f"🟢 Loaded design image: {design_path}")
        except Exception as e:
            print(f"❌ Failed to open design image: {design_path} → {e}")
            continue

        # --- Convert design image to NumPy array (RGBA) ---
        design_img_cv = np.array(design_img_pil)

        if design_img_cv.shape[2] == 3:
            alpha_channel = np.full((design_img_cv.shape[0], design_img_cv.shape[1], 1), 255, dtype=np.uint8)
            design_img_cv = np.concatenate([design_img_cv, alpha_channel], axis=2)

        src_h, src_w = design_img_cv.shape[:2]

        # --- Source rectangle points (full design image) ---
        src_pts = np.float32([[0, 0], [src_w, 0], [src_w, src_h], [0, src_h]])

        # --- Destination points from frame coordinates ---
        pts = frame["coordinates"]["points"]
        dst_pts = np.float32([[pts[0]["x"], pts[0]["y"]],
                              [pts[1]["x"], pts[1]["y"]],
                              [pts[2]["x"], pts[2]["y"]],
                              [pts[3]["x"], pts[3]["y"]]])

        # --- Perspective transform matrix ---
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)

        # --- Warp each channel separately to preserve alpha ---
        warped_channels = []
        for ch in range(4):  # R, G, B, A
            warped_ch = cv2.warpPerspective(design_img_cv[:, :, ch], M, (w, h),
                                            flags=interpolation,
                                            borderMode=cv2.BORDER_CONSTANT,
                                            borderValue=0)
            warped_channels.append(warped_ch)

        # --- Merge channels back ---
        warped_cv = cv2.merge(warped_channels)
        warped_pil = Image.fromarray(warped_cv, mode="RGBA")

        # --- Slight edge feathering on alpha ---
        r, g, b, a = warped_pil.split()
        a = a.filter(ImageFilter.GaussianBlur(radius=2))
        warped_pil = Image.merge("RGBA", (r, g, b, a))

        # --- Paste warped design using alpha ---
        base_img_pil.paste(warped_pil, (0, 0), warped_pil)
        print(f"🟢 Pasted frame {frame.get('id')} onto base image")

    # --- Save final image ---
    base_img_pil.save(output_image_path)
    print(f"✅ Saved final image in {time.time() - start_time:.2f}s → {output_image_path}")
    return output_image_path

# --------------------------------------------------
# MAIN SERVICE
# --------------------------------------------------

def overlay_design_on_base_image(
    base_image_path: str,
    design_image_path: str,
    output_path: str,
    frame_config: dict
) -> str:

    base = Image.open(base_image_path).convert("RGBA")
    design = Image.open(design_image_path).convert("RGBA")

    rotation = float(frame_config.get("rotationAngle", 0))
    opacity = float(frame_config.get("designOpacity", 1))
    blend_mode = frame_config.get("blendModeSelected", "normal")
    curvature = float(frame_config.get("curvatureStrength", 0))

    warp_coords = frame_config.get("warpCoords", [])
    frames = frame_config.get("frames", [])
    mesh_rows = int(frame_config.get("meshRows", 0))
    mesh_cols = int(frame_config.get("meshCols", 0))
    original_mesh = frame_config.get("originalMeshCoords", [])
    deformed_mesh = frame_config.get("deformedMeshCoords", [])

    if rotation != 0:
        design = design.rotate(-rotation, expand=True, resample=Image.BICUBIC)

    design_cv = pil_to_cv2(design)
    h, w = base.size[1], base.size[0]
    warped = np.zeros((h, w, 4), dtype=np.uint8)

    # -------- MESH WARP --------
    if mesh_rows and mesh_cols and original_mesh and deformed_mesh:
        src_h, src_w = design_cv.shape[:2]
        src_pts = np.float32([[p["x"] * src_w, p["y"] * src_h] for p in original_mesh])
        dst_pts = np.float32([[p["x"], p["y"]] for p in deformed_mesh])

        for r in range(mesh_rows):
            for c in range(mesh_cols):
                i = r * (mesh_cols + 1) + c
                idx = [i, i+1, i+mesh_cols+2, i+mesh_cols+1]
                M = cv2.getPerspectiveTransform(src_pts[idx], dst_pts[idx])
                temp = cv2.warpPerspective(design_cv, M, (w, h), borderMode=cv2.BORDER_TRANSPARENT)
                warped = np.where(temp[..., 3:] > 0, temp, warped)

    # -------- SIMPLE WARP --------
    elif len(warp_coords) == 4:
        src_h, src_w = design_cv.shape[:2]
        src = np.float32([[0,0],[src_w,0],[src_w,src_h],[0,src_h]])
        dst = np.float32([[p["x"], p["y"]] for p in warp_coords])
        M = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(design_cv, M, (w, h), borderMode=cv2.BORDER_TRANSPARENT)

    if curvature > 0:
        warped = apply_cylindrical_warp(warped, curvature)

    if frames:
        mask = create_mask((w, h), frames)
        if mask:
            warped[..., 3] = cv2.bitwise_and(warped[..., 3], np.array(mask))

    final = blend_images(base, cv2_to_pil(warped), blend_mode, opacity)
    final.save(output_path)

    return output_path