<!-- AWA-CI-DIGEST -->
## CI digest for `737e7778`

- **Preview URL**: n/a
- **Mirror path**: ci-logs/mirror-logs/branch-main/latest
- **Workflow run**: [18758148396](https://github.com/AlexBomber12/AWA-App/actions/runs/18758148396)

| Job | Conclusion | URL |
| --- | ---------- | --- |
| unit | ❌ Failure | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18758148396/job/53515342051) |
| integration | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18758148396/job/53515387018) |
| migrations | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18758148396/job/53515387071) |
| preview | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18758148396/job/53515387694) |
| mirror_logs | ⏳ In Progress | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18758148396/job/53515387397) |

### Failed tails

**unit** (`unit/unit-setup.log`)

```
Requirement already satisfied: pip in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (25.2)
Collecting Jinja2==3.1.6 (from -r requirements-dev.txt (line 2))
  Using cached jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting alembic==1.17.0 (from -r requirements-dev.txt (line 3))
  Downloading alembic-1.17.0-py3-none-any.whl.metadata (7.2 kB)
Collecting apscheduler==3.10.4 (from -r requirements-dev.txt (line 4))
  Using cached APScheduler-3.10.4-py3-none-any.whl.metadata (5.7 kB)
Collecting asgi-correlation-id==4.3.1 (from -r requirements-dev.txt (line 5))
  Using cached asgi_correlation_id-4.3.1-py3-none-any.whl.metadata (28 kB)
Collecting asyncpg==0.30.0 (from -r requirements-dev.txt (line 6))
  Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (5.0 kB)
Collecting black==25.9.0 (from -r requirements-dev.txt (line 7))
  Downloading black-25.9.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl.metadata (83 kB)
Collecting boto3==1.40.21 (from -r requirements-dev.txt (line 8))
  Using cached boto3-1.40.21-py3-none-any.whl.metadata (6.7 kB)
Collecting redis==6.* (from -r requirements-dev.txt (line 9))
  Using cached redis-6.4.0-py3-none-any.whl.metadata (10 kB)
Collecting minio==7.2.18 (from -r requirements-dev.txt (line 10))
  Downloading minio-7.2.18-py3-none-any.whl.metadata (6.5 kB)
Collecting vulture==2.10 (from -r requirements-dev.txt (line 11))
  Using cached vulture-2.10-py2.py3-none-any.whl.metadata (23 kB)
Collecting celery==5.5.3 (from -r requirements-dev.txt (line 12))
  Using cached celery-5.5.3-py3-none-any.whl.metadata (22 kB)
Collecting fastapi==0.116.1 (from -r requirements-dev.txt (line 13))
  Using cached fastapi-0.116.1-py3-none-any.whl.metadata (28 kB)
Collecting fastapi-limiter==0.1.6 (from -r requirements-dev.txt (line 15))
  Using cached fastapi_limiter-0.1.6-py3-none-any.whl.metadata (5.3 kB)
Collecting httpx<0.28,>=0.27 (from -r requirements-dev.txt (line 16))
  Using cached httpx-0.27.2-py3-none-any.whl.metadata (7.1 kB)
Collecting imapclient==3.0.1 (from -r requirements-dev.txt (line 17))
  Using cached IMAPClient-3.0.1-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting itsdangerous (from -r requirements-dev.txt (line 18))
  Using cached itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Collecting mypy==1.* (from -r requirements-dev.txt (line 19))
  Using cached mypy-1.18.2-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.2 kB)
Collecting mypy-extensions==1.1.0 (from -r requirements-dev.txt (line 20))
  Using cached mypy_extensions-1.1.0-py3-none-any.whl.metadata (1.1 kB)
Collecting numpy<2 (from -r requirements-dev.txt (line 21))
  Using cached numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (61 kB)
Collecting openpyxl==3.1.5 (from -r requirements-dev.txt (line 22))
  Using cached openpyxl-3.1.5-py2.py3-none-any.whl.metadata (2.5 kB)
Collecting pandas==2.3.2 (from -r requirements-dev.txt (line 23))
  Using cached pandas-2.3.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (91 kB)
Collecting psycopg2-binary==2.9.10 (from -r requirements-dev.txt (line 24))
  Using cached psycopg2_binary-2.9.10-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
ERROR: Cannot install psycopg==3.2.9 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested psycopg==3.2.9
    The user requested (constraint) psycopg==3.2.11

To fix this you could try to:
1. loosen the range of package versions you've specified
2. remove package versions to allow pip to attempt to solve the dependency conflict

ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
```

