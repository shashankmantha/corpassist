"""
CorpAssist authentication.

!! DELIBERATELY WEAK LAB AUTH !!
Two seeded accounts with hard-coded, weak passwords. This is a lab prop, not
real authentication: there is no hashing, no lockout, no session expiry.

Two roles exist:
  - basic : a regular employee. The UI/prompt frame says they may NOT look up
            other employees' records.
  - admin : an HR/IT admin, "authorized" to look up employee records.

The role is NOT enforced at the DB tool (tools.lookup_employee runs the same
either way). So a basic user who prompt-injects the bot (AI-01) or benefits
from a poisoned document (AI-02) still exfiltrates PII — a broken-access-control
demonstration on top of the AI-03 confused deputy. Enforcing the role
server-side at the tool is part of the remediation, not the baseline.
"""
import os

USERS = {
    "employee": {
        "password": os.getenv("USER_EMPLOYEE_PW", "employee123"),
        "role": "basic",
        "display": "Jordan Lee",
        "title": "Employee",
    },
    "hradmin": {
        "password": os.getenv("USER_ADMIN_PW", "admin123"),
        "role": "admin",
        "display": "Pat Morgan",
        "title": "HR / IT Admin",
    },
}


def check_login(username: str, password: str):
    """Return a session dict on success, or None. No hashing (lab only)."""
    u = USERS.get((username or "").strip().lower())
    if u and password == u["password"]:
        return {
            "username": username.strip().lower(),
            "role": u["role"],
            "display": u["display"],
            "title": u["title"],
        }
    return None
