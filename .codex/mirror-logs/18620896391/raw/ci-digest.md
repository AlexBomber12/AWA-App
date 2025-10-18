<!-- AWA-CI-DIGEST -->
## CI digest for `f761fb94`

- **Preview**: n/a
- **Mirror path**: ci-logs/mirror-logs/pr-438/latest
- **Artifacts**: Download debug bundles from the workflow run.

### First errors

**Unit setup** (`unit-setup.log`)

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
```

**docker compose logs** (`compose-logs.txt`)

```
exit_code=1
```

**Additional log (alembic.txt)** (`alembic.txt`)

```
exit_code=1
exit_code=1
```

**Additional log (compose-ps.txt)** (`compose-ps.txt`)

```
exit_code=1
```

**Additional log (preview/compose-logs.txt)** (`preview/compose-logs.txt`)

```
exit_code=1
```

**Additional log (preview/compose-ps.txt)** (`preview/compose-ps.txt`)

```
exit_code=1
```

**Additional log (preview/migrations/alembic.txt)** (`preview/migrations/alembic.txt`)

```
exit_code=1
exit_code=1
```

**Additional log (preview-alembic.txt)** (`preview-alembic.txt`)

```
exit_code=1
exit_code=1
```

**Additional log (preview-compose-logs.txt)** (`preview-compose-logs.txt`)

```
exit_code=1
```

**Additional log (preview-compose-ps.txt)** (`preview-compose-ps.txt`)

```
exit_code=1
```

**Additional log (preview-migrations-alembic.txt)** (`preview-migrations-alembic.txt`)

```
exit_code=1
exit_code=1
```

**Additional log (unit/compose-logs.txt)** (`unit/compose-logs.txt`)

```
exit_code=1
```

**Additional log (unit/compose-ps.txt)** (`unit/compose-ps.txt`)

```
exit_code=1
```

**Additional log (unit/migrations/alembic.txt)** (`unit/migrations/alembic.txt`)

```
exit_code=1
exit_code=1
```

**Additional log (unit/unit-setup.log)** (`unit/unit-setup.log`)

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
```

**Additional log (unit-alembic.txt)** (`unit-alembic.txt`)

```
exit_code=1
exit_code=1
```

**Additional log (unit-compose-logs.txt)** (`unit-compose-logs.txt`)

```
exit_code=1
```

**Additional log (unit-compose-ps.txt)** (`unit-compose-ps.txt`)

```
exit_code=1
```

**Additional log (unit-migrations-alembic.txt)** (`unit-migrations-alembic.txt`)

```
exit_code=1
exit_code=1
```

**Additional log (unit-unit-setup.log)** (`unit-unit-setup.log`)

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
```


### Log tails

<details>
<summary>Unit setup (`unit-setup.log`) — last 54 lines</summary>

```
Requirement already satisfied: shellingham>=1.3.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from typer>=0.15.1->fastapi-cli>=0.0.2->fastapi==0.111.0->-r services/llm_server/requirements.txt (line 1)) (1.5.4)
Downloading sentencepiece-0.2.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (1.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.3/1.3 MB 27.3 MB/s  0:00:00
Installing collected packages: sentencepiece
Successfully installed sentencepiece-0.2.0
Requirement already satisfied: apscheduler==3.10.4 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from -r services/logistics_etl/requirements.txt (line 1)) (3.10.4)
Collecting httpx==0.26.0 (from -r services/logistics_etl/requirements.txt (line 2))
  Using cached httpx-0.26.0-py3-none-any.whl.metadata (7.6 kB)
Requirement already satisfied: sqlalchemy==2.0.29 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from -r services/logistics_etl/requirements.txt (line 3)) (2.0.29)
Collecting asyncpg==0.30.0 (from -r services/logistics_etl/requirements.txt (line 4))
  Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (5.0 kB)
