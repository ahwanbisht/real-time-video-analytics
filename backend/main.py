import cv2
import time
from detector import Detector
from tracker import Tracker
from analytics import Analytics
from config import FRAME_WIDTH, FRAME_HEIGHT, PROCESS_EVERY_N_FRAMES

detector = Detector()
tracker = Tracker()

cap = cv2.VideoCapture(0)

frame_count = 0

prev_time = 0

analytics = Analytics(line_position=250, overcrowd_threshold=3)

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

        cv2.rectangle(frame, (int(l), int(t)), (int(r), int(b)), (0, 255, 0), 2)
        cv2.putText(frame, f"ID: {track_id}", (int(l), int(t - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Calculate and display FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time) if prev_time != 0 else 0
    prev_time = current_time
    cv2.putText(frame, f"FPS: {int(fps)}", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)    

    cv2.line(frame, (0, 250), (FRAME_WIDTH, 250), (0, 0, 255), 2)
    analytics.check_overcrowding()
    cv2.imshow("Retail Analytics - Phase 1", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