**unit** (`unit-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-logs.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml logs --no-color
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-ps.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml ps
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-migrations-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:25:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-setup.log`)

```
Requirement already satisfied: pip in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (25.2)
Collecting Jinja2==3.1.6 (from -r requirements-dev.txt (line 2))
  Using cached jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting alembic==1.17.0 (from -r requirements-dev.txt (line 3))
  Downloading alembic-1.17.0-py3-none-any.whl.metadata (7.2 kB)
Collecting apscheduler==3.10.4 (from -r requirements-dev.txt (line 4))
  Using cached APScheduler-3.10.4-py3-none-any.whl.metadata (5.7 kB)
Collecting asgi-correlation-id==4.3.1 (from -r requirements-dev.txt (line 5))
  Using cached asgi_correlation_id-4.3.1-py3-none-any.whl.metadata (28 kB)
Collecting asyncpg==0.30.0 (from -r requirements-dev.txt (line 6))
  Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (5.0 kB)
Collecting black==25.9.0 (from -r requirements-dev.txt (line 7))
  Downloading black-25.9.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl.metadata (83 kB)
Collecting boto3==1.40.21 (from -r requirements-dev.txt (line 8))
  Using cached boto3-1.40.21-py3-none-any.whl.metadata (6.7 kB)
Collecting redis==6.* (from -r requirements-dev.txt (line 9))
  Using cached redis-6.4.0-py3-none-any.whl.metadata (10 kB)
Collecting minio==7.2.18 (from -r requirements-dev.txt (line 10))
  Downloading minio-7.2.18-py3-none-any.whl.metadata (6.5 kB)
Collecting vulture==2.10 (from -r requirements-dev.txt (line 11))
  Using cached vulture-2.10-py2.py3-none-any.whl.metadata (23 kB)
Collecting celery==5.5.3 (from -r requirements-dev.txt (line 12))
  Using cached celery-5.5.3-py3-none-any.whl.metadata (22 kB)
Collecting fastapi==0.116.1 (from -r requirements-dev.txt (line 13))
  Using cached fastapi-0.116.1-py3-none-any.whl.metadata (28 kB)
Collecting fastapi-limiter==0.1.6 (from -r requirements-dev.txt (line 15))
  Using cached fastapi_limiter-0.1.6-py3-none-any.whl.metadata (5.3 kB)
Collecting httpx<0.28,>=0.27 (from -r requirements-dev.txt (line 16))
  Using cached httpx-0.27.2-py3-none-any.whl.metadata (7.1 kB)
Collecting imapclient==3.0.1 (from -r requirements-dev.txt (line 17))
  Using cached IMAPClient-3.0.1-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting itsdangerous (from -r requirements-dev.txt (line 18))
  Using cached itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Collecting mypy==1.* (from -r requirements-dev.txt (line 19))
  Using cached mypy-1.18.2-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.2 kB)
Collecting mypy-extensions==1.1.0 (from -r requirements-dev.txt (line 20))
  Using cached mypy_extensions-1.1.0-py3-none-any.whl.metadata (1.1 kB)
Collecting numpy<2 (from -r requirements-dev.txt (line 21))
  Using cached numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (61 kB)
Collecting openpyxl==3.1.5 (from -r requirements-dev.txt (line 22))
  Using cached openpyxl-3.1.5-py2.py3-none-any.whl.metadata (2.5 kB)
Collecting pandas==2.3.2 (from -r requirements-dev.txt (line 23))
  Using cached pandas-2.3.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (91 kB)
Collecting psycopg2-binary==2.9.10 (from -r requirements-dev.txt (line 24))
  Using cached psycopg2_binary-2.9.10-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
ERROR: Cannot install psycopg==3.2.9 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested psycopg==3.2.9
    The user requested (constraint) psycopg==3.2.11

To fix this you could try to:
1. loosen the range of package versions you've specified
2. remove package versions to allow pip to attempt to solve the dependency conflict

ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
```

**unit** (`unit-system.txt`)

