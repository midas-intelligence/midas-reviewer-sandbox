# midas-reviewer-sandbox

A small notes service used as a target for the Midas reviewer. The code is invented; nothing here
talks to a real system.

## Layout

    app/          Python API (FastAPI) over a SQLite data layer
      config.py   settings from the environment
      db.py       schema and connections
      security.py password hashing, bearer tokens, the role ladder
      services/   users and notes, and the access rules
      routers/    HTTP edge
    tests/        service tests, standard library only
    web/          TypeScript client (types, fetch wrapper, hooks, components)

## Run the API

    export NOTES_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
    pip install -r requirements.txt
    uvicorn app.main:app --reload

    curl -s localhost:8000/healthz

## Test

    python3 -m unittest discover -s tests

The service layer has no third-party imports, so the tests run without installing anything.

## Model

Users own notes. A note is `private`, `shared` or `public`. The owner can share a note with another
user at `viewer` or `editor`. Roles sit on a ladder: `viewer < editor < owner`.
