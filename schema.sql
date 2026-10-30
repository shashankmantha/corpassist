-- CorpAssist standalone DB seed (option 2 only).
-- Mirrors the lab's db-net schema with FAKE data so AI-03 has something to leak
-- when running off-lab. The real demo uses the db-net MySQL VM instead.
-- All data below is fictional.
--
-- This is the VULNERABLE baseline seed. The remediation (a least-privilege
-- app_ro account) is applied later from patch/harden.sql, not here.

CREATE DATABASE IF NOT EXISTS corp_sensitive;
USE corp_sensitive;

CREATE TABLE IF NOT EXISTS employees (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(150),
    ssn             VARCHAR(11),            -- plaintext PII (DB-01)
    salary          DECIMAL(10,2),
    department      VARCHAR(50),
    clearance_level ENUM('basic','secret','top_secret') DEFAULT 'basic'
);

INSERT INTO employees (full_name, email, ssn, salary, department, clearance_level) VALUES
  ('John Smith',    'jsmith@corp.local',   '123-45-6789', 85000,  'Engineering',   'secret'),
  ('Sarah Johnson', 'sjohnson@corp.local', '987-65-4321', 120000, 'Management',    'top_secret'),
  ('Mike Davis',    'mdavis@corp.local',   '456-78-9012', 72000,  'IT Operations', 'basic'),
  ('Lisa Chen',     'lchen@corp.local',    '321-54-8976', 98000,  'Finance',       'secret');

CREATE TABLE IF NOT EXISTS sys_credentials (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    system_name VARCHAR(100),
    username    VARCHAR(100),
    password    VARCHAR(100),               -- plaintext secrets (DB-02)
    notes       VARCHAR(255)
);

INSERT INTO sys_credentials (system_name, username, password, notes) VALUES
  ('corp.local AD', 'svcmonitor',  'Summer2024!', 'Monitoring service account'),
  ('pfSense Admin', 'admin',       'pfsense',     'Default password not changed'),
  ('Backup Server', 'backupadmin', 'backup123',   'Nightly backup account');

-- DB-03: the over-privileged account the chatbot tool uses (intentional).
CREATE USER IF NOT EXISTS 'dba_admin'@'%' IDENTIFIED BY 'dba123';
GRANT ALL PRIVILEGES ON *.* TO 'dba_admin'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
