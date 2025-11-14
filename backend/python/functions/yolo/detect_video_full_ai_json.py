import cv2
import json
import os
from ultralytics import YOLO
import numpy as np
import math
import time

# ---------------- SETTINGS ---------------- #

VIDEO_PATH = "/Users/halid/Downloads/testyolo.mp4"
SAVE_DIR = "/Users/halid/Downloads/yoloresults"
MODEL_PATH = "yolov9c.pt"

os.makedirs(SAVE_DIR, exist_ok=True)

# Load YOLO model
model = YOLO(MODEL_PATH)

# Open video
cap = cv2.VideoCapture(VIDEO_PATH)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080

# Tracking state
previous_centers = {}        # id -> [cx, cy]
missing_counts = {}         # id -> consecutive frames missing
stay_duration = {}          # id -> frames present consecutively
next_id = 1

previous_frame_gray = None
frame_index = 0

# Matching threshold (pixels). Tune if needed.
MATCH_DISTANCE_THRESHOLD = max(width, height) * 0.12  # ~12% of larger dim

def compute_scene_change(gray, prev_gray):
    if prev_gray is None:
        return False
    diff = cv2.absdiff(gray, prev_gray)
    score = float(np.mean(diff))
    return score > 25  # threshold for scene change

def calculate_importance(obj):
    # importance: area + motion + confidence (weighted)
    area_score = min(obj.get("bbox_area_percentage", 0) / 100.0, 1.0)
    motion_score = min(obj.get("motion_magnitude", 0) / 30.0, 1.0)
    conf_score = obj.get("confidence", 0)
    return 0.45 * area_score + 0.35 * motion_score + 0.20 * conf_score

