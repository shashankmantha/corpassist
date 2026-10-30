-- CorpAssist remediation — DB side (AI-03 / DB-03).
-- Apply AFTER the exploit demo, together with patch/remediation.patch.
--
-- Creates a read-only, column-scoped account for the chatbot tool so it can no
-- longer read ssn/salary or touch sys_credentials, and removes the app's need
-- for dba_admin. Run as root on the db-net MySQL VM:
--
--   mysql -h 172.16.0.10 -u root -p < patch/harden.sql
--
-- (Standalone mode: the account also exists via this file; run it against the
--  throwaway MySQL container the same way.)

-- 1. Least-privilege account the patched tool connects as.
CREATE USER IF NOT EXISTS 'app_ro'@'%' IDENTIFIED BY 'app_ro_Secure!2026';

-- Column-scoped SELECT: non-sensitive fields only, employees table only.
GRANT SELECT (full_name, email, department, clearance_level)
  ON corp_sensitive.employees TO 'app_ro'@'%';

-- 2. Shut the DB-03 door the exploit used.
--    (Optional but recommended for the retest: the bot no longer uses dba_admin,
--     and nothing else should. Comment out if other lab steps still need it.)
-- DROP USER IF EXISTS 'dba_admin'@'%';

FLUSH PRIVILEGES;

-- Retest expectation: lookups now return only the four safe columns; a SELECT
-- against ssn/salary or sys_credentials as app_ro is denied.
