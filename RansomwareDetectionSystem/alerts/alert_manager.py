from datetime import datetime


class AlertManager:

    def __init__(self):

        self.last_alert_level = None

    def check_risk(self, result):

        risk_level = result["risk_level"]

        if risk_level in ["HIGH", "CRITICAL"]:

            if risk_level != self.last_alert_level:

                self.generate_alert(result)

                self.last_alert_level = risk_level

        else:

            self.last_alert_level = None

    def generate_alert(self, result):

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        print()
        print("=" * 75)
        print("🚨 RANSOMWARE SECURITY ALERT")
        print("=" * 75)

        print(f"Time       : {timestamp}")
        print(f"Risk Level : {result['risk_level']}")
        print(f"Risk Score : {result['score']}/100")

        print()
        print("Suspicious behavior:")

        if result["reasons"]:

            for reason in result["reasons"]:

                print(f"  • {reason}")

        else:

            print("  • No specific reason recorded")

        print()
        print("Activity statistics:")

        print(
            f"  Modified files : "
            f"{result['modified']}"
        )

        print(
            f"  Renamed files  : "
            f"{result['renamed']}"
        )

        print(
            f"  Deleted files  : "
            f"{result['deleted']}"
        )

        print(
            f"  Created files  : "
            f"{result['created']}"
        )

        print(
            f"  Suspicious extensions : "
            f"{result['suspicious_extensions']}"
        )

        print()

        print(
            "ACTION: Investigate the affected "
            "system immediately."
        )

        print("=" * 75)
        print()