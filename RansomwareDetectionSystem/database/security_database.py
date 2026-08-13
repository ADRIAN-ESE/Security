import sqlite3
import os
from datetime import datetime


class SecurityDatabase:

    def __init__(self, db_path=None):
        """
        SQLite database manager.

        A new SQLite connection is created for each operation.
        This avoids the threading problem caused by Watchdog.
        """

        if db_path is None:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )

            db_path = os.path.join(
                base_dir,
                "security.db"
            )

        self.db_path = db_path

        self.initialize_database()

    # ==========================================================
    # DATABASE CONNECTION
    # ==========================================================

    def get_connection(self):
        connection = sqlite3.connect(
            self.db_path,
            timeout=10
        )

        connection.row_factory = sqlite3.Row

        return connection

    # ==========================================================
    # INITIALIZE DATABASE
    # ==========================================================

    def initialize_database(self):

        connection = self.get_connection()

        cursor = connection.cursor()

        # ------------------------------------------------------
        # FILE EVENTS
        # ------------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                risk_level TEXT DEFAULT 'LOW'
            )
        """)

        # ------------------------------------------------------
        # SECURITY INCIDENTS
        # ------------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_type TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                total_events INTEGER DEFAULT 0,
                modified INTEGER DEFAULT 0,
                renamed INTEGER DEFAULT 0,
                deleted INTEGER DEFAULT 0,
                created INTEGER DEFAULT 0,
                reasons TEXT DEFAULT '',
                status TEXT DEFAULT 'OPEN',
                timestamp TEXT NOT NULL
            )
        """)

        connection.commit()

        connection.close()

    # ==========================================================
    # SAVE EVENT
    # ==========================================================

    def save_event(
        self,
        event_type,
        file_path,
        score=0,
        risk_level="LOW"
    ):

        connection = self.get_connection()

        cursor = connection.cursor()

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
            INSERT INTO events (
                timestamp,
                event_type,
                file_path,
                score,
                risk_level
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            timestamp,
            event_type,
            file_path,
            score,
            risk_level
        ))

        connection.commit()

        event_id = cursor.lastrowid

        connection.close()

        return event_id

    # ==========================================================
    # SAVE INCIDENT
    # ==========================================================

    def save_incident(
        self,
        incident_type,
        risk_level,
        score,
        total_events,
        modified,
        renamed,
        deleted,
        created,
        reasons
    ):

        connection = self.get_connection()

        cursor = connection.cursor()

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
            INSERT INTO incidents (
                incident_type,
                risk_level,
                score,
                total_events,
                modified,
                renamed,
                deleted,
                created,
                reasons,
                status,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_type,
            risk_level,
            score,
            total_events,
            modified,
            renamed,
            deleted,
            created,
            reasons,
            "OPEN",
            timestamp
        ))

        connection.commit()

        incident_id = cursor.lastrowid

        connection.close()

        return incident_id

    # ==========================================================
    # GET SINGLE INCIDENT
    # ==========================================================

    def get_incident(self, incident_id):

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                incident_type,
                risk_level,
                score,
                total_events,
                modified,
                renamed,
                deleted,
                created,
                reasons,
                status,
                timestamp
            FROM incidents
            WHERE id = ?
        """, (
            incident_id,
        ))

        row = cursor.fetchone()

        connection.close()

        if row is None:
            return None

        return {
            "id": row["id"],
            "incident_type": row["incident_type"],
            "risk_level": row["risk_level"],
            "score": row["score"],
            "total_events": row["total_events"],
            "modified": row["modified"],
            "renamed": row["renamed"],
            "deleted": row["deleted"],
            "created": row["created"],
            "reasons": row["reasons"] or "",
            "status": row["status"],
            "timestamp": row["timestamp"]
        }

    # ==========================================================
    # GET RECENT INCIDENTS
    # ==========================================================

    def get_recent_incidents(self, limit=20):

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                timestamp,
                incident_type,
                score,
                risk_level,
                total_events,
                modified,
                renamed,
                deleted,
                created,
                reasons,
                status
            FROM incidents
            ORDER BY id DESC
            LIMIT ?
        """, (
            limit,
        ))

        rows = cursor.fetchall()

        connection.close()

        return [tuple(row) for row in rows]

    # ==========================================================
    # GET RECENT EVENTS
    # ==========================================================

    def get_recent_events(self, limit=50):

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                timestamp,
                event_type,
                file_path,
                score,
                risk_level
            FROM events
            ORDER BY id DESC
            LIMIT ?
        """, (
            limit,
        ))

        rows = cursor.fetchall()

        connection.close()

        return [tuple(row) for row in rows]

    # ==========================================================
    # GET TOTAL EVENTS
    # ==========================================================

    def get_total_events(self):

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM events
        """)

        result = cursor.fetchone()[0]

        connection.close()

        return result

    # ==========================================================
    # GET TOTAL INCIDENTS
    # ==========================================================

    def get_total_incidents(self):

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM incidents
        """)

        result = cursor.fetchone()[0]

        connection.close()

        return result

    # ==========================================================
    # GET RISK STATISTICS
    # ==========================================================

    def get_risk_statistics(self):

        connection = self.get_connection()

        cursor = connection.cursor()

        statistics = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0
        }

        cursor.execute("""
            SELECT
                UPPER(risk_level) AS risk_level,
                COUNT(*) AS total
            FROM events
            GROUP BY UPPER(risk_level)
        """)

        rows = cursor.fetchall()

        for row in rows:

            risk = row["risk_level"].lower()

            if risk in statistics:
                statistics[risk] = row["total"]

        connection.close()

        return statistics

    # ==========================================================
    # GET DASHBOARD STATISTICS
    # ==========================================================

    def get_statistics(self):

        return {
            "total_events": self.get_total_events(),

            "total_incidents": self.get_total_incidents(),

            "risk": self.get_risk_statistics()
        }

    # ==========================================================
    # UPDATE INCIDENT STATUS
    # ==========================================================

    def update_incident_status(
        self,
        incident_id,
        status
    ):

        allowed_statuses = {
            "OPEN",
            "INVESTIGATING",
            "RESOLVED",
            "CLOSED"
        }

        status = status.upper()

        if status not in allowed_statuses:
            raise ValueError(
                "Invalid incident status"
            )

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            UPDATE incidents
            SET status = ?
            WHERE id = ?
        """, (
            status,
            incident_id
        ))

        connection.commit()

        updated = cursor.rowcount

        connection.close()

        return updated