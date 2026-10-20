from app.rules import can_transition, validate_new_ticket


def test_valid_ticket_gets_default_priority():
    clean, error = validate_new_ticket({"title": "  Card declined  "})
    assert error is None
    assert clean["title"] == "Card declined"
    assert clean["priority"] == "medium"


def test_missing_title_rejected():
    assert validate_new_ticket({})[1] == "title is required"


def test_blank_title_rejected():
    assert validate_new_ticket({"title": "   "})[1] == "title is required"


def test_overlong_title_rejected():
    assert validate_new_ticket({"title": "x" * 121})[1] is not None


def test_bad_priority_rejected():
    assert validate_new_ticket({"title": "Hi", "priority": "panic"})[1] is not None


def test_non_object_body_rejected():
    assert validate_new_ticket(["not", "an", "object"])[1] is not None


def test_allowed_and_blocked_transitions():
    assert can_transition("open", "in_progress")
    assert not can_transition("open", "resolved")
    assert not can_transition("closed", "open")