Requirement already satisfied: six>=1.4.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (1.17.0)
Requirement already satisfied: pytz in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (2025.2)
Requirement already satisfied: tzlocal!=3.*,>=2.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (5.3.1)
Requirement already satisfied: anyio in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (4.11.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (2025.10.5)
Requirement already satisfied: httpcore==1.* in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (1.0.9)
Requirement already satisfied: idna in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (3.11)
Requirement already satisfied: sniffio in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (1.3.1)
Requirement already satisfied: typing-extensions>=4.6.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.29->-r services/logistics_etl/requirements.txt (line 3)) (4.15.0)
Requirement already satisfied: greenlet!=0.4.17 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.29->-r services/logistics_etl/requirements.txt (line 3)) (3.2.4)
Requirement already satisfied: h11>=0.16 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpcore==1.*->httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (0.16.0)
Using cached httpx-0.26.0-py3-none-any.whl (75 kB)
Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.1 MB)
Installing collected packages: asyncpg, httpx
  Attempting uninstall: asyncpg
    Found existing installation: asyncpg 0.29.0
    Uninstalling asyncpg-0.29.0:
      Successfully uninstalled asyncpg-0.29.0
  Attempting uninstall: httpx
    Found existing installation: httpx 0.27.2
    Uninstalling httpx-0.27.2:
      Successfully uninstalled httpx-0.27.2

ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
fastapi-cloud-cli 0.3.1 requires httpx>=0.27.0, but you have httpx 0.26.0 which is incompatible.
fastapi-cloud-cli 0.3.1 requires sentry-sdk>=2.20.0, but you have sentry-sdk 2.9.0 which is incompatible.
Successfully installed asyncpg-0.30.0 httpx-0.26.0
Requirement already satisfied: celery==5.4.* in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.4.0)
Requirement already satisfied: billiard<5.0,>=4.2.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (4.2.2)
Requirement already satisfied: kombu<6.0,>=5.3.4 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.5.4)
Requirement already satisfied: vine<6.0,>=5.1.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.1.0)
Requirement already satisfied: click<9.0,>=8.1.2 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (8.3.0)
Requirement already satisfied: click-didyoumean>=0.3.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (0.3.1)
Requirement already satisfied: click-repl>=0.2.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (0.3.0)
Requirement already satisfied: click-plugins>=1.1.1 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (1.1.1.2)
Requirement already satisfied: tzdata>=2022.7 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (2025.2)
Requirement already satisfied: python-dateutil>=2.8.2 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (2.9.0.post0)
Requirement already satisfied: redis!=4.5.5,<6.0.0,>=4.5.2 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.0.8)
Requirement already satisfied: amqp<6.0.0,>=5.1.1 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from kombu<6.0,>=5.3.4->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.3.1)
Requirement already satisfied: packaging in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from kombu<6.0,>=5.3.4->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (25.0)
Requirement already satisfied: prompt-toolkit>=3.0.36 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from click-repl>=0.2.0->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (3.0.52)
Requirement already satisfied: wcwidth in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (0.2.14)
Requirement already satisfied: six>=1.5 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from python-dateutil>=2.8.2->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (1.17.0)
```

</details>

<details>
<summary>docker compose logs (`compose-logs.txt`) — last 10 lines</summary>

```
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (alembic.txt) (`alembic.txt`) — last 20 lines</summary>

```
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (compose-ps.txt) (`compose-ps.txt`) — last 10 lines</summary>

```
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (preview/compose-logs.txt) (`preview/compose-logs.txt`) — last 10 lines</summary>

```
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (preview/compose-ps.txt) (`preview/compose-ps.txt`) — last 10 lines</summary>

```
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (preview/migrations/alembic.txt) (`preview/migrations/alembic.txt`) — last 20 lines</summary>

```
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (preview/system.txt) (`preview/system.txt`) — last 54 lines</summary>

```
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
 Runtimes: io.containerd.runc.v2 runc
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
 Kernel Version: 6.14.0-1012-azure
 Operating System: Ubuntu 24.04.3 LTS
 OSType: linux
 Architecture: x86_64
 CPUs: 4
 Total Memory: 15.62GiB
 Name: runnervmzdgdc
 ID: 0c68cb6d-35e1-4b96-a199-63d9e74069ac
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 Username: githubactions
 Experimental: false
 Insecure Registries:
  ::1/128
  127.0.0.0/8
 Live Restore Enabled: false

```

</details>

<details>
<summary>Additional log (preview-alembic.txt) (`preview-alembic.txt`) — last 20 lines</summary>

```
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (preview-compose-logs.txt) (`preview-compose-logs.txt`) — last 10 lines</summary>

