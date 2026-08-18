"""Configuration settings for the Log Analyzer application."""

import os

# Flask Configuration
DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"
HOST = os.getenv("FLASK_HOST", "localhost")
PORT = int(os.getenv("FLASK_PORT", 5000))

# Upload Configuration
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".log", ".txt"}

# Log Parsing Configuration
MAX_ENTRIES_DISPLAY = 5000
PAGE_SIZE = 12
SYSLOG_YEAR = None  # None means use current year

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
