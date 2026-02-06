import time
from state import live_metrics
from database import Database
from datetime import datetime

class Analytics:
    def __init__(self, line_position=250, overcrowd_threshold=5):
        try:
            self.db = Database()
            live_metrics["system_status"]["database"] = "online"
        except Exception as e:
            print(f"Database connection error: {e}")
            self.db = None
            live_metrics["system_status"]["database"] = "offline"
        self.line_position = line_position
        self.overcrowd_threshold = overcrowd_threshold

        self.count_in = 0
        self.count_out = 0
        self.current_inside = 0

        self.track_positions = {}
        self.entry_times = {}

    def update(self, track_id, center_y):
        now = time.time()

        # Check if we have previous position
        if track_id in self.track_positions:
            prev_y = self.track_positions[track_id]

            # Entry condition
            if prev_y < self.line_position and center_y > self.line_position:
                if self.db:
                    self.db.insert_event(track_id, "ENTRY")
                self.count_in += 1
                self.current_inside += 1
                self.entry_times[track_id] = now
                live_metrics["alerts"].append({
                    "type": "info",
                    "message": f"Customer {track_id} entered"
                })
                if len(live_metrics["alerts"]) > 5:
                    live_metrics["alerts"].pop(0)
                print(f"[ENTRY] ID {track_id} entered.")

            # Exit condition
            elif prev_y > self.line_position and center_y < self.line_position:
                if self.db:
                    self.db.insert_event(track_id, "EXIT")
                self.count_out += 1
                self.current_inside -= 1
                live_metrics["alerts"].append({
                    "type": "info",
                    "message": f"Customer {track_id} exited"
                })
                if len(live_metrics["alerts"]) > 5:
                    live_metrics["alerts"].pop(0)
                print(f"[EXIT] ID {track_id} exited.")

                if track_id in self.entry_times:
                    dwell = now - self.entry_times[track_id]
                    if self.db:
                        self.db.insert_customer(
                            track_id,
                            datetime.fromtimestamp(self.entry_times[track_id]),
                            datetime.fromtimestamp(now),
                            int(dwell)
                        )
                    print(f"[DWELL] ID {track_id} stayed {int(dwell)} seconds.")
                    del self.entry_times[track_id]

        self.track_positions[track_id] = center_y

        live_metrics["count_in"] = self.count_in
        live_metrics["count_out"] = self.count_out
        live_metrics["current_inside"] = self.current_inside


    def check_overcrowding(self):
        if self.current_inside >= self.overcrowd_threshold:
            # Add alert to shared state
            live_metrics["alerts"].append({
                "type": "critical",
                "message": "Overcrowding detected!"
            })

            # Keep only last 5 alerts
            if len(live_metrics["alerts"]) > 5:
                live_metrics["alerts"].pop(0)