```
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (preview-compose-ps.txt) (`preview-compose-ps.txt`) — last 10 lines</summary>

```
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (preview-migrations-alembic.txt) (`preview-migrations-alembic.txt`) — last 20 lines</summary>

```
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:59Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (preview-system.txt) (`preview-system.txt`) — last 54 lines</summary>

```
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
 Runtimes: io.containerd.runc.v2 runc
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
 Kernel Version: 6.14.0-1012-azure
 Operating System: Ubuntu 24.04.3 LTS
 OSType: linux
 Architecture: x86_64
 CPUs: 4
 Total Memory: 15.62GiB
 Name: runnervmzdgdc
 ID: 0c68cb6d-35e1-4b96-a199-63d9e74069ac
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 Username: githubactions
 Experimental: false
 Insecure Registries:
  ::1/128
  127.0.0.0/8
 Live Restore Enabled: false

```

</details>

<details>
<summary>Additional log (system.txt) (`system.txt`) — last 54 lines</summary>

```
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
 Runtimes: io.containerd.runc.v2 runc
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
 Kernel Version: 6.14.0-1012-azure
 Operating System: Ubuntu 24.04.3 LTS
 OSType: linux
 Architecture: x86_64
 CPUs: 4
 Total Memory: 15.62GiB
 Name: runnervmzdgdc
 ID: 0c68cb6d-35e1-4b96-a199-63d9e74069ac
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 Username: githubactions
 Experimental: false
 Insecure Registries:
  ::1/128
  127.0.0.0/8
 Live Restore Enabled: false

```

</details>

<details>
<summary>Additional log (unit/compose-logs.txt) (`unit/compose-logs.txt`) — last 10 lines</summary>

```
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (unit/compose-ps.txt) (`unit/compose-ps.txt`) — last 10 lines</summary>

```
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (unit/migrations/alembic.txt) (`unit/migrations/alembic.txt`) — last 20 lines</summary>

```
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (unit/system.txt) (`unit/system.txt`) — last 54 lines</summary>

```
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
 Runtimes: io.containerd.runc.v2 runc
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
 Kernel Version: 6.14.0-1012-azure
 Operating System: Ubuntu 24.04.3 LTS
 OSType: linux
 Architecture: x86_64
 CPUs: 4
 Total Memory: 15.62GiB
 Name: runnervmzdgdc
 ID: 0c68cb6d-35e1-4b96-a199-63d9e74069ac
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 Username: githubactions
 Experimental: false
 Insecure Registries:
  ::1/128
  127.0.0.0/8
 Live Restore Enabled: false

```

</details>

<details>
<summary>Additional log (unit/unit-setup.log) (`unit/unit-setup.log`) — last 54 lines</summary>

