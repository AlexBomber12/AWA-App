<!-- AWA-CI-DIGEST -->
## CI digest for `37a87235`

- **Preview URL**: n/a
- **Mirror path**: ci-logs/mirror-logs/pr-469/latest
- **Workflow run**: [18921884427](https://github.com/AlexBomber12/AWA-App/actions/runs/18921884427)

| Job | Conclusion | URL |
| --- | ---------- | --- |
| unit | ❌ Failure | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18921884427/job/54019890482) |
| secrets scan (gitleaks) | ✅ Success | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18921884427/job/54019890520) |
| migrations | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18921884427/job/54020122210) |
| preview | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18921884427/job/54020122253) |
| integration | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18921884427/job/54020122380) |
| k6 smoke (non-blocking) | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18921884427/job/54020122428) |
| mirror_logs | ⏳ In Progress | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18921884427/job/54020122189) |

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
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 959.6/959.6 kB 84.3 MB/s  0:00:00
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
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.0/6.0 MB 189.9 MB/s  0:00:00
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
  Stored in directory: /tmp/pip-ephem-wheel-cache-5x81d19f/wheels/58/da/3c/a7efd2bff9f1af19244156fcec46ad0dafb94fdf76dd747f48
Successfully built awa-common
Installing collected packages: awa-common
Successfully installed awa-common-0.0.1
```

**unit** (`unit/unit.log`)

```
E
==================================== ERRORS ====================================
_ ERROR at setup of test_rules_send_russian[check_a1-rows0-\u041c\u0430\u0440\u0436\u0430] _

fixturedef = <FixtureDef argname='migrate_db' scope='session' baseid='tests'>
request = <SubRequest 'migrate_db' for <Coroutine test_rules_send_russian[check_a1-rows0-\u041c\u0430\u0440\u0436\u0430]>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
                return (yield)
            if not _is_coroutine_or_asyncgen(fixturedef.func):
>               return (yield)
                        ^^^^^

/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/pytest_asyncio/plugin.py:683: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/conftest.py:133: in migrate_db
    subprocess.check_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

popenargs = (['alembic', '-c', 'services/api/alembic.ini', 'upgrade', 'head'],)
kwargs = {}, retcode = 1
cmd = ['alembic', '-c', 'services/api/alembic.ini', 'upgrade', 'head']

    def check_call(*popenargs, **kwargs):
        """Run command with arguments.  Wait for command to complete.  If
        the exit code was zero then return, otherwise raise
        CalledProcessError.  The CalledProcessError object will have the
        return code in the returncode attribute.
    
        The arguments are the same as for the call function.  Example:
    
        check_call(["ls", "-l"])
        """
        retcode = call(*popenargs, **kwargs)
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
>           raise CalledProcessError(retcode, cmd)
E           subprocess.CalledProcessError: Command '['alembic', '-c', 'services/api/alembic.ini', 'upgrade', 'head']' returned non-zero exit status 1.

