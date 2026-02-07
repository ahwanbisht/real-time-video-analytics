import time
from datetime import datetime
from database import Database
from state import live_metrics

class Analytics:
    def __init__(self, line_position=250, overcrowd_threshold=1):
        self.line_position = line_position
        self.overcrowd_threshold = overcrowd_threshold

        self.count_in = 0
        self.count_out = 0
        self.current_inside = 0

        self.track_positions = {}
        self.entry_times = {}

        try:
            self.db = Database()
            live_metrics["system_status"]["database"] = "online"
        except Exception as e:
            print("Database connection failed:", e)
            self.db = None
            live_metrics["system_status"]["database"] = "offline"

    def update(self, track_id, center_y):
        now = time.time()

        if track_id in self.track_positions:
            prev_y = self.track_positions[track_id]

            # ENTRY
            if prev_y < self.line_position and center_y > self.line_position:
                self.count_in += 1
                self.current_inside += 1
                self.entry_times[track_id] = now

                if self.db:
                    self.db.insert_event(track_id, "ENTRY")

                self.add_alert("info", f"Customer {track_id} entered")

            # EXIT
            elif prev_y > self.line_position and center_y < self.line_position:
                self.count_out += 1
                self.current_inside -= 1

                if self.db:
                    self.db.insert_event(track_id, "EXIT")

                self.add_alert("info", f"Customer {track_id} exited")

                if track_id in self.entry_times:
                    dwell = now - self.entry_times[track_id]

                    if self.db:
                        self.db.insert_customer(
                            track_id,
                            datetime.fromtimestamp(self.entry_times[track_id]),
                            datetime.fromtimestamp(now),
                            int(dwell)
                        )

                    del self.entry_times[track_id]

        self.track_positions[track_id] = center_y

        # Update shared metrics
        live_metrics["count_in"] = self.count_in
        live_metrics["count_out"] = self.count_out
        live_metrics["current_inside"] = self.current_inside

        self.check_overcrowding()

    def check_overcrowding(self):
        if self.current_inside >= self.overcrowd_threshold:
            self.add_alert("critical", "Overcrowding detected!")

    def add_alert(self, alert_type, message):
        live_metrics["alerts"].append({
            "type": alert_type,
            "message": message
        })

        if len(live_metrics["alerts"]) > 5:
            live_metrics["alerts"].pop(0)
