import cv2
import threading
import time

class Camera:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.frame = None
        self.lock = threading.Lock()
        self.running = True

        thread = threading.Thread(target=self.update, daemon=True)
        thread.start()

    def update(self):
        while self.running:
            if not self.cap.isOpened():
                continue

            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                print("Frame grab failed")

            time.sleep(0.01)   # 🔥 VERY IMPORTANT

    def get_frame(self):
        with self.lock:
            return self.frame
