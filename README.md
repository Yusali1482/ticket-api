# Support Ticket API

A REST API for tracking customer support tickets, built with Python, Flask and SQLite.

I work in customer service, so I built the tool I know the workflow of: tickets
come in, get picked up, get resolved and get closed - and they are not allowed
to skip steps.

## Endpoints

| Method | Path | What it does |
|--------|------|--------------|
| GET | `/health` | Liveness check |
| POST | `/tickets` | Create a ticket (`title` required, `priority` optional) |
| GET | `/tickets` | List tickets, optionally `?status=open&priority=high` |
| GET | `/tickets/<id>` | Fetch one ticket |
| PATCH | `/tickets/<id>` | Change `status` and/or `priority` |
| GET | `/stats` | Ticket counts by status |

## Status workflow

```
open -> in_progress -> resolved -> closed
  \________________________________/
```

`open` can also go straight to `closed`, and `in_progress` can return to `open`.
Anything else - such as `open -> resolved`, or reopening a `closed` ticket -
returns **409 Conflict**.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## Try it

```bash
curl -X POST localhost:5000/tickets -H "Content-Type: application/json" \
     -d '{"title": "Card declined abroad", "priority": "high"}'

curl -X PATCH localhost:5000/tickets/1 -H "Content-Type: application/json" \
     -d '{"status": "in_progress"}'

curl localhost:5000/stats
```

## Run the tests

```bash
pytest -v
```

19 tests cover validation, the status workflow, filtering, 404/400/409 responses
and a SQL-injection attempt. They run on every push via GitHub Actions.

## Design decisions

- **Business rules live in `rules.py`**, separate from Flask and the database,
  so they can be unit tested on their own.
- **Parameterised SQL everywhere** - user input is never concatenated into a query.
- **App factory (`create_app`)** so each test gets its own throwaway database.
- **Meaningful status codes**: 400 for bad input, 404 for unknown tickets,
  409 for a valid request that breaks the workflow.
- Uses made-up data only - never real customer information.

## What I'd improve next

- Authentication, so only agents can change tickets
- An SLA field that flags tickets open longer than their priority allows
- Pagination on `GET /tickets`
- Move from SQLite to PostgreSQL
