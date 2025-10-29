<!-- AWA-CI-DIGEST -->
## CI digest for `2910a532`

- **Preview URL**: n/a
- **Mirror path**: ci-logs/mirror-logs/pr-469/latest
- **Workflow run**: [18920760006](https://github.com/AlexBomber12/AWA-App/actions/runs/18920760006)

| Job | Conclusion | URL |
| --- | ---------- | --- |
| secrets scan (gitleaks) | ✅ Success | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18920760006/job/54015974164) |
| unit | ❌ Failure | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18920760006/job/54015974157) |
| k6 smoke (non-blocking) | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18920760006/job/54016171765) |
| preview | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18920760006/job/54016171816) |
| integration | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18920760006/job/54016171822) |
| migrations | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18920760006/job/54016171843) |
| mirror_logs | ⏳ In Progress | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18920760006/job/54016171808) |

### Failed tails

**unit** (`unit/unit-setup.log`)

```
Collecting rich>=13.7.1 (from rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached rich-14.2.0-py3-none-any.whl.metadata (18 kB)
Collecting markdown-it-py>=2.2.0 (from rich>=13.7.1->rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached markdown_it_py-4.0.0-py3-none-any.whl.metadata (7.3 kB)
Collecting mdurl~=0.1 (from markdown-it-py>=2.2.0->rich>=13.7.1->rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached mdurl-0.1.2-py3-none-any.whl.metadata (1.6 kB)
Collecting shellingham>=1.3.0 (from typer>=0.15.1->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached shellingham-1.5.4-py2.py3-none-any.whl.metadata (3.5 kB)
Collecting httptools>=0.6.3 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached httptools-0.7.1-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (3.5 kB)
Collecting uvloop>=0.15.1 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached uvloop-0.22.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (4.9 kB)
Collecting watchfiles>=0.13 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached watchfiles-1.1.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
Collecting websockets>=10.4 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.8 kB)
Collecting distlib<1,>=0.3.7 (from virtualenv>=20.10.0->pre-commit==3.7.1->-r requirements-dev.txt (line 20))
  Using cached distlib-0.4.0-py2.py3-none-any.whl.metadata (5.2 kB)
Collecting filelock<4,>=3.12.2 (from virtualenv>=20.10.0->pre-commit==3.7.1->-r requirements-dev.txt (line 20))
  Using cached filelock-3.20.0-py3-none-any.whl.metadata (2.1 kB)
Collecting argon2-cffi-bindings (from argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 11))
  Using cached argon2_cffi_bindings-25.1.0-cp39-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl.metadata (7.4 kB)
Collecting cffi>=1.0.1 (from argon2-cffi-bindings->argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 11))
  Using cached cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.6 kB)
Collecting pycparser (from cffi>=1.0.1->argon2-cffi-bindings->argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 11))
  Using cached pycparser-2.23-py3-none-any.whl.metadata (993 bytes)
Using cached jinja2-3.1.6-py3-none-any.whl (134 kB)
Using cached alembic-1.17.0-py3-none-any.whl (247 kB)
Using cached APScheduler-3.10.4-py3-none-any.whl (59 kB)
Using cached asgi_correlation_id-4.3.1-py3-none-any.whl (15 kB)
Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.1 MB)
Using cached Authlib-1.3.1-py2.py3-none-any.whl (223 kB)
Using cached black-25.9.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl (1.6 MB)
Using cached boto3-1.40.21-py3-none-any.whl (139 kB)
Using cached minio-7.2.18-py3-none-any.whl (93 kB)
Using cached vulture-2.10-py2.py3-none-any.whl (27 kB)
Using cached celery-5.5.3-py3-none-any.whl (438 kB)
Using cached fastapi-0.116.1-py3-none-any.whl (95 kB)
Using cached fastapi_limiter-0.1.6-py3-none-any.whl (15 kB)
Using cached IMAPClient-3.0.1-py2.py3-none-any.whl (182 kB)
Using cached pre_commit-3.7.1-py2.py3-none-any.whl (204 kB)
Using cached mypy_extensions-1.1.0-py3-none-any.whl (5.0 kB)
Using cached openpyxl-3.1.5-py2.py3-none-any.whl (250 kB)
Using cached pandas-2.3.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (12.4 MB)
Using cached prometheus_client-0.20.0-py3-none-any.whl (54 kB)
Using cached psycopg2_binary-2.9.10-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.0 MB)
Using cached psycopg-3.2.11-py3-none-any.whl (206 kB)
Using cached pytest_asyncio-1.1.0-py3-none-any.whl (15 kB)
Using cached pytest_cov-7.0.0-py3-none-any.whl (22 kB)
Using cached pytest_postgresql-7.0.2-py3-none-any.whl (41 kB)
Using cached pytest_timeout-2.3.1-py3-none-any.whl (14 kB)
Using cached python_jose-3.3.0-py2.py3-none-any.whl (33 kB)
Using cached python_telegram_bot-22.5-py3-none-any.whl (730 kB)
Using cached requests-2.32.5-py3-none-any.whl (64 kB)
Using cached respx-0.22.0-py2.py3-none-any.whl (25 kB)
Using cached ruff-0.7.0-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (10.9 MB)
Using cached sqlalchemy-2.0.43-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.3 MB)
Using cached structlog-24.1.0-py3-none-any.whl (65 kB)
Using cached testcontainers-4.12.0-py3-none-any.whl (111 kB)
Using cached types_requests-2.32.4.20250809-py3-none-any.whl (20 kB)
Using cached docspec_python-2.2.2-py3-none-any.whl (15 kB)
Using cached pydoc_markdown-4.8.2-py3-none-any.whl (67 kB)
Using cached docspec-2.2.1-py3-none-any.whl (9.8 kB)
Using cached pytest_xdist-3.6.1-py3-none-any.whl (46 kB)
Using cached psycopg_binary-3.2.11-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (4.4 MB)
Using cached redis-6.4.0-py3-none-any.whl (279 kB)
Using cached httpx-0.27.2-py3-none-any.whl (76 kB)
Using cached mypy-1.18.2-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (13.2 MB)
Using cached numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (18.3 MB)
Using cached pydantic-2.11.7-py3-none-any.whl (444 kB)
Using cached pydantic_core-2.33.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.0 MB)
Using cached pandera-0.26.1-py3-none-any.whl (292 kB)
Using cached billiard-4.2.2-py3-none-any.whl (86 kB)
Using cached botocore-1.40.61-py3-none-any.whl (14.1 MB)
Using cached charset_normalizer-3.4.4-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (151 kB)
Using cached click-8.3.0-py3-none-any.whl (107 kB)
Using cached databind.core-4.5.2-py3-none-any.whl (1.5 kB)
Using cached databind-4.5.2-py3-none-any.whl (49 kB)
Using cached databind.json-4.5.2-py3-none-any.whl (1.5 kB)
Downloading deprecated-1.3.0-py2.py3-none-any.whl (11 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
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
Downloading wrapt-2.0.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (114 kB)
Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Using cached pydantic_settings-2.2.1-py3-none-any.whl (13 kB)
Using cached python_dotenv-1.1.1-py3-none-any.whl (20 kB)
Using cached python_multipart-0.0.19-py3-none-any.whl (24 kB)
Using cached annotated_types-0.7.0-py3-none-any.whl (13 kB)
Using cached certifi-2025.10.5-py3-none-any.whl (163 kB)
Using cached cfgv-3.4.0-py2.py3-none-any.whl (7.2 kB)
Using cached click_didyoumean-0.3.1-py3-none-any.whl (3.6 kB)
Using cached click_plugins-1.1.1.2-py2.py3-none-any.whl (11 kB)
Using cached click_repl-0.3.0-py3-none-any.whl (10 kB)
Using cached coverage-7.11.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (248 kB)
Using cached ecdsa-0.19.1-py2.py3-none-any.whl (150 kB)
Using cached email_validator-2.3.0-py3-none-any.whl (35 kB)
Using cached dnspython-2.8.0-py3-none-any.whl (331 kB)
Using cached execnet-2.1.1-py3-none-any.whl (40 kB)
Using cached fastapi_cli-0.0.14-py3-none-any.whl (11 kB)
Using cached fastapi_cloud_cli-0.3.1-py3-none-any.whl (19 kB)
Using cached greenlet-3.2.4-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (587 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached identify-2.6.15-py2.py3-none-any.whl (99 kB)
Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Using cached markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Using cached mirakuru-2.6.1-py3-none-any.whl (26 kB)
Using cached nodeenv-1.9.1-py2.py3-none-any.whl (22 kB)
Using cached orjson-3.11.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (136 kB)
Using cached packaging-25.0-py3-none-any.whl (66 kB)
Using cached pathspec-0.12.1-py3-none-any.whl (31 kB)
Using cached platformdirs-4.5.0-py3-none-any.whl (18 kB)
Using cached port_for-1.0.0-py3-none-any.whl (17 kB)
Using cached prompt_toolkit-3.0.52-py3-none-any.whl (391 kB)
Using cached psutil-7.1.2-cp36-abi3-manylinux2010_x86_64.manylinux_2_12_x86_64.manylinux_2_28_x86_64.whl (258 kB)
Using cached pydantic_extra_types-2.10.6-py3-none-any.whl (40 kB)
Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
Using cached pytokens-0.2.0-py3-none-any.whl (12 kB)
Using cached pytz-2025.2-py2.py3-none-any.whl (509 kB)
Using cached rich_toolkit-0.15.1-py3-none-any.whl (29 kB)
Using cached rich-14.2.0-py3-none-any.whl (243 kB)
Using cached markdown_it_py-4.0.0-py3-none-any.whl (87 kB)
Using cached mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Downloading rignore-0.7.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (959 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 959.6/959.6 kB 37.0 MB/s  0:00:00
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
Downloading virtualenv-20.35.4-py3-none-any.whl (6.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.0/6.0 MB 145.8 MB/s  0:00:00
Using cached distlib-0.4.0-py2.py3-none-any.whl (469 kB)
Using cached filelock-3.20.0-py3-none-any.whl (16 kB)
Using cached watchfiles-1.1.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Using cached websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (182 kB)
Using cached yapf-0.43.0-py3-none-any.whl (256 kB)
Using cached argon2_cffi-25.1.0-py3-none-any.whl (14 kB)
Using cached argon2_cffi_bindings-25.1.0-cp39-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl (87 kB)
Using cached cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (215 kB)
Using cached cryptography-46.0.3-cp311-abi3-manylinux_2_34_x86_64.whl (4.5 MB)
Using cached docker-7.1.0-py3-none-any.whl (147 kB)
Using cached et_xmlfile-2.0.0-py3-none-any.whl (18 kB)
Using cached mako-1.3.10-py3-none-any.whl (78 kB)
Using cached pyasn1-0.6.1-py3-none-any.whl (83 kB)
Using cached pycparser-2.23-py3-none-any.whl (118 kB)
Using cached pycryptodome-3.23.0-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.3 MB)
Using cached rsa-4.9.1-py3-none-any.whl (34 kB)
Using cached toml-0.10.2-py2.py3-none-any.whl (16 kB)
Using cached typeguard-4.4.4-py3-none-any.whl (34 kB)
Using cached watchdog-6.0.0-py3-none-manylinux2014_x86_64.whl (79 kB)
Using cached wcwidth-0.2.14-py2.py3-none-any.whl (37 kB)
Installing collected packages: pytz, distlib, wrapt, websockets, wcwidth, watchdog, vine, uvloop, urllib3, ujson, tzlocal, tzdata, typing-extensions, tomli_w, tomli, toml, structlog, sniffio, six, shellingham, ruff, rignore, redis, pyyaml, pytokens, python-multipart, python-dotenv, pygments, pycryptodome, pycparser, pyasn1, psycopg2-binary, psycopg-binary, psutil, prometheus-client, port-for, pluggy, platformdirs, pathspec, packaging, orjson, numpy, nr-stream, nr-date, nodeenv, mypy-extensions, mdurl, MarkupSafe, jmespath, itsdangerous, iniconfig, imapclient, idna, identify, httptools, h11, greenlet, filelock, execnet, et-xmlfile, docstring-parser, dnspython, coverage, click, charset_normalizer, cfgv, certifi, billiard, asyncpg, annotated-types, yapf, vulture, virtualenv, uvicorn, typing-inspection, typing_inspect, types-requests, typeguard, typeapi, sqlalchemy, sentry-sdk, rsa, requests, python-dateutil, pytest, pydantic-core, psycopg, prompt-toolkit, openpyxl, mypy, mirakuru, markdown-it-py, Mako, Jinja2, httpcore, email-validator, ecdsa, Deprecated, click-plugins, click-didyoumean, cffi, black, apscheduler, anyio, amqp, watchfiles, starlette, rich, python-jose, pytest-xdist, pytest-timeout, pytest-postgresql, pytest-cov, pytest-asyncio, pydantic, pre-commit, pandas, nr-util, kombu, httpx, docker, databind, cryptography, click-repl, botocore, argon2-cffi-bindings, alembic, typer, testcontainers, s3transfer, rich-toolkit, respx, python-telegram-bot, pydantic-settings, pydantic-extra-types, pandera, fastapi, databind.json, databind.core, celery, authlib, asgi-correlation-id, argon2-cffi, minio, fastapi-limiter, fastapi-cloud-cli, fastapi-cli, docspec, boto3, docspec-python, pydoc-markdown

Successfully installed Deprecated-1.3.0 Jinja2-3.1.6 Mako-1.3.10 MarkupSafe-3.0.3 alembic-1.17.0 amqp-5.3.1 annotated-types-0.7.0 anyio-4.4.0 apscheduler-3.10.4 argon2-cffi-25.1.0 argon2-cffi-bindings-25.1.0 asgi-correlation-id-4.3.1 asyncpg-0.30.0 authlib-1.3.1 billiard-4.2.2 black-25.9.0 boto3-1.40.21 botocore-1.40.61 celery-5.5.3 certifi-2025.10.5 cffi-2.0.0 cfgv-3.4.0 charset_normalizer-3.4.4 click-8.3.0 click-didyoumean-0.3.1 click-plugins-1.1.1.2 click-repl-0.3.0 coverage-7.11.0 cryptography-46.0.3 databind-4.5.2 databind.core-4.5.2 databind.json-4.5.2 distlib-0.4.0 dnspython-2.8.0 docker-7.1.0 docspec-2.2.1 docspec-python-2.2.2 docstring-parser-0.11 ecdsa-0.19.1 email-validator-2.3.0 et-xmlfile-2.0.0 execnet-2.1.1 fastapi-0.116.1 fastapi-cli-0.0.14 fastapi-cloud-cli-0.3.1 fastapi-limiter-0.1.6 filelock-3.20.0 greenlet-3.2.4 h11-0.16.0 httpcore-1.0.9 httptools-0.7.1 httpx-0.27.2 identify-2.6.15 idna-3.11 imapclient-3.0.1 iniconfig-2.3.0 itsdangerous-2.2.0 jmespath-1.0.1 kombu-5.5.4 markdown-it-py-4.0.0 mdurl-0.1.2 minio-7.2.18 mirakuru-2.6.1 mypy-1.18.2 mypy-extensions-1.1.0 nodeenv-1.9.1 nr-date-2.1.0 nr-stream-1.1.5 nr-util-0.8.12 numpy-1.26.4 openpyxl-3.1.5 orjson-3.11.4 packaging-25.0 pandas-2.3.2 pandera-0.26.1 pathspec-0.12.1 platformdirs-4.5.0 pluggy-1.6.0 port-for-1.0.0 pre-commit-3.7.1 prometheus-client-0.20.0 prompt-toolkit-3.0.52 psutil-7.1.2 psycopg-3.2.11 psycopg-binary-3.2.11 psycopg2-binary-2.9.10 pyasn1-0.6.1 pycparser-2.23 pycryptodome-3.23.0 pydantic-2.11.7 pydantic-core-2.33.2 pydantic-extra-types-2.10.6 pydantic-settings-2.2.1 pydoc-markdown-4.8.2 pygments-2.19.2 pytest-8.4.2 pytest-asyncio-1.1.0 pytest-cov-7.0.0 pytest-postgresql-7.0.2 pytest-timeout-2.3.1 pytest-xdist-3.6.1 python-dateutil-2.9.0.post0 python-dotenv-1.1.1 python-jose-3.3.0 python-multipart-0.0.19 python-telegram-bot-22.5 pytokens-0.2.0 pytz-2025.2 pyyaml-6.0.3 redis-6.4.0 requests-2.32.5 respx-0.22.0 rich-14.2.0 rich-toolkit-0.15.1 rignore-0.7.2 rsa-4.9.1 ruff-0.7.0 s3transfer-0.13.1 sentry-sdk-2.20.0 shellingham-1.5.4 six-1.17.0 sniffio-1.3.1 sqlalchemy-2.0.43 starlette-0.47.3 structlog-24.1.0 testcontainers-4.12.0 toml-0.10.2 tomli-2.3.0 tomli_w-1.2.0 typeapi-2.3.0 typeguard-4.4.4 typer-0.20.0 types-requests-2.32.4.20250809 typing-extensions-4.15.0 typing-inspection-0.4.2 typing_inspect-0.9.0 tzdata-2025.2 tzlocal-5.3.1 ujson-5.11.0 urllib3-2.5.0 uvicorn-0.35.0 uvloop-0.22.1 vine-5.1.0 virtualenv-20.35.4 vulture-2.10 watchdog-6.0.0 watchfiles-1.1.1 wcwidth-0.2.14 websockets-15.0.1 wrapt-2.0.0 yapf-0.43.0
Obtaining file:///home/runner/work/AWA-App/AWA-App/packages/awa_common
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Getting requirements to build editable: started
  Getting requirements to build editable: finished with status 'done'
  Installing backend dependencies: started
  Installing backend dependencies: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'done'
Building wheels for collected packages: awa-common
  Building editable for awa-common (pyproject.toml): started
  Building editable for awa-common (pyproject.toml): finished with status 'done'
  Created wheel for awa-common: filename=awa_common-0.0.1-py3-none-any.whl size=986 sha256=c6310af8e5007b29b12eb82fcddba88773d429330b959c3ccb5f42a788487a78
  Stored in directory: /tmp/pip-ephem-wheel-cache-aul19bk8/wheels/58/da/3c/a7efd2bff9f1af19244156fcec46ad0dafb94fdf76dd747f48
Successfully built awa-common
Installing collected packages: awa-common
Successfully installed awa-common-0.0.1
```

