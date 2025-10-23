<!-- AWA-CI-DIGEST -->
## CI digest for `4cdd1de3`

- **Preview URL**: n/a
- **Mirror path**: ci-logs/mirror-logs/branch-main/latest
- **Workflow run**: [18758095548](https://github.com/AlexBomber12/AWA-App/actions/runs/18758095548)

| Job | Conclusion | URL |
| --- | ---------- | --- |
| unit | ⚠️ Cancelled | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18758095548/job/53515151862) |
| integration | ⚠️ Cancelled | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18758095548/job/53515265143) |
| preview | ⚠️ Cancelled | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18758095548/job/53515265406) |
| migrations | ⚠️ Cancelled | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18758095548/job/53515265408) |
| mirror_logs | ⏳ In Progress | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18758095548/job/53515265167) |

### Failed tails

**unit** (`unit/unit-setup.log`)

```
Requirement already satisfied: pytz>=2020.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandas==2.3.2->-r services/etl/requirements.txt (line 8)) (2025.2)
Requirement already satisfied: tzdata>=2022.7 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandas==2.3.2->-r services/etl/requirements.txt (line 8)) (2025.2)
Requirement already satisfied: argon2-cffi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from minio==7.2.16->-r services/etl/requirements.txt (line 2)) (25.1.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from minio==7.2.16->-r services/etl/requirements.txt (line 2)) (2025.10.5)
Requirement already satisfied: pycryptodome in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from minio==7.2.16->-r services/etl/requirements.txt (line 2)) (3.23.0)
Requirement already satisfied: typing-extensions in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from minio==7.2.16->-r services/etl/requirements.txt (line 2)) (4.15.0)
Requirement already satisfied: urllib3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from minio==7.2.16->-r services/etl/requirements.txt (line 2)) (2.5.0)
Requirement already satisfied: billiard<5.0,>=4.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (4.2.2)
Requirement already satisfied: kombu<5.6,>=5.5.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (5.5.4)
Requirement already satisfied: vine<6.0,>=5.1.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (5.1.0)
Requirement already satisfied: click<9.0,>=8.1.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (8.3.0)
Requirement already satisfied: click-didyoumean>=0.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (0.3.1)
Requirement already satisfied: click-repl>=0.2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (0.3.0)
Requirement already satisfied: click-plugins>=1.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (1.1.1.2)
Collecting cachetools>=4.2 (from python-amazon-sp-api==1.9.50->-r services/etl/requirements.txt (line 5))
  Using cached cachetools-6.2.1-py3-none-any.whl.metadata (5.5 kB)
Collecting confuse>=1.4 (from python-amazon-sp-api==1.9.50->-r services/etl/requirements.txt (line 5))
  Using cached confuse-2.0.1-py3-none-any.whl.metadata (3.7 kB)
Requirement already satisfied: python-dotenv>=0.21.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic-settings==2.2.1->-r services/etl/requirements.txt (line 6)) (1.1.1)
Requirement already satisfied: greenlet>=1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.43->-r services/etl/requirements.txt (line 14)) (3.2.4)
Requirement already satisfied: psycopg-binary==3.2.9 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from psycopg[binary]==3.2.9->-r services/etl/requirements.txt (line 11)) (3.2.9)
Collecting multimethod<=1.10.0 (from pandera==0.19.*->-r services/etl/requirements.txt (line 9))
  Using cached multimethod-1.10-py3-none-any.whl.metadata (8.2 kB)
Requirement already satisfied: packaging>=20.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandera==0.19.*->-r services/etl/requirements.txt (line 9)) (25.0)
Requirement already satisfied: typeguard in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandera==0.19.*->-r services/etl/requirements.txt (line 9)) (4.4.4)
Requirement already satisfied: typing-inspect>=0.6.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandera==0.19.*->-r services/etl/requirements.txt (line 9)) (0.9.0)
Requirement already satisfied: wrapt in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandera==0.19.*->-r services/etl/requirements.txt (line 9)) (1.17.3)
Requirement already satisfied: et-xmlfile in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from openpyxl==3.1.*->-r services/etl/requirements.txt (line 10)) (2.0.0)
Requirement already satisfied: amqp<6.0.0,>=5.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->-r services/etl/requirements.txt (line 3)) (5.3.1)
Requirement already satisfied: prompt-toolkit>=3.0.36 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from click-repl>=0.2.0->celery==5.5.3->-r services/etl/requirements.txt (line 3)) (3.0.52)
Requirement already satisfied: pyyaml in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from confuse>=1.4->python-amazon-sp-api==1.9.50->-r services/etl/requirements.txt (line 5)) (6.0.3)
Requirement already satisfied: wcwidth in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.5.3->-r services/etl/requirements.txt (line 3)) (0.2.14)
Requirement already satisfied: annotated-types>=0.6.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic->keepa==1.3.15->-r services/etl/requirements.txt (line 1)) (0.7.0)
Requirement already satisfied: pydantic-core==2.33.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic->keepa==1.3.15->-r services/etl/requirements.txt (line 1)) (2.33.2)
Requirement already satisfied: typing-inspection>=0.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic->keepa==1.3.15->-r services/etl/requirements.txt (line 1)) (0.4.2)
Requirement already satisfied: six>=1.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-dateutil>=2.8.2->pandas==2.3.2->-r services/etl/requirements.txt (line 8)) (1.17.0)
Requirement already satisfied: charset_normalizer<4,>=2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from requests>=2.2->keepa==1.3.15->-r services/etl/requirements.txt (line 1)) (3.4.4)
Requirement already satisfied: idna<4,>=2.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from requests>=2.2->keepa==1.3.15->-r services/etl/requirements.txt (line 1)) (3.11)
Requirement already satisfied: mypy-extensions>=0.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from typing-inspect>=0.6.0->pandera==0.19.*->-r services/etl/requirements.txt (line 9)) (1.1.0)
Collecting aiohappyeyeballs>=2.5.0 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached aiohappyeyeballs-2.6.1-py3-none-any.whl.metadata (5.9 kB)
Collecting aiosignal>=1.4.0 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached aiosignal-1.4.0-py3-none-any.whl.metadata (3.7 kB)
Collecting attrs>=17.3.0 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached attrs-25.4.0-py3-none-any.whl.metadata (10 kB)
Collecting frozenlist>=1.1.1 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached frozenlist-1.8.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (20 kB)
Collecting multidict<7.0,>=4.5 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached multidict-6.7.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (5.3 kB)
Collecting propcache>=0.2.0 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached propcache-0.4.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (13 kB)
Collecting yarl<2.0,>=1.17.0 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached yarl-1.22.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (75 kB)
Requirement already satisfied: argon2-cffi-bindings in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from argon2-cffi->minio==7.2.16->-r services/etl/requirements.txt (line 2)) (25.1.0)
Requirement already satisfied: cffi>=1.0.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from argon2-cffi-bindings->argon2-cffi->minio==7.2.16->-r services/etl/requirements.txt (line 2)) (2.0.0)
Requirement already satisfied: pycparser in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from cffi>=1.0.1->argon2-cffi-bindings->argon2-cffi->minio==7.2.16->-r services/etl/requirements.txt (line 2)) (2.23)
Using cached keepa-1.3.15-py3-none-any.whl (38 kB)
Using cached python_amazon_sp_api-1.9.50-py3-none-any.whl (135 kB)
Using cached pandera-0.19.3-py3-none-any.whl (251 kB)
Using cached multimethod-1.10-py3-none-any.whl (9.9 kB)
Using cached cachetools-6.2.1-py3-none-any.whl (11 kB)
Using cached confuse-2.0.1-py3-none-any.whl (24 kB)
Using cached aiohttp-3.13.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (1.7 MB)
Using cached multidict-6.7.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (246 kB)
Using cached yarl-1.22.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (365 kB)
Using cached aiohappyeyeballs-2.6.1-py3-none-any.whl (15 kB)
Using cached aiosignal-1.4.0-py3-none-any.whl (7.5 kB)
Using cached attrs-25.4.0-py3-none-any.whl (67 kB)
Using cached frozenlist-1.8.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (231 kB)
Using cached propcache-0.4.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (210 kB)
Using cached tqdm-4.67.1-py3-none-any.whl (78 kB)
Installing collected packages: tqdm, propcache, multimethod, multidict, frozenlist, confuse, cachetools, attrs, aiohappyeyeballs, yarl, python-amazon-sp-api, aiosignal, pandera, aiohttp, keepa
  Attempting uninstall: pandera
    Found existing installation: pandera 0.26.1
    Uninstalling pandera-0.26.1:
      Successfully uninstalled pandera-0.26.1

Successfully installed aiohappyeyeballs-2.6.1 aiohttp-3.13.1 aiosignal-1.4.0 attrs-25.4.0 cachetools-6.2.1 confuse-2.0.1 frozenlist-1.8.0 keepa-1.3.15 multidict-6.7.0 multimethod-1.10 pandera-0.19.3 propcache-0.4.1 python-amazon-sp-api-1.9.50 tqdm-4.67.1 yarl-1.22.0
Requirement already satisfied: celery==5.5.3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (5.5.3)
Requirement already satisfied: asyncpg==0.30.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/fees_h10/requirements.txt (line 2)) (0.30.0)
Requirement already satisfied: httpx<0.28,>=0.27 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/fees_h10/requirements.txt (line 3)) (0.27.2)
Requirement already satisfied: sqlalchemy==2.0.43 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/fees_h10/requirements.txt (line 4)) (2.0.43)
Requirement already satisfied: billiard<5.0,>=4.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (4.2.2)
Requirement already satisfied: kombu<5.6,>=5.5.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (5.5.4)
Requirement already satisfied: vine<6.0,>=5.1.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (5.1.0)
Requirement already satisfied: click<9.0,>=8.1.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (8.3.0)
Requirement already satisfied: click-didyoumean>=0.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (0.3.1)
Requirement already satisfied: click-repl>=0.2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (0.3.0)
Requirement already satisfied: click-plugins>=1.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (1.1.1.2)
Requirement already satisfied: python-dateutil>=2.8.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (2.9.0.post0)
Requirement already satisfied: greenlet>=1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.43->-r services/fees_h10/requirements.txt (line 4)) (3.2.4)
Requirement already satisfied: typing-extensions>=4.6.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.43->-r services/fees_h10/requirements.txt (line 4)) (4.15.0)
Requirement already satisfied: anyio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/fees_h10/requirements.txt (line 3)) (4.4.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/fees_h10/requirements.txt (line 3)) (2025.10.5)
Requirement already satisfied: httpcore==1.* in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/fees_h10/requirements.txt (line 3)) (1.0.5)
Requirement already satisfied: idna in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/fees_h10/requirements.txt (line 3)) (3.11)
Requirement already satisfied: sniffio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/fees_h10/requirements.txt (line 3)) (1.3.1)
Requirement already satisfied: h11<0.15,>=0.13 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpcore==1.*->httpx<0.28,>=0.27->-r services/fees_h10/requirements.txt (line 3)) (0.14.0)
Requirement already satisfied: amqp<6.0.0,>=5.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (5.3.1)
Requirement already satisfied: tzdata>=2025.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (2025.2)
Requirement already satisfied: packaging in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (25.0)
Requirement already satisfied: prompt-toolkit>=3.0.36 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from click-repl>=0.2.0->celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (3.0.52)
Requirement already satisfied: wcwidth in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (0.2.14)
Requirement already satisfied: six>=1.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-dateutil>=2.8.2->celery==5.5.3->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (1.17.0)
Requirement already satisfied: redis!=4.5.5,!=5.0.2,<=5.2.1,>=4.5.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu[redis]; extra == "redis"->celery[redis]==5.5.3->-r services/fees_h10/requirements.txt (line 1)) (5.0.8)
Requirement already satisfied: fastapi==0.116.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/llm_server/requirements.txt (line 1)) (0.116.1)
Requirement already satisfied: uvicorn==0.35.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/llm_server/requirements.txt (line 2)) (0.35.0)
Requirement already satisfied: numpy==1.26.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/llm_server/requirements.txt (line 3)) (1.26.4)
Collecting sentencepiece==0.2.0 (from -r services/llm_server/requirements.txt (line 4))
  Using cached sentencepiece-0.2.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (7.7 kB)
Requirement already satisfied: starlette<0.48.0,>=0.40.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from fastapi==0.116.1->-r services/llm_server/requirements.txt (line 1)) (0.47.3)
Requirement already satisfied: pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from fastapi==0.116.1->-r services/llm_server/requirements.txt (line 1)) (2.11.7)
Requirement already satisfied: typing-extensions>=4.8.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from fastapi==0.116.1->-r services/llm_server/requirements.txt (line 1)) (4.15.0)
Requirement already satisfied: click>=7.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn==0.35.0->uvicorn[standard]==0.35.0->-r services/llm_server/requirements.txt (line 2)) (8.3.0)
Requirement already satisfied: h11>=0.8 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn==0.35.0->uvicorn[standard]==0.35.0->-r services/llm_server/requirements.txt (line 2)) (0.14.0)
Requirement already satisfied: httptools>=0.6.3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/llm_server/requirements.txt (line 2)) (0.7.1)
Requirement already satisfied: python-dotenv>=0.13 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/llm_server/requirements.txt (line 2)) (1.1.1)
Requirement already satisfied: pyyaml>=5.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/llm_server/requirements.txt (line 2)) (6.0.3)
Requirement already satisfied: uvloop>=0.15.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/llm_server/requirements.txt (line 2)) (0.22.1)
Requirement already satisfied: watchfiles>=0.13 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/llm_server/requirements.txt (line 2)) (1.1.1)
Requirement already satisfied: websockets>=10.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/llm_server/requirements.txt (line 2)) (15.0.1)
Requirement already satisfied: annotated-types>=0.6.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4->fastapi==0.116.1->-r services/llm_server/requirements.txt (line 1)) (0.7.0)
Requirement already satisfied: pydantic-core==2.33.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4->fastapi==0.116.1->-r services/llm_server/requirements.txt (line 1)) (2.33.2)
Requirement already satisfied: typing-inspection>=0.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4->fastapi==0.116.1->-r services/llm_server/requirements.txt (line 1)) (0.4.2)
Requirement already satisfied: anyio<5,>=3.6.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from starlette<0.48.0,>=0.40.0->fastapi==0.116.1->-r services/llm_server/requirements.txt (line 1)) (4.4.0)
Requirement already satisfied: idna>=2.8 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from anyio<5,>=3.6.2->starlette<0.48.0,>=0.40.0->fastapi==0.116.1->-r services/llm_server/requirements.txt (line 1)) (3.11)
Requirement already satisfied: sniffio>=1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from anyio<5,>=3.6.2->starlette<0.48.0,>=0.40.0->fastapi==0.116.1->-r services/llm_server/requirements.txt (line 1)) (1.3.1)
Using cached sentencepiece-0.2.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (1.3 MB)
Installing collected packages: sentencepiece
Successfully installed sentencepiece-0.2.0
Requirement already satisfied: apscheduler==3.10.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/logistics_etl/requirements.txt (line 1)) (3.10.4)
Requirement already satisfied: httpx<0.28,>=0.27 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/logistics_etl/requirements.txt (line 2)) (0.27.2)
Requirement already satisfied: sqlalchemy==2.0.43 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/logistics_etl/requirements.txt (line 3)) (2.0.43)
Requirement already satisfied: asyncpg==0.30.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/logistics_etl/requirements.txt (line 4)) (0.30.0)
Requirement already satisfied: six>=1.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (1.17.0)
Requirement already satisfied: pytz in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (2025.2)
Requirement already satisfied: tzlocal!=3.*,>=2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from apscheduler==3.10.4->-r services/logistics_etl/requirements.txt (line 1)) (5.3.1)
Requirement already satisfied: greenlet>=1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.43->-r services/logistics_etl/requirements.txt (line 3)) (3.2.4)
Requirement already satisfied: typing-extensions>=4.6.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.43->-r services/logistics_etl/requirements.txt (line 3)) (4.15.0)
Requirement already satisfied: anyio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/logistics_etl/requirements.txt (line 2)) (4.4.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/logistics_etl/requirements.txt (line 2)) (2025.10.5)
Requirement already satisfied: httpcore==1.* in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/logistics_etl/requirements.txt (line 2)) (1.0.5)
Requirement already satisfied: idna in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/logistics_etl/requirements.txt (line 2)) (3.11)
Requirement already satisfied: sniffio in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpx<0.28,>=0.27->-r services/logistics_etl/requirements.txt (line 2)) (1.3.1)
Requirement already satisfied: h11<0.15,>=0.13 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from httpcore==1.*->httpx<0.28,>=0.27->-r services/logistics_etl/requirements.txt (line 2)) (0.14.0)
Requirement already satisfied: celery==5.5.3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (5.5.3)
Requirement already satisfied: billiard<5.0,>=4.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (4.2.2)
Requirement already satisfied: kombu<5.6,>=5.5.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (5.5.4)
Requirement already satisfied: vine<6.0,>=5.1.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (5.1.0)
Requirement already satisfied: click<9.0,>=8.1.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (8.3.0)
Requirement already satisfied: click-didyoumean>=0.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (0.3.1)
Requirement already satisfied: click-repl>=0.2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (0.3.0)
Requirement already satisfied: click-plugins>=1.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (1.1.1.2)
Requirement already satisfied: python-dateutil>=2.8.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (2.9.0.post0)
Requirement already satisfied: amqp<6.0.0,>=5.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (5.3.1)
Requirement already satisfied: tzdata>=2025.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (2025.2)
Requirement already satisfied: packaging in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (25.0)
Requirement already satisfied: prompt-toolkit>=3.0.36 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from click-repl>=0.2.0->celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (3.0.52)
Requirement already satisfied: wcwidth in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (0.2.14)
Requirement already satisfied: six>=1.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-dateutil>=2.8.2->celery==5.5.3->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (1.17.0)
Requirement already satisfied: redis!=4.5.5,!=5.0.2,<=5.2.1,>=4.5.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu[redis]; extra == "redis"->celery[redis]==5.5.3->-r services/price_importer/requirements.txt (line 1)) (5.0.8)
Requirement already satisfied: fastapi==0.116.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/worker/requirements.txt (line 1)) (0.116.1)
Requirement already satisfied: uvicorn==0.35.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/worker/requirements.txt (line 2)) (0.35.0)
Requirement already satisfied: pydantic-settings==2.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/worker/requirements.txt (line 3)) (2.2.1)
Requirement already satisfied: celery==5.5.3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/worker/requirements.txt (line 4)) (5.5.3)
Requirement already satisfied: redis==5.0.8 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from -r services/worker/requirements.txt (line 5)) (5.0.8)
Requirement already satisfied: sentry-sdk==2.20.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sentry-sdk[celery,fastapi]==2.20.0->-r services/worker/requirements.txt (line 6)) (2.20.0)
Requirement already satisfied: starlette<0.48.0,>=0.40.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from fastapi==0.116.1->-r services/worker/requirements.txt (line 1)) (0.47.3)
Requirement already satisfied: pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from fastapi==0.116.1->-r services/worker/requirements.txt (line 1)) (2.11.7)
Requirement already satisfied: typing-extensions>=4.8.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from fastapi==0.116.1->-r services/worker/requirements.txt (line 1)) (4.15.0)
Requirement already satisfied: click>=7.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn==0.35.0->uvicorn[standard]==0.35.0->-r services/worker/requirements.txt (line 2)) (8.3.0)
Requirement already satisfied: h11>=0.8 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn==0.35.0->uvicorn[standard]==0.35.0->-r services/worker/requirements.txt (line 2)) (0.14.0)
Requirement already satisfied: python-dotenv>=0.21.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic-settings==2.2.1->-r services/worker/requirements.txt (line 3)) (1.1.1)
Requirement already satisfied: billiard<5.0,>=4.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/worker/requirements.txt (line 4)) (4.2.2)
Requirement already satisfied: kombu<5.6,>=5.5.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/worker/requirements.txt (line 4)) (5.5.4)
Requirement already satisfied: vine<6.0,>=5.1.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/worker/requirements.txt (line 4)) (5.1.0)
Requirement already satisfied: click-didyoumean>=0.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/worker/requirements.txt (line 4)) (0.3.1)
Requirement already satisfied: click-repl>=0.2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/worker/requirements.txt (line 4)) (0.3.0)
Requirement already satisfied: click-plugins>=1.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/worker/requirements.txt (line 4)) (1.1.1.2)
Requirement already satisfied: python-dateutil>=2.8.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/worker/requirements.txt (line 4)) (2.9.0.post0)
Requirement already satisfied: urllib3>=1.26.11 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sentry-sdk==2.20.0->sentry-sdk[celery,fastapi]==2.20.0->-r services/worker/requirements.txt (line 6)) (2.5.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sentry-sdk==2.20.0->sentry-sdk[celery,fastapi]==2.20.0->-r services/worker/requirements.txt (line 6)) (2025.10.5)
Requirement already satisfied: httptools>=0.6.3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/worker/requirements.txt (line 2)) (0.7.1)
Requirement already satisfied: pyyaml>=5.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/worker/requirements.txt (line 2)) (6.0.3)
Requirement already satisfied: uvloop>=0.15.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/worker/requirements.txt (line 2)) (0.22.1)
Requirement already satisfied: watchfiles>=0.13 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/worker/requirements.txt (line 2)) (1.1.1)
Requirement already satisfied: websockets>=10.4 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from uvicorn[standard]==0.35.0->-r services/worker/requirements.txt (line 2)) (15.0.1)
Requirement already satisfied: amqp<6.0.0,>=5.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->-r services/worker/requirements.txt (line 4)) (5.3.1)
Requirement already satisfied: tzdata>=2025.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->-r services/worker/requirements.txt (line 4)) (2025.2)
Requirement already satisfied: packaging in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->-r services/worker/requirements.txt (line 4)) (25.0)
Requirement already satisfied: annotated-types>=0.6.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4->fastapi==0.116.1->-r services/worker/requirements.txt (line 1)) (0.7.0)
Requirement already satisfied: pydantic-core==2.33.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4->fastapi==0.116.1->-r services/worker/requirements.txt (line 1)) (2.33.2)
Requirement already satisfied: typing-inspection>=0.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4->fastapi==0.116.1->-r services/worker/requirements.txt (line 1)) (0.4.2)
Requirement already satisfied: anyio<5,>=3.6.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from starlette<0.48.0,>=0.40.0->fastapi==0.116.1->-r services/worker/requirements.txt (line 1)) (4.4.0)
Requirement already satisfied: idna>=2.8 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from anyio<5,>=3.6.2->starlette<0.48.0,>=0.40.0->fastapi==0.116.1->-r services/worker/requirements.txt (line 1)) (3.11)
Requirement already satisfied: sniffio>=1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from anyio<5,>=3.6.2->starlette<0.48.0,>=0.40.0->fastapi==0.116.1->-r services/worker/requirements.txt (line 1)) (1.3.1)
Requirement already satisfied: prompt-toolkit>=3.0.36 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from click-repl>=0.2.0->celery==5.5.3->-r services/worker/requirements.txt (line 4)) (3.0.52)
Requirement already satisfied: wcwidth in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.5.3->-r services/worker/requirements.txt (line 4)) (0.2.14)
Requirement already satisfied: six>=1.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-dateutil>=2.8.2->celery==5.5.3->-r services/worker/requirements.txt (line 4)) (1.17.0)
No broken requirements found.
```

