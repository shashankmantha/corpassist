# CorpAssist convenience targets. Run from the repo root.
# Requires Docker + Compose. corp-net is 192.168.50.0/24 in this lab.
#
# The app ships vulnerable. Remediation is a patch applied post-exploit:
#   make patch     # apply patch/remediation.patch + patch/harden.sql, then retest
#   make unpatch   # roll the code change back

COMPOSE        = docker compose
STANDALONE     = docker compose -f docker-compose.yml -f docker-compose.standalone.yml

.PHONY: help up standalone down clean logs smoke poison reingest patch unpatch

help:
	@echo "CorpAssist targets:"
	@echo "  make up          # real lab (external db-net MySQL), vulnerable baseline"
	@echo "  make standalone  # self-contained w/ throwaway MySQL (off-lab dev)"
	@echo "  make smoke       # run the smoke test against the running stack"
	@echo "  make poison      # plant the AI-02 doc and re-ingest"
	@echo "  make reingest    # rebuild the RAG index"
	@echo "  make logs        # tail the app logs"
	@echo "  make down        # stop and remove containers"
	@echo "  make clean       # down + drop the model volume (next run re-pulls)"
	@echo "  make patch       # apply the remediation (code patch + harden.sql), rebuild"
	@echo "  make unpatch     # revert the code patch"

up:
	$(COMPOSE) up --build

standalone:
	$(STANDALONE) up --build

smoke:
	bash smoke_test.sh

poison:
	cp docs/it_notice_directory_sync.md.poisoned docs/it_notice_directory_sync.md
	$(COMPOSE) restart app
	@echo "Poison doc planted + re-ingested. Ask a benign question as a victim."

reingest:
	$(COMPOSE) exec app python ingest.py

logs:
	$(COMPOSE) logs -f app

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v
	rm -f docs/it_notice_directory_sync.md

# --- Remediation (post-exploit) ----------------------------------------------
patch:
	git apply patch/remediation.patch
	@echo "Code patched. Now apply the DB change and rebuild:"
	@echo "  mysql -h $${DB_HOST:-172.16.0.10} -u root -p < patch/harden.sql   (real lab)"
	@echo "  then: docker compose up --build  &&  make smoke"

unpatch:
	git apply -R patch/remediation.patch
	@echo "Code patch reverted (back to vulnerable). DB account app_ro left in place."