```
Requirement already satisfied: shellingham>=1.3.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from typer>=0.15.1->fastapi-cli>=0.0.2->fastapi==0.111.0->-r services/llm_server/requirements.txt (line 1)) (1.5.4)
Downloading sentencepiece-0.2.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (1.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.3/1.3 MB 27.3 MB/s  0:00:00
Installing collected packages: sentencepiece
Successfully installed sentencepiece-0.2.0
Requirement already satisfied: apscheduler==3.10.4 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from -r services/logistics_etl/requirements.txt (line 1)) (3.10.4)
Collecting httpx==0.26.0 (from -r services/logistics_etl/requirements.txt (line 2))
  Using cached httpx-0.26.0-py3-none-any.whl.metadata (7.6 kB)
Requirement already satisfied: sqlalchemy==2.0.29 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from -r services/logistics_etl/requirements.txt (line 3)) (2.0.29)
Collecting asyncpg==0.30.0 (from -r services/logistics_etl/requirements.txt (line 4))
  Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (5.0 kB)
Requirement already satisfied: six>=1.4.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (1.17.0)
Requirement already satisfied: pytz in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (2025.2)
Requirement already satisfied: tzlocal!=3.*,>=2.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (5.3.1)
Requirement already satisfied: anyio in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (4.11.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (2025.10.5)
Requirement already satisfied: httpcore==1.* in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (1.0.9)
Requirement already satisfied: idna in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (3.11)
Requirement already satisfied: sniffio in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (1.3.1)
Requirement already satisfied: typing-extensions>=4.6.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.29->-r services/logistics_etl/requirements.txt (line 3)) (4.15.0)
Requirement already satisfied: greenlet!=0.4.17 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.29->-r services/logistics_etl/requirements.txt (line 3)) (3.2.4)
Requirement already satisfied: h11>=0.16 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpcore==1.*->httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (0.16.0)
Using cached httpx-0.26.0-py3-none-any.whl (75 kB)
Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.1 MB)
Installing collected packages: asyncpg, httpx
  Attempting uninstall: asyncpg
    Found existing installation: asyncpg 0.29.0
    Uninstalling asyncpg-0.29.0:
      Successfully uninstalled asyncpg-0.29.0
  Attempting uninstall: httpx
    Found existing installation: httpx 0.27.2
    Uninstalling httpx-0.27.2:
      Successfully uninstalled httpx-0.27.2

ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
fastapi-cloud-cli 0.3.1 requires httpx>=0.27.0, but you have httpx 0.26.0 which is incompatible.
fastapi-cloud-cli 0.3.1 requires sentry-sdk>=2.20.0, but you have sentry-sdk 2.9.0 which is incompatible.
Successfully installed asyncpg-0.30.0 httpx-0.26.0
Requirement already satisfied: celery==5.4.* in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.4.0)
Requirement already satisfied: billiard<5.0,>=4.2.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (4.2.2)
Requirement already satisfied: kombu<6.0,>=5.3.4 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.5.4)
Requirement already satisfied: vine<6.0,>=5.1.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.1.0)
Requirement already satisfied: click<9.0,>=8.1.2 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (8.3.0)
Requirement already satisfied: click-didyoumean>=0.3.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (0.3.1)
Requirement already satisfied: click-repl>=0.2.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (0.3.0)
Requirement already satisfied: click-plugins>=1.1.1 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (1.1.1.2)
Requirement already satisfied: tzdata>=2022.7 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (2025.2)
Requirement already satisfied: python-dateutil>=2.8.2 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (2.9.0.post0)
Requirement already satisfied: redis!=4.5.5,<6.0.0,>=4.5.2 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.0.8)
Requirement already satisfied: amqp<6.0.0,>=5.1.1 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from kombu<6.0,>=5.3.4->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.3.1)
Requirement already satisfied: packaging in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from kombu<6.0,>=5.3.4->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (25.0)
Requirement already satisfied: prompt-toolkit>=3.0.36 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from click-repl>=0.2.0->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (3.0.52)
Requirement already satisfied: wcwidth in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (0.2.14)
Requirement already satisfied: six>=1.5 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from python-dateutil>=2.8.2->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (1.17.0)
```

</details>

<details>
<summary>Additional log (unit-alembic.txt) (`unit-alembic.txt`) — last 20 lines</summary>

```
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (unit-compose-logs.txt) (`unit-compose-logs.txt`) — last 10 lines</summary>

```
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (unit-compose-ps.txt) (`unit-compose-ps.txt`) — last 10 lines</summary>

```
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:49Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (unit-migrations-alembic.txt) (`unit-migrations-alembic.txt`) — last 20 lines</summary>

```
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-18T21:01:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

</details>

<details>
<summary>Additional log (unit-system.txt) (`unit-system.txt`) — last 54 lines</summary>

```
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
 Runtimes: io.containerd.runc.v2 runc
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
 Kernel Version: 6.14.0-1012-azure
 Operating System: Ubuntu 24.04.3 LTS
 OSType: linux
 Architecture: x86_64
 CPUs: 4
 Total Memory: 15.62GiB
 Name: runnervmzdgdc
 ID: 0c68cb6d-35e1-4b96-a199-63d9e74069ac
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 Username: githubactions
 Experimental: false
 Insecure Registries:
  ::1/128
  127.0.0.0/8
 Live Restore Enabled: false

```

</details>

<details>
<summary>Additional log (unit-unit-setup.log) (`unit-unit-setup.log`) — last 54 lines</summary>

