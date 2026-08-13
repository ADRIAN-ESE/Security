import os
import time
from collections import deque


class BehaviorAnalyzer:

    # =========================================================
    # CONFIGURATION
    # =========================================================

    TIME_WINDOW = 10

    MODIFICATION_THRESHOLD = 10
    MASS_MODIFICATION_THRESHOLD = 50
    MASS_RENAME_THRESHOLD = 10
    MASS_DELETE_THRESHOLD = 10

    # File extensions commonly associated with encrypted files
    SUSPICIOUS_EXTENSIONS = {
        ".encrypted",
        ".enc",
        ".locked",
        ".lock",
        ".crypt",
        ".crypto",
        ".wncry",
        ".wcry",
        ".ransom"
    }

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self):

        # Store recent filesystem events
        self.events = deque()

    # =========================================================
    # RECORD EVENT
    # =========================================================

    def record_event(self, event_type, file_path):

        current_time = time.time()

        event = {
            "time": current_time,
            "type": event_type,
            "file": file_path
        }

        self.events.append(event)

        # Remove events outside our detection window
        self.remove_old_events(current_time)

        # Analyze current behavior
        return self.analyze()

    # =========================================================
    # REMOVE OLD EVENTS
    # =========================================================

    def remove_old_events(self, current_time):

        while self.events:

            oldest_event = self.events[0]

            event_age = (
                current_time -
                oldest_event["time"]
            )

            if event_age > self.TIME_WINDOW:

                self.events.popleft()

            else:

                break

    # =========================================================
    # ANALYZE BEHAVIOR
    # =========================================================

    def analyze(self):

        modified = 0
        renamed = 0
        deleted = 0
        created = 0

        suspicious_extensions = 0

        # -----------------------------------------------------
        # Count events
        # -----------------------------------------------------

        for event in self.events:

            event_type = event["type"]
            file_path = event["file"]

            if event_type == "modified":

                modified += 1

            elif event_type == "renamed":

                renamed += 1

            elif event_type == "deleted":

                deleted += 1

            elif event_type == "created":

                created += 1

            # Check suspicious extension
            extension = os.path.splitext(
                file_path
            )[1].lower()

            if extension in self.SUSPICIOUS_EXTENSIONS:

                suspicious_extensions += 1

        # -----------------------------------------------------
        # Calculate risk
        # -----------------------------------------------------

        score = 0

        reasons = []

        # -----------------------------------------------------
        # Rapid modification
        # -----------------------------------------------------

        if modified >= self.MODIFICATION_THRESHOLD:

            score += 20

            reasons.append(
                "Rapid file modification"
            )

        # -----------------------------------------------------
        # Mass modification
        # -----------------------------------------------------

        if modified >= self.MASS_MODIFICATION_THRESHOLD:

            score += 30

            reasons.append(
                "Mass file modification"
            )

        # -----------------------------------------------------
        # Mass rename
        # -----------------------------------------------------

        if renamed >= self.MASS_RENAME_THRESHOLD:

            score += 20

            reasons.append(
                "Mass file renaming"
            )

        # -----------------------------------------------------
        # Mass deletion
        # -----------------------------------------------------

        if deleted >= self.MASS_DELETE_THRESHOLD:

            score += 20

            reasons.append(
                "Mass file deletion"
            )

        # -----------------------------------------------------
        # Suspicious extensions
        # -----------------------------------------------------

        if suspicious_extensions >= 5:

            score += 25

            reasons.append(
                "Suspicious file extensions detected"
            )

        # -----------------------------------------------------
        # Combined behavior
        # -----------------------------------------------------

        if modified >= 10 and renamed >= 5:

            score += 20

            reasons.append(
                "Modification and rename combination"
            )

        # -----------------------------------------------------
        # Cap score
        # -----------------------------------------------------

        score = min(score, 100)

        # -----------------------------------------------------
        # Determine risk level
        # -----------------------------------------------------

        if score >= 80:

            risk_level = "CRITICAL"

        elif score >= 50:

            risk_level = "HIGH"

        elif score >= 20:

            risk_level = "MEDIUM"

        else:

            risk_level = "LOW"

        # -----------------------------------------------------
        # Return analysis
        # -----------------------------------------------------

        return {

            "score": score,

            "risk_level": risk_level,

            "total_events": len(self.events),

            "modified": modified,

            "renamed": renamed,

            "deleted": deleted,

            "created": created,

            "suspicious_extensions":
                suspicious_extensions,

            "reasons": reasons
        }