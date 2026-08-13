from flask import (
    Flask,
    render_template,
    jsonify,
    abort
)

import os
import sys


# ==========================================================
# PROJECT PATH
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(
        0,
        BASE_DIR
    )


# ==========================================================
# DATABASE IMPORT
# ==========================================================

from database.security_database import SecurityDatabase


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(
    __name__,
    template_folder="templates"
)


# ==========================================================
# DATABASE HELPER
# ==========================================================

def get_database():

    return SecurityDatabase()


# ==========================================================
# DASHBOARD
# ==========================================================

@app.route("/")
def dashboard():

    db = get_database()

    statistics = db.get_statistics()

    recent_incidents = (
        db.get_recent_incidents(20)
    )

    recent_events = (
        db.get_recent_events(50)
    )

    return render_template(
        "dashboard.html",

        total_events=statistics[
            "total_events"
        ],

        total_incidents=statistics[
            "total_incidents"
        ],

        recent_incidents=recent_incidents,

        recent_events=recent_events
    )


# ==========================================================
# INCIDENT DETAILS PAGE
# ==========================================================

@app.route("/incident/<int:incident_id>")
def incident_details(incident_id):

    db = get_database()

    incident = db.get_incident(
        incident_id
    )

    if incident is None:

        abort(
            404,
            description=(
                f"Incident #{incident_id} "
                "was not found."
            )
        )

    return render_template(
        "incident.html"
    )


# ==========================================================
# INCIDENT API
# ==========================================================

@app.route(
    "/api/incidents/<int:incident_id>"
)
def incident_api(incident_id):

    db = get_database()

    incident = db.get_incident(
        incident_id
    )

    if incident is None:

        return jsonify({
            "error": "Incident not found",
            "incident_id": incident_id
        }), 404

    return jsonify(incident)


# ==========================================================
# ALL INCIDENTS API
# ==========================================================

@app.route("/api/incidents")
def incidents_api():

    db = get_database()

    incidents = (
        db.get_recent_incidents(100)
    )

    result = []

    for incident in incidents:

        result.append({

            "id": incident[0],

            "timestamp": incident[1],

            "incident_type": incident[2],

            "score": incident[3],

            "risk_level": incident[4],

            "total_events": incident[5],

            "modified": incident[6],

            "renamed": incident[7],

            "deleted": incident[8],

            "created": incident[9],

            "reasons": incident[10],

            "status": incident[11]
        })

    return jsonify({
        "count": len(result),
        "incidents": result
    })


# ==========================================================
# DASHBOARD STATISTICS API
# ==========================================================

@app.route("/api/stats")
def statistics_api():

    db = get_database()

    statistics = db.get_statistics()

    return jsonify(
        statistics
    )


# ==========================================================
# RECENT EVENTS API
# ==========================================================

@app.route("/api/events")
def events_api():

    db = get_database()

    events = (
        db.get_recent_events(100)
    )

    result = []

    for event in events:

        result.append({

            "id": event[0],

            "timestamp": event[1],

            "event_type": event[2],

            "file_path": event[3],

            "score": event[4],

            "risk_level": event[5]
        })

    return jsonify({
        "count": len(result),
        "events": result
    })


# ==========================================================
# ERROR HANDLERS
# ==========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "error": "Resource not found",
        "message": str(error)
    }), 404


@app.errorhandler(500)
def internal_error(error):

    return jsonify({
        "error": "Internal server error",
        "message": str(error)
    }), 500


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print(" RANSOMWARE DETECTION SYSTEM")
    print("=" * 60)
    print()
    print(" Dashboard:")
    print(" http://127.0.0.1:5000/")
    print()
    print(" Incident example:")
    print(" http://127.0.0.1:5000/incident/1")
    print()
    print(" API:")
    print(" http://127.0.0.1:5000/api/incidents")
    print()
    print("=" * 60)
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )