DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api') THEN
    CREATE ROLE api WITH LOGIN PASSWORD 'pass';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'awa') THEN
    CREATE DATABASE awa OWNER api;
  END IF;
END$$;