```
ANDROID_NDK_ROOT=/usr/local/lib/android/sdk/ndk/27.3.13750724
ANDROID_SDK_ROOT=/usr/local/lib/android/sdk
ANT_HOME=/usr/share/ant
AZURE_EXTENSION_DIR=/opt/az/azcliextensions
BOOTSTRAP_HASKELL_NONINTERACTIVE=1
CHROMEWEBDRIVER=/usr/local/share/chromedriver-linux64
CHROME_BIN=/usr/bin/google-chrome
CI=true
COMPOSE_DOCKER_CLI_BUILD=1
CONDA=/usr/share/miniconda
DEBIAN_FRONTEND=noninteractive
DOCKER_BUILDKIT=1
DOTNET_MULTILEVEL_LOOKUP=0
DOTNET_NOLOGO=1
DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
EDGEWEBDRIVER=/usr/local/share/edge_driver
ENABLE_RUNNER_TRACING=true
GECKOWEBDRIVER=/usr/local/share/gecko_driver
GHCUP_INSTALL_BASE_PREFIX=/usr/local
GITHUB_ACTION=__run_11
GITHUB_ACTIONS=true
GITHUB_ACTION_REF=
GITHUB_ACTION_REPOSITORY=
GITHUB_ACTOR=AlexBomber12
GITHUB_ACTOR_ID=48256657
GITHUB_API_URL=https://api.github.com
GITHUB_BASE_REF=
GITHUB_ENV=/home/runner/work/_temp/_runner_file_commands/set_env_d1e1b55a-c3e1-4794-afdf-3aa3306a38f9
GITHUB_EVENT_NAME=push
GITHUB_EVENT_PATH=/home/runner/work/_temp/_github_workflow/event.json
GITHUB_GRAPHQL_URL=https://api.github.com/graphql
GITHUB_HEAD_REF=
GITHUB_JOB=unit
GITHUB_OUTPUT=/home/runner/work/_temp/_runner_file_commands/set_output_d1e1b55a-c3e1-4794-afdf-3aa3306a38f9
GITHUB_PATH=/home/runner/work/_temp/_runner_file_commands/add_path_d1e1b55a-c3e1-4794-afdf-3aa3306a38f9
GITHUB_REF=refs/heads/main
GITHUB_REF_NAME=main
GITHUB_REF_PROTECTED=false
GITHUB_REF_TYPE=branch
GITHUB_REPOSITORY=AlexBomber12/AWA-App
GITHUB_REPOSITORY_ID=1011502908
GITHUB_REPOSITORY_OWNER=AlexBomber12
GITHUB_REPOSITORY_OWNER_ID=48256657
GITHUB_RETENTION_DAYS=90
GITHUB_RUN_ATTEMPT=1
GITHUB_RUN_ID=18758148396
GITHUB_RUN_NUMBER=1217
GITHUB_SERVER_URL=https://github.com
GITHUB_SHA=737e7778aac91c0f46332e80262a7d183b528c20
GITHUB_STATE=/home/runner/work/_temp/_runner_file_commands/save_state_d1e1b55a-c3e1-4794-afdf-3aa3306a38f9
GITHUB_STEP_SUMMARY=/home/runner/work/_temp/_runner_file_commands/step_summary_d1e1b55a-c3e1-4794-afdf-3aa3306a38f9
GITHUB_TRIGGERING_ACTOR=AlexBomber12
GITHUB_WORKFLOW=ci
GITHUB_WORKFLOW_REF=AlexBomber12/AWA-App/.github/workflows/ci.yml@refs/heads/main
GITHUB_WORKFLOW_SHA=737e7778aac91c0f46332e80262a7d183b528c20
GITHUB_WORKSPACE=/home/runner/work/AWA-App/AWA-App
GOROOT_1_22_X64=/opt/hostedtoolcache/go/1.22.12/x64
GOROOT_1_23_X64=/opt/hostedtoolcache/go/1.23.12/x64
GOROOT_1_24_X64=/opt/hostedtoolcache/go/1.24.7/x64
GRADLE_HOME=/usr/share/gradle-9.1.0
HOME=/home/runner
HOMEBREW_CLEANUP_PERIODIC_FULL_DAYS=3650
HOMEBREW_NO_AUTO_UPDATE=1
INVOCATION_ID=11373a3126dd4e88affbe302aa4abd55
ImageOS=ubuntu24
ImageVersion=20250929.60.1
JAVA_HOME=/usr/lib/jvm/temurin-17-jdk-amd64
JAVA_HOME_11_X64=/usr/lib/jvm/temurin-11-jdk-amd64
JAVA_HOME_17_X64=/usr/lib/jvm/temurin-17-jdk-amd64
JAVA_HOME_21_X64=/usr/lib/jvm/temurin-21-jdk-amd64
JAVA_HOME_25_X64=/usr/lib/jvm/temurin-25-jdk-amd64
JAVA_HOME_8_X64=/usr/lib/jvm/temurin-8-jdk-amd64
JOURNAL_STREAM=9:11803
LANG=C.UTF-8
LD_LIBRARY_PATH=/opt/hostedtoolcache/Python/3.11.13/x64/lib
LOGNAME=runner
MEMORY_PRESSURE_WATCH=/sys/fs/cgroup/system.slice/hosted-compute-agent.service/memory.pressure
MEMORY_PRESSURE_WRITE=c29tZSAyMDAwMDAgMjAwMDAwMAA=
NODE_VERSION=20
NVM_DIR=/home/runner/.nvm
PATH=/opt/hostedtoolcache/Python/3.11.13/x64/bin:/opt/hostedtoolcache/Python/3.11.13/x64:/snap/bin:/home/runner/.local/bin:/opt/pipx_bin:/home/runner/.cargo/bin:/home/runner/.config/composer/vendor/bin:/usr/local/.ghcup/bin:/home/runner/.dotnet/tools:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
PIPX_BIN_DIR=/opt/pipx_bin
PIPX_HOME=/opt/pipx
PKG_CONFIG_PATH=/opt/hostedtoolcache/Python/3.11.13/x64/lib/pkgconfig
POWERSHELL_DISTRIBUTION_CHANNEL=GitHub-Actions-ubuntu24
PWD=/home/runner/work/AWA-App/AWA-App
PYTHON_VERSION=3.11
Python2_ROOT_DIR=/opt/hostedtoolcache/Python/3.11.13/x64
Python3_ROOT_DIR=/opt/hostedtoolcache/Python/3.11.13/x64
Python_ROOT_DIR=/opt/hostedtoolcache/Python/3.11.13/x64
RUNNER_ARCH=X64
RUNNER_ENVIRONMENT=github-hosted
RUNNER_NAME=GitHub Actions 1000008432
RUNNER_OS=Linux
RUNNER_TEMP=/home/runner/work/_temp
RUNNER_TOOL_CACHE=/opt/hostedtoolcache
RUNNER_TRACKING_ID=github_972cfff8-36cf-4f14-914a-10cd0a578205
RUNNER_WORKSPACE=/home/runner/work/AWA-App
SELENIUM_JAR_PATH=/usr/share/java/selenium-server.jar
SGX_AESM_ADDR=1
SHELL=/bin/bash
SHLVL=2
SWIFT_PATH=/usr/share/swift/usr/bin
SYSTEMD_EXEC_PID=1882
USER=runner
VCPKG_INSTALLATION_ROOT=/usr/local/share/vcpkg
XDG_CONFIG_HOME=/home/runner/.config
XDG_RUNTIME_DIR=/run/user/1001
_=/opt/hostedtoolcache/Python/3.11.13/x64/bin/python
pythonLocation=/opt/hostedtoolcache/Python/3.11.13/x64

## Docker
Client: Docker Engine - Community
 Version:           28.0.4
 API version:       1.48
 Go version:        go1.23.7
 Git commit:        b8034c0
 Built:             Tue Mar 25 15:07:16 2025
 OS/Arch:           linux/amd64
 Context:           default

Server: Docker Engine - Community
 Engine:
  Version:          28.0.4
  API version:      1.48 (minimum version 1.24)
  Go version:       go1.23.7
  Git commit:       6430e49
  Built:            Tue Mar 25 15:07:16 2025
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          v1.7.28
  GitCommit:        b98a3aace656320842a23f4a392a33f46af97866
 runc:
  Version:          1.3.0
  GitCommit:        v1.3.0-0-g4ca628d1
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0
Client: Docker Engine - Community
 Version:    28.0.4
 Context:    default
 Debug Mode: false
 Plugins:
  buildx: Docker Buildx (Docker Inc.)
    Version:  v0.28.0
    Path:     /usr/libexec/docker/cli-plugins/docker-buildx
  compose: Docker Compose (Docker Inc.)
    Version:  v2.38.2
    Path:     /usr/libexec/docker/cli-plugins/docker-compose

Server:
 Containers: 0
  Running: 0
  Paused: 0
  Stopped: 0
 Images: 0
 Server Version: 28.0.4
 Storage Driver: overlay2
  Backing Filesystem: extfs
  Supports d_type: true
  Using metacopy: false
  Native Overlay Diff: false
  userxattr: false
 Logging Driver: json-file
 Cgroup Driver: systemd
 Cgroup Version: 2
 Plugins:
  Volume: local
  Network: bridge host ipvlan macvlan null overlay
  Log: awslogs fluentd gcplogs gelf journald json-file local splunk syslog
 Swarm: inactive
 Runtimes: runc io.containerd.runc.v2
 Default Runtime: runc
 Init Binary: docker-init
 containerd version: b98a3aace656320842a23f4a392a33f46af97866
 runc version: v1.3.0-0-g4ca628d1
 init version: de40ad0
 Security Options:
  apparmor
  seccomp
   Profile: builtin
  cgroupns
 Kernel Version: 6.11.0-1018-azure
 Operating System: Ubuntu 24.04.3 LTS
 OSType: linux
 Architecture: x86_64
 CPUs: 4
 Total Memory: 15.62GiB
 Name: runnervmwhb2z
 ID: ac1187db-1850-4397-a0f7-3b6e6ef293d6
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 Username: githubactions
 Experimental: false
 Insecure Registries:
  ::1/128
  127.0.0.0/8
 Live Restore Enabled: false

```

