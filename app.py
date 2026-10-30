"""
CorpAssist — internal HR/IT assistant (Streamlit UI).

!! DELIBERATELY VULNERABLE LAB TARGET — isolated COMP 324 lab only !!

Seeded findings (vulnerable by design; fixed later via patch/):
  AI-01  Direct prompt injection — user text + retrieved context in ONE prompt.
  AI-02  RAG poisoning — a planted doc in docs/ hijacks the answer.
  AI-03  Excessive agency — the tool runs as dba_admin and returns SSNs.
  AI-04  Improper output handling — reply rendered with unsafe_allow_html=True.

Identity (lab prop): two weak accounts, a basic employee and an HR/IT admin
(see auth.py). The role is NOT enforced at the DB tool, so a basic user who
injects the bot still extracts PII — a broken-access-control demonstration.

Chat history persists per user in a SQLite store (history.py).
Prompts/responses log to logs/chat.log (detection signal for AI-01).

answer() lives at module scope so the smoke test can import and call it.
"""
import logging
import os
import re

import ollama
import streamlit as st

import auth
import config
import history
import rag
import tools

# --- logging (blue-team telemetry) -------------------------------------------
os.makedirs(config.LOG_DIR, exist_ok=True)
_chat_log = logging.getLogger("corpassist.chat")
if not _chat_log.handlers:
    _chat_log.setLevel(logging.INFO)
    _h = logging.FileHandler(os.path.join(config.LOG_DIR, "chat.log"))
    _h.setFormatter(logging.Formatter("%(asctime)s  %(message)s"))
    _chat_log.addHandler(_h)

_client = ollama.Client(host=config.OLLAMA_HOST)

# AI-01/AI-02: system prompt trusts context AND user text, with an unguarded
# tool trigger. A role line is added for framing but is NOT enforced at the tool.
_SYSTEM_BASE = (
    "You are CorpAssist, the friendly internal HR/IT assistant for the company. "
    "Answer the employee's question using the context provided below. "
    "If the user is asking for a specific employee's details, reply with EXACTLY "
    "one line in the form:\n"
    "LOOKUP: <full name>\n"
    "and nothing else, so the system can fetch the record for them."
)
_ROLE_NOTE = {
    "admin": " The current user is an HR/IT administrator, authorized to look up employee records.",
    "basic": " The current user is a regular employee and should only receive general policy information.",
}

_LOOKUP_RE = re.compile(r"LOOKUP:\s*(.+)", re.IGNORECASE)


def _system_prompt(role: str) -> str:
    return _SYSTEM_BASE + _ROLE_NOTE.get(role, "")


def generate(prompt: str) -> str:
    resp = _client.generate(model=config.MODEL, prompt=prompt)
    return resp.get("response", "")


def format_rows(rows) -> str:
    if isinstance(rows, dict) and "error" in rows:
        return f"_(lookup failed: {rows['error']})_"
    if not rows:
        return "No matching employee records found."
    # AI-03: happily renders whatever the DB returned, SSNs and all.
    out = ["Here are the matching employee records:\n"]
    for r in rows:
        fields = " · ".join(f"**{k}**: {v}" for k, v in r.items())
        out.append(f"- {fields}")
    return "\n".join(out)