```
Requirement already satisfied: shellingham>=1.3.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from typer>=0.15.1->fastapi-cli>=0.0.2->fastapi==0.111.0->-r services/llm_server/requirements.txt (line 1)) (1.5.4)
Downloading sentencepiece-0.2.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (1.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.3/1.3 MB 27.3 MB/s  0:00:00
Installing collected packages: sentencepiece
Successfully installed sentencepiece-0.2.0
Requirement already satisfied: apscheduler==3.10.4 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from -r services/logistics_etl/requirements.txt (line 1)) (3.10.4)
Collecting httpx==0.26.0 (from -r services/logistics_etl/requirements.txt (line 2))
  Using cached httpx-0.26.0-py3-none-any.whl.metadata (7.6 kB)
Requirement already satisfied: sqlalchemy==2.0.29 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from -r services/logistics_etl/requirements.txt (line 3)) (2.0.29)
Collecting asyncpg==0.30.0 (from -r services/logistics_etl/requirements.txt (line 4))
  Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (5.0 kB)
Requirement already satisfied: six>=1.4.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (1.17.0)
Requirement already satisfied: pytz in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (2025.2)
Requirement already satisfied: tzlocal!=3.*,>=2.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (5.3.1)
Requirement already satisfied: anyio in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (4.11.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (2025.10.5)
Requirement already satisfied: httpcore==1.* in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (1.0.9)
Requirement already satisfied: idna in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (3.11)
Requirement already satisfied: sniffio in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (1.3.1)
Requirement already satisfied: typing-extensions>=4.6.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.29->-r services/logistics_etl/requirements.txt (line 3)) (4.15.0)
Requirement already satisfied: greenlet!=0.4.17 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.29->-r services/logistics_etl/requirements.txt (line 3)) (3.2.4)
Requirement already satisfied: h11>=0.16 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from httpcore==1.*->httpx==0.26.0->-r services/logistics_etl/requirements.txt (line 2)) (0.16.0)
Using cached httpx-0.26.0-py3-none-any.whl (75 kB)
Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.1 MB)
Installing collected packages: asyncpg, httpx
  Attempting uninstall: asyncpg
    Found existing installation: asyncpg 0.29.0
    Uninstalling asyncpg-0.29.0:
      Successfully uninstalled asyncpg-0.29.0
  Attempting uninstall: httpx
    Found existing installation: httpx 0.27.2
    Uninstalling httpx-0.27.2:
      Successfully uninstalled httpx-0.27.2

ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
fastapi-cloud-cli 0.3.1 requires httpx>=0.27.0, but you have httpx 0.26.0 which is incompatible.
fastapi-cloud-cli 0.3.1 requires sentry-sdk>=2.20.0, but you have sentry-sdk 2.9.0 which is incompatible.
Successfully installed asyncpg-0.30.0 httpx-0.26.0
Requirement already satisfied: celery==5.4.* in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.4.0)
Requirement already satisfied: billiard<5.0,>=4.2.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (4.2.2)
Requirement already satisfied: kombu<6.0,>=5.3.4 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.5.4)
Requirement already satisfied: vine<6.0,>=5.1.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.1.0)
Requirement already satisfied: click<9.0,>=8.1.2 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (8.3.0)
Requirement already satisfied: click-didyoumean>=0.3.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (0.3.1)
Requirement already satisfied: click-repl>=0.2.0 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (0.3.0)
Requirement already satisfied: click-plugins>=1.1.1 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (1.1.1.2)
Requirement already satisfied: tzdata>=2022.7 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (2025.2)
Requirement already satisfied: python-dateutil>=2.8.2 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (2.9.0.post0)
Requirement already satisfied: redis!=4.5.5,<6.0.0,>=4.5.2 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.0.8)
Requirement already satisfied: amqp<6.0.0,>=5.1.1 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from kombu<6.0,>=5.3.4->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (5.3.1)
Requirement already satisfied: packaging in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from kombu<6.0,>=5.3.4->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (25.0)
Requirement already satisfied: prompt-toolkit>=3.0.36 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from click-repl>=0.2.0->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (3.0.52)
Requirement already satisfied: wcwidth in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (0.2.14)
Requirement already satisfied: six>=1.5 in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (from python-dateutil>=2.8.2->celery==5.4.*->celery[redis]==5.4.*->-r services/price_importer/requirements.txt (line 1)) (1.17.0)
```

</details>