**unit** (`unit-unit-setup.log`)

```
Requirement already satisfied: pip in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (25.2)
Collecting Jinja2==3.1.6 (from -r requirements-dev.txt (line 2))
  Using cached jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting alembic==1.17.0 (from -r requirements-dev.txt (line 3))
  Downloading alembic-1.17.0-py3-none-any.whl.metadata (7.2 kB)
Collecting apscheduler==3.10.4 (from -r requirements-dev.txt (line 4))
  Using cached APScheduler-3.10.4-py3-none-any.whl.metadata (5.7 kB)
Collecting asgi-correlation-id==4.3.1 (from -r requirements-dev.txt (line 5))
  Using cached asgi_correlation_id-4.3.1-py3-none-any.whl.metadata (28 kB)
Collecting asyncpg==0.30.0 (from -r requirements-dev.txt (line 6))
  Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (5.0 kB)
Collecting black==25.9.0 (from -r requirements-dev.txt (line 7))
  Downloading black-25.9.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl.metadata (83 kB)
Collecting boto3==1.40.21 (from -r requirements-dev.txt (line 8))
  Using cached boto3-1.40.21-py3-none-any.whl.metadata (6.7 kB)
Collecting redis==6.* (from -r requirements-dev.txt (line 9))
  Using cached redis-6.4.0-py3-none-any.whl.metadata (10 kB)
Collecting minio==7.2.18 (from -r requirements-dev.txt (line 10))
  Downloading minio-7.2.18-py3-none-any.whl.metadata (6.5 kB)
Collecting vulture==2.10 (from -r requirements-dev.txt (line 11))
  Using cached vulture-2.10-py2.py3-none-any.whl.metadata (23 kB)
Collecting celery==5.5.3 (from -r requirements-dev.txt (line 12))
  Using cached celery-5.5.3-py3-none-any.whl.metadata (22 kB)
Collecting fastapi==0.116.1 (from -r requirements-dev.txt (line 13))
  Using cached fastapi-0.116.1-py3-none-any.whl.metadata (28 kB)
Collecting fastapi-limiter==0.1.6 (from -r requirements-dev.txt (line 15))
  Using cached fastapi_limiter-0.1.6-py3-none-any.whl.metadata (5.3 kB)
Collecting httpx<0.28,>=0.27 (from -r requirements-dev.txt (line 16))
  Using cached httpx-0.27.2-py3-none-any.whl.metadata (7.1 kB)
Collecting imapclient==3.0.1 (from -r requirements-dev.txt (line 17))
  Using cached IMAPClient-3.0.1-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting itsdangerous (from -r requirements-dev.txt (line 18))
  Using cached itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Collecting mypy==1.* (from -r requirements-dev.txt (line 19))
  Using cached mypy-1.18.2-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.2 kB)
Collecting mypy-extensions==1.1.0 (from -r requirements-dev.txt (line 20))
  Using cached mypy_extensions-1.1.0-py3-none-any.whl.metadata (1.1 kB)
Collecting numpy<2 (from -r requirements-dev.txt (line 21))
  Using cached numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (61 kB)
Collecting openpyxl==3.1.5 (from -r requirements-dev.txt (line 22))
  Using cached openpyxl-3.1.5-py2.py3-none-any.whl.metadata (2.5 kB)
Collecting pandas==2.3.2 (from -r requirements-dev.txt (line 23))
  Using cached pandas-2.3.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (91 kB)
Collecting psycopg2-binary==2.9.10 (from -r requirements-dev.txt (line 24))
  Using cached psycopg2_binary-2.9.10-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
ERROR: Cannot install psycopg==3.2.9 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested psycopg==3.2.9
    The user requested (constraint) psycopg==3.2.11

To fix this you could try to:
1. loosen the range of package versions you've specified
2. remove package versions to allow pip to attempt to solve the dependency conflict

ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
```
