"""
CorpAssist configuration.

!! DELIBERATELY VULNERABLE LAB TARGET !!
This app is an intentionally insecure internal RAG chatbot built for an
isolated COMP 324 red-team/blue-team lab. It demonstrates OWASP LLM Top 10
findings (AI-01 prompt injection, AI-02 RAG poisoning, AI-03 excessive agency,
AI-04 improper output handling). It must only run on the isolated lab network
with fake data. Do not deploy anywhere real.

The app is shipped vulnerable on purpose. Remediation is applied AFTER the
exploit demo, as a version-controlled patch (see patch/). Do not harden here.

Every setting reads from the environment (see .env.example) so the same image
runs against the real db-net MySQL VM or a throwaway standalone container.
"""
import os

# --- Model / Ollama -----------------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
MODEL = os.getenv("CORPASSIST_MODEL", "llama3.1:8b")   # qwen2.5:7b is the fallback

# --- Retrieval ----------------------------------------------------------------
DOCS_DIR = os.getenv("CORPASSIST_DOCS", "docs")
CHROMA_DIR = os.getenv("CORPASSIST_CHROMA", "chroma")
EMBED_MODEL = os.getenv("CORPASSIST_EMBED", "all-MiniLM-L6-v2")
TOP_K = int(os.getenv("CORPASSIST_TOPK", "4"))

# --- Database -----------------------------------------------------------------
# AI-03 / DB-03: the tool is wired to the over-privileged `dba_admin` account on
# purpose. In the real lab, DB_HOST points at the db-net MySQL VM, reached
# through pfSense's corp->db:3306 rule (the confused-deputy path).
# corp-net is 192.168.50.0/24; the db-net MySQL VM is 172.16.0.10.
DB_HOST = os.getenv("DB_HOST", "172.16.0.10")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "dba_admin")        # over-privileged on purpose
DB_PASSWORD = os.getenv("DB_PASSWORD", "dba123")   # weak password on purpose
DB_NAME = os.getenv("DB_NAME", "corp_sensitive")

# --- Logging (blue-team telemetry) --------------------------------------------
# chat.log  -> prompts + responses  (detection signal for AI-01)
# tool.log  -> every DB tool call + the exact SQL  (detection signal for AI-03)
LOG_DIR = os.getenv("CORPASSIST_LOGS", "logs")

# --- Persistence --------------------------------------------------------------
# Per-user chat history lives in a small SQLite file under DATA_DIR so it
# survives container restarts (bind-mounted to the host in docker-compose).
DATA_DIR = os.getenv("CORPASSIST_DATA", "data")
