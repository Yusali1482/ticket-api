from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from .db import get_db
from .rules import PRIORITIES, STATUSES, can_transition, validate_new_ticket

bp = Blueprint("tickets", __name__)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _error(message, status):
    return jsonify({"error": message}), status


def _fetch(ticket_id):
    return get_db().execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/tickets")
def create_ticket():
    clean, error = validate_new_ticket(request.get_json(silent=True))
    if error:
        return _error(error, 400)
    now = _now()
    db = get_db()
    cur = db.execute(
        "INSERT INTO tickets (title, description, priority, status, created_at, updated_at) "
        "VALUES (?, ?, ?, 'open', ?, ?)",
        (clean["title"], clean["description"], clean["priority"], now, now),
    )
    db.commit()
    return jsonify(dict(_fetch(cur.lastrowid))), 201


@bp.get("/tickets")
def list_tickets():
    query, params = "SELECT * FROM tickets WHERE 1=1", []
    for field, allowed in (("status", STATUSES), ("priority", PRIORITIES)):
        value = request.args.get(field)
        if value is not None:
            if value not in allowed:
                return _error(f"{field} must be one of: {', '.join(allowed)}", 400)
            query += f" AND {field} = ?"  # field comes from our own tuple, never from the user
            params.append(value)
    rows = get_db().execute(query + " ORDER BY id", params).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.get("/tickets/<int:ticket_id>")
def get_ticket(ticket_id):
    row = _fetch(ticket_id)
    if row is None:
        return _error("ticket not found", 404)
    return jsonify(dict(row))


@bp.patch("/tickets/<int:ticket_id>")
def update_ticket(ticket_id):
    row = _fetch(ticket_id)
    if row is None:
        return _error("ticket not found", 404)
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return _error("send a JSON object with status and/or priority", 400)

    status, priority = row["status"], row["priority"]
    if "priority" in data:
        if data["priority"] not in PRIORITIES:
            return _error(f"priority must be one of: {', '.join(PRIORITIES)}", 400)
        priority = data["priority"]
    if "status" in data:
        if data["status"] not in STATUSES:
            return _error(f"status must be one of: {', '.join(STATUSES)}", 400)
        if data["status"] != status and not can_transition(status, data["status"]):
            return _error(f"cannot move a ticket from {status} to {data['status']}", 409)
        status = data["status"]

    db = get_db()
    db.execute(
        "UPDATE tickets SET status = ?, priority = ?, updated_at = ? WHERE id = ?",
        (status, priority, _now(), ticket_id),
    )
    db.commit()
    return jsonify(dict(_fetch(ticket_id)))


@bp.get("/stats")
def stats():
    counts = {s: 0 for s in STATUSES}
    rows = get_db().execute("SELECT status, COUNT(*) AS n FROM tickets GROUP BY status").fetchall()
    for r in rows:
        counts[r["status"]] = r["n"]
    counts["total"] = sum(counts.values())
    return jsonify(counts)
