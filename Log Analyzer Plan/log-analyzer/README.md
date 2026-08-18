# System Log Analyzer

A Flask-based web application for analyzing and visualizing system logs in real-time.

## Features

- **Multi-format Support**: Parses syslog, Apache/Nginx access logs, and generic level-tagged logs
- **Interactive Dashboard**: Real-time statistics, charts, and filtered log viewing
- **Smart Filtering**: Filter by log level, search messages and sources
- **Statistics**: Error rates, timeline analysis, top errors, and source tracking
- **Dark Theme UI**: Modern, responsive design with Chart.js visualizations
- **File Upload**: Support for local log files (up to 10 MB)
- **Sample Data**: Pre-loaded sample logs for quick testing

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

### Upload Options
- **Drop files** onto the upload zone
- **Click** to browse and select files
- **Load Sample** for demo data

## Supported Log Formats

### Syslog
```
Aug 18 10:23:01 hostname process[pid]: message
```

### Apache/Nginx Access Logs
```
192.168.1.1 - - [18/Aug/2026:10:23:01 +0000] "GET /path HTTP/1.1" 200 1234
```

### Generic ISO/Generic Format
```
2026-08-18T10:23:01 [ERROR] message
2026-08-18 10:23:01 [WARNING] message
```

## Configuration

- **MAX_CONTENT_LENGTH**: Maximum file upload size (default: 10 MB)
- **PAGE_SIZE**: Entries per page in the table (default: 12, in app.js)
- **PORT**: Flask development port (default: 5000)

## API Endpoints

- `GET /` - Main dashboard
- `POST /api/upload` - Upload and analyze log file
- `GET /api/sample` - Load sample log data

## Architecture

- **Backend**: Flask (Python)
  - `app.py` - Flask application and API endpoints
  - `parser.py` - Log parsing engine

- **Frontend**: Vanilla JavaScript
  - `app.js` - Dashboard logic and interactivity
  - `style.css` - Dark theme styling
  - `index.html` - HTML structure

## Limitations

- Maximum 5000 entries displayed per upload
- File must be readable as UTF-8 or Latin-1
- Year detection in syslog uses current system year

## Future Enhancements

- [ ] Export functionality (CSV, JSON)
- [ ] Advanced filtering and regex support
- [ ] Log tailing for real-time monitoring
- [ ] Database storage for log history
- [ ] User authentication
- [ ] CSRF protection
- [ ] API rate limiting