**unit** (`unit-alembic.txt`)

```
 4c23e505b671 Extracting [>                                                  ]  163.8kB/15.34MB
 e69f32e226f6 Extracting [=====================================>             ]   4.85MB/6.437MB
 e69f32e226f6 Extracting [==================================================>]  6.437MB/6.437MB
 4c23e505b671 Extracting [======================>                            ]  6.881MB/15.34MB
 e69f32e226f6 Pull complete 
 147d1d7c0318 Extracting [=>                                                 ]  32.77kB/1.257MB
 147d1d7c0318 Extracting [==================================================>]  1.257MB/1.257MB
 147d1d7c0318 Pull complete 
 bc405403221b Extracting [>                                                  ]   98.3kB/8.204MB
 4c23e505b671 Extracting [=============================================>     ]  14.09MB/15.34MB
 4c23e505b671 Extracting [==================================================>]  15.34MB/15.34MB
 4c23e505b671 Pull complete 
 7985e01408e3 Extracting [==================================================>]      95B/95B
 7985e01408e3 Extracting [==================================================>]      95B/95B
 7985e01408e3 Pull complete 
 4f4fb700ef54 Extracting [==================================================>]      32B/32B
 4f4fb700ef54 Extracting [==================================================>]      32B/32B
 4f4fb700ef54 Pull complete 
 477049afe86c Extracting [==================================================>]     573B/573B
 477049afe86c Extracting [==================================================>]     573B/573B
 477049afe86c Pull complete 
 redis Pulled 
 bc405403221b Extracting [====================>                              ]  3.441MB/8.204MB
 bc405403221b Extracting [===================================>               ]  5.898MB/8.204MB
 bc405403221b Extracting [==================================================>]  8.204MB/8.204MB
 bc405403221b Pull complete 
 82742b6e768c Extracting [=>                                                 ]  32.77kB/1.311MB
 82742b6e768c Extracting [==================================================>]  1.311MB/1.311MB
 82742b6e768c Pull complete 
 bd122ab2336d Extracting [==================================================>]     116B/116B
 bd122ab2336d Extracting [==================================================>]     116B/116B
 bd122ab2336d Pull complete 
 91264d87777d Extracting [==================================================>]   3.14kB/3.14kB
 91264d87777d Extracting [==================================================>]   3.14kB/3.14kB
 91264d87777d Pull complete 
 e7fca4723572 Extracting [>                                                  ]  557.1kB/113.1MB
 e7fca4723572 Extracting [===>                                               ]  7.799MB/113.1MB
 e7fca4723572 Extracting [====>                                              ]  10.58MB/113.1MB
 e7fca4723572 Extracting [======>                                            ]  15.04MB/113.1MB
 e7fca4723572 Extracting [========>                                          ]  20.05MB/113.1MB
 e7fca4723572 Extracting [===========>                                       ]  25.62MB/113.1MB
 e7fca4723572 Extracting [===============>                                   ]  35.09MB/113.1MB
 e7fca4723572 Extracting [===================>                               ]  44.56MB/113.1MB
 e7fca4723572 Extracting [=======================>                           ]  53.48MB/113.1MB
 e7fca4723572 Extracting [==========================>                        ]  59.05MB/113.1MB
 e7fca4723572 Extracting [==============================>                    ]  67.96MB/113.1MB
 e7fca4723572 Extracting [==================================>                ]  77.99MB/113.1MB
 e7fca4723572 Extracting [======================================>            ]   86.9MB/113.1MB
 e7fca4723572 Extracting [==========================================>        ]  95.26MB/113.1MB
 e7fca4723572 Extracting [===========================================>       ]  99.16MB/113.1MB
 e7fca4723572 Extracting [============================================>      ]  101.4MB/113.1MB
 e7fca4723572 Extracting [==============================================>    ]  105.3MB/113.1MB
 e7fca4723572 Extracting [===============================================>   ]  107.5MB/113.1MB
 e7fca4723572 Extracting [================================================>  ]  109.2MB/113.1MB
 e7fca4723572 Extracting [=================================================> ]  111.4MB/113.1MB
 e7fca4723572 Extracting [=================================================> ]  112.5MB/113.1MB
 e7fca4723572 Extracting [==================================================>]  113.1MB/113.1MB
 e7fca4723572 Extracting [==================================================>]  113.1MB/113.1MB
 e7fca4723572 Pull complete 
 45e682a0ad62 Extracting [==================================================>]  10.01kB/10.01kB
 45e682a0ad62 Extracting [==================================================>]  10.01kB/10.01kB
 45e682a0ad62 Pull complete 
 8221e00ace81 Extracting [==================================================>]     128B/128B
 8221e00ace81 Extracting [==================================================>]     128B/128B
 8221e00ace81 Pull complete 
 f50de807d554 Extracting [==================================================>]     167B/167B
 f50de807d554 Extracting [==================================================>]     167B/167B
 f50de807d554 Pull complete 
 b9fcf05c0044 Extracting [==================================================>]  6.078kB/6.078kB
 b9fcf05c0044 Extracting [==================================================>]  6.078kB/6.078kB
 b9fcf05c0044 Pull complete 
 85ec668df6b0 Extracting [==================================================>]     184B/184B
 85ec668df6b0 Extracting [==================================================>]     184B/184B
 85ec668df6b0 Pull complete 
 db Pulled 
#1 [internal] load local bake definitions
#1 reading from stdin 390B done
#1 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 804B done
#2 WARN: LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 10)
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/postgres:16
#3 DONE 0.0s

#4 [internal] load .dockerignore
#4 transferring context: 183B done
#4 DONE 0.0s

#5 [internal] load build context
#5 transferring context: 577B done
#5 DONE 0.0s

#6 [1/6] FROM docker.io/library/postgres:16
#6 DONE 0.0s

#7 [2/6] RUN set -eux;     if [ -f /etc/apt/sources.list ]; then         sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list;     fi;     apt-get update;     apt-get install -y locales;     locale-gen en_US.UTF-8;     rm -rf /var/lib/apt/lists/*
#7 0.130 + [ -f /etc/apt/sources.list ]
#7 0.130 + apt-get update
#7 0.187 Get:1 http://deb.debian.org/debian trixie InRelease [140 kB]
#7 0.272 Get:2 http://apt.postgresql.org/pub/repos/apt trixie-pgdg InRelease [107 kB]
#7 0.286 Get:3 http://apt.postgresql.org/pub/repos/apt trixie-pgdg/16 amd64 Packages [2,574 B]
#7 0.299 Get:4 http://apt.postgresql.org/pub/repos/apt trixie-pgdg/main amd64 Packages [350 kB]
#7 0.311 Get:5 http://deb.debian.org/debian trixie-updates InRelease [47.3 kB]
#7 0.355 Get:6 http://deb.debian.org/debian-security trixie-security InRelease [43.4 kB]
#7 0.370 Get:7 http://deb.debian.org/debian trixie/main amd64 Packages [9,669 kB]
#7 0.488 Get:8 http://deb.debian.org/debian trixie-updates/main amd64 Packages [5,412 B]
#7 0.502 Get:9 http://deb.debian.org/debian-security trixie-security/main amd64 Packages [67.8 kB]
#7 1.135 Fetched 10.4 MB in 1s (10.6 MB/s)
#7 1.135 Reading package lists...
#7 1.634 + apt-get install -y locales
#7 1.642 Reading package lists...
#7 2.157 Building dependency tree...
#7 2.306 Reading state information...
#7 2.476 locales is already the newest version (2.41-12).
#7 2.476 0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.
#7 2.477 + locale-gen en_US.UTF-8
#7 2.480 Generating locales (this might take a while)...
#7 2.489   en_US.UTF-8... done
#7 3.668 Generation complete.
#7 3.669 + rm -rf /var/lib/apt/lists/apt.postgresql.org_pub_repos_apt_dists_trixie-pgdg_16_binary-amd64_Packages.lz4 /var/lib/apt/lists/apt.postgresql.org_pub_repos_apt_dists_trixie-pgdg_InRelease /var/lib/apt/lists/apt.postgresql.org_pub_repos_apt_dists_trixie-pgdg_main_binary-amd64_Packages.lz4 /var/lib/apt/lists/auxfiles /var/lib/apt/lists/deb.debian.org_debian-security_dists_trixie-security_InRelease /var/lib/apt/lists/deb.debian.org_debian-security_dists_trixie-security_main_binary-amd64_Packages.lz4 /var/lib/apt/lists/deb.debian.org_debian_dists_trixie-updates_InRelease /var/lib/apt/lists/deb.debian.org_debian_dists_trixie-updates_main_binary-amd64_Packages.lz4 /var/lib/apt/lists/deb.debian.org_debian_dists_trixie_InRelease /var/lib/apt/lists/deb.debian.org_debian_dists_trixie_main_binary-amd64_Packages.lz4 /var/lib/apt/lists/lock /var/lib/apt/lists/partial
#7 DONE 3.7s

#8 [3/6] COPY infra/postgres/pg_hba.conf /etc/postgresql/pg_hba.conf
#8 DONE 0.0s

#9 [4/6] COPY infra/postgres/init-pg_hba.sh /docker-entrypoint-initdb.d/10_init_pg_hba.sh
#9 DONE 0.0s

#10 [5/6] COPY infra/postgres/postgresql.conf /etc/postgresql/postgresql.conf
#10 DONE 0.0s

#11 [6/6] RUN chmod 0644 /etc/postgresql/pg_hba.conf &&     chmod +x /docker-entrypoint-initdb.d/10_init_pg_hba.sh
#11 DONE 0.1s

#12 exporting to image
#12 exporting layers
#12 exporting layers 0.8s done
#12 writing image sha256:2ca9e476e5878f889fe117913896486536cc5bd1e509d89e1aaf8005b645faf2 done
#12 naming to docker.io/library/awa-app-postgres done
#12 DONE 0.8s

#13 resolving provenance for metadata file
#13 DONE 0.0s
 postgres  Built
 Network awa-app_awa-net  Creating
 Network awa-app_awa-net  Created
 Network awa-app_default  Creating
 Network awa-app_default  Created
 Volume "awa-app_awa-data"  Creating
 Volume "awa-app_awa-data"  Created
 Volume "awa-app_awa-pgdata"  Creating
 Volume "awa-app_awa-pgdata"  Created
 Container awa-app-db-1  Creating
 Container awa-app-postgres-1  Creating
 Container awa-app-redis-1  Creating
 Container awa-app-postgres-1  Created
 Container awa-app-redis-1  Created
 Container awa-app-db-1  Created
 Container awa-app-postgres-1  Starting
 Container awa-app-db-1  Starting
 Container awa-app-redis-1  Starting
 Container awa-app-redis-1  Started
 Container awa-app-db-1  Started
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint awa-app-postgres-1 (ae42b495f779aff59c6e39f984c641afb449fe5b31917d0fbb4ab1f8819f2769): Bind for 0.0.0.0:5432 failed: port is already allocated
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
 Container awa-app-db-1  Running
 Container awa-app-redis-1  Running
 Container awa-app-postgres-1  Recreate
 Container awa-app-postgres-1  Recreated
 Container awa-app-postgres-1  Starting
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint awa-app-postgres-1 (7f56efc7bb891113d1b0522cc5952c2d11c419d656cd19047d4cfd2531c941b8): Bind for 0.0.0.0:5432 failed: port is already allocated
exit_code=1
```

