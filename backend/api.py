from fastapi import FastAPI, WebSocket
from logger import setup_logger
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import cv2
import asyncio
import time

from detector import Detector
from tracker import Tracker
from analytics import Analytics
from settings import Settings
from state import live_metrics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = setup_logger()

#SINGLE CAMERA INSTANCE (stable on Windows)
cap = cv2.VideoCapture(Settings.CAMERA_INDEX, cv2.CAP_DSHOW)

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
    logger.info("Detection loop started")
    detector = Detector()
    tracker = Tracker()
    analytics = Analytics()

    frame_count = 0
    prev_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.warning("Camera frame read failed")
            continue

        frame = cv2.resize(frame, (Settings.FRAME_WIDTH, Settings.FRAME_HEIGHT))
        frame_count += 1

        # Skip frames for performance
        if frame_count % Settings.PROCESS_EVERY_N_FRAMES != 0:
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
        cv2.line(frame, (0, Settings.LINE_POSITION), (Settings.FRAME_WIDTH, Settings.LINE_POSITION), (0, 0, 255), 2)

        # FPS Calculation
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

@app.get("/history")
def get_history():
    try:
        from database import Database
        db = Database()
        cursor = db.cursor

        # Total sessions
        cursor.execute("SELECT COUNT(*) FROM customers")
        total_customers = cursor.fetchone()[0]

        # Average dwell
        cursor.execute("SELECT AVG(dwell_time) FROM customers")
        avg_dwell = cursor.fetchone()[0] or 0

        # Maximum dwell
        cursor.execute("SELECT MAX(dwell_time) FROM customers")
        max_dwell = cursor.fetchone()[0] or 0

        # Dwell time distribution
        cursor.execute("SELECT dwell_time FROM customers")
        dwell_distribution = [row[0] for row in cursor.fetchall()]

        # Entry per day trend
        cursor.execute("""
            SELECT DATE(timestamp), COUNT(*)
            FROM events
            WHERE event_type='ENTRY'
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
        """)
        trend_data = cursor.fetchall()

        dates = [str(row[0]) for row in trend_data]
        counts = [row[1] for row in trend_data]

        peak_traffic = max(counts) if counts else 0

        return {
            "total_customers": total_customers,
            "avg_dwell": round(avg_dwell, 2),
            "max_dwell": max_dwell,
            "dwell_distribution": dwell_distribution,
            "trend_dates": dates,
            "trend_counts": counts,
            "peak_traffic": peak_traffic
        }

    except Exception as e:
        logger.error(f"History API error: {e}")
        return {
            "total_customers": 0,
            "avg_dwell": 0,
            "max_dwell": 0,
            "dwell_distribution": [],
            "trend_dates": [],
            "trend_counts": [],
            "peak_traffic": 0
        }
