"""Flask backend for the System Log Analyzer."""

import os
import logging

from flask import Flask, jsonify, render_template, request

from parser import parse_text, summarize

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def analyze_text(text):
    """Analyze log text and return parsed entries with statistics."""
    try:
        entries = parse_text(text)
        if not entries:
            logger.warning("No valid log entries found in uploaded file")
        return {"entries": entries[:5000], "stats": summarize(entries)}
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        raise


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    """Handle file upload and analyze logs."""
    if "file" not in request.files:
        logger.warning("Upload attempt with no file")
        return jsonify({"error": "No file provided"}), 400
    
    f = request.files["file"]
    if not f.filename:
        logger.warning("Upload attempt with empty filename")
        return jsonify({"error": "Empty filename"}), 400
    
    # Validate file extension
    allowed_extensions = {".log", ".txt"}
    if not any(f.filename.lower().endswith(ext) for ext in allowed_extensions):
        logger.warning(f"Upload attempt with unsupported file: {f.filename}")
        return jsonify({"error": "Only .log and .txt files are supported"}), 400
    
    try:
        raw = f.read()
        if not raw:
            return jsonify({"error": "File is empty"}), 400
        
        # Try multiple encodings
        text = None
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                text = raw.decode(enc)
                logger.info(f"Successfully decoded file with {enc}")
                break
            except (UnicodeDecodeError, AttributeError):
                continue
        
        if text is None:
            text = raw.decode("utf-8", errors="replace")
            logger.warning("Used fallback decoding with error replacement")
        
        result = analyze_text(text)
        result["filename"] = f.filename
        logger.info(f"Successfully analyzed {f.filename}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": "Failed to process file"}), 500


@app.route("/api/sample")
def sample():
    """Load and analyze sample log file."""
    try:
        sample_path = os.path.join(BASE_DIR, "sample.log")
        if not os.path.exists(sample_path):
            logger.error("Sample log file not found")
            return jsonify({"error": "Sample log file not available"}), 404
        
        with open(sample_path, encoding="utf-8") as fh:
            result = analyze_text(fh.read())
        result["filename"] = "sample.log"
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Sample endpoint error: {e}")
        return jsonify({"error": "Failed to load sample log"}), 500


@app.errorhandler(413)
def too_large(_):
    """Handle file too large errors."""
    logger.warning("File too large upload attempt")
    return jsonify({"error": "File too large (max 10 MB)"}), 413


@app.errorhandler(404)
def not_found(_):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(_):
    """Handle 500 errors."""
    logger.error("Internal server error")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("Starting System Log Analyzer on http://localhost:5000")
    app.run(debug=True, port=5000)
