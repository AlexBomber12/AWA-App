DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'appuser') THEN
    CREATE ROLE appuser WITH LOGIN PASSWORD 'apppass' SUPERUSER;
  END IF;
END$$;
