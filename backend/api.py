from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import cv2
import asyncio
import time

from detector import Detector
from tracker import Tracker
from analytics import Analytics
from config import FRAME_WIDTH, FRAME_HEIGHT, PROCESS_EVERY_N_FRAMES
from state import live_metrics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 SINGLE CAMERA INSTANCE (stable on Windows)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

latest_frame = None
active_connections = []


# ------------------- REST -------------------

@app.get("/stats")
def get_stats():
    return live_metrics


# ------------------- WEBSOCKET -------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            await asyncio.sleep(1)
            await websocket.send_json(live_metrics)
    except:
        active_connections.remove(websocket)


# ------------------- DETECTION LOOP -------------------

def detection_loop():
    global latest_frame

    detector = Detector()
    tracker = Tracker()
    analytics = Analytics()

    frame_count = 0
    prev_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        frame_count += 1

        # 🔥 Skip frames for performance
        if frame_count % PROCESS_EVERY_N_FRAMES != 0:
            continue

        detections = detector.detect(frame)
        tracks = tracker.update(detections, frame)

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            l, t, r, b = track.to_ltrb()
            l, t, r, b = int(l), int(t), int(r), int(b)

            center_y = int((t + b) / 2)
            analytics.update(track_id, center_y)

            # Draw clean bounding box
            cv2.rectangle(frame, (l, t), (r, b), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"ID {track_id}",
                (l, t - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        # Draw entry/exit line
        cv2.line(frame, (0, 250), (FRAME_WIDTH, 250), (0, 0, 255), 2)

        # 🔥 FPS Calculation
        current_time = time.time()
        fps = 1 / (current_time - prev_time) if prev_time != 0 else 0
        prev_time = current_time

        cv2.putText(
            frame,
            f"FPS: {int(fps)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 0),
            2
        )

        latest_frame = frame


@app.on_event("startup")
def start_detection():
    thread = threading.Thread(target=detection_loop, daemon=True)
    thread.start()


# ------------------- VIDEO STREAM -------------------

def generate_frames():
    global latest_frame
    while True:
        if latest_frame is None:
            time.sleep(0.01)
            continue

        ret, buffer = cv2.imencode(".jpg", latest_frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


@app.get("/video")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
