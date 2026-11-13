# CorpAssist

> ⚠️ **Deliberately vulnerable lab target.** An intentionally insecure internal
> RAG chatbot for an isolated COMP 324 red-team/blue-team lab. It demonstrates
> the OWASP LLM Top 10. **Isolated lab network and fake data only — never
> deploy anywhere real.**

A small internal HR/IT chatbot: local LLM (Ollama) + local RAG (Chroma) + a DB
tool wired to the over-privileged `dba_admin` account. It ships **vulnerable on
purpose**. You exploit it, then apply the remediation as a version-controlled
**patch** (see `patch/`) and retest — the blue-team detect → fix → retest loop.

| ID | Finding | Where | Patched by |
| -- | ------- | ----- | ---------- |
| AI-01 | Direct prompt injection | `app.py` — no data/instruction boundary | `patch/remediation.patch` |
| AI-02 | RAG poisoning (indirect injection) | `docs/` + `rag.py` | `patch/remediation.patch` |
| AI-03 | Excessive agency → PII leak | `tools.py` — `SELECT *` as `dba_admin` | patch + `patch/harden.sql` |
| AI-04 | Improper output handling | `app.py` — `unsafe_allow_html=True` | `patch/remediation.patch` |
| BAC   | Broken access control — role not enforced at the tool | `app.py` | patch (gates lookup to admins) |

Findings map to OWASP LLM Top 10 **2025** and MITRE ATLAS — see the As-Built Spec.

## Requirements

Docker + Compose, on a Linux host (the lab runs it on a **Lubuntu VM on
corp-net**). First run pulls the model (~4.7 GB) once, then it's cached.

## Start it (helper scripts)

```bash
./corp-assist.sh              # real lab — connects to the db-net MySQL VM (DB_HOST in .env)
./corp-assist.sh standalone   # dev / off-lab — self-contained throwaway MySQL
./corp-assist.sh stop         # stop the stack
```

The script seeds `.env` on first run, starts the stack detached, and prints the
URL, the login accounts, and the log-follow command. Open **http://localhost:8501**
(or `http://<vm-ip>:8501` from another corp-net machine).

`make up` / `make standalone` do the same if you prefer `make`.

## Deploy & update (git workflow)

The repo is the source of truth. On the deployed VM:

```bash
git clone https://github.com/shashankmantha/corpassist.git
cd corpassist
./corp-assist.sh              # first boot

# to pull updates later:
git pull && ./rebuild.sh      # rebuild the image + restart; data/ and chroma/ are preserved
```

`./rebuild.sh` (optionally `./rebuild.sh standalone`) rebuilds after any code
change. Your `.env`, chat history (`data/`), vector store (`chroma/`), and the
model cache survive pulls and rebuilds (all gitignored).

## Network

corp-net is **`192.168.50.0/24`** in this lab (not `192.168.1.0/24`, the physical
home LAN). db-net stays `172.16.0.0/24`. The app runs on corp-net and reaches the
db-net MySQL VM through pfSense's `corp→db:3306` rule.

## Accounts & chat history

The UI has a login with two **deliberately weak** lab accounts (also shown on the
login screen):

| Account | Password | Role |
| ------- | -------- | ---- |
| `employee` | `employee123` | basic employee |
| `hradmin`  | `admin123`    | HR / IT admin |

Chat history persists per user in a SQLite store under `data/` (survives
restarts). Two endpoints can connect at once — open the URL in two browsers and
sign in as each account; each keeps its own history.

The role is **not** enforced at the DB tool in the baseline, so a basic user who
prompt-injects the bot (AI-01) or benefits from a poisoned doc (AI-02) still
extracts PII — a broken-access-control demo on top of AI-03. The patch gates the
lookup to admins, closing that gap.

## Exploit → patch → retest

```bash
make smoke            # confirms the stack is up and the baseline is vulnerable
make poison           # plant the AI-02 doc + re-ingest, then ask a benign question
```

- **AI-01 / AI-03:** ask for an employee by name → SSNs returned; see `logs/tool.log`.
- **AI-02:** after `make poison`, ask "what's the PTO policy?" → mass leak.
- **AI-04:** get injected HTML into a reply and watch it render.
- **BAC:** sign in as `employee` and prompt-inject → still leaks (role not enforced).

Then remediate and retest:

```bash
make patch            # apply patch/remediation.patch (git apply)
mysql -h <db> -u root -p < patch/harden.sql   # create the read-only app_ro account
./rebuild.sh && make smoke                    # smoke now shows the leaks are closed
make unpatch          # roll the code change back if you need the vulnerable build again
```

See `patch/README.md` for what the patch changes and how to roll it back, the
**Setup & Integration Guide** for the corp-net VM placement, and the **As-Built
Spec** for the architecture and findings map.