def convert_numpy(obj):
    """Recursively convert numpy types and other non-json types to python built-ins."""
    if isinstance(obj, dict):
        return {str(k): convert_numpy(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [convert_numpy(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.bool_, )):
        return bool(obj)
    if isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    # float, int, str, bool stay as-is
    return obj

def safe_float(x):
    try:
        return float(x)
    except Exception:
        try:
            return float(np.array(x).astype(float).tolist())
        except Exception:
            return 0.0

start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Timestamp in seconds
    timestamp = frame_index / fps

    # Convert to grayscale for scene detection
    try:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    except Exception:
        gray_frame = None

    # Inference (catch unexpected errors)
    try:
        results = model(frame, verbose=False)[0]
    except Exception as e:
        print(f"[frame {frame_index}] inference error:", e)
        frame_index += 1
        previous_frame_gray = gray_frame
        continue

    frame_data = {
        "frame": int(frame_index),
        "timestamp": round(float(timestamp), 3),
        "fps": float(fps),
        "resolution": [int(width), int(height)],
        "objects": []
    }

    # Scene change detection
    frame_data["is_scene_change"] = bool(compute_scene_change(gray_frame, previous_frame_gray)) if gray_frame is not None else False

    seen_ids_this_frame = set()
    detected_centers = []

    # Parse objects
    for box in results.boxes:
        # safe extraction of fields (box members may be numpy-like)
        try:
            cls = int(box.cls[0])
        except Exception:
            try:
                cls = int(getattr(box, "cls", 0))
            except Exception:
                cls = 0
        try:
            conf = safe_float(box.conf[0])
        except Exception:
            conf = safe_float(getattr(box, "conf", 0.0))

        try:
            xyxy = box.xyxy[0].tolist()
        except Exception:
            try:
                xyxy = list(map(float, box.xyxy))
            except Exception:
                xyxy = [0.0, 0.0, 0.0, 0.0]

        x1, y1, x2, y2 = [safe_float(v) for v in xyxy]
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        w = max(0.0, x2 - x1)
        h = max(0.0, y2 - y1)
        area = w * h
        area_pct = (area / (width * height)) * 100.0 if (width * height) > 0 else 0.0

        # Find matching previous id by nearest center
        obj_id = None
        min_dist = float("inf")
        for pid, pc in previous_centers.items():
            d = math.hypot(cx - pc[0], cy - pc[1])
            if d < min_dist:
                min_dist = d
                obj_id = pid

        if obj_id is None or min_dist > MATCH_DISTANCE_THRESHOLD:
            # new object
            obj_id = next_id
            next_id += 1
            # initialize missing/stay counters
            missing_counts[obj_id] = 0
            stay_duration[obj_id] = 0

        # Motion vector from previous center (if exists)
        if obj_id in previous_centers:
            vx = cx - previous_centers[obj_id][0]
            vy = cy - previous_centers[obj_id][1]
            missing_counts[obj_id] = 0
            stay_duration[obj_id] = stay_duration.get(obj_id, 0) + 1
        else:
            vx, vy = 0.0, 0.0
            missing_counts[obj_id] = 0
            stay_duration[obj_id] = 1

        motion_mag = float(math.hypot(vx, vy))
        velocity = motion_mag * fps

        obj = {
            "id": int(obj_id),
            "class_id": int(cls),
            "class_name": str(results.names[cls]) if hasattr(results, "names") and cls in results.names else str(cls),
            "confidence": float(conf),

            "bbox_xyxy": [float(x1), float(y1), float(x2), float(y2)],
            "bbox_center": [float(cx), float(cy)],
            "bbox_xywh": [float(cx), float(cy), float(w), float(h)],
            "bbox_normalized": [float(cx/width), float(cy/height), float(w/width), float(h/height)],
            "bbox_area_pixels": float(area),
            "bbox_area_percentage": float(area_pct),

            "motion_vector": [float(vx), float(vy)],
            "motion_magnitude": float(motion_mag),
            "velocity_px_frame": float(motion_mag),
            "velocity_px_second": float(velocity),

            "is_new": bool(stay_duration.get(obj_id, 0) <= 1),
            "is_exiting": False,   # placeholder - will set below if missing for many frames
            "stay_duration_frames": int(stay_duration.get(obj_id, 0)),
        }

        # importance score
        obj["importance_score"] = float(calculate_importance(obj))

        frame_data["objects"].append(obj)
        seen_ids_this_frame.add(obj_id)

        # update current center map for this id (for next frame)
        detected_centers.append((obj_id, cx, cy))

    # Update tracking maps: handle missing counts and update positions
    # First, mark missing for previous ids not seen this frame
    for pid in list(previous_centers.keys()):
        if pid not in seen_ids_this_frame:
            missing_counts[pid] = missing_counts.get(pid, 0) + 1
            # if missing for > (fps * 2) frames (2 seconds), we consider it exited
            if missing_counts[pid] > max(2, int(fps * 2)):
                # mark exiting (not present in this frame, but recordable elsewhere)
                # remove from previous_centers so id can be reused only after long time (we don't reuse)
                previous_centers.pop(pid, None)
                missing_counts.pop(pid, None)
                stay_duration.pop(pid, None)

    # Now update previous_centers with newly detected centers
    for (pid, cx, cy) in detected_centers:
        previous_centers[pid] = [cx, cy]

    # Determine dominant subject and frame-level scores
    if frame_data["objects"]:
        dominant = max(frame_data["objects"], key=lambda o: o["importance_score"])
        frame_data["dominant_subject_id"] = int(dominant["id"])
        frame_data["dominant_subject_confidence"] = float(dominant["importance_score"])
        frame_data["frame_focus_center"] = [float(dominant["bbox_center"][0]), float(dominant["bbox_center"][1])]
        frame_data["frame_focus_strength"] = float(dominant["importance_score"])
    else:
        frame_data["dominant_subject_id"] = None
        frame_data["dominant_subject_confidence"] = 0.0
        frame_data["frame_focus_center"] = [width/2.0, height/2.0]
        frame_data["frame_focus_strength"] = 0.0

    # Frame event score: average importance of objects scaled by motion & scene change
    if frame_data["objects"]:
        avg_importance = float(sum(o["importance_score"] for o in frame_data["objects"]) / len(frame_data["objects"]))
        motion_factor = float(sum(o["motion_magnitude"] for o in frame_data["objects"]) / (len(frame_data["objects"]) * (math.sqrt(width**2 + height**2) + 1)))
        frame_event_score = float(min(1.0, avg_importance + motion_factor + (0.5 if frame_data["is_scene_change"] else 0.0)))
    else:
        frame_event_score = 0.0
    frame_data["frame_event_score"] = frame_event_score
    frame_data["model_inference_ms"] = float(getattr(results, "speed", {}).get("inference", 0.0))

    # Convert numpy types to python natives recursively and save JSON
    json_safe = convert_numpy(frame_data)
    json_path = os.path.join(SAVE_DIR, f"frame_{frame_index:05}.json")
    try:
        with open(json_path, "w") as f:
            json.dump(json_safe, f, indent=4)
    except Exception as e:
        print(f"[frame {frame_index}] JSON write error:", e)
        # attempt a fallback by stringifying problematic parts
        try:
            with open(json_path, "w") as f:
                f.write(json.dumps(json_safe, default=str, indent=4))
        except Exception as e2:
            print("[fallback] failed to write JSON:", e2)

    if frame_index % 50 == 0:
        elapsed = time.time() - start_time
        print(f"frame {frame_index} processed, elapsed {elapsed:.1f}s, saved {json_path}")

    previous_frame_gray = gray_frame
    frame_index += 1

cap.release()
print("FULL AI JSON extraction complete.")

