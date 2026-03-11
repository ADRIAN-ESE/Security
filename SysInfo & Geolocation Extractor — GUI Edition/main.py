"""main.py — Entry point for the SysInfo & Geolocation Extractor GUI."""

import sys
import os

# Allow imports from this directory
sys.path.insert(0, os.path.dirname(__file__))

from app import SysInfoApp

if __name__ == "__main__":
    app = SysInfoApp()
    app.mainloop()
