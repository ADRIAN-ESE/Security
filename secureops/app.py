"""
SecureOps Dashboard — Web Interface

Run with:
    pip install -r requirements.txt
    python app.py

Then open http://localhost:5000
"""

import secrets

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO

from core import SecureOpsDashboard

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

dashboard = SecureOpsDashboard()


@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/snapshot')
def api_snapshot():
    return jsonify(dashboard.get_snapshot())


@app.route('/api/events')
def api_events():
    """Decrypted event history. ?limit=N, ?decrypt=false for raw ciphertext."""
    limit = request.args.get('limit', 50, type=int)
    decrypt = request.args.get('decrypt', 'true').lower() != 'false'
    return jsonify(dashboard.encrypted_store.retrieve_events(limit=limit, decrypt=decrypt))


@socketio.on('connect')
def handle_connect():
    socketio.emit('initial_data', dashboard.get_snapshot())


def broadcast_update(event, threat, record):
    socketio.emit('new_event', {
        'event': event.to_dict(),
        'threat': threat,
        'record_nonce': record.nonce
    })


dashboard.subscribe(broadcast_update)


if __name__ == '__main__':
    dashboard.start_monitoring()
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
    finally:
        dashboard.stop()
