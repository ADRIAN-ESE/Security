import os
import sys


# ============================================================
# FIND PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Add the project root to Python's import path
sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORT DATABASE CLASS
# ============================================================

from database.security_database import SecurityDatabase


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():

    # Create database connection
    db = SecurityDatabase()

    # Get the 20 most recent events
    events = db.get_recent_events(20)

    print()

    print("=" * 100)
    print("                 RANSOMWARE DETECTION SYSTEM")
    print("                    RECENT SECURITY EVENTS")
    print("=" * 100)

    # Check whether the database contains events
    if not events:

        print()
        print("No security events recorded yet.")
        print()

    else:

        # Display each event
        for event in events:

            event_id = event[0]
            timestamp = event[1]
            event_type = event[2]
            file_path = event[3]
            risk_score = event[4]
            risk_level = event[5]

            print()
            print(f"ID          : {event_id}")
            print(f"Timestamp   : {timestamp}")
            print(f"Event Type  : {event_type}")
            print(f"Risk Level  : {risk_level}")
            print(f"Risk Score  : {risk_score}/100")
            print(f"File        : {file_path}")

            print("-" * 100)

    # Close database
    db.close()

    print()
    print("=" * 100)
    print("Database query completed.")
    print("=" * 100)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()