/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/subprocess.py:413: CalledProcessError
---------------------------- Captured stderr setup -----------------------------
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.11.13/x64/bin/alembic", line 7, in <module>
    sys.exit(main())
             ^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/alembic/config.py", line 1022, in main
    CommandLine(prog=prog).main(argv=argv)
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/alembic/config.py", line 1012, in main
    self.run_cmd(cfg, options)
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/alembic/config.py", line 946, in run_cmd
    fn(
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/alembic/command.py", line 483, in upgrade
    script.run_env()
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/alembic/script/base.py", line 545, in run_env
    util.load_python_file(self.dir, "env.py")
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/alembic/util/pyfiles.py", line 116, in load_python_file
    module = load_module_py(module_id, path)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/alembic/util/pyfiles.py", line 136, in load_module_py
    spec.loader.exec_module(module)  # type: ignore
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/home/runner/work/AWA-App/AWA-App/services/api/migrations/env.py", line 11, in <module>
    from services.db.utils import views as view_helpers
ModuleNotFoundError: No module named 'services'
=========================== short test summary info ============================
ERROR tests/alerts/test_rules_send_russian.py::test_rules_send_russian[check_a1-rows0-\u041c\u0430\u0440\u0436\u0430] - subprocess.CalledProcessError: Command '['alembic', '-c', 'services/api/alembic.ini', 'upgrade', 'head']' returned non-zero exit status 1.
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
```

**unit** (`unit-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
 Container awa-app-redis-1  Running
 Container awa-app-postgres-1  Recreate
 Container awa-app-postgres-1  Recreated
 Container awa-app-db-1  Starting
 Container awa-app-postgres-1  Starting
 Container awa-app-db-1  Started
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint awa-app-postgres-1 (07427f71e71c6e53f2752f0da993fc109e74e2225d7be811095fc81fb23285b7): Bind for 0.0.0.0:5432 failed: port is already allocated
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
 Container awa-app-db-1  Running
 Container awa-app-redis-1  Running
 Container awa-app-postgres-1  Starting
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint awa-app-postgres-1 (d955c4723d343e5902ce3f995abe88a3eb3b9554ffc3fb452e94c0523e6224f1): Bind for 0.0.0.0:5432 failed: port is already allocated
exit_code=1
```

**unit** (`unit-compose-logs.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml logs --no-color
redis-1  | 1:C 29 Oct 2025 21:00:14.566 # WARNING Memory overcommit must be enabled! Without it, a background save or replication may fail under low memory condition. Being disabled, it can also cause failures without low memory condition, see https://github.com/jemalloc/jemalloc/issues/1328. To fix this issue add 'vm.overcommit_memory = 1' to /etc/sysctl.conf and then reboot or run the command 'sysctl vm.overcommit_memory=1' for this to take effect.
redis-1  | 1:C 29 Oct 2025 21:00:14.566 * oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
redis-1  | 1:C 29 Oct 2025 21:00:14.567 * Redis version=7.4.6, bits=64, commit=00000000, modified=0, pid=1, just started
redis-1  | 1:C 29 Oct 2025 21:00:14.567 # Warning: no config file specified, using the default config. In order to specify a config file use redis-server /path/to/redis.conf
redis-1  | 1:M 29 Oct 2025 21:00:14.567 * monotonic clock: POSIX clock_gettime
redis-1  | 1:M 29 Oct 2025 21:00:14.567 * Running mode=standalone, port=6379.
redis-1  | 1:M 29 Oct 2025 21:00:14.568 * Server initialized
redis-1  | 1:M 29 Oct 2025 21:00:14.568 * Ready to accept connections tcp
postgres-1  | The files belonging to this database system will be owned by user "postgres".
postgres-1  | This user must also own the server process.
postgres-1  | 
postgres-1  | The database cluster will be initialized with locale "en_US.UTF-8".
postgres-1  | The default text search configuration will be set to "english".
postgres-1  | 
postgres-1  | Data page checksums are disabled.
postgres-1  | 
postgres-1  | fixing permissions on existing directory /var/lib/postgresql/data ... ok
postgres-1  | creating subdirectories ... ok
postgres-1  | selecting dynamic shared memory implementation ... posix
postgres-1  | selecting default max_connections ... 100
postgres-1  | selecting default shared_buffers ... 128MB
postgres-1  | selecting default time zone ... UTC
postgres-1  | creating configuration files ... ok
postgres-1  | running bootstrap script ... ok
postgres-1  | performing post-bootstrap initialization ... ok
postgres-1  | initdb: warning: enabling "trust" authentication for local connections
postgres-1  | syncing data to disk ... ok
postgres-1  | initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the next time you run initdb.
postgres-1  | 
postgres-1  | 
postgres-1  | Success. You can now start the database server using:
postgres-1  | 
postgres-1  |     pg_ctl -D /var/lib/postgresql/data -l logfile start
postgres-1  | 
postgres-1  | waiting for server to start....2025-10-29 21:00:15.199 UTC [48] LOG:  starting PostgreSQL 16.10 (Debian 16.10-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
postgres-1  | 2025-10-29 21:00:15.201 UTC [48] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
postgres-1  | 2025-10-29 21:00:15.205 UTC [51] LOG:  database system was shut down at 2025-10-29 21:00:15 UTC
postgres-1  | 2025-10-29 21:00:15.210 UTC [48] LOG:  database system is ready to accept connections
postgres-1  |  done
postgres-1  | server started
postgres-1  | CREATE DATABASE
postgres-1  | 
postgres-1  | 
postgres-1  | /usr/local/bin/docker-entrypoint.sh: running /docker-entrypoint-initdb.d/10_init_pg_hba.sh
postgres-1  | 
postgres-1  | 2025-10-29 21:00:15.395 UTC [48] LOG:  received fast shutdown request
postgres-1  | waiting for server to shut down....2025-10-29 21:00:15.396 UTC [48] LOG:  aborting any active transactions
postgres-1  | 2025-10-29 21:00:15.398 UTC [48] LOG:  background worker "logical replication launcher" (PID 54) exited with exit code 1
postgres-1  | 2025-10-29 21:00:15.399 UTC [49] LOG:  shutting down
postgres-1  | 2025-10-29 21:00:15.400 UTC [49] LOG:  checkpoint starting: shutdown immediate
postgres-1  | 2025-10-29 21:00:15.419 UTC [49] LOG:  checkpoint complete: wrote 926 buffers (5.7%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.016 s, sync=0.003 s, total=0.021 s; sync files=301, longest=0.001 s, average=0.001 s; distance=4273 kB, estimate=4273 kB; lsn=0/191F0A8, redo lsn=0/191F0A8
postgres-1  | 2025-10-29 21:00:15.427 UTC [48] LOG:  database system is shut down
postgres-1  |  done
postgres-1  | server stopped
postgres-1  | 
postgres-1  | PostgreSQL init process complete; ready for start up.
postgres-1  | 
postgres-1  | 2025-10-29 21:00:15.517 UTC [1] LOG:  starting PostgreSQL 16.10 (Debian 16.10-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
postgres-1  | 2025-10-29 21:00:15.517 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
postgres-1  | 2025-10-29 21:00:15.517 UTC [1] LOG:  listening on IPv6 address "::", port 5432
postgres-1  | 2025-10-29 21:00:15.518 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
postgres-1  | 2025-10-29 21:00:15.523 UTC [66] LOG:  database system was shut down at 2025-10-29 21:00:15 UTC
postgres-1  | 2025-10-29 21:00:15.529 UTC [1] LOG:  database system is ready to accept connections
exit_code=0
```

**unit** (`unit-compose-ps.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml ps
NAME                 IMAGE              COMMAND                  SERVICE    CREATED          STATUS                    PORTS
awa-app-postgres-1   awa-app-postgres   "docker-entrypoint.s…"   postgres   13 seconds ago   Up 13 seconds (healthy)   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
awa-app-redis-1      redis:7            "docker-entrypoint.s…"   redis      13 seconds ago   Up 13 seconds (healthy)   0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp
exit_code=0
```

**unit** (`unit-eslint.log`)

```

> lint
> eslint --fix

```

**unit** (`unit-migrations-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
 Container awa-app-redis-1  Running
 Container awa-app-postgres-1  Recreate
 Container awa-app-postgres-1  Recreated
 Container awa-app-db-1  Starting
 Container awa-app-postgres-1  Starting
 Container awa-app-db-1  Started
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint awa-app-postgres-1 (07427f71e71c6e53f2752f0da993fc109e74e2225d7be811095fc81fb23285b7): Bind for 0.0.0.0:5432 failed: port is already allocated
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
 Container awa-app-db-1  Running
 Container awa-app-redis-1  Running
 Container awa-app-postgres-1  Starting
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint awa-app-postgres-1 (d955c4723d343e5902ce3f995abe88a3eb3b9554ffc3fb452e94c0523e6224f1): Bind for 0.0.0.0:5432 failed: port is already allocated
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
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 959.6/959.6 kB 84.3 MB/s  0:00:00
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
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.0/6.0 MB 189.9 MB/s  0:00:00
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
  Stored in directory: /tmp/pip-ephem-wheel-cache-5x81d19f/wheels/58/da/3c/a7efd2bff9f1af19244156fcec46ad0dafb94fdf76dd747f48
Successfully built awa-common
Installing collected packages: awa-common
Successfully installed awa-common-0.0.1
```

**unit** (`unit-system.txt`)

```
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
GITHUB_ACTION=__run_20
GITHUB_ACTIONS=true
GITHUB_ACTION_REF=
GITHUB_ACTION_REPOSITORY=
GITHUB_ACTOR=AlexBomber12
GITHUB_ACTOR_ID=48256657
GITHUB_API_URL=https://api.github.com
GITHUB_BASE_REF=main
GITHUB_ENV=/home/runner/work/_temp/_runner_file_commands/set_env_2d6d6a49-73b6-47fa-ac22-b2078d86e338
GITHUB_EVENT_NAME=pull_request
GITHUB_EVENT_PATH=/home/runner/work/_temp/_github_workflow/event.json
GITHUB_GRAPHQL_URL=https://api.github.com/graphql
GITHUB_HEAD_REF=PR-A
GITHUB_JOB=unit
GITHUB_OUTPUT=/home/runner/work/_temp/_runner_file_commands/set_output_2d6d6a49-73b6-47fa-ac22-b2078d86e338
GITHUB_PATH=/home/runner/work/_temp/_runner_file_commands/add_path_2d6d6a49-73b6-47fa-ac22-b2078d86e338
GITHUB_REF=refs/pull/469/merge
GITHUB_REF_NAME=469/merge
GITHUB_REF_PROTECTED=false
GITHUB_REF_TYPE=branch
GITHUB_REPOSITORY=AlexBomber12/AWA-App
GITHUB_REPOSITORY_ID=1011502908
GITHUB_REPOSITORY_OWNER=AlexBomber12
GITHUB_REPOSITORY_OWNER_ID=48256657
GITHUB_RETENTION_DAYS=90
GITHUB_RUN_ATTEMPT=1
GITHUB_RUN_ID=18921884427
GITHUB_RUN_NUMBER=1283
GITHUB_SERVER_URL=https://github.com
GITHUB_SHA=37a87235bc5d36f9d1429ef50d6cef4021d231ec
GITHUB_STATE=/home/runner/work/_temp/_runner_file_commands/save_state_2d6d6a49-73b6-47fa-ac22-b2078d86e338
GITHUB_STEP_SUMMARY=/home/runner/work/_temp/_runner_file_commands/step_summary_2d6d6a49-73b6-47fa-ac22-b2078d86e338
GITHUB_TRIGGERING_ACTOR=AlexBomber12
GITHUB_WORKFLOW=ci
GITHUB_WORKFLOW_REF=AlexBomber12/AWA-App/.github/workflows/ci.yml@refs/pull/469/merge
GITHUB_WORKFLOW_SHA=37a87235bc5d36f9d1429ef50d6cef4021d231ec
GITHUB_WORKSPACE=/home/runner/work/AWA-App/AWA-App
GOROOT_1_22_X64=/opt/hostedtoolcache/go/1.22.12/x64
GOROOT_1_23_X64=/opt/hostedtoolcache/go/1.23.12/x64
GOROOT_1_24_X64=/opt/hostedtoolcache/go/1.24.7/x64
GRADLE_HOME=/usr/share/gradle-9.1.0
HOME=/home/runner
HOMEBREW_CLEANUP_PERIODIC_FULL_DAYS=3650
HOMEBREW_NO_AUTO_UPDATE=1
INVOCATION_ID=35da464ab63c4d1fa24bd02ca914bff2
ImageOS=ubuntu24
ImageVersion=20250929.60.1
JAVA_HOME=/usr/lib/jvm/temurin-17-jdk-amd64
JAVA_HOME_11_X64=/usr/lib/jvm/temurin-11-jdk-amd64
JAVA_HOME_17_X64=/usr/lib/jvm/temurin-17-jdk-amd64
JAVA_HOME_21_X64=/usr/lib/jvm/temurin-21-jdk-amd64
JAVA_HOME_25_X64=/usr/lib/jvm/temurin-25-jdk-amd64
JAVA_HOME_8_X64=/usr/lib/jvm/temurin-8-jdk-amd64
JOURNAL_STREAM=9:13819
LANG=C.UTF-8
LD_LIBRARY_PATH=/opt/hostedtoolcache/Python/3.11.13/x64/lib
LOGNAME=runner
MEMORY_PRESSURE_WATCH=/sys/fs/cgroup/system.slice/hosted-compute-agent.service/memory.pressure
MEMORY_PRESSURE_WRITE=c29tZSAyMDAwMDAgMjAwMDAwMAA=
NODE_VERSION=20
NVM_DIR=/home/runner/.nvm
PATH=/opt/hostedtoolcache/node/20.19.5/x64/bin:/opt/hostedtoolcache/Python/3.11.13/x64/bin:/opt/hostedtoolcache/Python/3.11.13/x64:/snap/bin:/home/runner/.local/bin:/opt/pipx_bin:/home/runner/.cargo/bin:/home/runner/.config/composer/vendor/bin:/usr/local/.ghcup/bin:/home/runner/.dotnet/tools:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
PG_DATABASE=awa
PG_HOST=postgres
PG_PASSWORD=<redacted>
PG_PORT=5432
PG_USER=postgres
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
RUNNER_NAME=GitHub Actions 1000008749
RUNNER_OS=Linux
RUNNER_TEMP=/home/runner/work/_temp
RUNNER_TOOL_CACHE=/opt/hostedtoolcache
RUNNER_TRACKING_ID=github_22a86d53-6229-465f-ad07-355193b28860
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
 Containers: 3
  Running: 2
  Paused: 0
  Stopped: 1
 Images: 3
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

**unit** (`unit-tsc.log`)

```
```

**unit** (`unit-unit-setup.log`)

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
Downloading deprecate

_Truncated digest: original length exceeded limit._
