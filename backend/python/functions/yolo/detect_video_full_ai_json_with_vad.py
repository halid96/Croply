import cv2
import json
import os
import numpy as np
import math
import time
from ultralytics import YOLO

# --- IMPORT YOUR VAD FUNCTION ---
from audio_vad import get_vad_segments

# ---------------- SETTINGS ---------------- #

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Navigate to backend root: from functions/yolo/ -> backend/
BACKEND_DIR = os.path.join(SCRIPT_DIR, "..", "..")
# Paths relative to backend directory
STORAGE_DIR = os.path.join(BACKEND_DIR, "..", "storage")
MODELS_DIR = os.path.join(BACKEND_DIR, "models")

def process_video(video_id):
    """
    Process a video with YOLO detection and VAD analysis.
    
    Args:
        video_id: The ID of the video (used for input and output paths)
    """
    # Construct paths based on video_id
    VIDEO_PATH = os.path.join(STORAGE_DIR, "uploads", f"{video_id}.mp4")
    AUDIO_PATH = VIDEO_PATH  # same video source → audio extracted automatically
    SAVE_DIR = os.path.join(STORAGE_DIR, "video_frames_json", str(video_id))
    MODEL_PATH = os.path.join(MODELS_DIR, "yolov9c.pt")
    
    # Create save directory if it doesn't exist
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    # Verify video file exists
    if not os.path.exists(VIDEO_PATH):
        raise FileNotFoundError(f"Video file not found: {VIDEO_PATH}")
    
    # Verify model file exists
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    # ---------------- AUDIO VAD PRELOAD ---------------- #

    print("Extracting audio VAD...")
    try:
        vad_list = get_vad_segments(AUDIO_PATH, frame_duration=0.04)  # ≈ 25 FPS, adjust later
        print(f"Loaded VAD frames: {len(vad_list)}")
    except Exception as e:
        print("VAD ERROR:", e)
        vad_list = []

    # ---------------- LOAD VIDEO ---------------- #

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(VIDEO_PATH)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080

    # --- Convert VAD to video FPS scale ---
    # Video frames:     N video frames
    # Audio VAD frames: M VAD frames
    # Map audio index -> video index

    def vad_for_frame(idx):
        if not vad_list:
            return {"is_speech": False, "speech_prob": 0.0}

        mapped = int((idx / fps) * (1.0 / 0.04))  # 0.04s per VAD frame
        if mapped < 0 or mapped >= len(vad_list):
            return {"is_speech": False, "speech_prob": 0.0}
        # Map audio_vad output to expected format
        vad_data = vad_list[mapped]
        return {
            "is_speech": vad_data.get("is_talking", False),
            "speech_prob": vad_data.get("speech_prob", 0.0)
        }

    # ---------------- ALL YOUR YOLO CODE ---------------- #

    previous_centers = {}
    missing_counts = {}
    stay_duration = {}
    next_id = 1
    previous_frame_gray = None
    frame_index = 0

    MATCH_DISTANCE_THRESHOLD = max(width, height) * 0.12

    start_time = time.time()

    def compute_scene_change(gray, prev_gray):
        if prev_gray is None:
            return False
        diff = cv2.absdiff(gray, prev_gray)
        score = float(np.mean(diff))
        return score > 25

    def calculate_importance(obj):
        area_score = min(obj.get("bbox_area_percentage", 0) / 100.0, 1.0)
        motion_score = min(obj.get("motion_magnitude", 0) / 30.0, 1.0)
        conf_score = obj.get("confidence", 0)
        return 0.45 * area_score + 0.35 * motion_score + 0.20 * conf_score

    def convert_numpy(obj):
        if isinstance(obj, dict):
            return {str(k): convert_numpy(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [convert_numpy(v) for v in obj]
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    def safe_float(x):
        try:
            return float(x)
        except:
            return 0.0

    # ---------------- MAIN LOOP ---------------- #

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = frame_index / fps
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # YOLO inference
        try:
            results = model(frame, verbose=False)[0]
        except:
            frame_index += 1
            continue

        frame_data = {
            "frame": int(frame_index),
            "timestamp": round(float(timestamp), 3),
            "fps": float(fps),
            "resolution": [int(width), int(height)],
            "objects": []
        }

        # ---------------- ADD AUDIO VAD HERE ---------------- #

        frame_data["audio"] = vad_for_frame(frame_index)

        # Scene change
        frame_data["is_scene_change"] = bool(
            compute_scene_change(gray_frame, previous_frame_gray)
        )

        detected_centers = []
        seen_ids_this_frame = set()

        # Object parsing
        for box in results.boxes:
            cls = int(box.cls[0])
            conf = safe_float(box.conf[0])
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = map(float, xyxy)

            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            w = x2 - x1
            h = y2 - y1
            area = w * h
            area_pct = (area / (width * height)) * 100

            # Track ID matching
            obj_id = None
            min_dist = float("inf")

            for pid, prev in previous_centers.items():
                d = math.hypot(cx - prev[0], cy - prev[1])
                if d < min_dist:
                    min_dist = d
                    obj_id = pid

            if obj_id is None or min_dist > MATCH_DISTANCE_THRESHOLD:
                obj_id = next_id
                next_id += 1
                missing_counts[obj_id] = 0
                stay_duration[obj_id] = 0

            # Motion
            if obj_id in previous_centers:
                vx = cx - previous_centers[obj_id][0]
                vy = cy - previous_centers[obj_id][1]
                stay_duration[obj_id] += 1
            else:
                vx, vy = 0.0, 0.0
                stay_duration[obj_id] = 1

            motion_mag = math.hypot(vx, vy)
            velocity = motion_mag * fps

            obj = {
                "id": int(obj_id),
                "class_id": int(cls),
                "class_name": str(results.names[cls]),
                "confidence": float(conf),
                "bbox_xyxy": [x1, y1, x2, y2],
                "bbox_center": [cx, cy],
                "bbox_xywh": [cx, cy, w, h],
                "bbox_normalized": [cx/width, cy/height, w/width, h/height],
                "bbox_area_pixels": area,
                "bbox_area_percentage": area_pct,
                "motion_vector": [vx, vy],
                "motion_magnitude": motion_mag,
                "velocity_px_second": velocity,
                "stay_duration_frames": stay_duration[obj_id],
            }

            obj["importance_score"] = calculate_importance(obj)

            frame_data["objects"].append(obj)
            detected_centers.append((obj_id, cx, cy))
            seen_ids_this_frame.add(obj_id)

        # Update trackers
        for pid in list(previous_centers.keys()):
            if pid not in seen_ids_this_frame:
                missing_counts[pid] += 1
                if missing_counts[pid] > fps * 2:
                    previous_centers.pop(pid, None)
                    missing_counts.pop(pid, None)
                    stay_duration.pop(pid, None)

        for pid, cx, cy in detected_centers:
            previous_centers[pid] = [cx, cy]

        # Dominant subject
        if frame_data["objects"]:
            dom = max(frame_data["objects"], key=lambda o: o["importance_score"])
            frame_data["dominant_subject_id"] = dom["id"]
            frame_data["dominant_subject_confidence"] = dom["importance_score"]
            frame_data["frame_focus_center"] = dom["bbox_center"]
        else:
            frame_data["dominant_subject_id"] = None
            frame_data["dominant_subject_confidence"] = 0.0
            frame_data["frame_focus_center"] = [width/2, height/2]

        # Save JSON
        json_safe = convert_numpy(frame_data)
        path = os.path.join(SAVE_DIR, f"frame_{frame_index:05}.json")

        with open(path, "w") as f:
            json.dump(json_safe, f, indent=4)

        if frame_index % 50 == 0:
            print("Saved:", path)

        previous_frame_gray = gray_frame
        frame_index += 1

    cap.release()
    print("FULL AI + AUDIO JSON extraction complete.")


# Allow script to be run directly with video_id as command line argument
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python detect_video_full_ai_json_with_vad.py <video_id>")
        sys.exit(1)
    video_id = sys.argv[1]
    process_video(video_id)