**unit** (`unit-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-logs.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml logs --no-color
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-ps.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml ps
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-migrations-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:31Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-23T18:24:32Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-setup.log`)

```
Requirement already satisfied: pytz>=2020.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandas==2.3.2->-r services/etl/requirements.txt (line 8)) (2025.2)
Requirement already satisfied: tzdata>=2022.7 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandas==2.3.2->-r services/etl/requirements.txt (line 8)) (2025.2)
Requirement already satisfied: argon2-cffi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from minio==7.2.16->-r services/etl/requirements.txt (line 2)) (25.1.0)
Requirement already satisfied: certifi in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from minio==7.2.16->-r services/etl/requirements.txt (line 2)) (2025.10.5)
Requirement already satisfied: pycryptodome in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from minio==7.2.16->-r services/etl/requirements.txt (line 2)) (3.23.0)
Requirement already satisfied: typing-extensions in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from minio==7.2.16->-r services/etl/requirements.txt (line 2)) (4.15.0)
Requirement already satisfied: urllib3 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from minio==7.2.16->-r services/etl/requirements.txt (line 2)) (2.5.0)
Requirement already satisfied: billiard<5.0,>=4.2.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (4.2.2)
Requirement already satisfied: kombu<5.6,>=5.5.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (5.5.4)
Requirement already satisfied: vine<6.0,>=5.1.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (5.1.0)
Requirement already satisfied: click<9.0,>=8.1.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (8.3.0)
Requirement already satisfied: click-didyoumean>=0.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (0.3.1)
Requirement already satisfied: click-repl>=0.2.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (0.3.0)
Requirement already satisfied: click-plugins>=1.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from celery==5.5.3->-r services/etl/requirements.txt (line 3)) (1.1.1.2)
Collecting cachetools>=4.2 (from python-amazon-sp-api==1.9.50->-r services/etl/requirements.txt (line 5))
  Using cached cachetools-6.2.1-py3-none-any.whl.metadata (5.5 kB)
Collecting confuse>=1.4 (from python-amazon-sp-api==1.9.50->-r services/etl/requirements.txt (line 5))
  Using cached confuse-2.0.1-py3-none-any.whl.metadata (3.7 kB)
Requirement already satisfied: python-dotenv>=0.21.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic-settings==2.2.1->-r services/etl/requirements.txt (line 6)) (1.1.1)
Requirement already satisfied: greenlet>=1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from sqlalchemy==2.0.43->-r services/etl/requirements.txt (line 14)) (3.2.4)
Requirement already satisfied: psycopg-binary==3.2.9 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from psycopg[binary]==3.2.9->-r services/etl/requirements.txt (line 11)) (3.2.9)
Collecting multimethod<=1.10.0 (from pandera==0.19.*->-r services/etl/requirements.txt (line 9))
  Using cached multimethod-1.10-py3-none-any.whl.metadata (8.2 kB)
Requirement already satisfied: packaging>=20.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandera==0.19.*->-r services/etl/requirements.txt (line 9)) (25.0)
Requirement already satisfied: typeguard in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandera==0.19.*->-r services/etl/requirements.txt (line 9)) (4.4.4)
Requirement already satisfied: typing-inspect>=0.6.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandera==0.19.*->-r services/etl/requirements.txt (line 9)) (0.9.0)
Requirement already satisfied: wrapt in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pandera==0.19.*->-r services/etl/requirements.txt (line 9)) (1.17.3)
Requirement already satisfied: et-xmlfile in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from openpyxl==3.1.*->-r services/etl/requirements.txt (line 10)) (2.0.0)
Requirement already satisfied: amqp<6.0.0,>=5.1.1 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from kombu<5.6,>=5.5.2->celery==5.5.3->-r services/etl/requirements.txt (line 3)) (5.3.1)
Requirement already satisfied: prompt-toolkit>=3.0.36 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from click-repl>=0.2.0->celery==5.5.3->-r services/etl/requirements.txt (line 3)) (3.0.52)
Requirement already satisfied: pyyaml in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from confuse>=1.4->python-amazon-sp-api==1.9.50->-r services/etl/requirements.txt (line 5)) (6.0.3)
Requirement already satisfied: wcwidth in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from prompt-toolkit>=3.0.36->click-repl>=0.2.0->celery==5.5.3->-r services/etl/requirements.txt (line 3)) (0.2.14)
Requirement already satisfied: annotated-types>=0.6.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic->keepa==1.3.15->-r services/etl/requirements.txt (line 1)) (0.7.0)
Requirement already satisfied: pydantic-core==2.33.2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic->keepa==1.3.15->-r services/etl/requirements.txt (line 1)) (2.33.2)
Requirement already satisfied: typing-inspection>=0.4.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from pydantic->keepa==1.3.15->-r services/etl/requirements.txt (line 1)) (0.4.2)
Requirement already satisfied: six>=1.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from python-dateutil>=2.8.2->pandas==2.3.2->-r services/etl/requirements.txt (line 8)) (1.17.0)
Requirement already satisfied: charset_normalizer<4,>=2 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from requests>=2.2->keepa==1.3.15->-r services/etl/requirements.txt (line 1)) (3.4.4)
Requirement already satisfied: idna<4,>=2.5 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from requests>=2.2->keepa==1.3.15->-r services/etl/requirements.txt (line 1)) (3.11)
Requirement already satisfied: mypy-extensions>=0.3.0 in /opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages (from typing-inspect>=0.6.0->pandera==0.19.*->-r services/etl/requirements.txt (line 9)) (1.1.0)
Collecting aiohappyeyeballs>=2.5.0 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached aiohappyeyeballs-2.6.1-py3-none-any.whl.metadata (5.9 kB)
Collecting aiosignal>=1.4.0 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached aiosignal-1.4.0-py3-none-any.whl.metadata (3.7 kB)
Collecting attrs>=17.3.0 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached attrs-25.4.0-py3-none-any.whl.metadata (10 kB)
Collecting frozenlist>=1.1.1 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached frozenlist-1.8.0-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (20 kB)
Collecting multidict<7.0,>=4.5 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached multidict-6.7.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (5.3 kB)
Collecting propcache>=0.2.0 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached propcache-0.4.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (13 kB)
Collecting yarl<2.0,>=1.17.0 (from aiohttp->keepa==1.3.15->-r services/etl/requirements.txt (line 1))
  Using cached yarl-1.22.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (75 kB)
Requirement already satisfied: argon2-cf

_Truncated digest: original length exceeded limit._
