<!-- AWA-CI-DIGEST -->
## CI digest for `8835b862`

- **Preview URL**: n/a
- **Mirror path**: ci-logs/mirror-logs/pr-460/latest
- **Workflow run**: [18853836109](https://github.com/AlexBomber12/AWA-App/actions/runs/18853836109)

| Job | Conclusion | URL |
| --- | ---------- | --- |
| unit | ❌ Failure | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18853836109/job/53796625445) |
| integration | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18853836109/job/53796690196) |
| migrations | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18853836109/job/53796690223) |
| preview | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18853836109/job/53796690233) |
| mirror_logs | ⏳ In Progress | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18853836109/job/53796690123) |

### Failed tails

**unit** (`unit/unit-setup.log`)

```
Collecting fastapi-cloud-cli>=0.1.1 (from fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached fastapi_cloud_cli-0.3.1-py3-none-any.whl.metadata (3.2 kB)
Collecting rignore>=0.5.1 (from fastapi-cloud-cli>=0.1.1->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached rignore-0.7.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.2 kB)
Collecting sentry-sdk>=2.20.0 (from fastapi-cloud-cli>=0.1.1->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached sentry_sdk-2.20.0-py2.py3-none-any.whl.metadata (10 kB)
Collecting psutil>=4.0.0 (from mirakuru>=2.6.0->pytest-postgresql==7.0.2->-r requirements-dev.txt (line 31))
  Downloading psutil-7.1.2-cp36-abi3-manylinux2010_x86_64.manylinux_2_12_x86_64.manylinux_2_28_x86_64.whl.metadata (23 kB)
Collecting wcwidth (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.5.3->-r requirements-dev.txt (line 12))
  Using cached wcwidth-0.2.14-py2.py3-none-any.whl.metadata (15 kB)
Collecting rich>=13.7.1 (from rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached rich-14.2.0-py3-none-any.whl.metadata (18 kB)
Collecting markdown-it-py>=2.2.0 (from rich>=13.7.1->rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached markdown_it_py-4.0.0-py3-none-any.whl.metadata (7.3 kB)
Collecting mdurl~=0.1 (from markdown-it-py>=2.2.0->rich>=13.7.1->rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached mdurl-0.1.2-py3-none-any.whl.metadata (1.6 kB)
Collecting shellingham>=1.3.0 (from typer>=0.15.1->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached shellingham-1.5.4-py2.py3-none-any.whl.metadata (3.5 kB)
Collecting httptools>=0.6.3 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached httptools-0.7.1-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (3.5 kB)
Collecting uvloop>=0.15.1 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached uvloop-0.22.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (4.9 kB)
Collecting watchfiles>=0.13 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached watchfiles-1.1.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
Collecting websockets>=10.4 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.8 kB)
Collecting argon2-cffi-bindings (from argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 10))
  Using cached argon2_cffi_bindings-25.1.0-cp39-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl.metadata (7.4 kB)
Collecting cffi>=1.0.1 (from argon2-cffi-bindings->argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 10))
  Using cached cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.6 kB)
Collecting pycparser (from cffi>=1.0.1->argon2-cffi-bindings->argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 10))
  Using cached pycparser-2.23-py3-none-any.whl.metadata (993 bytes)
Using cached jinja2-3.1.6-py3-none-any.whl (134 kB)
Using cached alembic-1.17.0-py3-none-any.whl (247 kB)
Using cached APScheduler-3.10.4-py3-none-any.whl (59 kB)
Using cached asgi_correlation_id-4.3.1-py3-none-any.whl (15 kB)
Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.1 MB)
Using cached black-25.9.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl (1.6 MB)
Using cached boto3-1.40.21-py3-none-any.whl (139 kB)
Using cached minio-7.2.18-py3-none-any.whl (93 kB)
Using cached vulture-2.10-py2.py3-none-any.whl (27 kB)
Using cached celery-5.5.3-py3-none-any.whl (438 kB)
Using cached fastapi-0.116.1-py3-none-any.whl (95 kB)
Using cached fastapi_limiter-0.1.6-py3-none-any.whl (15 kB)
Using cached IMAPClient-3.0.1-py2.py3-none-any.whl (182 kB)
Using cached mypy_extensions-1.1.0-py3-none-any.whl (5.0 kB)
Using cached openpyxl-3.1.5-py2.py3-none-any.whl (250 kB)
Using cached pandas-2.3.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (12.4 MB)
Using cached psycopg2_binary-2.9.10-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.0 MB)
Using cached psycopg-3.2.11-py3-none-any.whl (206 kB)
Using cached pytest_asyncio-1.1.0-py3-none-any.whl (15 kB)
Using cached pytest_cov-7.0.0-py3-none-any.whl (22 kB)
Using cached pytest_postgresql-7.0.2-py3-none-any.whl (41 kB)
Using cached python_telegram_bot-22.5-py3-none-any.whl (730 kB)
Using cached requests-2.32.5-py3-none-any.whl (64 kB)
Using cached respx-0.22.0-py2.py3-none-any.whl (25 kB)
Using cached ruff-0.12.11-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (13.2 MB)
Downloading sqlalchemy-2.0.44-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.3/3.3 MB 49.0 MB/s  0:00:00
Using cached structlog-24.1.0-py3-none-any.whl (65 kB)
Using cached testcontainers-4.12.0-py3-none-any.whl (111 kB)
Using cached types_requests-2.32.4.20250809-py3-none-any.whl (20 kB)
Using cached docspec_python-2.2.2-py3-none-any.whl (15 kB)
Using cached pydoc_markdown-4.8.2-py3-none-any.whl (67 kB)
Using cached docspec-2.2.1-py3-none-any.whl (9.8 kB)
Using cached psycopg_binary-3.2.11-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (4.4 MB)
Using cached redis-6.4.0-py3-none-any.whl (279 kB)
Using cached httpx-0.27.2-py3-none-any.whl (76 kB)
Using cached mypy-1.18.2-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (13.2 MB)
Using cached numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (18.3 MB)
Using cached pydantic-2.11.7-py3-none-any.whl (444 kB)
Using cached pydantic_core-2.33.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.0 MB)
Using cached pandera-0.26.1-py3-none-any.whl (292 kB)
Using cached billiard-4.2.2-py3-none-any.whl (86 kB)
Downloading botocore-1.40.60-py3-none-any.whl (14.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 14.1/14.1 MB 166.0 MB/s  0:00:00
Using cached charset_normalizer-3.4.4-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (151 kB)
Using cached click-8.3.0-py3-none-any.whl (107 kB)
Using cached databind.core-4.5.2-py3-none-any.whl (1.5 kB)
Using cached databind-4.5.2-py3-none-any.whl (49 kB)
Using cached databind.json-4.5.2-py3-none-any.whl (1.5 kB)
Using cached Deprecated-1.2.18-py2.py3-none-any.whl (10.0 kB)
Using cached httpcore-1.0.5-py3-none-any.whl (77 kB)
Using cached h11-0.14.0-py3-none-any.whl (58 kB)
Using cached idna-3.11-py3-none-any.whl (71 kB)
Using cached jmespath-1.0.1-py3-none-any.whl (20 kB)
Using cached kombu-5.5.4-py3-none-any.whl (210 kB)
Using cached vine-5.1.0-py3-none-any.whl (9.6 kB)
Using cached amqp-5.3.1-py3-none-any.whl (50 kB)
Using cached nr_date-2.1.0-py3-none-any.whl (10 kB)
Using cached nr_stream-1.1.5-py3-none-any.whl (10 kB)
Using cached nr.util-0.8.12-py3-none-any.whl (90 kB)
Using cached pytest-8.4.2-py3-none-any.whl (365 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
Using cached pyyaml-6.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (806 kB)
Using cached s3transfer-0.13.1-py3-none-any.whl (85 kB)
Using cached starlette-0.47.3-py3-none-any.whl (72 kB)
Using cached anyio-4.4.0-py3-none-any.whl (86 kB)
Using cached tomli-2.3.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (242 kB)
Using cached tomli_w-1.2.0-py3-none-any.whl (6.7 kB)
Using cached typeapi-2.3.0-py3-none-any.whl (26 kB)
Using cached typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Using cached urllib3-2.5.0-py3-none-any.whl (129 kB)
Using cached wrapt-1.17.3-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (82 kB)
Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Using cached pydantic_settings-2.2.1-py3-none-any.whl (13 kB)
Using cached python_dotenv-1.1.1-py3-none-any.whl (20 kB)
Using cached python_multipart-0.0.19-py3-none-any.whl (24 kB)
Using cached annotated_types-0.7.0-py3-none-any.whl (13 kB)
Using cached certifi-2025.10.5-py3-none-any.whl (163 kB)
Using cached click_didyoumean-0.3.1-py3-none-any.whl (3.6 kB)
Using cached click_plugins-1.1.1.2-py2.py3-none-any.whl (11 kB)
Using cached click_repl-0.3.0-py3-none-any.whl (10 kB)
Using cached coverage-7.11.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (248 kB)
Using cached email_validator-2.3.0-py3-none-any.whl (35 kB)
Using cached dnspython-2.8.0-py3-none-any.whl (331 kB)
Using cached fastapi_cli-0.0.14-py3-none-any.whl (11 kB)
Using cached fastapi_cloud_cli-0.3.1-py3-none-any.whl (19 kB)
Using cached greenlet-3.2.4-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (587 kB)
Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Using cached markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Using cached mirakuru-2.6.1-py3-none-any.whl (26 kB)
Downloading orjson-3.11.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (136 kB)
Using cached packaging-25.0-py3-none-any.whl (66 kB)
Using cached pathspec-0.12.1-py3-none-any.whl (31 kB)
Using cached platformdirs-4.5.0-py3-none-any.whl (18 kB)
Using cached port_for-1.0.0-py3-none-any.whl (17 kB)
Using cached prompt_toolkit-3.0.52-py3-none-any.whl (391 kB)
Downloading psutil-7.1.2-cp36-abi3-manylinux2010_x86_64.manylinux_2_12_x86_64.manylinux_2_28_x86_64.whl (258 kB)
Using cached pydantic_extra_types-2.10.6-py3-none-any.whl (40 kB)
Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
Using cached pytokens-0.2.0-py3-none-any.whl (12 kB)
Using cached pytz-2025.2-py2.py3-none-any.whl (509 kB)
Using cached rich_toolkit-0.15.1-py3-none-any.whl (29 kB)
Using cached rich-14.2.0-py3-none-any.whl (243 kB)
Using cached markdown_it_py-4.0.0-py3-none-any.whl (87 kB)
Using cached mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Using cached rignore-0.7.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (952 kB)
Using cached sentry_sdk-2.20.0-py2.py3-none-any.whl (322 kB)
Using cached six-1.17.0-py2.py3-none-any.whl (11 kB)
Using cached sniffio-1.3.1-py3-none-any.whl (10 kB)
Using cached typer-0.20.0-py3-none-any.whl (47 kB)
Using cached shellingham-1.5.4-py2.py3-none-any.whl (9.8 kB)
Using cached typing_inspect-0.9.0-py3-none-any.whl (8.8 kB)
Using cached typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Using cached tzdata-2025.2-py2.py3-none-any.whl (347 kB)
Using cached tzlocal-5.3.1-py3-none-any.whl (18 kB)
Using cached ujson-5.11.0-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (57 kB)
Using cached uvicorn-0.35.0-py3-none-any.whl (66 kB)
Using cached httptools-0.7.1-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (456 kB)
Using cached uvloop-0.22.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (3.8 MB)
Using cached watchfiles-1.1.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Using cached websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (182 kB)
Using cached yapf-0.43.0-py3-none-any.whl (256 kB)
Using cached argon2_cffi-25.1.0-py3-none-any.whl (14 kB)
Using cached argon2_cffi_bindings-25.1.0-cp39-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl (87 kB)
Using cached cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (215 kB)
Using cached docker-7.1.0-py3-none-any.whl (147 kB)
Using cached et_xmlfile-2.0.0-py3-none-any.whl (18 kB)
Using cached mako-1.3.10-py3-none-any.whl (78 kB)
Using cached pycparser-2.23-py3-none-any.whl (118 kB)
Using cached pycryptodome-3.23.0-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.3 MB)
Using cached toml-0.10.2-py2.py3-none-any.whl (16 kB)
Using cached typeguard-4.4.4-py3-none-any.whl (34 kB)
Using cached watchdog-6.0.0-py3-none-manylinux2014_x86_64.whl (79 kB)
Using cached wcwidth-0.2.14-py2.py3-none-any.whl (37 kB)
Installing collected packages: pytz, wrapt, websockets, wcwidth, watchdog, vine, uvloop, urllib3, ujson, tzlocal, tzdata, typing-extensions, tomli_w, tomli, toml, structlog, sniffio, six, shellingham, ruff, rignore, redis, PyYAML, pytokens, python-multipart, python-dotenv, pygments, pycryptodome, pycparser, psycopg2-binary, psycopg-binary, psutil, port-for, pluggy, platformdirs, pathspec, packaging, orjson, numpy, nr-stream, nr-date, mypy-extensions, mdurl, MarkupSafe, jmespath, itsdangerous, iniconfig, imapclient, idna, httptools, h11, greenlet, et-xmlfile, docstring-parser, dnspython, coverage, click, charset_normalizer, certifi, billiard, asyncpg, annotated-types, yapf, vulture, uvicorn, typing-inspection, typing_inspect, types-requests, typeguard, typeapi, sqlalchemy, sentry-sdk, requests, python-dateutil, pytest, pydantic-core, psycopg, prompt-toolkit, openpyxl, mypy, mirakuru, markdown-it-py, Mako, Jinja2, httpcore, email-validator, Deprecated, click-plugins, click-didyoumean, cffi, black, apscheduler, anyio, amqp, watchfiles, starlette, rich, pytest-postgresql, pytest-cov, pytest-asyncio, pydantic, pandas, nr-util, kombu, httpx, docker, databind, click-repl, botocore, argon2-cffi-bindings, alembic, typer, testcontainers, s3transfer, rich-toolkit, respx, python-telegram-bot, pydantic-settings, pydantic-extra-types, pandera, fastapi, databind.json, databind.core, celery, asgi-correlation-id, argon2-cffi, minio, fastapi-limiter, fastapi-cloud-cli, fastapi-cli, docspec, boto3, docspec-python, pydoc-markdown

Successfully installed Deprecated-1.2.18 Jinja2-3.1.6 Mako-1.3.10 MarkupSafe-3.0.3 PyYAML-6.0.3 alembic-1.17.0 amqp-5.3.1 annotated-types-0.7.0 anyio-4.4.0 apscheduler-3.10.4 argon2-cffi-25.1.0 argon2-cffi-bindings-25.1.0 asgi-correlation-id-4.3.1 asyncpg-0.30.0 billiard-4.2.2 black-25.9.0 boto3-1.40.21 botocore-1.40.60 celery-5.5.3 certifi-2025.10.5 cffi-2.0.0 charset_normalizer-3.4.4 click-8.3.0 click-didyoumean-0.3.1 click-plugins-1.1.1.2 click-repl-0.3.0 coverage-7.11.0 databind-4.5.2 databind.core-4.5.2 databind.json-4.5.2 dnspython-2.8.0 docker-7.1.0 docspec-2.2.1 docspec-python-2.2.2 docstring-parser-0.11 email-validator-2.3.0 et-xmlfile-2.0.0 fastapi-0.116.1 fastapi-cli-0.0.14 fastapi-cloud-cli-0.3.1 fastapi-limiter-0.1.6 greenlet-3.2.4 h11-0.14.0 httpcore-1.0.5 httptools-0.7.1 httpx-0.27.2 idna-3.11 imapclient-3.0.1 iniconfig-2.3.0 itsdangerous-2.2.0 jmespath-1.0.1 kombu-5.5.4 markdown-it-py-4.0.0 mdurl-0.1.2 minio-7.2.18 mirakuru-2.6.1 mypy-1.18.2 mypy-extensions-1.1.0 nr-date-2.1.0 nr-stream-1.1.5 nr-util-0.8.12 numpy-1.26.4 openpyxl-3.1.5 orjson-3.11.4 packaging-25.0 pandas-2.3.2 pandera-0.26.1 pathspec-0.12.1 platformdirs-4.5.0 pluggy-1.6.0 port-for-1.0.0 prompt-toolkit-3.0.52 psutil-7.1.2 psycopg-3.2.11 psycopg-binary-3.2.11 psycopg2-binary-2.9.10 pycparser-2.23 pycryptodome-3.23.0 pydantic-2.11.7 pydantic-core-2.33.2 pydantic-extra-types-2.10.6 pydantic-settings-2.2.1 pydoc-markdown-4.8.2 pygments-2.19.2 pytest-8.4.2 pytest-asyncio-1.1.0 pytest-cov-7.0.0 pytest-postgresql-7.0.2 python-dateutil-2.9.0.post0 python-dotenv-1.1.1 python-multipart-0.0.19 python-telegram-bot-22.5 pytokens-0.2.0 pytz-2025.2 redis-6.4.0 requests-2.32.5 respx-0.22.0 rich-14.2.0 rich-toolkit-0.15.1 rignore-0.7.1 ruff-0.12.11 s3transfer-0.13.1 sentry-sdk-2.20.0 shellingham-1.5.4 six-1.17.0 sniffio-1.3.1 sqlalchemy-2.0.44 starlette-0.47.3 structlog-24.1.0 testcontainers-4.12.0 toml-0.10.2 tomli-2.3.0 tomli_w-1.2.0 typeapi-2.3.0 typeguard-4.4.4 typer-0.20.0 types-requests-2.32.4.20250809 typing-extensions-4.15.0 typing-inspection-0.4.2 typing_inspect-0.9.0 tzdata-2025.2 tzlocal-5.3.1 ujson-5.11.0 urllib3-2.5.0 uvicorn-0.35.0 uvloop-0.22.1 vine-5.1.0 vulture-2.10 watchdog-6.0.0 watchfiles-1.1.1 wcwidth-0.2.14 websockets-15.0.1 wrapt-1.17.3 yapf-0.43.0
Requirement already satisfied: python-telegram-bot==22.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 1)) (22.5)
Requirement already satisfied: apscheduler==3.10.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 2)) (3.10.4)
Requirement already satisfied: asyncpg==0.30.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 3)) (0.30.0)
Requirement already satisfied: httpx<0.29,>=0.27 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (0.27.2)
Requirement already satisfied: six>=1.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (1.17.0)
Requirement already satisfied: pytz in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (2025.2)
Requirement already satisfied: tzlocal!=3.*,>=2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (5.3.1)
Requirement already satisfied: anyio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (4.4.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (2025.10.5)
Requirement already satisfied: httpcore==1.* in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (1.0.5)
Requirement already satisfied: idna in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (3.11)
Requirement already satisfied: sniffio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (1.3.1)
Requirement already satisfied: h11<0.15,>=0.13 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpcore==1.*->httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (0.14.0)
Requirement already satisfied: uvicorn==0.35.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 1)) (0.35.0)
Requirement already satisfied: pydantic-settings==2.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 2)) (2.2.1)
Requirement already satisfied: fastapi==0.116.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 3)) (0.116.1)
ERROR: Cannot install sqlalchemy==2.0.43 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested sqlalchemy==2.0.43
    The user requested (constraint) sqlalchemy==2.0.44

Additionally, some packages in these conflicts have no matching distributions available for your environment:
    sqlalchemy

To fix this you could try to:
1. loosen the range of package versions you've specified
2. remove package versions to allow pip to attempt to solve the dependency conflict

ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
```

