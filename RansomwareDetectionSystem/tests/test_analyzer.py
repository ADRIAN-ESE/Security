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

# Add project root to Python import path
sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORT ANALYZER
# ============================================================

from detector.analyzer import BehaviorAnalyzer


# ============================================================
# TEST FUNCTION
# ============================================================

def main():

    analyzer = BehaviorAnalyzer()

    print()
    print("=" * 70)
    print("          RANSOMWARE BEHAVIOR ANALYZER TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # TEST 1 — NORMAL ACTIVITY
    # --------------------------------------------------------

    print()
    print("[TEST 1] Normal file activity")

    result = analyzer.record_event(
        "created",
        "test.txt"
    )

    print(
        f"Risk Level : {result['risk_level']}"
    )

    print(
        f"Risk Score : {result['score']}/100"
    )

    # --------------------------------------------------------
    # TEST 2 — RAPID MODIFICATIONS
    # --------------------------------------------------------

    print()
    print("[TEST 2] Rapid file modifications")

    for i in range(15):

        result = analyzer.record_event(
            "modified",
            f"document_{i}.txt"
        )

    print(
        f"Risk Level : {result['risk_level']}"
    )

    print(
        f"Risk Score : {result['score']}/100"
    )

    print(
        f"Modified   : {result['modified']}"
    )

    print(
        f"Reasons    : {result['reasons']}"
    )

    # --------------------------------------------------------
    # TEST 3 — MASS MODIFICATIONS
    # --------------------------------------------------------

    print()
    print("[TEST 3] Mass file modifications")

    for i in range(50):

        result = analyzer.record_event(
            "modified",
            f"important_{i}.txt"
        )

    print(
        f"Risk Level : {result['risk_level']}"
    )

    print(
        f"Risk Score : {result['score']}/100"
    )

    print(
        f"Modified   : {result['modified']}"
    )

    print(
        f"Reasons    : {result['reasons']}"
    )

    # --------------------------------------------------------
    # TEST 4 — SUSPICIOUS EXTENSIONS
    # --------------------------------------------------------

    print()
    print("[TEST 4] Suspicious file extensions")

    for i in range(5):

        result = analyzer.record_event(
            "renamed",
            f"document_{i}.encrypted"
        )

    print(
        f"Risk Level : {result['risk_level']}"
    )

    print(
        f"Risk Score : {result['score']}/100"
    )

    print(
        f"Suspicious extensions : "
        f"{result['suspicious_extensions']}"
    )

    print(
        f"Reasons : {result['reasons']}"
    )

    # --------------------------------------------------------
    # FINISHED
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)
    print()


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()