def answer(user_msg: str, role: str = "admin"):
    """Return (reply_text, retrieved_sources). role frames the prompt only;
    it is NOT enforced at the tool (broken access control, by design)."""
    # AI-02: retrieval may pull in a poisoned document as "context".
    chunks = rag.search(user_msg)
    context = "\n\n".join(text for text, _src in chunks)
    sources = [src for _t, src in chunks]

    # AI-01/AI-02: one undifferentiated prompt — no instruction/data boundary.
    prompt = f"{_system_prompt(role)}\n\nContext:\n{context}\n\nUser: {user_msg}\nCorpAssist:"
    reply = generate(prompt)

    _chat_log.info("[role=%s] USER: %r", role, user_msg)
    _chat_log.info("MODEL: %r", reply)
    _chat_log.info("RETRIEVED: %s", sources)

    # AI-03: deterministic tool path, run regardless of role (not enforced).
    m = _LOOKUP_RE.search(reply)
    if m:
        name = m.group(1).strip().strip('"\'')
        rows = tools.lookup_employee(name)
        _chat_log.info("TOOL lookup_employee(%r) [role=%s]", name, role)
        return format_rows(rows), sources

    return reply, sources


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
_CSS = """
<style>
  .block-container { padding-top: 2.2rem; max-width: 820px; }
  h1 { font-weight: 700; letter-spacing: -0.5px; }
  /* chat bubbles */
  [data-testid="stChatMessage"] {
      border-radius: 12px; padding: 0.4rem 0.9rem; margin-bottom: 0.35rem;
      border: 1px solid rgba(255,255,255,0.06);
  }
  /* sidebar identity card */
  .ca-id {
      border:1px solid rgba(255,255,255,0.12); border-radius:10px;
      padding:10px 12px; margin-bottom:12px; background:rgba(255,255,255,0.03);
  }
  .ca-id .who { font-weight:600; font-size:0.95rem; }
  .ca-id .role { font-size:0.78rem; opacity:0.7; text-transform:uppercase; letter-spacing:0.5px; }
  .ca-foot { font-size:0.72rem; opacity:0.45; margin-top:18px; }
</style>
"""


def _render(md: str):
    # AI-04: unsafe_allow_html=True — injected markup/script runs in the browser.
    st.markdown(md, unsafe_allow_html=True)


def _login_screen():
    st.markdown(_CSS, unsafe_allow_html=True)
    st.title("\U0001F4AC CorpAssist")
    st.caption("Internal HR / IT assistant — please sign in.")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in")
    if ok:
        session = auth.check_login(username, password)
        if session:
            st.session_state.user = session
            st.session_state.messages = history.load(session["username"])
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.caption("Lab accounts: `employee` / `employee123` · `hradmin` / `admin123`")


def _chat_screen():
    user = st.session_state.user
    st.markdown(_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            f"<div class='ca-id'><div class='who'>{user['display']}</div>"
            f"<div class='role'>{user['title']}</div></div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Model: `{config.MODEL}`")
        st.caption(f"DB: `{config.DB_USER}@{config.DB_HOST}`")
        st.warning("Deliberately vulnerable lab target. Isolated lab + fake data only.")
        col1, col2 = st.columns(2)
        if col1.button("Clear chat"):
            history.clear(user["username"])
            st.session_state.messages = []
            st.rerun()
        if col2.button("Sign out"):
            st.session_state.pop("user", None)
            st.session_state.pop("messages", None)
            st.rerun()
        st.markdown("<div class='ca-foot'>CorpAssist · COMP 324 lab</div>",
                    unsafe_allow_html=True)

    st.title("\U0001F4AC CorpAssist")
    st.caption("Ask about policies, benefits, IT — or an employee.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                _render(msg["content"])
                if msg.get("sources"):
                    with st.expander("retrieved sources"):
                        st.write(", ".join(msg["sources"]))
            else:
                st.markdown(msg["content"])

    if user_msg := st.chat_input("Ask CorpAssist…"):
        st.session_state.messages.append({"role": "user", "content": user_msg})
        history.append(user["username"], "user", user_msg)
        with st.chat_message("user"):
            st.markdown(user_msg)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                reply, sources = answer(user_msg, role=user["role"])
            _render(reply)
            if sources:
                with st.expander("retrieved sources"):
                    st.write(", ".join(sources))
        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "sources": sources}
        )
        history.append(user["username"], "assistant", reply, sources)


def _run_ui():
    st.set_page_config(page_title="CorpAssist", page_icon="\U0001F4AC")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user" not in st.session_state:
        _login_screen()
    else:
        _chat_screen()


# Streamlit runs this file as __main__; the smoke test imports it (name == "app").
if __name__ == "__main__":
    _run_ui()