**unit** (`unit-compose-logs.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml logs --no-color
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
exit_code=0
```

**unit** (`unit-compose-ps.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml ps
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:34Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS
exit_code=0
```

**unit** (`unit-migrations-alembic.txt`)

```
 4c23e505b671 Extracting [>                                                  ]  163.8kB/15.34MB
 e69f32e226f6 Extracting [=====================================>             ]   4.85MB/6.437MB
 e69f32e226f6 Extracting [==================================================>]  6.437MB/6.437MB
 4c23e505b671 Extracting [======================>                            ]  6.881MB/15.34MB
 e69f32e226f6 Pull complete 
 147d1d7c0318 Extracting [=>                                                 ]  32.77kB/1.257MB
 147d1d7c0318 Extracting [==================================================>]  1.257MB/1.257MB
 147d1d7c0318 Pull complete 
 bc405403221b Extracting [>                                                  ]   98.3kB/8.204MB
 4c23e505b671 Extracting [=============================================>     ]  14.09MB/15.34MB
 4c23e505b671 Extracting [==================================================>]  15.34MB/15.34MB
 4c23e505b671 Pull complete 
 7985e01408e3 Extracting [==================================================>]      95B/95B
 7985e01408e3 Extracting [==================================================>]      95B/95B
 7985e01408e3 Pull complete 
 4f4fb700ef54 Extracting [==================================================>]      32B/32B
 4f4fb700ef54 Extracting [==================================================>]      32B/32B
 4f4fb700ef54 Pull complete 
 477049afe86c Extracting [==================================================>]     573B/573B
 477049afe86c Extracting [==================================================>]     573B/573B
 477049afe86c Pull complete 
 redis Pulled 
 bc405403221b Extracting [====================>                              ]  3.441MB/8.204MB
 bc405403221b Extracting [===================================>               ]  5.898MB/8.204MB
 bc405403221b Extracting [==================================================>]  8.204MB/8.204MB
 bc405403221b Pull complete 
 82742b6e768c Extracting [=>                                                 ]  32.77kB/1.311MB
 82742b6e768c Extracting [==================================================>]  1.311MB/1.311MB
 82742b6e768c Pull complete 
 bd122ab2336d Extracting [==================================================>]     116B/116B
 bd122ab2336d Extracting [==================================================>]     116B/116B
 bd122ab2336d Pull complete 
 91264d87777d Extracting [==================================================>]   3.14kB/3.14kB
 91264d87777d Extracting [==================================================>]   3.14kB/3.14kB
 91264d87777d Pull complete 
 e7fca4723572 Extracting [>                                                  ]  557.1kB/113.1MB
 e7fca4723572 Extracting [===>                                               ]  7.799MB/113.1MB
 e7fca4723572 Extracting [====>                                              ]  10.58MB/113.1MB
 e7fca4723572 Extracting [======>                                            ]  15.04MB/113.1MB
 e7fca4723572 Extracting [========>                                          ]  20.05MB/113.1MB
 e7fca4723572 Extracting [===========>                                       ]  25.62MB/113.1MB
 e7fca4723572 Extracting [===============>                                   ]  35.09MB/113.1MB
 e7fca4723572 Extracting [===================>                               ]  44.56MB/113.1MB
 e7fca4723572 Extracting [=======================>                           ]  53.48MB/113.1MB
 e7fca4723572 Extracting [==========================>                        ]  59.05MB/113.1MB
 e7fca4723572 Extracting [==============================>                    ]  67.96MB/113.1MB
 e7fca4723572 Extracting [==================================>                ]  77.99MB/113.1MB
 e7fca4723572 Extracting [======================================>            ]   86.9MB/113.1MB
 e7fca4723572 Extracting [==========================================>        ]  95.26MB/113.1MB
 e7fca4723572 Extracting [===========================================>       ]  99.16MB/113.1MB
 e7fca4723572 Extracting [============================================>      ]  101.4MB/113.1MB
 e7fca4723572 Extracting [==============================================>    ]  105.3MB/113.1MB
 e7fca4723572 Extracting [===============================================>   ]  107.5MB/113.1MB
 e7fca4723572 Extracting [================================================>  ]  109.2MB/113.1MB
 e7fca4723572 Extracting [=================================================> ]  111.4MB/113.1MB
 e7fca4723572 Extracting [=================================================> ]  112.5MB/113.1MB
 e7fca4723572 Extracting [==================================================>]  113.1MB/113.1MB
 e7fca4723572 Extracting [==================================================>]  113.1MB/113.1MB
 e7fca4723572 Pull complete 
 45e682a0ad62 Extracting [==================================================>]  10.01kB/10.01kB
 45e682a0ad62 Extracting [==================================================>]  10.01kB/10.01kB
 45e682a0ad62 Pull complete 
 8221e00ace81 Extracting [==================================================>]     128B/128B
 8221e00ace81 Extracting [==================================================>]     128B/128B
 8221e00ace81 Pull complete 
 f50de807d554 Extracting [==================================================>]     167B/167B
 f50de807d554 Extracting [==================================================>]     167B/167B
 f50de807d554 Pull complete 
 b9fcf05c0044 Extracting [==================================================>]  6.078kB/6.078kB
 b9fcf05c0044 Extracting [==================================================>]  6.078kB/6.078kB
 b9fcf05c0044 Pull complete 
 85ec668df6b0 Extracting [==================================================>]     184B/184B
 85ec668df6b0 Extracting [==================================================>]     184B/184B
 85ec668df6b0 Pull complete 
 db Pulled 
#1 [internal] load local bake definitions
#1 reading from stdin 390B done
#1 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 804B done
#2 WARN: LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 10)
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/postgres:16
#3 DONE 0.0s

#4 [internal] load .dockerignore
#4 transferring context: 183B done
#4 DONE 0.0s

#5 [internal] load build context
#5 transferring context: 577B done
#5 DONE 0.0s

#6 [1/6] FROM docker.io/library/postgres:16
#6 DONE 0.0s

#7 [2/6] RUN set -eux;     if [ -f /etc/apt/sources.list ]; then         sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list;     fi;     apt-get update;     apt-get install -y locales;     locale-gen en_US.UTF-8;     rm -rf /var/lib/apt/lists/*
#7 0.130 + [ -f /etc/apt/sources.list ]
#7 0.130 + apt-get update
#7 0.187 Get:1 http://deb.debian.org/debian trixie InRelease [140 kB]
#7 0.272 Get:2 http://apt.postgresql.org/pub/repos/apt trixie-pgdg InRelease [107 kB]
#7 0.286 Get:3 http://apt.postgresql.org/pub/repos/apt trixie-pgdg/16 amd64 Packages [2,574 B]
#7 0.299 Get:4 http://apt.postgresql.org/pub/repos/apt trixie-pgdg/main amd64 Packages [350 kB]
#7 0.311 Get:5 http://deb.debian.org/debian trixie-updates InRelease [47.3 kB]
#7 0.355 Get:6 http://deb.debian.org/debian-security trixie-security InRelease [43.4 kB]
#7 0.370 Get:7 http://deb.debian.org/debian trixie/main amd64 Packages [9,669 kB]
#7 0.488 Get:8 http://deb.debian.org/debian trixie-updates/main amd64 Packages [5,412 B]
#7 0.502 Get:9 http://deb.debian.org/debian-security trixie-security/main amd64 Packages [67.8 kB]
#7 1.135 Fetched 10.4 MB in 1s (10.6 MB/s)
#7 1.135 Reading package lists...
#7 1.634 + apt-get install -y locales
#7 1.642 Reading package lists...
#7 2.157 Building dependency tree...
#7 2.306 Reading state information...
#7 2.476 locales is already the newest version (2.41-12).
#7 2.476 0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.
#7 2.477 + locale-gen en_US.UTF-8
#7 2.480 Generating locales (this might take a while)...
#7 2.489   en_US.UTF-8... done
#7 3.668 Generation complete.
#7 3.669 + rm -rf /var/lib/apt/lists/apt.postgresql.org_pub_repos_apt_dists_trixie-pgdg_16_binary-amd64_Packages.lz4 /var/lib/apt/lists/apt.postgresql.org_pub_repos_apt_dists_trixie-pgdg_InRelease /var/lib/apt/lists/apt.postgresql.org_pub_repos_apt_dists_trixie-pgdg_main_binary-amd64_Packages.lz4 /var/lib/apt/lists/auxfiles /var/lib/apt/lists/deb.debian.org_debian-security_dists_trixie-security_InRelease /var/lib/apt/lists/deb.debian.org_debian-security_dists_trixie-security_main_binary-amd64_Packages.lz4 /var/lib/apt/lists/deb.debian.org_debian_dists_trixie-updates_InRelease /var/lib/apt/lists/deb.debian.org_debian_dists_trixie-updates_main_binary-amd64_Packages.lz4 /var/lib/apt/lists/deb.debian.org_debian_dists_trixie_InRelease /var/lib/apt/lists/deb.debian.org_debian_dists_trixie_main_binary-amd64_Packages.lz4 /var/lib/apt/lists/lock /var/lib/apt/lists/partial
#7 DONE 3.7s

#8 [3/6] COPY infra/postgres/pg_hba.conf /etc/postgresql/pg_hba.conf
#8 DONE 0.0s

#9 [4/6] COPY infra/postgres/init-pg_hba.sh /docker-entrypoint-initdb.d/10_init_pg_hba.sh
#9 DONE 0.0s

#10 [5/6] COPY infra/postgres/postgresql.conf /etc/postgresql/postgresql.conf
#10 DONE 0.0s

#11 [6/6] RUN chmod 0644 /etc/postgresql/pg_hba.conf &&     chmod +x /docker-entrypoint-initdb.d/10_init_pg_hba.sh
#11 DONE 0.1s

#12 exporting to image
#12 exporting layers
#12 exporting layers 0.8s done
#12 writing image sha256:2ca9e476e5878f889fe117913896486536cc5bd1e509d89e1aaf8005b645faf2 done
#12 naming to docker.io/library/awa-app-postgres done
#12 DONE 0.8s

#13 resolving provenance for metadata file
#13 DONE 0.0s
 postgres  Built
 Network awa-app_awa-net  Creating
 Network awa-app_awa-net  Created
 Network awa-app_default  Creating
 Network awa-app_default  Created
 Volume "awa-app_awa-data"  Creating
 Volume "awa-app_awa-data"  Created
 Volume "awa-app_awa-pgdata"  Creating
 Volume "awa-app_awa-pgdata"  Created
 Container awa-app-db-1  Creating
 Container awa-app-postgres-1  Creating
 Container awa-app-redis-1  Creating
 Container awa-app-postgres-1  Created
 Container awa-app-redis-1  Created
 Container awa-app-db-1  Created
 Container awa-app-postgres-1  Starting
 Container awa-app-db-1  Starting
 Container awa-app-redis-1  Starting
 Container awa-app-redis-1  Started
 Container awa-app-db-1  Started
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint awa-app-postgres-1 (ae42b495f779aff59c6e39f984c641afb449fe5b31917d0fbb4ab1f8819f2769): Bind for 0.0.0.0:5432 failed: port is already allocated
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-29T20:12:48Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
 Container awa-app-db-1  Running
 Container awa-app-redis-1  Running
 Container awa-app-postgres-1  Recreate
 Container awa-app-postgres-1  Recreated
 Container awa-app-postgres-1  Starting
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint awa-app-postgres-1 (7f56efc7bb891113d1b0522cc5952c2d11c419d656cd19047d4cfd2531c941b8): Bind for 0.0.0.0:5432 failed: port is already allocated
exit_code=1
```

**unit** (`unit-setup.log`)

```
Collecting rich>=13.7.1 (from rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached rich-14.2.0-py3-none-any.whl.metadata (18 kB)
Collecting markdown-it-py>=2.2.0 (from rich>=13.7.1->rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached markdown_it_py-4.0.0-py3-none-any.whl.metadata (7.3 kB)
Collecting mdurl~=0.1 (from markdown-it-py>=2.2.0->rich>=13.7.1->rich-toolkit>=0.14.8->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached mdurl-0.1.2-py3-none-any.whl.metadata (1.6 kB)
Collecting shellingham>=1.3.0 (from typer>=0.15.1->fastapi-cli>=0.0.8->fastapi-cli[standard]>=0.0.8; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached shellingham-1.5.4-py2.py3-none-any.whl.metadata (3.5 kB)
Collecting httptools>=0.6.3 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached httptools-0.7.1-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (3.5 kB)
Collecting uvloop>=0.15.1 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached uvloop-0.22.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (4.9 kB)
Collecting watchfiles>=0.13 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached watchfiles-1.1.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
Collecting websockets>=10.4 (from uvicorn[standard]>=0.12.0; extra == "all"->fastapi[all]==0.116.1->-r requirements-dev.txt (line 15))
  Using cached websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.8 kB)
Collecting distlib<1,>=0.3.7 (from virtualenv>=20.10.0->pre-commit==3.7.1->-r requirements-dev.txt (line 20))
  Using cached distlib-0.4.0-py2.py3-none-any.whl.metadata (5.2 kB)
Collecting filelock<4,>=3.12.2 (from virtualenv>=20.10.0->pre-commit==3.7.1->-r requirements-dev.txt (line 20))
  Using cached filelock-3.20.0-py3-none-any.whl.metadata (2.1 kB)
Collecting argon2-cffi-bindings (from argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 11))
  Using cached argon2_cffi_bindings-25.1.0-cp39-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl.metadata (7.4 kB)
Collecting cffi>=1.0.1 (from argon2-cffi-bindings->argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 11))
  Using cached cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.6 kB)
Collecting pycparser (from cffi>=1.0.1->argon2-cffi-bindings->argon2-cffi->minio==7.2.18->-r requirements-dev.txt (line 11))
  Using cached pycparser-2.23-py3-none-any.whl.metadata (993 bytes)
Using cached jinja2-3.1.6-py3-none-any.whl (134 kB)
Using cached alembic-1.17.0-py3-none-any.whl (247 kB)
Using cached APScheduler-3.10.4-py3-none-any.whl (59 kB)
Using cached asgi_correlation_id-4.3.1-py3-none-any.whl (15 kB)
Using cached asyncpg-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.1 MB)
Using cached Authlib-1.3.1-py2.py3-none-any.whl (223 kB)
Using cached black-25.9.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl (1.6 MB)
Using cached boto3-1.40.21-py3-none-any.whl (139 kB)
Using cached minio-7.2.18-py3-none-any.whl (93 kB)
Using cached vulture-2.10-py2.py3-none-any.whl (27 kB)
Using cached celery-5.5.3-py3-none-any.whl (438 kB)
Using cached fastapi-0.116.1-py3-none-any.whl (95 kB)
Using cached fastapi_limiter-0.1.6-py3-none-any.whl (15 kB)
Using cached IMAPClient-3.0.1-py2.py3-none-any.whl (182 kB)
Using cached pre_commit-3.7.1-py2.py3-none-any.whl (204 kB)
Using cached mypy_extensions-1.1.0-py3-none-any.whl (5.0 kB)
Using cached openpyxl-3.1.5-py2.py3-none-any.whl (250 kB)
Using cached pandas-2.3.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (12.4 MB)
Using cached prometheus_client-0.20.0-py3-none-any.whl (54 kB)
Using cached psycopg2_binary-2.9.10-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.0 MB)
Using cached psycopg-3.2.11-py3-none-any.whl (206 kB)
Using cached pytest_asyncio-1.1.0-py3-none-any.whl (15 kB)
Using cached pytest_cov-7.0.0-py3-none-any.whl (22 kB)
Using cached pytest_postgresql-7.0.2-py3-none-any.whl (41 kB)
Using cached pytest_timeout-2.3.1-py3-none-any.whl (14 kB)
Using cached python_jose-3.3.0-py2.py3-none-any.whl (33 kB)
Using cached python_telegram_bot-22.5-py3-none-any.whl (730 kB)
Using cached requests-2.32.5-py3-none-any.whl (64 kB)
Using cached respx-0.22.0-py2.py3-none-any.whl (25 kB)
Using cached ruff-0.7.0-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (10.9 MB)
Using cached sqlalchemy-2.0.43-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.3 MB)
Using cached structlog-24.1.0-py3-none-any.whl (65 kB)
Using cached testcontainers-4.12.0-py3-none-any.whl (111 kB)
Using cached types_requests-2.32.4.20250809-py3-none-any.whl (20 kB)
Using cached docspec_python-2.2.2-py3-none-any.whl (15 kB)
Using cached pydoc_markdown-4.8.2-py3-none-any.whl (67 kB)
Using cached docspec-2.2.1-py3-none-any.whl (9.8 kB)
Using cached pytest_xdist-3.6.1-py3-none-any.whl (46 kB)
Using cached psycopg_binary-3.2.11-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (4.4 MB)
Using cached redis-6.4.0-py3-none-any.whl (279 kB)
Using cached httpx-0.27.2-py3-none-any.whl (76 kB)
Using cached mypy-1.18.2-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (13.2 MB)
Using cached numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (18.3 MB)
Using cached pydantic-2.11.7-py3-none-any.whl (444 kB)
Using cached pydantic_core-2.33.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.0 MB)
Using cached pandera-0.26.1-py3-none-any.whl (292 kB)
Using cached billiard-4.2.2-py3-none-any.whl (86 kB)
Using cached botocore-1.40.61-py3-none-any.whl (14.1 MB)
Using cached charset_normalizer-3.4.4-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (151 kB)
Using cached click-8.3.0-py3-none-any.whl (107 kB)
Using cached databind.core-4.5.2-py3-none-any.whl (1.5 kB)
Using cached databind-4.5.2-py3-none-any.whl (49 kB)
Using cached databind.json-4.5.2-py3-none-any.whl (1.5 kB)
Downloading deprecated-1.3.0-py2.py3-none-any.whl (11 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
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
Downloading wrapt-2.0.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (114 kB)
Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Using cached pydantic_settings-2.2.1-py3-none-any.whl (13 kB)
Using cached python_dotenv-1.1.1-py3-none-any.whl (20 kB)
Using cached python_multipart-0.0.19-py3-none-any.whl (24 kB)
Using cached annotated_types-0.7.0-py3-none-any.whl (13 kB)
Using cached certifi-2025.10.5-py3-none-any.whl (163 kB)
Using cached cfgv-3.4.0-py2.py3-none-any.whl (7.2 kB)
Using cached click_didyoumean-0.3.1-py3-none-any.whl (3.6 kB)
Using cached click_plugins-1.1.1.2-py2.py3-none-any.whl (11 kB)
Using cached click_repl-0.3.0-py3-none-any.whl (10 kB)
Using cached coverage-7.11.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (248 kB)
Using cached ecdsa-0.19.1-py2.py3-none-any.whl (150 kB)
Using cached email_validator-2.3.0-py3-none-any.whl (35 kB)
Using cached dnspython-2.8.0-py3-none-any.whl (331 kB)
Using cached execnet-2.1.1-py3-none-any.whl (40 kB)
Using cached fastapi_cli-0.0.14-py3-none-any.whl (11 kB)
Using cached fastapi_cloud_cli-0.3.1-py3-none-any.whl (19 kB)
Using cached greenlet-3.2.4-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (587 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached identify-2.6.15-py2.py3-none-any.whl (99 kB)
Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Using cached markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Using cached mirakuru-2.6.1-py3-none-any.whl (26 kB)
Using cached nodeenv-1.9.1-py2.py3-none-any.whl (22 kB)
Using cached orjson-3.11.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (136 kB)
Using cached packaging-25.0-py3-none-any.whl (66 kB)
Using cached pathspec-0.12.1-py3-none-any.whl (31 kB)
Using cached platformdirs-4.5.0-py3-none-any.whl (18 kB)
Using cached port_for-1.0.0-py3-none-any.whl (17 kB)
Using cached prompt_toolkit-3.0.52-py3-none-any.whl (391 kB)
Using cached psutil-7.1.2-cp36-abi3-manylinux2010_x86_64.manylinux_2_12_x86_64.manylinux_2_28_x86_64.whl (258 kB)
Using cached pydantic_extra_types-2.10.6-py3-none-any.whl (40 kB)
Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
Using cached pytokens-0.2.0-py3-none-any.whl (12 kB)
Using cached pytz-2025.2-py2.py3-none-any.whl (509 kB)
Using cached rich_toolkit-0.15.1-py3-none-any.whl (29 kB)
Using cached rich-14.2.0-py3-none-any.whl (243 kB)
Using cached markdown_it_py-4.0.0-py3-none-any.whl (87 kB)
Using cached mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Downloading rignore-0.7.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (959 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 959.6/959.6 kB 37.0 MB/s  0:00:00
Using cached sentry_sdk-

_Truncated digest: original length exceeded limit._
