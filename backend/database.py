import psycopg2
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            "postgresql://postgres:TanU,Tan$090@db.eabjerwsqxsnogvihhtw.supabase.co:5432/postgres"
        )
        self.cursor = self.conn.cursor()

    def insert_event(self, track_id, event_type):
        query = """
        INSERT INTO events (track_id, event_type, timestamp)
        VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (track_id, event_type, datetime.utcnow()))
        self.conn.commit()

    def insert_customer(self, track_id, entry_time, exit_time, dwell_time):
        query = """
        INSERT INTO customers (track_id, entry_time, exit_time, dwell_time)
        VALUES (%s, %s, %s, %s)
        """
        self.cursor.execute(query, (track_id, entry_time, exit_time, dwell_time))
        self.conn.commit()
