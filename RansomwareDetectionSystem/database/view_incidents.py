import os
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT
)


from database.security_database import SecurityDatabase


# ============================================================
# MAIN
# ============================================================

def main():

    db = SecurityDatabase()

    incidents = db.get_recent_incidents(20)

    print()

    print("=" * 100)
    print("              RANSOMWARE DETECTION SYSTEM")
    print("                   SECURITY INCIDENTS")
    print("=" * 100)

    if not incidents:

        print()
        print("No security incidents recorded.")
        print()

    else:

        for incident in incidents:

            print()

            print(
                f"Incident ID : {incident[0]}"
            )

            print(
                f"Start Time  : {incident[1]}"
            )

            print(
                f"End Time    : {incident[2]}"
            )

            print(
                f"Risk Level  : {incident[4]}"
            )

            print(
                f"Risk Score  : {incident[3]}/100"
            )

            print(
                f"Events      : {incident[5]}"
            )

            print(
                f"Modified    : {incident[6]}"
            )

            print(
                f"Renamed     : {incident[7]}"
            )

            print(
                f"Deleted     : {incident[8]}"
            )

            print(
                f"Created     : {incident[9]}"
            )

            print(
                f"Suspicious Extensions : {incident[10]}"
            )

            print(
                f"Status      : {incident[11]}"
            )

            print("-" * 100)

    db.close()


if __name__ == "__main__":

    main()