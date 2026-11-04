#!/usr/bin/env python3
"""Validate verdicts and keep a local, transactional review history."""
from __future__ import annotations

import argparse
from contextlib import closing, contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys

import direction_core as core

SCHEMA = """
CREATE TABLE IF NOT EXISTS project(revision INTEGER NOT NULL);
INSERT INTO project SELECT 0 WHERE NOT EXISTS(SELECT 1 FROM project);
CREATE TABLE IF NOT EXISTS reviews(
 id TEXT PRIMARY KEY, report TEXT NOT NULL, report_sha TEXT NOT NULL,
 requirements TEXT NOT NULL, requirements_sha TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('formal','legacy')),
 verdict TEXT NOT NULL, implied TEXT NOT NULL,
 direction REAL NOT NULL, outlook REAL, tier TEXT
);
CREATE TABLE IF NOT EXISTS decisions(
 revision INTEGER PRIMARY KEY, review TEXT NOT NULL REFERENCES reviews(id),
 verdict TEXT NOT NULL, decided_on TEXT NOT NULL, reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS conditions(
 review TEXT NOT NULL REFERENCES reviews(id), id TEXT NOT NULL,
 deadline TEXT NOT NULL, description TEXT NOT NULL,
 resolved_on TEXT, evidence TEXT,
 PRIMARY KEY(review,id)
);
PRAGMA user_version=1;
"""
IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_date(value):
    if not core.valid_date(value):
        raise ValueError("Use an explicit valid YYYY-MM-DD date.")
    return value


def within(project, name):
    path = (project / name).resolve(strict=True)
    if not path.is_relative_to(project) or not path.is_file():
        raise ValueError("Select a regular file inside the project.")
    return path


def db_path(project):
    folder = project / ".idea-triage"
    path = folder / "state.sqlite3"
    if folder.is_symlink() or path.is_symlink():
        raise ValueError("The state directory and database must not be symlinks.")
    return path