**unit** (`unit-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-logs.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml logs --no-color
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-ps.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml ps
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:03Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-migrations-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T19:44:04Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-setup.log`)

```
Collecting fastapi-cloud-cli>=0.1.1 (from fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached fastapi_cloud_cli-0.3.1-py3-none-any.whl.metadata (3.2 kB)
Collecting rignore>=0.5.1 (from fastapi-cloud-cli>=0.1.1->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached rignore-0.7.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.2 kB)
Collecting sentry-sdk>=2.20.0 (from fastapi-cloud-cli>=0.1.1->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached sentry_sdk-2.20.0-py2.py3-none-any.whl.metadata (10 kB)
Collecting psutil>=4.0.0 (from mirakuru>=2.6.0->pytest-postgresql==7.0.2->-r requirements-dev.txt (line 31))
  Downloading psutil-7.1.2-cp36-abi3-manylinux2010_x86_64.manylinux_2_12_x86_64.manylinux_2_28_x86_64.whl.metadata (23 kB)
Collecting wcwidth (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.5.3->-r requirements-dev.txt (line 12))
  Using cached wcwidth-0.2.14-py2.py3-none-any.whl.metadata (15 kB)
Collecting rich>=13.7.1 (from rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached rich-14.2.0-py3-none-any.whl.metadata (18 kB)
Collecting markdown-it-py>=2.2.0 (from rich>=13.7.1->rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached markdown_it_py-4.0.0-py3-none-any.whl.metadata (7.3 kB)
Collecting mdurl~=0.1 (from markdown-it-py>=2.2.0->rich>=13.7.1->rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached mdurl-0.1.2-py3-none-any.whl.metadata (1.6 kB)
Collecting shellingham>=1.3.0 (from typer>=0.15.1->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached shellingham-1.5.4-py2.py3-none-any.whl.metadata (3.5 kB)
Collecting httptools>=0.6.3 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached httptools-0.7.1-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (3.5 kB)
Collecting uvloop>=0.15.1 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached uvloop-0.22.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (4.9 kB)
Collecting watchfiles>=0.13 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached watchfiles-1.1.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
Collecting websockets>=10.4 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 14))
  Using cached websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.8 kB)
Collecting argon2-cffi-bindings (from argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 10))
  Using cached argon2_cffi_bindings-25.1.0-cp39-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl.metadata (7.4 kB)
Collecting cffi>=1.0.1 (from argon2-cffi-bindings->argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 10))
  Using cached cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.6 kB)
Collecting pycparser (from cffi>=1.0.1->argon2-cffi-bindings->argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 10))
  Using cached pycparser-2.23-py3-none-any.whl.metadata (993 bytes)
Using cached jinja2-3.1.6-py3-none-any.whl (134 kB)
Using cached alembic-1.17.0-py3-none-any.whl (247 kB)
Using cached APScheduler-3.10.4-py3-none-any.whl (59 kB)
Using cached asgi_correlation_id-4.3.1-py3-none-any.whl (15 kB)
Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.1 MB)
Using cached black-25.9.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl (1.6 MB)
Using cached boto3-1.40.21-py3-none-any.whl (139 kB)
Using cached minio-7.2.18-py3-none-any.whl (93 kB)
Using cached vulture-2.10-py2.py3-none-any.whl (27 kB)
Using cached celery-5.5.3-py3-none-any.whl (438 kB)
Using cached fastapi-0.116.1-py3-none-any.whl (95 kB)
Using cached fastapi_limiter-0.1.6-py3-none-any.whl (15 kB)
Using cached IMAPClient-3.0.1-py2.py3-none-any.whl (182 kB)
Using cached mypy_extensions-1.1.0-py3-none-any.whl (5.0 kB)
Using cached openpyxl-3.1.5-py2.py3-none-any.whl (250 kB)
Using cached pandas-2.3.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (12.4 MB)
Using cached psycopg2_binary-2.9.10-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.0 MB)
Using cached psycopg-3.2.11-py3-none-any.whl (206 kB)
Using cached pytest_asyncio-1.1.0-py3-none-any.whl (15 kB)
Using cached pytest_cov-7.0.0-py3-none-any.whl (22 kB)
Using cached pytest_postgresql-7.0.2-py3-none-any.whl (41 kB)
Using cached python_telegram_bot-22.5-py3-none-any.whl (730 kB)
Using cached requests-2.32.5-py3-none-any.whl (64 kB)
Using cached respx-0.22.0-py2.py3-none-any.whl (25 kB)
Using cached ruff-0.12.11-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (13.2 MB)
Downloading sqlalchemy-2.0.44-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.3/3.3 MB 49.0 MB/s  0:00:00
Using cached structlog-24.1.0-py3-none-any.whl (65 kB)
Using cached testcontainers-4.12.0-py3-none-any.whl (111 kB)
Using cached types_requests-2.32.4.20250809-py3-none-any.whl (20 kB)
Using cached docspec_python-2.2.2-py3-none-any.whl (15 kB)
Using cached pydoc_markdown-4.8.2-py3-none-any.whl (67 kB)
Using cached docspec-2.2.1-py3-none-any.whl (9.8 kB)
Using cached psycopg_binary-3.2.11-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (4.4 MB)
Using cached redis-6.4.0-py3-none-any.whl (279 kB)
Using cached httpx-0.27.2-py3-none-any.whl (76 kB)
Using cached mypy-1.18.2-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (13.2 MB)
Using cached numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (18.3 MB)
Using cached pydantic-2.11.7-py3-none-any.whl (444 kB)
Using cached pydantic_core-2.33.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.0 MB)
Using cached pandera-0.26.1-py3-none-any.whl (292 kB)
Using cached billiard-4.2.2-py3-none-any.whl (86 kB)
Downloading botocore-1.40.60-py3-none-any.whl (14.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 14.1/14.1 MB 166.0 MB/s  0:00:00
Using cached charset_normalizer-3.4.4-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (151 kB)
Using cached click-8.3.0-py3-none-any.whl (107 kB)
Using cached databind.core-4.5.2-py3-none-any.whl (1.5 kB)
Using cached databind-4.5.2-py3-none-any.whl (49 kB)
Using cached databind.json-4.5.2-py3-none-any.whl (1.5 kB)
Using cached Deprecated-1.2.18-py2.py3-none-any.whl (10.0 kB)
Using cached httpcore-1.0.5-py3-none-any.whl (77 kB)
Using cached h11-0.14.0-py3-none-any.whl (58 kB)
Using cached idna-3.11-py3-none-any.whl (71 kB)
Using cached jmespath-1.0.1-py3-none-any.whl (20 kB)
Using cached kombu-5.5.4-py3-none-any.whl (210 kB)
Using cached vine-5.1.0-py3-none-any.whl (9.6 kB)
Using cached amqp-5.3.1-py3-none-any.whl (50 kB)
Using cached nr_date-2.1.0-py3-none-any.whl (10 kB)
Using cached nr_stream-1.1.5-py3-none-any.whl (10 kB)
Using cached nr.util-0.8.12-py3-none-any.whl (90 kB)
Using cached pytest-8.4.2-py3-none-any.whl (365 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
Using cached pyyaml-6.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (806 kB)
Using cached s3transfer-0.13.1-py3-none-any.whl (85 kB)
Using cached starlette-0.47.3-py3-none-any.whl (72 kB)
Using cached anyio-4.4.0-py3-none-any.whl (86 kB)
Using cached tomli-2.3.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (242 kB)
Using cached tomli_w-1.2.0-py3-none-any.whl (6.7 kB)
Using cached typeapi-2.3.0-py3-none-any.whl (26 kB)
Using cached typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Using cached urllib3-2.5.0-py3-none-any.whl (129 kB)
Using cached wrapt-1.17.3-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (82 kB)
Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Using cached pydantic_settings-2.2.1-py3-none-any.whl (13 kB)
Using cached python_dotenv-1.1.1-py3-none-any.whl (20 kB)
Using cached python_multipart-0.0.19-py3-none-any.whl (24 kB)
Using cached annotated_types-0.7.0-py3-none-any.whl (13 kB)
Using cached certifi-2025.10.5-py3-none-any.whl (163 kB)
Using cached click_didyoumean-0.3.1-py3-none-any.whl (3.6 kB)
Using cached click_plugins-1.1.1.2-py2.py3-none-any.whl (11 kB)
Using cached click_repl-0.3.0-py3-none-any.whl (10 kB)
Using cached coverage-7.11.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (248 kB)
Using cached email_validator-2.3.0-py3-none-any.whl (35 kB)
Using cached dnspython-2.8.0-py3-none-any.whl (331 kB)
Using cached fastapi_cli-0.0.14-py3-none-any.whl (11 kB)
Using cached fastapi_cloud_cli-0.3.1-py3-none-any.whl (19 kB)
Using cached greenlet-3.2.4-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (587 kB)
Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Using cached markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Using cached mirakuru-2.6.1-py3-none-any.whl (26 kB)
Downloading orjson-3.11.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (136 kB)
Using cached packaging-25.0-py3-none-any.whl (66 kB)
Using cached pathspec-0.12.1-py3-none-any.whl (31 kB)
Using cached platformdirs-4.5.0-py3-none-any.whl (18 kB)
Using cached port_for-1.0.0-py3-none-any.whl (17 kB)
Using cached prompt_toolkit-3.0.52-py3-none-any.whl (391 kB)
Downloading psutil-7.1.2-cp36-abi3-manylinux2010_x86_64.manylinux_2_12_x86_64.manylinux_2_28_x86_64.whl (258 kB)
Using cached pydantic_extra_types-2.10.6-py3-none-any.whl (40 kB)
Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
Using cached pytokens-0.2.0-py3-none-any.whl (12 kB)
Using cached pytz-2025.2-py2.py3-none-any.whl (509 kB)
Using cached rich_toolkit-0.15.1-py3-none-any.whl (29 kB)
Using cached rich-14.2.0-py3-none-any.whl (243 kB)
Using cached markdown_it_py-4.0.0-py3-none-any.whl (87 kB)
Using cached mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Using cached rignore-0.7.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (952 kB)
Using cached sentry_sdk-2.20.0-py2.py3-none-any.whl (322 kB)
Using cached six-1.17.0-py2.py3-none-any.whl (11 kB)
Using cached sniffio-1.3.1-py3-none-any.whl (10 kB)
Using cached typer-0.20.0-py3-none-any.whl (47 kB)
Using cached shellingham-1.5.4-py2.py3-none-any.whl (9.8 kB)
Using cached typing_inspect-0.9.0-py3-none-any.whl (8.8 kB)
Using cached typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Using cached tzdata-2025.2-py2.py3-none-any.whl (347 kB)
Using cached tzlocal-5.3.1-py3-none-any.whl (18 kB)
Using cached ujson-5.11.0-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (57 kB)
Using cached uvicorn-0.35.0-py3-none-any.whl (66 kB)
Using cached httptools-0.7.1-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (456 kB)
Using cached uvloop-0.22.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (3.8 MB)
Using cached watchfiles-1.1.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Using cached websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (182 kB)
Using cached yapf-0.43.0-py3-none-any.whl (256 kB)
Using cached argon2_cffi-25.1.0-py3-none-any.whl (14 kB)
Using cached argon2_cffi_bindings-25.1.0-cp39-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl (87 kB)
Using cached cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (215 kB)
Using cached docker-7.1.0-py3-none-any.whl (147 kB)
Using cached et_xmlfile-2.0.0-py3-none-any.whl (18 kB)
Using cached mako-1.3.10-py3-none-any.whl (78 kB)
Using cached pycparser-2.23-py3-none-any.whl (118 kB)
Using cached pycryptodome-3.23.0-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.3 MB)
Using cached toml-0.10.2-py2.py3-none-any.whl (16 kB)
Using cached typeguard-4.4.4-py3-none-any.whl (34 kB)
Using cached watchdog-6.0.0-py3-none-manylinux2014_x86_64.whl (79 kB)
Using cached wcwidth-0.2.14-py2.py3-none-any.whl (37 kB)
Installing collected packages: pytz, wrapt, websockets, wcwidth, watchdog, vine, uvloop, urllib3, ujson, tzlocal, tzdata, typing-extensions, tomli_w, tomli, toml, structlog, sniffio, six, shellingham, ruff, rignore, redis, PyYAML, pytokens, python-multipart, python-dotenv, pygments, pycryptodome, pycparser, psycopg2-binary, psycopg-binary, psutil, port-for, pluggy, platformdirs, pathspec, packaging, orjson, numpy, nr-stream, nr-date, mypy-extensions, mdurl, MarkupSafe, jmespath, itsdangerous, iniconfig, imapclient, idna, httptools, h11, greenlet, et-xmlfile, docstring-parser, dnspython, coverage, click, charset_normalizer, certifi, billiard, asyncpg, annotated-types, yapf, vulture, uvicorn, typing-inspection, typing_inspect, types-requests, typeguard, typeapi, sqlalchemy, sentry-sdk, requests, python-dateutil, pytest, pydantic-core, psycopg, prompt-toolkit, openpyxl, mypy, mirakuru, markdown-it-py, Mako, Jinja2, httpcore, email-validator, Deprecated, click-plugins, click-didyoumean, cffi, black, apscheduler, anyio, amqp, watchfiles, starlette, rich, pytest-postgresql, pytest-cov, pytest-asyncio, pydantic, pandas, nr-util, kombu, httpx, docker, databind, click-repl, botocore, argon2-cffi-bindings, alembic, typer, testcontainers, s3transfer, rich-toolkit, respx, python-telegram-bot, pydantic-settings, pydantic-extra-types, pandera, fastapi, databind.json, databind.core, celery, asgi-correlation-id, argon2-cffi, minio, fastapi-limiter, fastapi-cloud-cli, fastapi-cli, docspec, boto3, docspec-python, pydoc-markdown

Successfully installed Deprecated-1.2.18 Jinja2-3.1.6 Mako-1.3.10 MarkupSafe-3.0.3 PyYAML-6.0.3 alembic-1.17.0 amqp-5.3.1 annotated-types-0.7.0 anyio-4.4.0 apscheduler-3.10.4 argon2-cffi-25.1.0 argon2-cffi-bindings-25.1.0 asgi-correlation-id-4.3.1 asyncpg-0.30.0 billiard-4.2.2 black-25.9.0 boto3-1.40.21 botocore-1.40.60 celery-5.5.3 certifi-2025.10.5 cffi-2.0.0 charset_normalizer-3.4.4 click-8.3.0 click-didyoumean-0.3.1 click-plugins-1.1.1.2 click-repl-0.3.0 coverage-7.11.0 databind-4.5.2 databind.core-4.5.2 databind.json-4.5.2 dnspython-2.8.0 docker-7.1.0 docspec-2.2.1 docspec-python-2.2.2 docstring-parser-0.11 email-validator-2.3.0 et-xmlfile-2.0.0 fastapi-0.116.1 fastapi-cli-0.0.14 fastapi-cloud-cli-0.3.1 fastapi-limiter-0.1.6 greenlet-3.2.4 h11-0.14.0 httpcore-1.0.5 httptools-0.7.1 httpx-0.27.2 idna-3.11 imapclient-3.0.1 iniconfig-2.3.0 itsdangerous-2.2.0 jmespath-1.0.1 kombu-5.5.4 markdown-it-py-4.0.0 mdurl-0.1.2 minio-7.2.18 mirakuru-2.6.1 mypy-1.18.2 mypy-extensions-1.1.0 nr-date-2.1.0 nr-stream-1.1.5 nr-util-0.8.12 numpy-1.26.4 openpyxl-3.1.5 orjson-3.11.4 packaging-25.0 pandas-2.3.2 pandera-0.26.1 pathspec-0.12.1 platformdirs-4.5.0 pluggy-1.6.0 port-for-1.0.0 prompt-toolkit-3.0.52 psutil-7.1.2 psycopg-3.2.11 psycopg-binary-3.2.11 psycopg2-binary-2.9.10 pycparser-2.23 pycryptodome-3.23.0 pydantic-2.11.7 pydantic-core-2.33.2 pydantic-extra-types-2.10.6 pydantic-settings-2.2.1 pydoc-markdown-4.8.2 pygments-2.19.2 pytest-8.4.2 pytest-asyncio-1.1.0 pytest-cov-7.0.0 pytest-postgresql-7.0.2 python-dateutil-2.9.0.post0 python-dotenv-1.1.1 python-multipart-0.0.19 python-telegram-bot-22.5 pytokens-0.2.0 pytz-2025.2 redis-6.4.0 requests-2.32.5 respx-0.22.0 rich-14.2.0 rich-toolkit-0.15.1 rignore-0.7.1 ruff-0.12.11 s3transfer-0.13.1 sentry-sdk-2.20.0 shellingham-1.5.4 six-1.17.0 sniffio-1.3.1 sqlalchemy-2.0.44 starlette-0.47.3 structlog-24.1.0 testcontainers-4.12.0 toml-0.10.2 tomli-2.3.0 tomli_w-1.2.0 typeapi-2.3.0 typeguard-4.4.4 typer-0.20.0 types-requests-2.32.4.20250809 typing-extensions-4.15.0 typing-inspection-0.4.2 typing_inspect-0.9.0 tzdata-2025.2 tzlocal-5.3.1 ujson-5.11.0 urllib3-2.5.0 uvicorn-0.35.0 uvloop-0.22.1 vine-5.1.0 vulture-2.10 watchdog-6.0.0 watchfiles-1.1.1 wcwidth-0.2.14 websockets-15.0.1 wrapt-1.17.3 yapf-0.43.0
Requirement already satisfied: python-telegram-bot==22.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 1)) (22.5)
Requirement already satisfied: apscheduler==3.10.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 2)) (3.10.4)
Requirement already satisfied: asyncpg==0.30.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 3)) (0.30.0)
Requirement already satisfied: httpx<0.29,>=0.27 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (0.27.2)
Requirement already satisfied: six>=1.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (1.17.0)
Requirement already satisfied: pytz in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (2025.2)
Requirement already satisfied: tzlocal!=3.*,>=2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (5.3.1)
Requirement already satisfied: anyio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (4.4.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (2025.10.5)
Requirement already satisfied: httpcore==1.* in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (1.0.5)
Requirement already satisfied: idna in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (3.11)
Requirement already satisfied: sniffio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (1.3.1)
Requirement already satisfied: h11<0.15,>=0.13 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpcore==1.*->httpx<0.29,>=0.27->python-telegram-bot==22.5->-r services/alert_bot/requirements.txt (line 1)) (0.14.0)
Requirement already satisfied: uvicorn==0.35.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 1)) (0.35.0)
Requirement already satisfied: pydantic-settings==2.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 2)) (2.2.1)
Requirement already satisfied: fastapi==0.116.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 3)) (0.116.1)
ERROR: Cannot install sqlalchemy==2.0.43 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested sqlalchemy==2.0.43
    The user requested (constraint) sqlalchemy==2.0.44

Additionally, some packages in these conflicts have no matching distributions available for your environment:
    sqlalchemy

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
GITHUB_ACTOR=dependabot[bot]
GITHUB_ACTOR_ID=49699333
GITHUB_API_URL=https://api.github.com
GITHUB_BASE_REF=main
GITHUB_ENV=/home/runner/work/_temp/_runner_file_commands/set_env_e4e0aef3-53c7-481a-b074-c0061ba62ab2
GITHUB_EVENT_NAME=pull_request
GITHUB_EVENT_PATH=/home/runner/work/_temp/_github_workflow/event.json
GITHUB_GRAPHQL_URL=https://api.github.com/graphql
GITHUB_HEAD_REF=dependabot/pip/main/sqlalchemy-2.0.44
GITHUB_JOB=unit
GITHUB_OUTPUT=/home/runner/work/_temp/_runner_file_commands/set_output_e4e0aef3-53c7-481a-b074-c0061ba62ab2
GITHUB_PATH=/home/runner/work/_temp/_runner_file_commands/add_path_e4e0aef3-53c7-481a-b074-c0061ba62ab2
GITHUB_REF=refs/pull/460/merge
GITHUB_REF_NAME=460/merge
GITHUB_REF_PROTECTED=false
GITHUB_REF_TYPE=branch
GITHUB_REPOSITORY=AlexBomber12/AWA-App
GITHUB_REPOSITORY_ID=1011502908
GITHUB_REPOSITORY_OWNER=AlexBomber12
GITHUB_REPOSITORY_OWNER_ID=48256657
GITHUB_RETENTION_DAYS=90
GITHUB_RUN_ATTEMPT=1
GITHUB_RUN_ID=18853836109
GITHUB_RUN_NUMBER=1244
GITHUB_SERVER_URL=https://github.com
GITHUB_SHA=8835b862b2ea33cc1eded69c3b091a31950d3f1e
GITHUB_STATE=/home/runner/work/_temp/_runner_file_commands/save_state_e4e0aef3-53c7-481a-b074-c0061ba62ab2
GITHUB_STEP_SUMMARY=/home/runner/work/_temp/_runner_file_commands/step_summary_e4e0aef3-53c7-481a-b074-c0061ba62ab2
GITHUB_TRIGGERING_ACTOR=dependabot[bot]
GITHUB_WORKFLOW=ci
GITHUB_WORKFLOW_REF=AlexBomber12/AWA-App/.github/workflows/ci.yml@refs/pull/460/merge
GITHUB_WORKFLOW_SHA=8835b862b2ea33cc1eded69c3b091a31950d3f1e
GITHUB_WORKSPACE=/home/runner/work/AWA-App/AWA-App
GOROOT_1_22_X64=/opt/hostedtoolcache/go/1.22.12/x64
GOROOT_1_23_X64=/opt/hostedtoolcache/go/1.23.12/x64
GOROOT_1_24_X64=/opt/hostedtoolcache/go/1.24.7/x64
GRADLE_HOME=/usr/share/gradle-9.1.0
HOME=/home/runner
HOMEBREW_CLEANUP_PERIODIC_FULL_DAYS=3650
HOMEBREW_NO_AUTO_UPDATE=1
INVOCATION_ID=ce90f2378ccc4073983e5adec7d57041
ImageOS=ubuntu24
ImageVersion=20250929.60.1
JAVA_HOME=/usr/lib/jvm/temurin-17-jdk-amd64
JAVA_HOME_11_X64=/usr/lib/jvm/temurin-11-jdk-amd64
JAVA_HOME_17_X64=/usr/lib/jvm/temurin-17-jdk-amd64
JAVA_HOME_21_X64=/usr/lib/jvm/temurin-21-jdk-amd64
JAVA_HOME_25_X64=/usr/lib/jvm/temurin-25-jdk-amd64
JAVA_HOME_8_X64=/usr/lib/jvm/temurin-8-jdk-amd64
JOURNAL_STREAM=9:14865
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
Python3_ROOT_DI

_Truncated digest: original length exceeded limit._
