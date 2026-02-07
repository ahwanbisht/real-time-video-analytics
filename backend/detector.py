from ultralytics import YOLO
from settings import Settings

class Detector:
    def __init__(self):
        self.model = YOLO("yolov8n.pt")

    def detect(self, frame):
        results = self.model(frame, verbose = False)

        detections = []
        #loop through all objects and extract each object (box) class id
        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])

                #yolo is pretrained on COCO dataset, class id 0 is for person
                if cls == 0:
                    conf = float(box.conf[0])
                    if conf > Settings.CONFIDENCE_THRESHOLD:
                        x1, y1, x2, y2 = box.xyxy[0]
                        w = x2 - x1
                        h = y2 - y1
                        detections.append(
                            ([float(x1), float(y1), float(w), float(h)], conf, 'person')
                        )

        return detections