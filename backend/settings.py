import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DB_URL = os.getenv("DB_URL")

    # Camera
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))

    # Frame settings
    FRAME_WIDTH = int(os.getenv("FRAME_WIDTH", 640))
    FRAME_HEIGHT = int(os.getenv("FRAME_HEIGHT", 480))
    PROCESS_EVERY_N_FRAMES = int(os.getenv("PROCESS_EVERY_N_FRAMES", 3))

    # Analytics
    LINE_POSITION = int(os.getenv("LINE_POSITION", 250))
    OVERCROWD_THRESHOLD = int(os.getenv("OVERCROWD_THRESHOLD", 3))
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.4))


settings = Settings()
