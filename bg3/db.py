""" A small local database (SQLite) of leaderboard runs: every saved ranking with the full spec of each build in it, so rankings can be
    compared over time and any build rebuilt from its fingerprint.

    PERSONAL DATA: local_data/bg3.sqlite is committed on purpose, this is a single user tool. Before making the repository public, add
    local_data/ to .gitignore and remove the file from git (git rm --cached local_data/bg3.sqlite).

    Tables
      builds   fingerprint (primary key), name, spec (one line), build (JSON), first_seen
      runs     id, created, label, kind ('examples' from python -m bg3.leaderboard, 'party' from the planner), commit, settings (JSON)
      results  run_id, key (name|source|variant), name, source, variant, fingerprint, entry (JSON: damage by scenario@enemies and act, AC, score)
"""
import json
import sqlite3
import subprocess
from contextlib import closing
from datetime import datetime
from pathlib import Path

PATH = Path(__file__).parent.parent / "local_data" / "bg3.sqlite"
SCHEMA = """
CREATE TABLE IF NOT EXISTS builds (fingerprint TEXT PRIMARY KEY, name TEXT, spec TEXT, build TEXT, first_seen TEXT);
CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, label TEXT, kind TEXT, git_commit TEXT, settings TEXT);
CREATE TABLE IF NOT EXISTS results (run_id INTEGER REFERENCES runs(id), key TEXT, name TEXT, source TEXT, variant TEXT, fingerprint TEXT, entry TEXT);
CREATE INDEX IF NOT EXISTS results_run ON results(run_id);
"""

def connect(path=None):
    path = Path(path or PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    return db

def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True,
                              cwd=Path(__file__).parent).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""

def save_run(entries, builds, kind, label="", settings=None, path=None):
    """ Saves entries (leaderboard rows) and their builds ({fingerprint: Bg3Build}); returns the run id """
    now = datetime.now().isoformat(timespec="seconds")
    with closing(connect(path)) as db, db:
        cursor = db.execute("INSERT INTO runs (created, label, kind, git_commit, settings) VALUES (?, ?, ?, ?, ?)",
                            (now, label, kind, git_commit(), json.dumps(settings or {})))
        run_id = cursor.lastrowid
        for fp, build in builds.items():
            spec = next((e["spec"] for e in entries if e["fingerprint"] == fp), "")
            db.execute("INSERT OR IGNORE INTO builds (fingerprint, name, spec, build, first_seen) VALUES (?, ?, ?, ?, ?)",
                       (fp, build.name, spec, json.dumps(build.to_dict()), now))
        db.executemany("INSERT INTO results (run_id, key, name, source, variant, fingerprint, entry) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       [(run_id, f"{e['name']}|{e['source']}|{e.get('variant', 'planned')}", e["name"], e["source"], e.get("variant", "planned"),
                         e["fingerprint"], json.dumps(e)) for e in entries])
    return run_id

def runs(kind=None, path=None):
    """ [{id, created, label, kind, commit, count}] newest first """
    if not Path(path or PATH).exists():
        return []
    with closing(connect(path)) as db:
        rows = db.execute("SELECT r.id, r.created, r.label, r.kind, r.git_commit, COUNT(x.key) FROM runs r LEFT JOIN results x ON x.run_id = r.id "
                          + ("WHERE r.kind = ? " if kind else "") + "GROUP BY r.id ORDER BY r.id DESC", (kind,) if kind else ()).fetchall()
    return [{"id": i, "created": c, "label": lab, "kind": k, "commit": g, "count": n} for i, c, lab, k, g, n in rows]

def load_run(run_id, path=None):
    """ The run's entries """
    if not Path(path or PATH).exists():
        return []
    with closing(connect(path)) as db:
        return [json.loads(e) for (e,) in db.execute("SELECT entry FROM results WHERE run_id = ?", (run_id,))]

def latest(kind, path=None):
    found = runs(kind, path)
    return (found[0], load_run(found[0]["id"], path)) if found else (None, [])

def build_by_fingerprint(fingerprint, path=None):
    """ The saved build (a dict) for a fingerprint, or None """
    if not Path(path or PATH).exists():
        return None
    with closing(connect(path)) as db:
        row = db.execute("SELECT build FROM builds WHERE fingerprint = ?", (fingerprint,)).fetchone()
    return json.loads(row[0]) if row else None
