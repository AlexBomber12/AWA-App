import subprocess, os, uuid, pytest, psycopg

DB = f"awa_test_{uuid.uuid4().hex[:8]}"
DSN = f"postgresql://postgres:pass@localhost:5432/{DB}"


@pytest.fixture(scope="session", autouse=True)
def tmp_db():
    subprocess.run(["createdb", DB], check=True)
    os.environ["DATABASE_URL"] = DSN
    yield
    subprocess.run(["dropdb", "--if-exists", DB], check=True)


def test_upgrade_and_downgrade():
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    subprocess.run(["alembic", "downgrade", "base"], check=True)
