# Log Analyzer - Development & Testing Guide

## Local Development Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation Steps

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # OR
   source venv/bin/activate      # On macOS/Linux
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the application:**
   - Open browser to `http://localhost:5000`

## Configuration

Edit `config.py` to customize:
- `PORT`: Server port (default: 5000)
- `HOST`: Server host (default: localhost)
- `DEBUG`: Debug mode (default: True)
- `MAX_UPLOAD_SIZE`: File size limit (default: 10 MB)
- `MAX_ENTRIES_DISPLAY`: Max entries shown per file (default: 5000)

## Testing

### Manual Testing
1. Use the "Load Sample" button to test with sample.log
2. Upload custom log files via the drag-and-drop interface
3. Test filters, search, and pagination

### Log Files to Test
- **Syslog Format**: System logs from `/var/log/syslog`
- **Apache Logs**: Access logs from `/var/log/apache2/access.log`
- **Generic Logs**: Any timestamped log with level indicators

## Troubleshooting

### "File too large" error
- Maximum file size is 10 MB (configurable in app.py)
- Try uploading a smaller portion of your log

### "Failed to process file" error
- Log file encoding must be UTF-8, Latin-1, or CP1252
- Check that file has valid text content

### Charts not displaying
- Requires Chart.js library (loaded from CDN)
- Check browser console for JavaScript errors

### No entries parsed
- Verify log format matches one of the supported formats
- Check that timestamps and levels are recognizable

## Performance Notes

- Frontend displays maximum 5000 entries per upload
- Pagination shows 12 entries per page by default
- Filtering/search is performed client-side
- Large files (>5MB) may be slow to process

## Browser Compatibility

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- IE11: Not supported (Chart.js incompatibility)

## Deployment

For production:
1. Set `DEBUG = False` in config.py
2. Use a production WSGI server (gunicorn, waitress)
3. Set proper logging levels
4. Configure proper file upload security

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
