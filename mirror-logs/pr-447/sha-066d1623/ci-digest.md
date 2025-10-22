<!-- AWA-CI-DIGEST -->
## CI digest for `066d1623`

- **Preview URL**: n/a
- **Mirror path**: ci-logs/mirror-logs/pr-447/latest
- **Workflow run**: [18730123856](https://github.com/AlexBomber12/AWA-App/actions/runs/18730123856)

| Job | Conclusion | URL |
| --- | ---------- | --- |
| unit | ❌ Failure | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18730123856/job/53424817722) |
| migrations | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18730123856/job/53424904325) |
| integration | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18730123856/job/53424904422) |
| preview | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18730123856/job/53424904699) |
| mirror_logs | ⏳ In Progress | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18730123856/job/53424904245) |

### Failed tails

**unit** (`unit/unit-setup.log`)

```
Downloading s3transfer-0.13.1-py3-none-any.whl (85 kB)
Downloading starlette-0.47.3-py3-none-any.whl (72 kB)
Downloading anyio-4.4.0-py3-none-any.whl (86 kB)
Downloading tomli-2.3.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (242 kB)
Downloading tomli_w-1.2.0-py3-none-any.whl (6.7 kB)
Downloading typeapi-2.2.4-py3-none-any.whl (26 kB)
Downloading typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Downloading urllib3-2.5.0-py3-none-any.whl (129 kB)
Downloading wrapt-1.17.3-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (82 kB)
Downloading itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Downloading pydantic_settings-2.2.1-py3-none-any.whl (13 kB)
Downloading python_dotenv-1.1.1-py3-none-any.whl (20 kB)
Downloading python_multipart-0.0.19-py3-none-any.whl (24 kB)
Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
Downloading certifi-2025.10.5-py3-none-any.whl (163 kB)
Downloading click_didyoumean-0.3.1-py3-none-any.whl (3.6 kB)
Downloading click_plugins-1.1.1.2-py2.py3-none-any.whl (11 kB)
Downloading click_repl-0.3.0-py3-none-any.whl (10 kB)
Downloading coverage-7.11.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (248 kB)
Downloading email_validator-2.3.0-py3-none-any.whl (35 kB)
Downloading dnspython-2.8.0-py3-none-any.whl (331 kB)
Downloading fastapi_cli-0.0.14-py3-none-any.whl (11 kB)
Downloading fastapi_cloud_cli-0.3.1-py3-none-any.whl (19 kB)
Downloading greenlet-3.2.4-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (587 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 587.7/587.7 kB 97.4 MB/s  0:00:00
Downloading iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Downloading markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Downloading mirakuru-2.6.1-py3-none-any.whl (26 kB)
Downloading orjson-3.11.3-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (132 kB)
Downloading packaging-25.0-py3-none-any.whl (66 kB)
Downloading pathspec-0.12.1-py3-none-any.whl (31 kB)
Downloading platformdirs-4.5.0-py3-none-any.whl (18 kB)
Downloading port_for-1.0.0-py3-none-any.whl (17 kB)
Downloading prompt_toolkit-3.0.52-py3-none-any.whl (391 kB)
Downloading psutil-7.1.1-cp36-abi3-manylinux_2_12_x86_64.manylinux2010_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (290 kB)
Downloading pydantic_extra_types-2.10.6-py3-none-any.whl (40 kB)
Downloading pygments-2.19.2-py3-none-any.whl (1.2 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.2/1.2 MB 166.8 MB/s  0:00:00
Downloading pytz-2025.2-py2.py3-none-any.whl (509 kB)
Downloading rich_toolkit-0.15.1-py3-none-any.whl (29 kB)
Downloading rich-14.2.0-py3-none-any.whl (243 kB)
Downloading markdown_it_py-4.0.0-py3-none-any.whl (87 kB)
Downloading mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Downloading rignore-0.7.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (952 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 952.3/952.3 kB 145.8 MB/s  0:00:00
Downloading sentry_sdk-2.20.0-py2.py3-none-any.whl (322 kB)
Downloading six-1.17.0-py2.py3-none-any.whl (11 kB)
Downloading sniffio-1.3.1-py3-none-any.whl (10 kB)
Downloading typer-0.20.0-py3-none-any.whl (47 kB)
Downloading shellingham-1.5.4-py2.py3-none-any.whl (9.8 kB)
Downloading typing_inspect-0.9.0-py3-none-any.whl (8.8 kB)
Downloading typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Downloading tzdata-2025.2-py2.py3-none-any.whl (347 kB)
Downloading tzlocal-5.3.1-py3-none-any.whl (18 kB)
Downloading ujson-5.11.0-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (57 kB)
Downloading uvicorn-0.35.0-py3-none-any.whl (66 kB)
Downloading httptools-0.7.1-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (456 kB)
Downloading uvloop-0.22.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (3.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.8/3.8 MB 215.0 MB/s  0:00:00
Downloading watchfiles-1.1.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Downloading websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (182 kB)
Downloading yapf-0.43.0-py3-none-any.whl (256 kB)
Downloading argon2_cffi-25.1.0-py3-none-any.whl (14 kB)
Downloading argon2_cffi_bindings-25.1.0-cp39-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl (87 kB)
Downloading cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (215 kB)
Downloading docker-7.1.0-py3-none-any.whl (147 kB)
Downloading et_xmlfile-2.0.0-py3-none-any.whl (18 kB)
Downloading mako-1.3.10-py3-none-any.whl (78 kB)
Downloading pycparser-2.23-py3-none-any.whl (118 kB)
Downloading pycryptodome-3.23.0-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.3/2.3 MB 196.7 MB/s  0:00:00
Downloading toml-0.10.2-py2.py3-none-any.whl (16 kB)
Downloading typeguard-4.4.4-py3-none-any.whl (34 kB)
Downloading watchdog-6.0.0-py3-none-manylinux2014_x86_64.whl (79 kB)
Downloading wcwidth-0.2.14-py2.py3-none-any.whl (37 kB)
Building wheels for collected packages: docstring-parser
  Building wheel for docstring-parser (pyproject.toml): started
  Building wheel for docstring-parser (pyproject.toml): finished with status 'done'
  Created wheel for docstring-parser: filename=docstring_parser-0.11-py3-none-any.whl size=31551 sha256=07f7185ccec9a92ba4ce4118f81a35c3095d31d26830b2d294b3b29063acc618
  Stored in directory: /home/runner/.cache/pip/wheels/0f/f9/78/1186f8bf3425dbd3fb3fa32beee828876c792f49eb2554e888
Successfully built docstring-parser
Installing collected packages: pytz, wrapt, websockets, wcwidth, watchdog, vine, uvloop, urllib3, ujson, tzlocal, tzdata, typing-extensions, tomli_w, tomli, toml, structlog, sniffio, six, shellingham, ruff, rignore, redis, PyYAML, python-multipart, python-dotenv, pygments, pycryptodome, pycparser, psycopg2-binary, psycopg-binary, psutil, port-for, pluggy, platformdirs, pathspec, packaging, orjson, numpy, nr-stream, nr-date, mypy-extensions, mdurl, MarkupSafe, jmespath, itsdangerous, iniconfig, imapclient, idna, httptools, h11, greenlet, et-xmlfile, docstring-parser, dnspython, coverage, click, charset_normalizer, certifi, billiard, asyncpg, annotated-types, yapf, vulture, uvicorn, typing-inspection, typing_inspect, types-requests, typeguard, typeapi, sqlalchemy, sentry-sdk, requests, python-dateutil, pytest, pydantic-core, psycopg, prompt-toolkit, openpyxl, mypy, mirakuru, markdown-it-py, Mako, Jinja2, httpcore, email-validator, Deprecated, click-plugins, click-didyoumean, cffi, black, apscheduler, anyio, amqp, watchfiles, starlette, rich, pytest-postgresql, pytest-cov, pytest-asyncio, pydantic, pandas, nr-util, kombu, httpx, docker, databind, click-repl, botocore, argon2-cffi-bindings, alembic, typer, testcontainers, s3transfer, rich-toolkit, respx, python-telegram-bot, pydantic-settings, pydantic-extra-types, pandera, fastapi, databind.json, databind.core, celery, asgi-correlation-id, argon2-cffi, minio, fastapi-limiter, fastapi-cloud-cli, fastapi-cli, docspec, boto3, docspec-python, pydoc-markdown

Successfully installed Deprecated-1.2.18 Jinja2-3.1.6 Mako-1.3.10 MarkupSafe-3.0.3 PyYAML-6.0.3 alembic-1.16.4 amqp-5.3.1 annotated-types-0.7.0 anyio-4.4.0 apscheduler-3.10.4 argon2-cffi-25.1.0 argon2-cffi-bindings-25.1.0 asgi-correlation-id-4.3.1 asyncpg-0.30.0 billiard-4.2.2 black-25.1.0 boto3-1.40.21 botocore-1.40.57 celery-5.5.3 certifi-2025.10.5 cffi-2.0.0 charset_normalizer-3.4.4 click-8.3.0 click-didyoumean-0.3.1 click-plugins-1.1.1.2 click-repl-0.3.0 coverage-7.11.0 databind-4.5.2 databind.core-4.5.2 databind.json-4.5.2 dnspython-2.8.0 docker-7.1.0 docspec-2.2.1 docspec-python-2.2.2 docstring-parser-0.11 email-validator-2.3.0 et-xmlfile-2.0.0 fastapi-0.116.1 fastapi-cli-0.0.14 fastapi-cloud-cli-0.3.1 fastapi-limiter-0.1.6 greenlet-3.2.4 h11-0.14.0 httpcore-1.0.5 httptools-0.7.1 httpx-0.27.2 idna-3.11 imapclient-3.0.1 iniconfig-2.3.0 itsdangerous-2.2.0 jmespath-1.0.1 kombu-5.5.4 markdown-it-py-4.0.0 mdurl-0.1.2 minio-7.2.18 mirakuru-2.6.1 mypy-1.18.2 mypy-extensions-1.1.0 nr-date-2.1.0 nr-stream-1.1.5 nr-util-0.8.12 numpy-1.26.4 openpyxl-3.1.5 orjson-3.11.3 packaging-25.0 pandas-2.3.2 pandera-0.26.1 pathspec-0.12.1 platformdirs-4.5.0 pluggy-1.6.0 port-for-1.0.0 prompt-toolkit-3.0.52 psutil-7.1.1 psycopg-3.2.9 psycopg-binary-3.2.9 psycopg2-binary-2.9.10 pycparser-2.23 pycryptodome-3.23.0 pydantic-2.11.7 pydantic-core-2.33.2 pydantic-extra-types-2.10.6 pydantic-settings-2.2.1 pydoc-markdown-4.8.2 pygments-2.19.2 pytest-8.4.2 pytest-asyncio-1.1.0 pytest-cov-7.0.0 pytest-postgresql-7.0.2 python-dateutil-2.9.0.post0 python-dotenv-1.1.1 python-multipart-0.0.19 python-telegram-bot-22.3 pytz-2025.2 redis-6.4.0 requests-2.32.5 respx-0.22.0 rich-14.2.0 rich-toolkit-0.15.1 rignore-0.7.1 ruff-0.12.11 s3transfer-0.13.1 sentry-sdk-2.20.0 shellingham-1.5.4 six-1.17.0 sniffio-1.3.1 sqlalchemy-2.0.43 starlette-0.47.3 structlog-24.1.0 testcontainers-4.12.0 toml-0.10.2 tomli-2.3.0 tomli_w-1.2.0 typeapi-2.2.4 typeguard-4.4.4 typer-0.20.0 types-requests-2.32.4.20250809 typing-extensions-4.15.0 typing-inspection-0.4.2 typing_inspect-0.9.0 tzdata-2025.2 tzlocal-5.3.1 ujson-5.11.0 urllib3-2.5.0 uvicorn-0.35.0 uvloop-0.22.1 vine-5.1.0 vulture-2.10 watchdog-6.0.0 watchfiles-1.1.1 wcwidth-0.2.14 websockets-15.0.1 wrapt-1.17.3 yapf-0.43.0
Requirement already satisfied: python-telegram-bot==22.3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 1)) (22.3)
Requirement already satisfied: apscheduler==3.10.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 2)) (3.10.4)
Requirement already satisfied: asyncpg==0.30.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 3)) (0.30.0)
Requirement already satisfied: httpx<0.29,>=0.27 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (0.27.2)
Requirement already satisfied: six>=1.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (1.17.0)
Requirement already satisfied: pytz in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (2025.2)
Requirement already satisfied: tzlocal!=3.*,>=2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (5.3.1)
Requirement already satisfied: anyio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (4.4.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (2025.10.5)
Requirement already satisfied: httpcore==1.* in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (1.0.5)
Requirement already satisfied: idna in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (3.11)
Requirement already satisfied: sniffio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (1.3.1)
Requirement already satisfied: h11<0.15,>=0.13 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpcore==1.*->httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (0.14.0)
Requirement already satisfied: uvicorn==0.35.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 1)) (0.35.0)
Requirement already satisfied: pydantic-settings==2.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 2)) (2.2.1)
Requirement already satisfied: fastapi==0.116.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 3)) (0.116.1)
Requirement already satisfied: sqlalchemy==2.0.43 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 4)) (2.0.43)
Requirement already satisfied: alembic==1.16.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 5)) (1.16.4)
Requirement already satisfied: psycopg==3.2.9 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from psycopg[binary]==3.2.9->-r services/api/requirements.txt (line 6)) (3.2.9)
Requirement already satisfied: httpx<0.28,>=0.27 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 7)) (0.27.2)
Requirement already satisfied: asyncpg==0.30.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 8)) (0.30.0)
Requirement already satisfied: boto3==1.40.21 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 9)) (1.40.21)
Collecting Jinja2==3.1.5 (from -r services/api/requirements.txt (line 10))
  Downloading jinja2-3.1.5-py3-none-any.whl.metadata (2.6 kB)
Requirement already satisfied: celery==5.5.3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 11)) (5.5.3)
Requirement already satisfied: structlog==24.1.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 12)) (24.1.0)
Requirement already satisfied: asgi-correlation-id==4.3.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 13)) (4.3.1)
Requirement already satisfied: fastapi-limiter==0.1.6 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 14)) (0.1.6)
Requirement already satisfied: python-multipart in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 15)) (0.0.19)
Collecting redis==5.0.8 (from -r services/api/requirements.txt (line 16))
  Downloading redis-5.0.8-py3-none-any.whl.metadata (9.2 kB)
Requirement already satisfied: sentry-sdk==2.20.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sentry-sdk[celery,fastapi,sqlalchemy]==2.20.0->-r services/api/requirements.txt (line 17)) (2.20.0)
Requirement already satisfied: imapclient==3.0.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 18)) (3.0.1)
Requirement already satisfied: click>=7.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn==0.35.0->-r services/api/requirements.txt (line 1)) (8.3.0)
Requirement already satisfied: h11>=0.8 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn==0.35.0->-r services/api/requirements.txt (line 1)) (0.14.0)
Requirement already satisfied: pydantic>=2.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic-settings==2.2.1->-r services/api/requirements.txt (line 2)) (2.11.7)
Requirement already satisfied: python-dotenv>=0.21.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic-settings==2.2.1->-r services/api/requirements.txt (line 2)) (1.1.1)
Requirement already satisfied: starlette<0.48.0,>=0.40.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from fastapi==0.116.1->-r services/api/requirements.txt (line 3)) (0.47.3)
Requirement already satisfied: typing-extensions>=4.8.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from fastapi==0.116.1->-r services/api/requirements.txt (line 3)) (4.15.0)
Requirement already satisfied: greenlet>=1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.43->-r services/api/requirements.txt (line 4)) (3.2.4)
Requirement already satisfied: Mako in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from alembic==1.16.4->-r services/api/requirements.txt (line 5)) (1.3.10)
Requirement already satisfied: botocore<1.41.0,>=1.40.21 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from boto3==1.40.21->-r services/api/requirements.txt (line 9)) (1.40.57)
Requirement already satisfied: jmespath<2.0.0,>=0.7.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from boto3==1.40.21->-r services/api/requirements.txt (line 9)) (1.0.1)
Requirement already satisfied: s3transfer<0.14.0,>=0.13.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from boto3==1.40.21->-r services/api/requirements.txt (line 9)) (0.13.1)
Requirement already satisfied: MarkupSafe>=2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from Jinja2==3.1.5->-r services/api/requirements.txt (line 10)) (3.0.3)
Requirement already satisfied: billiard<5.0,>=4.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/api/requirements.txt (line 11)) (4.2.2)
Requirement already satisfied: kombu<5.6,>=5.5.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/api/requirements.txt (line 11)) (5.5.4)
Requirement already satisfied: vine<6.0,>=5.1.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/api/requirements.txt (line 11)) (5.1.0)
Requirement already satisfied: click-didyoumean>=0.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/api/requirements.txt (line 11)) (0.3.1)
Requirement already satisfied: click-repl>=0.2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/api/requirements.txt (line 11)) (0.3.0)
Requirement already satisfied: click-plugins>=1.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/api/requirements.txt (line 11)) (1.1.1.2)
Requirement already satisfied: python-dateutil>=2.8.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/api/requirements.txt (line 11)) (2.9.0.post0)
Requirement already satisfied: urllib3>=1.26.11 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sentry-sdk==2.20.0->sentry-sdk[celery,fastapi,sqlalchemy]==2.20.0->-r services/api/requirements.txt (line 17)) (2.5.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sentry-sdk==2.20.0->sentry-sdk[celery,fastapi,sqlalchemy]==2.20.0->-r services/api/requirements.txt (line 17)) (2025.10.5)
Requirement already satisfied: psycopg-binary==3.2.9 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from psycopg[binary]==3.2.9->-r services/api/requirements.txt (line 6)) (3.2.9)
Requirement already satisfied: anyio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/api/requirements.txt (line 7)) (4.4.0)
Requirement already satisfied: httpcore==1.* in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/api/requirements.txt (line 7)) (1.0.5)
Requirement already satisfied: idna in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/api/requirements.txt (line 7)) (3.11)
Requirement already satisfied: sniffio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/api/requirements.txt (line 7)) (1.3.1)
Requirement already satisfied: amqp<6.0.0,>=5.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->-r services/api/requirements.txt (line 11)) (5.3.1)
Requirement already satisfied: tzdata>=2025.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->-r services/api/requirements.txt (line 11)) (2025.2)
Requirement already satisfied: packaging in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->-r services/api/requirements.txt (line 11)) (25.0)
Requirement already satisfied: annotated-types>=0.6.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic>=2.3.0->pydantic-settings==2.2.1->-r services/api/requirements.txt (line 2)) (0.7.0)
Requirement already satisfied: pydantic-core==2.33.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic>=2.3.0->pydantic-settings==2.2.1->-r services/api/requirements.txt (line 2)) (2.33.2)
Requirement already satisfied: typing-inspection>=0.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic>=2.3.0->pydantic-settings==2.2.1->-r services/api/requirements.txt (line 2)) (0.4.2)
Requirement already satisfied: six>=1.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-dateutil>=2.8.2->celery==5.5.3->-r services/api/requirements.txt (line 11)) (1.17.0)
Requirement already satisfied: prompt-toolkit>=3.0.36 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from click-repl>=0.2.0->celery==5.5.3->-r services/api/requirements.txt (line 11)) (3.0.52)
Requirement already satisfied: wcwidth in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.5.3->-r services/api/requirements.txt (line 11)) (0.2.14)
Downloading jinja2-3.1.5-py3-none-any.whl (134 kB)
Downloading redis-5.0.8-py3-none-any.whl (255 kB)
Installing collected packages: redis, Jinja2
  Attempting uninstall: redis
    Found existing installation: redis 6.4.0
    Uninstalling redis-6.4.0:
      Successfully uninstalled redis-6.4.0
  Attempting uninstall: Jinja2
    Found existing installation: Jinja2 3.1.6
    Uninstalling Jinja2-3.1.6:
      Successfully uninstalled Jinja2-3.1.6

Successfully installed Jinja2-3.1.5 redis-5.0.8
Requirement already satisfied: alembic==1.16.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/db/requirements.txt (line 1)) (1.16.4)
Requirement already satisfied: SQLAlchemy>=1.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from alembic==1.16.4->-r services/db/requirements.txt (line 1)) (2.0.43)
Requirement already satisfied: Mako in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from alembic==1.16.4->-r services/db/requirements.txt (line 1)) (1.3.10)
Requirement already satisfied: typing-extensions>=4.12 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from alembic==1.16.4->-r services/db/requirements.txt (line 1)) (4.15.0)
Requirement already satisfied: greenlet>=1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from SQLAlchemy>=1.4.0->alembic==1.16.4->-r services/db/requirements.txt (line 1)) (3.2.4)
Requirement already satisfied: MarkupSafe>=0.9.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from Mako->alembic==1.16.4->-r services/db/requirements.txt (line 1)) (3.0.3)
Requirement already satisfied: celery==5.5.3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (5.5.3)
Requirement already satisfied: billiard<5.0,>=4.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (4.2.2)
Requirement already satisfied: kombu<5.6,>=5.5.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (5.5.4)
Requirement already satisfied: vine<6.0,>=5.1.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (5.1.0)
Requirement already satisfied: click<9.0,>=8.1.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (8.3.0)
Requirement already satisfied: click-didyoumean>=0.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (0.3.1)
Requirement already satisfied: click-repl>=0.2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (0.3.0)
Requirement already satisfied: click-plugins>=1.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (1.1.1.2)
Requirement already satisfied: python-dateutil>=2.8.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (2.9.0.post0)
Requirement already satisfied: amqp<6.0.0,>=5.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (5.3.1)
Requirement already satisfied: tzdata>=2025.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (2025.2)
Requirement already satisfied: packaging in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (25.0)
Requirement already satisfied: prompt-toolkit>=3.0.36 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from click-repl>=0.2.0->celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (3.0.52)
Requirement already satisfied: wcwidth in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (0.2.14)
Requirement already satisfied: six>=1.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-dateutil>=2.8.2->celery==5.5.3->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (1.17.0)
Requirement already satisfied: redis!=4.5.5,!=5.0.2,<=5.2.1,>=4.5.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu[redis]; extra == "redis"->celery[redis]==5.5.3->-r services/emailer/requirements.txt (line 1)) (5.0.8)
Collecting keepa==1.3.15 (from -r services/etl/requirements.txt (line 1))
  Downloading keepa-1.3.15-py3-none-any.whl.metadata (11 kB)
ERROR: Cannot install minio==7.2.16 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested minio==7.2.16
    The user requested (constraint) minio==7.2.18

To fix this you could try to:
1. loosen the range of package versions you've specified
2. remove package versions to allow pip to attempt to solve the dependency conflict

ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
```

