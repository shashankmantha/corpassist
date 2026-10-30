# CorpAssist remediation patch

Apply this **after** the exploit demo to close all four findings, then retest.
It is the blue-team "fix" half of detect → fix → retest.

## What's in here

- `remediation.patch` — the code fix (unified diff for `config.py`, `tools.py`, `app.py`).
- `harden.sql` — the DB fix: creates the read-only, column-scoped `app_ro` account.

## What it changes

| Finding | Fix |
| ------- | --- |
| AI-03 Excessive agency | tool connects as read-only `app_ro`, returns only `full_name, email, department, clearance_level` (no ssn/salary), **parameterised** query (no SQLi) |
| AI-01 Direct injection | system prompt labels retrieved material as untrusted DATA; tool fires only on the user's own request |
| AI-02 RAG poisoning | retrieved context is sanitised (instruction-like lines stripped) and delimited in `<context>` tags |
| AI-04 Improper output | reply rendered escaped (no `unsafe_allow_html`) |
| Broken access control | the employee lookup is gated to the `admin` role (basic users can no longer trigger it, even via injection) |

## Apply

```bash
# 1. code
git apply patch/remediation.patch          # or: make patch

# 2. database (real lab — run against the db-net MySQL VM)
mysql -h 172.16.0.10 -u root -p < patch/harden.sql
#    standalone: mysql -h 127.0.0.1 -u root -p < patch/harden.sql

# 3. rebuild + retest
docker compose up --build
make smoke          # the AI-03 / end-to-end checks should now report NO leak
```

With `app_ro` in place the patched tool authenticates as a least-privilege user;
the `.env`/compose defaults for `DB_USER`/`DB_PASSWORD` are updated by the patch
to `app_ro`, so no manual env change is needed (override in `.env` if you renamed
the account).

## Roll back (return to the vulnerable build)

```bash
git apply -R patch/remediation.patch        # or: make unpatch
docker compose up --build
```

The `app_ro` DB account is harmless to leave in place; to fully revert the DB,
`DROP USER 'app_ro'@'%';`.

## Capturing before/after evidence

Run `make smoke` (and the manual demos) once **before** applying — that's your
"before": leaks fire, `logs/tool.log` shows `dba_admin` + `SELECT *`. Apply, then
run the same checks for the "after": no PII returned, `logs/tool.log` shows
`app_ro` + a parameterised, column-scoped query. The two log sets are your M6
remediation proof.
