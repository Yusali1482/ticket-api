"""Business rules, kept free of Flask and the database so they are easy to test."""

PRIORITIES = ("low", "medium", "high", "urgent")
STATUSES = ("open", "in_progress", "resolved", "closed")

# A ticket can only move along these paths.
TRANSITIONS = {
    "open": {"in_progress", "closed"},
    "in_progress": {"resolved", "open"},
    "resolved": {"closed", "in_progress"},
    "closed": set(),
}

MAX_TITLE = 120


def validate_new_ticket(data):
    """Return (clean_data, error). Exactly one of the two is None."""
    if not isinstance(data, dict):
        return None, "request body must be a JSON object"
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return None, "title is required"
    title = title.strip()
    if len(title) > MAX_TITLE:
        return None, f"title must be {MAX_TITLE} characters or fewer"
    description = data.get("description", "")
    if not isinstance(description, str):
        return None, "description must be text"
    priority = data.get("priority", "medium")
    if priority not in PRIORITIES:
        return None, f"priority must be one of: {', '.join(PRIORITIES)}"
    return {"title": title, "description": description, "priority": priority}, None


def can_transition(current, new):
    return new in TRANSITIONS.get(current, set())
