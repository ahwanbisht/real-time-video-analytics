from fastapi import FastAPI, WebSocket
import asyncio
import threading
import cv2
from detector import Detector
from tracker import Tracker
from analytics import Analytics
from config import FRAME_WIDTH, FRAME_HEIGHT, PROCESS_EVERY_N_FRAMES

app = FastAPI()

from state import live_metrics

active_connections = []

@app.get("/stats")
def get_stats():
    return live_metrics


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


# Detection Loop as Background Thread
def detection_loop():
    detector = Detector()
    tracker = Tracker()
    analytics = Analytics()

    cap = cv2.VideoCapture(0)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        frame_count += 1

        if frame_count % PROCESS_EVERY_N_FRAMES != 0:
            continue

        detections = detector.detect(frame)
        tracks = tracker.update(detections, frame)

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            l, t, r, b = track.to_ltrb()
            center_y = int((t + b) / 2)

            analytics.update(track_id, center_y)


# Start detection automatically when API starts
@app.on_event("startup")
def start_detection():
    thread = threading.Thread(target=detection_loop, daemon=True)
    thread.start()