@contextmanager
def connection(project, *, write=False, create=False):
    path = db_path(project)
    if create:
        path.parent.mkdir(mode=0o700, exist_ok=True)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(fd)
    uri = path.as_uri() + ("?mode=rw" if write else "?mode=ro")
    with closing(sqlite3.connect(uri, uri=True, timeout=5)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        with conn:
            conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if create and version == 0:
                if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table'").fetchone():
                    raise ValueError("Unknown database. Restore or select a different project.")
                for statement in SCHEMA.split(";"):
                    if statement.strip():
                        conn.execute(statement)
                version = 1
            if version != 1:
                raise ValueError(f"Unsupported database version: {version}")
            yield conn


def analyze(path, require_outlook):
    d = core.parse(path)
    errors = core.validate(d)
    if require_outlook and not d["outlook"]:
        errors.append("A formal review requires the second axis (outlook).")
    if errors:
        raise ValueError("\n".join(errors))
    conditions = review_conditions(d) if require_outlook else []
    direction, _ = core.weighted_total(d)
    implied = core.implied_verdict(direction)
    outlook, _ = core.outlook_score(d)
    tier = core.investment_tier(implied, outlook)[0] if outlook is not None else None
    return conditions, {
        "verdict": d["verdict"], "implied": implied, "direction": direction,
        "outlook": outlook, "tier": tier, "conflict": d["verdict"] != implied,
    }


def review_conditions(doc):
    conditions = []
    seen = set()
    for description in doc["conditions"]:
        match = re.search(r"\bid:\s*[\"']?([A-Za-z0-9_.-]+)", description)
        deadline = re.search(r"\bdeadline:\s*[\"']?(\d{4}-\d{2}-\d{2})\b", description)
        if not match or not IDENT.fullmatch(match[1]) or not deadline or match[1] in seen:
            raise ValueError("Each condition needs a unique stable id and valid deadline.")
        seen.add(match[1])
        conditions.append((match[1], check_date(deadline[1]), description))
    return conditions


def register(project, args):
    if not IDENT.fullmatch(args.id):
        raise ValueError("Invalid review id.")
    report = within(project, args.report)
    req_name = args.requirements
    if req_name is None and not args.legacy:
        req_name = Path("requirements.md")
    requirements = within(project, req_name) if req_name is not None else None
    requirements_sha = sha(requirements) if requirements is not None else ""
    if not args.legacy and args.requirements_sha != requirements_sha:
        raise ValueError("Requirements changed or no input snapshot was supplied.")
    report_sha = sha(report)
    conditions, result = analyze(report, require_outlook=not args.legacy)
    if sha(report) != report_sha or (requirements is not None and sha(requirements) != requirements_sha):
        raise ValueError("Report or requirements changed during validation. Read them again.")
    values = (
        args.id, report.relative_to(project).as_posix(), report_sha,
        requirements.relative_to(project).as_posix() if requirements is not None else "",
        requirements_sha,
        "legacy" if args.legacy else "formal",
        *(result[k] for k in ("verdict", "implied", "direction", "outlook", "tier")),
    )
    with connection(project, write=True, create=True) as conn:
        existing = conn.execute("SELECT * FROM reviews WHERE id=?", (args.id,)).fetchone()
        if existing and tuple(existing) != values:
            raise ValueError("Review id already refers to different content.")
        if not existing:
            conn.execute("INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?,?,?,?)", values)
            conn.executemany(
                "INSERT INTO conditions(review,id,deadline,description) VALUES (?,?,?,?)",
                [(args.id, *condition) for condition in conditions],
            )
    return {"id": args.id, "duplicate": bool(existing), **result}, 0


def revision(conn):
    return conn.execute("SELECT revision FROM project").fetchone()[0]


def current(conn):
    return conn.execute("""
        SELECT d.revision,d.verdict AS decided,d.decided_on,d.reason,r.*
        FROM decisions d JOIN reviews r ON r.id=d.review
        ORDER BY d.revision DESC LIMIT 1
    """).fetchone()


def changed_files(project, review):
    changed = []
    for role in ("report", "requirements"):
        try:
            if sha(within(project, review[role])) != review[role + "_sha"]:
                changed.append(role)
        except (OSError, ValueError):
            changed.append(role)
    return changed


def status(project, args):
    as_of = check_date(args.as_of) if args.cmd == "due" else None
    if not db_path(project).exists():
        if as_of is not None:
            return {"revision": 0, "current": None, "state": "no_decision"}, 1
        return {"revision": 0, "current": None, "reviews": [], "decisions": [], "conditions": []}, 0
    with connection(project) as conn:
        rev = revision(conn)
        row = current(conn)
        if args.cmd == "status":
            reviews = [dict(x) for x in conn.execute(
                "SELECT id,report,kind,verdict,implied,direction,outlook,tier FROM reviews ORDER BY id"
            )]
            decisions = [dict(x) for x in conn.execute("SELECT * FROM decisions ORDER BY revision")]
            conditions = [dict(x) for x in conn.execute("SELECT * FROM conditions ORDER BY review,id")]
            selected = dict(row) if row else None
            if selected:
                selected["changed_files"] = changed_files(project, row)
            return {
                "revision": rev, "current": selected, "reviews": reviews,
                "decisions": decisions, "conditions": conditions,
            }, 0
        if not row:
            return {"revision": rev, "current": None, "state": "no_decision"}, 1
        changed = changed_files(project, row)
        if changed:
            return {"revision": rev, "current": row["id"], "state": "stale", "changed_files": changed}, 1
        overdue = []
        if row["decided"] == "conditional-go":
            overdue = [dict(x) for x in conn.execute(
                "SELECT id,deadline,description FROM conditions WHERE review=? "
                "AND resolved_on IS NULL AND deadline<=? ORDER BY deadline,id", (row["id"], as_of),
            )]
        return {
            "revision": rev, "current": row["id"],
            "state": "overdue" if overdue else "no_overdue", "overdue": overdue,
        }, int(bool(overdue))


def update(project, args):
    when = check_date(args.date)
    note = args.reason.strip()
    if not note:
        raise ValueError("Record the user's decision or the evidence for resolving the condition.")
    with connection(project, write=True) as conn:
        rev = revision(conn)
        if rev != args.expect:
            raise ValueError("Project revision changed. Run status and review the change.")
        if args.cmd == "decide":
            review = conn.execute("SELECT * FROM reviews WHERE id=?", (args.id,)).fetchone()
            if not review or review["kind"] != "formal" or changed_files(project, review):
                raise ValueError("The review is missing, historical, or no longer matches its inputs.")
            verdict = args.verdict or review["verdict"]
            if verdict == "conditional-go" and not conn.execute(
                "SELECT 1 FROM conditions WHERE review=?", (args.id,)
            ).fetchone():
                raise ValueError("Conditional decisions require recorded conditions.")
            conn.execute("INSERT INTO decisions VALUES (?,?,?,?,?)", (rev + 1, args.id, verdict, when, note))
        else:
            row = current(conn)
            if not row or row["decided"] != "conditional-go" or changed_files(project, row):
                raise ValueError("No current conditional decision matching the project inputs.")
            result = conn.execute(
                "UPDATE conditions SET resolved_on=?,evidence=? WHERE review=? AND id=? AND resolved_on IS NULL",
                (when, note, row["id"], args.id),
            )
            if result.rowcount != 1:
                raise ValueError("Condition not found or already resolved.")
        conn.execute("UPDATE project SET revision=?", (rev + 1,))
    return {"revision": rev + 1}, 0


def backup(project, args):
    target = args.out.absolute()
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with connection(project) as src, closing(sqlite3.connect(target)) as dst:
            src.backup(dst)
    except BaseException:
        target.unlink()
        raise
    return {"backup": str(target)}, 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path("."))
    subs = parser.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "tier"):
        sub = subs.add_parser(name)
        sub.add_argument("report", type=Path)
    sub = subs.add_parser("register")
    sub.add_argument("id")
    sub.add_argument("report", type=Path)
    sub.add_argument("--requirements", type=Path)
    sub.add_argument("--requirements-sha")
    sub.add_argument("--legacy", action="store_true")
    subs.add_parser("snapshot").add_argument("requirements", type=Path)
    subs.add_parser("status")
    subs.add_parser("due").add_argument("--as-of", required=True)
    subs.add_parser("backup").add_argument("out", type=Path)
    for name in ("decide", "resolve"):
        sub = subs.add_parser(name)
        sub.add_argument("id")
        sub.add_argument("--expect", type=int, required=True)
        sub.add_argument("--date", required=True)
        sub.add_argument("--reason", required=True)
        if name == "decide":
            sub.add_argument("--verdict", choices=sorted(core.VERDICTS))
    args = parser.parse_args()
    try:
        project = args.project.resolve(strict=True)
        if not project.is_dir():
            raise ValueError("Project must be a directory.")
        if args.cmd in {"validate", "tier"}:
            _, result = analyze(within(project, args.report), require_outlook=args.cmd == "tier")
            rc = int(result["conflict"] and args.cmd == "tier")
        elif args.cmd == "snapshot":
            result, rc = {"sha256": sha(within(project, args.requirements))}, 0
        else:
            handler = {
                "register": register, "status": status, "due": status,
                "decide": update, "resolve": update, "backup": backup,
            }[args.cmd]
            result, rc = handler(project, args)
    except (OSError, ValueError, sqlite3.Error) as error:
        print(error, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
