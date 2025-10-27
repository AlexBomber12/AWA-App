<!-- AWA-CI-DIGEST -->
## CI digest for `74fea396`

- **Preview URL**: n/a
- **Mirror path**: ci-logs/mirror-logs/pr-454/latest
- **Workflow run**: [18825391921](https://github.com/AlexBomber12/AWA-App/actions/runs/18825391921)

| Job | Conclusion | URL |
| --- | ---------- | --- |
| unit | ❌ Failure | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18825391921/job/53707773490) |
| migrations | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18825391921/job/53707862894) |
| integration | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18825391921/job/53707862895) |
| preview | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18825391921/job/53707862945) |
| mirror_logs | ⏳ In Progress | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18825391921/job/53707862863) |

### Failed tails

**unit** (`unit-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-logs.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml logs --no-color
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-ps.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml ps
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-eslint.log`)

```

> lint
> eslint --fix

```

**unit** (`unit-migrations-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:50Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-27T00:02:51Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
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
GITHUB_ACTION=__run_15
GITHUB_ACTIONS=true
GITHUB_ACTION_REF=
GITHUB_ACTION_REPOSITORY=
GITHUB_ACTOR=AlexBomber12
GITHUB_ACTOR_ID=48256657
GITHUB_API_URL=https://api.github.com
GITHUB_BASE_REF=main
GITHUB_ENV=/home/runner/work/_temp/_runner_file_commands/set_env_e6c1af9e-f33d-49cc-88d0-9fc6f0b4b01d
GITHUB_EVENT_NAME=pull_request
GITHUB_EVENT_PATH=/home/runner/work/_temp/_github_workflow/event.json
GITHUB_GRAPHQL_URL=https://api.github.com/graphql
GITHUB_HEAD_REF=pr-104-linters-quality-gate
GITHUB_JOB=unit
GITHUB_OUTPUT=/home/runner/work/_temp/_runner_file_commands/set_output_e6c1af9e-f33d-49cc-88d0-9fc6f0b4b01d
GITHUB_PATH=/home/runner/work/_temp/_runner_file_commands/add_path_e6c1af9e-f33d-49cc-88d0-9fc6f0b4b01d
GITHUB_REF=refs/pull/454/merge
GITHUB_REF_NAME=454/merge
GITHUB_REF_PROTECTED=false
GITHUB_REF_TYPE=branch
GITHUB_REPOSITORY=AlexBomber12/AWA-App
GITHUB_REPOSITORY_ID=1011502908
GITHUB_REPOSITORY_OWNER=AlexBomber12
GITHUB_REPOSITORY_OWNER_ID=48256657
GITHUB_RETENTION_DAYS=90
GITHUB_RUN_ATTEMPT=2
GITHUB_RUN_ID=18825391921
GITHUB_RUN_NUMBER=1228
GITHUB_SERVER_URL=https://github.com
GITHUB_SHA=74fea39666aeb3f105bfa55fa4fecf349f0bf5f1
GITHUB_STATE=/home/runner/work/_temp/_runner_file_commands/save_state_e6c1af9e-f33d-49cc-88d0-9fc6f0b4b01d
GITHUB_STEP_SUMMARY=/home/runner/work/_temp/_runner_file_commands/step_summary_e6c1af9e-f33d-49cc-88d0-9fc6f0b4b01d
GITHUB_TRIGGERING_ACTOR=AlexBomber12
GITHUB_WORKFLOW=ci
GITHUB_WORKFLOW_REF=AlexBomber12/AWA-App/.github/workflows/ci.yml@refs/pull/454/merge
GITHUB_WORKFLOW_SHA=74fea39666aeb3f105bfa55fa4fecf349f0bf5f1
GITHUB_WORKSPACE=/home/runner/work/AWA-App/AWA-App
GOROOT_1_22_X64=/opt/hostedtoolcache/go/1.22.12/x64
GOROOT_1_23_X64=/opt/hostedtoolcache/go/1.23.12/x64
GOROOT_1_24_X64=/opt/hostedtoolcache/go/1.24.7/x64
GRADLE_HOME=/usr/share/gradle-9.1.0
HOME=/home/runner
HOMEBREW_CLEANUP_PERIODIC_FULL_DAYS=3650
HOMEBREW_NO_AUTO_UPDATE=1
INVOCATION_ID=af14711a44554829af6415a22ee0b34c
ImageOS=ubuntu24
ImageVersion=20250929.60.1
JAVA_HOME=/usr/lib/jvm/temurin-17-jdk-amd64
JAVA_HOME_11_X64=/usr/lib/jvm/temurin-11-jdk-amd64
JAVA_HOME_17_X64=/usr/lib/jvm/temurin-17-jdk-amd64
JAVA_HOME_21_X64=/usr/lib/jvm/temurin-21-jdk-amd64
JAVA_HOME_25_X64=/usr/lib/jvm/temurin-25-jdk-amd64
JAVA_HOME_8_X64=/usr/lib/jvm/temurin-8-jdk-amd64
JOURNAL_STREAM=9:10923
LANG=C.UTF-8
LD_LIBRARY_PATH=/opt/hostedtoolcache/Python/3.11.13/x64/lib
LOGNAME=runner
MEMORY_PRESSURE_WATCH=/sys/fs/cgroup/system.slice/hosted-compute-agent.service/memory.pressure
MEMORY_PRESSURE_WRITE=c29tZSAyMDAwMDAgMjAwMDAwMAA=
NODE_VERSION=20
NVM_DIR=/home/runner/.nvm
PATH=/opt/hostedtoolcache/node/20.19.5/x64/bin:/opt/hostedtoolcache/Python/3.11.13/x64/bin:/opt/hostedtoolcache/Python/3.11.13/x64:/snap/bin:/home/runner/.local/bin:/opt/pipx_bin:/home/runner/.cargo/bin:/home/runner/.config/composer/vendor/bin:/usr/local/.ghcup/bin:/home/runner/.dotnet/tools:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
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
RUNNER_NAME=GitHub Actions 1000008465
RUNNER_OS=Linux
RUNNER_TEMP=/home/runner/work/_temp
RUNNER_TOOL_CACHE=/opt/hostedtoolcache
RUNNER_TRACKING_ID=github_e827f6b4-0eff-489d-8adc-108d308d1fe7
RUNNER_WORKSPACE=/home/runner/work/AWA-App
SELENIUM_JAR_PATH=/usr/share/java/selenium-server.jar
SGX_AESM_ADDR=1
SHELL=/bin/bash
SHLVL=2
SWIFT_PATH=/usr/share/swift/usr/bin
SYSTEMD_EXEC_PID=1907
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
app/health/page.tsx(3,10): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/layout.tsx(5,5): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/layout.tsx(6,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/page.tsx(1,22): error TS6142: Module '../components/Card' was resolved to '/home/runner/work/AWA-App/AWA-App/webapp/components/Card.tsx', but '--jsx' is not set.
app/page.tsx(2,27): error TS6142: Module '../components/DataTable' was resolved to '/home/runner/work/AWA-App/AWA-App/webapp/components/DataTable.tsx', but '--jsx' is not set.
app/page.tsx(14,5): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/page.tsx(15,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/sku/[asin]/approve-button.tsx(8,5): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/sku/[asin]/page.tsx(1,22): error TS6142: Module '../../../components/Card' was resolved to '/home/runner/work/AWA-App/AWA-App/webapp/components/Card.tsx', but '--jsx' is not set.
app/sku/[asin]/page.tsx(2,24): error TS6142: Module '../../../components/PriceChart' was resolved to '/home/runner/work/AWA-App/AWA-App/webapp/components/PriceChart.tsx', but '--jsx' is not set.
app/sku/[asin]/page.tsx(3,27): error TS6142: Module './approve-button' was resolved to '/home/runner/work/AWA-App/AWA-App/webapp/app/sku/[asin]/approve-button.tsx', but '--jsx' is not set.
app/sku/[asin]/page.tsx(20,5): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/sku/[asin]/page.tsx(21,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/sku/[asin]/page.tsx(22,9): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/sku/[asin]/page.tsx(23,9): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/sku/[asin]/page.tsx(24,9): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/sku/[asin]/page.tsx(25,9): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/sku/[asin]/page.tsx(27,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
app/sku/[asin]/page.tsx(28,9): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/Card.tsx(3,5): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(11,8): error TS6142: Module './ui/table' was resolved to '/home/runner/work/AWA-App/AWA-App/webapp/components/ui/table.tsx', but '--jsx' is not set.
components/DataTable.tsx(12,23): error TS6142: Module './StatBadge' was resolved to '/home/runner/work/AWA-App/AWA-App/webapp/components/StatBadge.tsx', but '--jsx' is not set.
components/DataTable.tsx(23,5): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(24,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(25,9): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(26,11): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(27,11): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(28,11): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(31,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(33,11): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(38,13): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(39,13): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(40,13): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/DataTable.tsx(41,15): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/PriceChart.tsx(7,5): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/PriceChart.tsx(8,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/PriceChart.tsx(9,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/PriceChart.tsx(10,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/PriceChart.tsx(11,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/Sidebar.tsx(5,5): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/Sidebar.tsx(6,7): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/Sidebar.tsx(7,9): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/Sidebar.tsx(10,9): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/StatBadge.tsx(8,5): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/ui/table.tsx(9,3): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/ui/table.tsx(10,5): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/ui/table.tsx(23,3): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/ui/table.tsx(31,3): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/ui/table.tsx(43,3): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/ui/table.tsx(58,3): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/ui/table.tsx(73,3): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/ui/table.tsx(88,3): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
components/ui/table.tsx(103,3): error TS17004: Cannot use JSX unless the '--jsx' flag is provided.
node_modules/next/dist/build/templates/app-page.d.ts(10,40): error TS2307: Cannot find module 'VAR_MODULE_GLOBAL_ERROR' or its corresponding type declarations.
node_modules/next/dist/build/webpack-config.d.ts(10,104): error TS2694: Namespace '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/next/dist/compiled/webpack/webpack".webpack' has no exported member 'RuleSetUseItem'.
node_modules/next/dist/build/webpack/loaders/next-app-loader.d.ts(1,13): error TS2613: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/next/dist/compiled/webpack/webpack"' has no default export. Did you mean to use 'import { webpack } from "/home/runner/work/AWA-App/AWA-App/webapp/node_modules/next/dist/compiled/webpack/webpack"' instead?
node_modules/next/dist/build/webpack/plugins/define-env-plugin.d.ts(74,86): error TS2694: Namespace '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/next/dist/compiled/webpack/webpack".webpack' has no exported member 'DefinePlugin'.
node_modules/next/dist/client/components/error-boundary.d.ts(2,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/client/components/layout-router.d.ts(3,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/client/components/not-found-boundary.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/client/components/static-generation-searchparams-bailout-provider.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/client/link.d.ts(2,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/client/with-router.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/server/app-render/entry-base.d.ts(1,85): error TS2307: Cannot find module 'react-server-dom-webpack/server.edge' or its corresponding type declarations.
node_modules/next/dist/server/render.d.ts(16,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/shared/lib/amp-context.shared-runtime.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/shared/lib/app-router-context.shared-runtime.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/shared/lib/head-manager-context.shared-runtime.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/shared/lib/image-config-context.shared-runtime.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/shared/lib/loadable-context.shared-runtime.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/shared/lib/loadable.shared-runtime.d.ts(21,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/shared/lib/router-context.shared-runtime.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/shared/lib/server-inserted-html.shared-runtime.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/next/dist/shared/lib/utils.d.ts(12,13): error TS1192: Module '"fs"' has no default export.
node_modules/next/types/index.d.ts(4,23): error TS2688: Cannot find type definition file for 'react-dom'.
node_modules/next/types/index.d.ts(5,23): error TS2688: Cannot find type definition file for 'react-dom/experimental'.
node_modules/next/types/index.d.ts(10,13): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/Area.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/Bar.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/Brush.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/CartesianAxis.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/CartesianGrid.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/ErrorBar.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/Line.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/ReferenceArea.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/ReferenceDot.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/ReferenceLine.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/cartesian/Scatter.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/chart/Sankey.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/chart/SunburstChart.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/chart/Treemap.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/chart/generateCategoricalChart.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/component/Customized.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/component/DefaultLegendContent.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/component/DefaultTooltipContent.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/component/Label.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/component/LabelList.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/component/Legend.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/component/ResponsiveContainer.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/component/Text.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/component/Tooltip.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/container/Layer.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/container/Surface.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/numberAxis/Funnel.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/polar/Pie.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/polar/PolarAngleAxis.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/polar/PolarGrid.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/polar/PolarRadiusAxis.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/polar/Radar.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/polar/RadialBar.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/shape/Cross.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/shape/Polygon.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/shape/Rectangle.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/shape/Sector.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/shape/Symbols.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/shape/Trapezoid.d.ts(4,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
node_modules/recharts/types/util/BarUtils.d.ts(1,8): error TS1259: Module '"/home/runner/work/AWA-App/AWA-App/webapp/node_modules/@types/react/index"' can only be default-imported using the 'esModuleInterop' flag
tsconfig.json(2,14): error TS6053: File 'next/tsconfig.json' not found.
```
