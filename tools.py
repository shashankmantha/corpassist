"""
CorpAssist DB tool.

!! AI-03 — EXCESSIVE AGENCY (intentional vulnerability) !!
lookup_employee() is the chatbot's one "tool". It is deliberately flawed in
three ways, each a seeded finding:
  1. It connects as `dba_admin` (DB-03) -> full access, not least privilege.
  2. It runs `SELECT *` -> returns every column, SSNs and salaries included.
  3. The `name` argument is concatenated straight into the SQL -> injectable.

Every call is logged to logs/tool.log with the exact SQL, which is the
blue-team detection signal for AI-03. The remediation is delivered later as a
patch (see patch/remediation.patch), not toggled here.
"""
import logging
import os

import mysql.connector

import config

os.makedirs(config.LOG_DIR, exist_ok=True)

_log = logging.getLogger("corpassist.tool")
if not _log.handlers:
    _log.setLevel(logging.INFO)
    _h = logging.FileHandler(os.path.join(config.LOG_DIR, "tool.log"))
    _h.setFormatter(logging.Formatter("%(asctime)s  %(message)s"))
    _log.addHandler(_h)


def lookup_employee(name: str):
    """Look up employee records by (partial) name. Returns a list of dict rows,
    or {"error": ...} on failure.

    Deliberately vulnerable: runs as dba_admin, SELECT *, string-formatted SQL.
    """
    name = (name or "").strip()

    # AI-03: SELECT * as dba_admin, with the name spliced in (SQL-injectable).
    query = (
        f"SELECT * FROM {config.DB_NAME}.employees "
        f"WHERE full_name LIKE '%{name}%'"
    )

    # Detection signal: log who ran what, verbatim.
    _log.info("lookup_employee(%r) as user=%s  SQL: %s", name, config.DB_USER, query)

    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            connection_timeout=5,
        )
    except mysql.connector.Error as exc:
        _log.info("DB connection failed: %s", exc)
        return {"error": f"database unreachable: {exc}"}

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query)          # intentionally unparameterised
        rows = cur.fetchall()
        _log.info("returned %d row(s)", len(rows))
        return rows
    except mysql.connector.Error as exc:
        _log.info("query failed: %s", exc)
        return {"error": f"query failed: {exc}"}
    finally:
        conn.close()
