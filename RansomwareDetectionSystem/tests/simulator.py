import os
import sys
import time
import random


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


# ============================================================
# TEST FOLDER
# ============================================================

TEST_FOLDER = os.path.join(
    PROJECT_ROOT,
    "test_folder"
)


# ============================================================
# CONFIGURATION
# ============================================================

NUMBER_OF_FILES = 60

DELAY_BETWEEN_FILES = 0.08


# ============================================================
# CREATE TEST FOLDER
# ============================================================

def prepare_test_folder():

    os.makedirs(
        TEST_FOLDER,
        exist_ok=True
    )

    print(
        f"[SIMULATOR] Test folder:"
    )

    print(
        f"[SIMULATOR] {TEST_FOLDER}"
    )


# ============================================================
# CREATE NORMAL FILES
# ============================================================

def create_test_files():

    print()

    print(
        "[SIMULATOR] Creating test files..."
    )

    for i in range(NUMBER_OF_FILES):

        file_path = os.path.join(
            TEST_FOLDER,
            f"document_{i}.txt"
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "This is a harmless ransomware "
                "detection test file.\n"
            )

            file.write(
                f"Test file number: {i}\n"
            )

    print(
        f"[SIMULATOR] Created "
        f"{NUMBER_OF_FILES} test files."
    )


# ============================================================
# SIMULATE RAPID MODIFICATION
# ============================================================

def simulate_modifications():

    print()

    print(
        "[SIMULATOR] Simulating rapid "
        "file modifications..."
    )

    files = []

    for i in range(NUMBER_OF_FILES):

        file_path = os.path.join(
            TEST_FOLDER,
            f"document_{i}.txt"
        )

        files.append(file_path)

        with open(
            file_path,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                "Harmless simulated modification.\n"
            )

        time.sleep(
            DELAY_BETWEEN_FILES
        )

    print(
        "[SIMULATOR] Modification phase complete."
    )

    return files


# ============================================================
# SIMULATE RENAMING
# ============================================================

def simulate_renames(files):

    print()

    print(
        "[SIMULATOR] Simulating suspicious "
        "file renaming..."
    )

    renamed_files = []

    for file_path in files:

        if not os.path.exists(file_path):
            continue

        directory = os.path.dirname(
            file_path
        )

        filename = os.path.basename(
            file_path
        )

        name, extension = os.path.splitext(
            filename
        )

        new_name = (
            f"{name}.encrypted"
        )

        new_path = os.path.join(
            directory,
            new_name
        )

        os.rename(
            file_path,
            new_path
        )

        renamed_files.append(
            new_path
        )

        time.sleep(
            DELAY_BETWEEN_FILES
        )

    print(
        "[SIMULATOR] Rename phase complete."
    )

    return renamed_files


# ============================================================
# CLEANUP
# ============================================================

def cleanup():

    print()

    print(
        "[SIMULATOR] Cleaning up test files..."
    )

    if not os.path.exists(TEST_FOLDER):

        print(
            "[SIMULATOR] Nothing to clean."
        )

        return

    for filename in os.listdir(
        TEST_FOLDER
    ):

        file_path = os.path.join(
            TEST_FOLDER,
            filename
        )

        if os.path.isfile(file_path):

            try:

                os.remove(
                    file_path
                )

            except OSError as error:

                print(
                    f"[SIMULATOR] Could not remove "
                    f"{file_path}: {error}"
                )

    print(
        "[SIMULATOR] Cleanup complete."
    )


# ============================================================
# MAIN SIMULATION
# ============================================================

def main():

    print()

    print("=" * 70)

    print(
        "       SAFE RANSOMWARE BEHAVIOR SIMULATOR"
    )

    print("=" * 70)

    print()

    print(
        "This simulator only operates inside:"
    )

    print(
        TEST_FOLDER
    )

    print()

    prepare_test_folder()

    # --------------------------------------------------------
    # Create harmless files
    # --------------------------------------------------------

    create_test_files()

    time.sleep(1)

    # --------------------------------------------------------
    # Simulate rapid modifications
    # --------------------------------------------------------

    files = simulate_modifications()

    time.sleep(1)

    # --------------------------------------------------------
    # Simulate suspicious renaming
    # --------------------------------------------------------

    simulate_renames(files)

    # --------------------------------------------------------
    # Give the monitor time to process events
    # --------------------------------------------------------

    print()

    print(
        "[SIMULATOR] Waiting for detector "
        "to process events..."
    )

    time.sleep(3)

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    cleanup()

    print()

    print("=" * 70)

    print(
        "SIMULATION COMPLETED"
    )

    print("=" * 70)

    print()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
    