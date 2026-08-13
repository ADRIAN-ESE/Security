import os
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from detector.analyzer import BehaviorAnalyzer
from alerts.alert_manager import AlertManager
from database.security_database import SecurityDatabase


# ============================================================
# FILE EVENT HANDLER
# ============================================================

class RansomwareEventHandler(FileSystemEventHandler):

    def __init__(self):

        super().__init__()

        # Behavioral analysis
        self.analyzer = BehaviorAnalyzer()

        # Alert system
        self.alert_manager = AlertManager()

        # SQLite database
        self.database = SecurityDatabase()

        # Prevent duplicate incidents
        self.incident_active = False

    # ========================================================
    # PROCESS EVENT
    # ========================================================

    def process_event(
        self,
        event_type,
        file_path
    ):

        try:

            # ------------------------------------------------
            # Analyze filesystem behavior
            # ------------------------------------------------

            result = self.analyzer.record_event(
                event_type,
                file_path
            )

            # ------------------------------------------------
            # Save individual event
            # ------------------------------------------------

            self.database.save_event(
                event_type,
                file_path,
                result["score"],
                result["risk_level"]
            )

            # ------------------------------------------------
            # INCIDENT DETECTION
            # ------------------------------------------------

            if result["risk_level"] in [
                "HIGH",
                "CRITICAL"
            ]:

                # Only create one incident for the
                # current suspicious activity burst.

                if not self.incident_active:

                    incident_id = (
                        self.database.save_incident(
                            result
                        )
                    )

                    self.incident_active = True

                    print()
                    print(
                        f"[INCIDENT] "
                        f"Incident #{incident_id} created"
                    )

            else:

                # Activity has returned to a lower risk level.
                # A future HIGH/CRITICAL burst can therefore
                # create a new incident.

                self.incident_active = False

            # ------------------------------------------------
            # DISPLAY ANALYSIS
            # ------------------------------------------------

            print(
                f"[ANALYSIS] "
                f"Events={result['total_events']} | "
                f"Modified={result['modified']} | "
                f"Renamed={result['renamed']} | "
                f"Deleted={result['deleted']} | "
                f"Created={result['created']} | "
                f"Risk={result['risk_level']} "
                f"({result['score']}/100)"
            )

            # ------------------------------------------------
            # DISPLAY REASONS
            # ------------------------------------------------

            if result["reasons"]:

                for reason in result["reasons"]:

                    print(
                        f"[REASON] {reason}"
                    )

            # ------------------------------------------------
            # ALERT MANAGER
            # ------------------------------------------------

            self.alert_manager.check_risk(
                result
            )

        except Exception as error:

            print(
                f"[ERROR] Failed to process "
                f"{event_type} event: {error}"
            )

    # ========================================================
    # FILE CREATED
    # ========================================================

    def on_created(self, event):

        if event.is_directory:
            return

        print(
            f"[EVENT] CREATED: "
            f"{event.src_path}"
        )

        self.process_event(
            "created",
            event.src_path
        )

    # ========================================================
    # FILE MODIFIED
    # ========================================================

    def on_modified(self, event):

        if event.is_directory:
            return

        print(
            f"[EVENT] MODIFIED: "
            f"{event.src_path}"
        )

        self.process_event(
            "modified",
            event.src_path
        )

    # ========================================================
    # FILE DELETED
    # ========================================================

    def on_deleted(self, event):

        if event.is_directory:
            return

        print(
            f"[EVENT] DELETED: "
            f"{event.src_path}"
        )

        self.process_event(
            "deleted",
            event.src_path
        )

    # ========================================================
    # FILE RENAMED
    # ========================================================

    def on_moved(self, event):

        if event.is_directory:
            return

        print(
            f"[EVENT] RENAMED: "
            f"{event.src_path}"
            f" -> "
            f"{event.dest_path}"
        )

        # Analyze the destination filename because
        # ransomware may rename files to suspicious
        # extensions.

        self.process_event(
            "renamed",
            event.dest_path
        )


# ============================================================
# START MONITOR
# ============================================================

def start_monitor(folder_path):

    # --------------------------------------------------------
    # Verify folder
    # --------------------------------------------------------

    if not os.path.exists(folder_path):

        print(
            f"[ERROR] Monitoring folder does not exist:"
        )

        print(
            f"        {folder_path}"
        )

        return

    # --------------------------------------------------------
    # Create event handler
    # --------------------------------------------------------

    event_handler = RansomwareEventHandler()

    # --------------------------------------------------------
    # Create watchdog observer
    # --------------------------------------------------------

    observer = Observer()

    observer.schedule(
        event_handler,
        folder_path,
        recursive=True
    )

    # --------------------------------------------------------
    # Start observer
    # --------------------------------------------------------

    observer.start()

    print()
    print("=" * 70)
    print("        RANSOMWARE DETECTION SYSTEM")
    print("=" * 70)

    print(
        f"[MONITOR] Started monitoring:"
    )

    print(
        f"[MONITOR] {folder_path}"
    )

    print(
        "[MONITOR] Waiting for file activity..."
    )

    print(
        "[MONITOR] Press CTRL+C to stop."
    )

    print("=" * 70)
    print()

    try:

        while True:

            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print(
            "[MONITOR] Stopping monitor..."
        )

        observer.stop()

    finally:

        observer.join()

        print(
            "[MONITOR] Monitor stopped."
        )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Find project root
    # --------------------------------------------------------

    PROJECT_ROOT = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    # --------------------------------------------------------
    # Locate test folder
    # --------------------------------------------------------

    TEST_FOLDER = os.path.join(
        PROJECT_ROOT,
        "test_folder"
    )

    # --------------------------------------------------------
    # Start monitoring
    # --------------------------------------------------------

    start_monitor(
        TEST_FOLDER
    )