**unit** (`unit-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-logs.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml logs --no-color
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-ps.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml ps
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-migrations-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-22T21:17:23Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-setup.log`)

```
Downloading s3transfer-0.13.1-py3-none-any.whl (85 kB)
Downloading starlette-0.47.3-py3-none-any.whl (72 kB)
Downloading anyio-4.4.0-py3-none-any.whl (86 kB)
Downloading tomli-2.3.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (242 kB)
Downloading tomli_w-1.2.0-py3-none-any.whl (6.7 kB)
Downloading typeapi-2.2.4-py3-none-any.whl (26 kB)
Downloading typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Downloading urllib3-2.5.0-py3-none-any.whl (129 kB)
Downloading wrapt-1.17.3-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (82 kB)
Downloading itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Downloading pydantic_settings-2.2.1-py3-none-any.whl (13 kB)
Downloading python_dotenv-1.1.1-py3-none-any.whl (20 kB)
Downloading python_multipart-0.0.19-py3-none-any.whl (24 kB)
Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
Downloading certifi-2025.10.5-py3-none-any.whl (163 kB)
Downloading click_didyoumean-0.3.1-py3-none-any.whl (3.6 kB)
Downloading click_plugins-1.1.1.2-py2.py3-none-any.whl (11 kB)
Downloading click_repl-0.3.0-py3-none-any.whl (10 kB)
Downloading coverage-7.11.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (248 kB)
Downloading email_validator-2.3.0-py3-none-any.whl (35 kB)
Downloading dnspython-2.8.0-py3-none-any.whl (331 kB)
Downloading fastapi_cli-0.0.14-py3-none-any.whl (11 kB)
Downloading fastapi_cloud_cli-0.3.1-py3-none-any.whl (19 kB)
Downloading greenlet-3.2.4-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (587 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 587.7/587.7 kB 97.4 MB/s  0:00:00
Downloading iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Downloading markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Downloading mirakuru-2.6.1-py3-none-any.whl (26 kB)
Downloading orjson-3.11.3-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (132 kB)
Downloading packaging-25.0-py3-none-any.whl (66 kB)
Downloading pathspec-0.12.1-py3-none-any.whl (31 kB)
Downloading platformdirs-4.5.0-py3-none-any.whl (18 kB)
Downloading port_for-1.0.0-py3-none-any.whl (17 kB)
Downloading prompt_toolkit-3.0.52-py3-none-any.whl (391 kB)
Downloading psutil-7.1.1-cp36-abi3-manylinux_2_12_x86_64.manylinux2010_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (290 kB)
Downloading pydantic_extra_types-2.10.6-py3-none-any.whl (40 kB)
Downloading pygments-2.19.2-py3-none-any.whl (1.2 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.2/1.2 MB 166.8 MB/s  0:00:00
Downloading pytz-2025.2-py2.py3-none-any.whl (509 kB)
Downloading rich_toolkit-0.15.1-py3-none-any.whl (29 kB)
Downloading rich-14.2.0-py3-none-any.whl (243 kB)
Downloading markdown_it_py-4.0.0-py3-none-any.whl (87 kB)
Downloading mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Downloading rignore-0.7.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (952 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 952.3/952.3 kB 145.8 MB/s  0:00:00
Downloading sentry_sdk-2.20.0-py2.py3-none-any.whl (322 kB)
Downloading six-1.17.0-py2.py3-none-any.whl (11 kB)
Downloading sniffio-1.3.1-py3-none-any.whl (10 kB)
Downloading typer-0.20.0-py3-none-any.whl (47 kB)
Downloading shellingham-1.5.4-py2.py3-none-any.whl (9.8 kB)
Downloading typing_inspect-0.9.0-py3-none-any.whl (8.8 kB)
Downloading typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Downloading tzdata-2025.2-py2.py3-none-any.whl (347 kB)
Downloading tzlocal-5.3.1-py3-none-any.whl (18 kB)
Downloading ujson-5.11.0-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (57 kB)
Downloading uvicorn-0.35.0-py3-none-any.whl (66 kB)
Downloading httptools-0.7.1-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (456 kB)
Downloading uvloop-0.22.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (3.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.8/3.8 MB 215.0 MB/s  0:00:00
Downloading watchfiles-1.1.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Downloading websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (182 kB)
Downloading yapf-0.43.0-py3-none-any.whl (256 kB)
Downloading argon2_cffi-25.1.0-py3-none-any.whl (14 kB)
Downloading argon2_cffi_bindings-25.1.0-cp39-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl (87 kB)
Downloading cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (215 kB)
Downloading docker-7.1.0-py3-none-any.whl (147 kB)
Downloading et_xmlfile-2.0.0-py3-none-any.whl (18 kB)
Downloading mako-1.3.10-py3-none-any.whl (78 kB)
Downloading pycparser-2.23-py3-none-any.whl (118 kB)
Downloading pycryptodome-3.23.0-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.3/2.3 MB 196.7 MB/s  0:00:00
Downloading toml-0.10.2-py2.py3-none-any.whl (16 kB)
Downloading typeguard-4.4.4-py3-none-any.whl (34 kB)
Downloading watchdog-6.0.0-py3-none-manylinux2014_x86_64.whl (79 kB)
Downloading wcwidth-0.2.14-py2.py3-none-any.whl (37 kB)
Building wheels for collected packages: docstring-parser
  Building wheel for docstring-parser (pyproject.toml): started
  Building wheel for docstring-parser (pyproject.toml): finished with status 'done'
  Created wheel for docstring-parser: filename=docstring_parser-0.11-py3-none-any.whl size=31551 sha256=07f7185ccec9a92ba4ce4118f81a35c3095d31d26830b2d294b3b29063acc618
  Stored in directory: /home/runner/.cache/pip/wheels/0f/f9/78/1186f8bf3425dbd3fb3fa32beee828876c792f49eb2554e888
Successfully built docstring-parser
Installing collected packages: pytz, wrapt, websockets, wcwidth, watchdog, vine, uvloop, urllib3, ujson, tzlocal, tzdata, typing-extensions, tomli_w, tomli, toml, structlog, sniffio, six, shellingham, ruff, rignore, redis, PyYAML, python-multipart, python-dotenv, pygments, pycryptodome, pycparser, psycopg2-binary, psycopg-binary, psutil, port-for, pluggy, platformdirs, pathspec, packaging, orjson, numpy, nr-stream, nr-date, mypy-extensions, mdurl, MarkupSafe, jmespath, itsdangerous, iniconfig, imapclient, idna, httptools, h11, greenlet, et-xmlfile, docstring-parser, dnspython, coverage, click, charset_normalizer, certifi, billiard, asyncpg, annotated-types, yapf, vulture, uvicorn, typing-inspection, typing_inspect, types-requests, typeguard, typeapi, sqlalchemy, sentry-sdk, requests, python-dateutil, pytest, pydantic-core, psycopg, prompt-toolkit, openpyxl, mypy, mirakuru, markdown-it-py, Mako, Jinja2, httpcore, email-validator, Deprecated, click-plugins, click-didyoumean, cffi, black, apscheduler, anyio, amqp, watchfiles, starlette, rich, pytest-postgresql, pytest-cov, pytest-asyncio, pydantic, pandas, nr-util, kombu, httpx, docker, databind, click-repl, botocore, argon2-cffi-bindings, alembic, typer, testcontainers, s3transfer, rich-toolkit, respx, python-telegram-bot, pydantic-settings, pydantic-extra-types, pandera, fastapi, databind.json, databind.core, celery, asgi-correlation-id, argon2-cffi, minio, fastapi-limiter, fastapi-cloud-cli, fastapi-cli, docspec, boto3, docspec-python, pydoc-markdown

Successfully installed Deprecated-1.2.18 Jinja2-3.1.6 Mako-1.3.10 MarkupSafe-3.0.3 PyYAML-6.0.3 alembic-1.16.4 amqp-5.3.1 annotated-types-0.7.0 anyio-4.4.0 apscheduler-3.10.4 argon2-cffi-25.1.0 argon2-cffi-bindings-25.1.0 asgi-correlation-id-4.3.1 asyncpg-0.30.0 billiard-4.2.2 black-25.1.0 boto3-1.40.21 botocore-1.40.57 celery-5.5.3 certifi-2025.10.5 cffi-2.0.0 charset_normalizer-3.4.4 click-8.3.0 click-didyoumean-0.3.1 click-plugins-1.1.1.2 click-repl-0.3.0 coverage-7.11.0 databind-4.5.2 databind.core-4.5.2 databind.json-4.5.2 dnspython-2.8.0 docker-7.1.0 docspec-2.2.1 docspec-python-2.2.2 docstring-parser-0.11 email-validator-2.3.0 et-xmlfile-2.0.0 fastapi-0.116.1 fastapi-cli-0.0.14 fastapi-cloud-cli-0.3.1 fastapi-limiter-0.1.6 greenlet-3.2.4 h11-0.14.0 httpcore-1.0.5 httptools-0.7.1 httpx-0.27.2 idna-3.11 imapclient-3.0.1 iniconfig-2.3.0 itsdangerous-2.2.0 jmespath-1.0.1 kombu-5.5.4 markdown-it-py-4.0.0 mdurl-0.1.2 minio-7.2.18 mirakuru-2.6.1 mypy-1.18.2 mypy-extensions-1.1.0 nr-date-2.1.0 nr-stream-1.1.5 nr-util-0.8.12 numpy-1.26.4 openpyxl-3.1.5 orjson-3.11.3 packaging-25.0 pandas-2.3.2 pandera-0.26.1 pathspec-0.12.1 platformdirs-4.5.0 pluggy-1.6.0 port-for-1.0.0 prompt-toolkit-3.0.52 psutil-7.1.1 psycopg-3.2.9 psycopg-binary-3.2.9 psycopg2-binary-2.9.10 pycparser-2.23 pycryptodome-3.23.0 pydantic-2.11.7 pydantic-core-2.33.2 pydantic-extra-types-2.10.6 pydantic-settings-2.2.1 pydoc-markdown-4.8.2 pygments-2.19.2 pytest-8.4.2 pytest-asyncio-1.1.0 pytest-cov-7.0.0 pytest-postgresql-7.0.2 python-dateutil-2.9.0.post0 python-dotenv-1.1.1 python-multipart-0.0.19 python-telegram-bot-22.3 pytz-2025.2 redis-6.4.0 requests-2.32.5 respx-0.22.0 rich-14.2.0 rich-toolkit-0.15.1 rignore-0.7.1 ruff-0.12.11 s3transfer-0.13.1 sentry-sdk-2.20.0 shellingham-1.5.4 six-1.17.0 sniffio-1.3.1 sqlalchemy-2.0.43 starlette-0.47.3 structlog-24.1.0 testcontainers-4.12.0 toml-0.10.2 tomli-2.3.0 tomli_w-1.2.0 typeapi-2.2.4 typeguard-4.4.4 typer-0.20.0 types-requests-2.32.4.20250809 typing-extensions-4.15.0 typing-inspection-0.4.2 typing_inspect-0.9.0 tzdata-2025.2 tzlocal-5.3.1 ujson-5.11.0 urllib3-2.5.0 uvicorn-0.35.0 uvloop-0.22.1 vine-5.1.0 vulture-2.10 watchdog-6.0.0 watchfiles-1.1.1 wcwidth-0.2.14 websockets-15.0.1 wrapt-1.17.3 yapf-0.43.0
Requirement already satisfied: python-telegram-bot==22.3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 1)) (22.3)
Requirement already satisfied: apscheduler==3.10.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 2)) (3.10.4)
Requirement already satisfied: asyncpg==0.30.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/alert_bot/requirements.txt (line 3)) (0.30.0)
Requirement already satisfied: httpx<0.29,>=0.27 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (0.27.2)
Requirement already satisfied: six>=1.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (1.17.0)
Requirement already satisfied: pytz in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (2025.2)
Requirement already satisfied: tzlocal!=3.*,>=2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/alert_bot/requirements.txt (line 2)) (5.3.1)
Requirement already satisfied: anyio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (4.4.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (2025.10.5)
Requirement already satisfied: httpcore==1.* in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (1.0.5)
Requirement already satisfied: idna in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (3.11)
Requirement already satisfied: sniffio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (1.3.1)
Requirement already satisfied: h11<0.15,>=0.13 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpcore==1.*->httpx<0.29,>=0.27->python-telegram-bot==22.3->-r services/alert_bot/requirements.txt (line 1)) (0.14.0)
Requirement already satisfied: uvicorn==0.35.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 1)) (0.35.0)
Requirement already satisfied: pydantic-settings==2.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 2)) (2.2.1)
Requirement already satisfied: fastapi==0.116.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 3)) (0.116.1)
Requirement already satisfied: sqlalchemy==2.0.43 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 4)) (2.0.43)
Requirement already satisfied: alembic==1.16.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 5)) (1.16.4)
Requirement already satisfied: psycopg==3.2.9 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from psycopg[binary]==3.2.9->-r services/api/requirements.txt (line 6)) (3.2.9)
Requirement already satisfied: httpx<0.28,>=0.27 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 7)) (0.27.2)
Requirement already satisfied: asyncpg==0.30.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 8)) (0.30.0)
Requirement already satisfied: boto3==1.40.21 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 9)) (1.40.21)
Collecting Jinja2==3.1.5 (from -r services/api/requirements.txt (line 10))
  Downloading jinja2-3.1.5-py3-none-any.whl.metadata (2.6 kB)
Requirement already satisfied: celery==5.5.3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 11)) (5.5.3)
Requirement already satisfied: structlog==24.1.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 12)) (24.1.0)
Requirement already satisfied: asgi-correlation-id==4.3.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 13)) (4.3.1)
Requirement already satisfied: fastapi-limiter==0.1.6 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 14)) (0.1.6)
Requirement already satisfied: python-multipart in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 15)) (0.0.19)
Collecting redis==5.0.8 (from -r services/api/requirements.txt (line 16))
  Downloading redis-5.0.8-py3-none-any.whl.metadata (9.2 kB)
Requirement already satisfied: sentry-sdk==2.20.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sentry-sdk[celery,fastapi,sqlalchemy]==2.20.0->-r services/api/requirements.txt (line 17)) (2.20.0)
Requirement already satisfied: imapclient==3.0.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/api/requirements.txt (line 18)) (3.0.1)
Requirement already satisfied: click>=7.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn==0.35.0->-r services/api/requirements.txt (line 1)) (8.3.0)
Requirement already satisfied: h11>=0.8 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn==0.35.0->-r services/api/requirements.txt (line 1)) (0.14.0)
Requirement already satisfied: pydantic>=2.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic-settings==2.2.1->-r services/api/requirements.txt (line 2)) (2.11.7)
Requirement already satisfied: python-dotenv>=0.21.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic-settings==2.2.1->-r services/api/requirements.txt (line 2)) (1.1.1)
Requirement already satisfied: starlette<0.48.0,>=0.40.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from fastapi==0.116.1->-r services/api/requirements.txt (line 3)) (0.47.3)
Requirement already satisfied: typing-extensions>=4.8.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from fastapi==0.116.1->-r services/api/requirements.txt (line 3)) (4.15.0)
Requirement already satisfied: greenlet>=1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from

_Truncated digest: original length exceeded limit._
