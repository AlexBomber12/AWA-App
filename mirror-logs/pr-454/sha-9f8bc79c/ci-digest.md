<!-- AWA-CI-DIGEST -->
## CI digest for `9f8bc79c`

- **Preview URL**: n/a
- **Mirror path**: ci-logs/mirror-logs/pr-454/latest
- **Workflow run**: [18825119046](https://github.com/AlexBomber12/AWA-App/actions/runs/18825119046)

| Job | Conclusion | URL |
| --- | ---------- | --- |
| unit | ❌ Failure | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18825119046/job/53706526386) |
| migrations | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18825119046/job/53706578976) |
| integration | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18825119046/job/53706579052) |
| preview | ⚪ Skipped | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18825119046/job/53706579084) |
| mirror_logs | ⏳ In Progress | [Logs](https://github.com/AlexBomber12/AWA-App/actions/runs/18825119046/job/53706578987) |

### Failed tails

**unit** (`unit-alembic.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic current
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-logs.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml logs --no-color
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
```

**unit** (`unit-compose-ps.txt`)

```
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml ps
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:54Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
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
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
env file /home/runner/work/AWA-App/AWA-App/.env.postgres not found: stat /home/runner/work/AWA-App/AWA-App/.env.postgres: no such file or directory
exit_code=1
$ docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml run --rm api alembic history -20
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_USER\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PASSWORD\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_DATABASE\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_HOST\" variable is not set. Defaulting to a blank string."
time="2025-10-26T23:13:55Z" level=warning msg="The \"PG_PORT\" variable is not set. Defaulting to a blank string."
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
GITHUB_ENV=/home/runner/work/_temp/_runner_file_commands/set_env_6ea87555-e2e7-4490-9621-f89d987734f1
GITHUB_EVENT_NAME=pull_request
GITHUB_EVENT_PATH=/home/runner/work/_temp/_github_workflow/event.json
GITHUB_GRAPHQL_URL=https://api.github.com/graphql
GITHUB_HEAD_REF=pr-104-linters-quality-gate
GITHUB_JOB=unit
GITHUB_OUTPUT=/home/runner/work/_temp/_runner_file_commands/set_output_6ea87555-e2e7-4490-9621-f89d987734f1
GITHUB_PATH=/home/runner/work/_temp/_runner_file_commands/add_path_6ea87555-e2e7-4490-9621-f89d987734f1
GITHUB_REF=refs/pull/454/merge
GITHUB_REF_NAME=454/merge
GITHUB_REF_PROTECTED=false
GITHUB_REF_TYPE=branch
GITHUB_REPOSITORY=AlexBomber12/AWA-App
GITHUB_REPOSITORY_ID=1011502908
GITHUB_REPOSITORY_OWNER=AlexBomber12
GITHUB_REPOSITORY_OWNER_ID=48256657
GITHUB_RETENTION_DAYS=90
GITHUB_RUN_ATTEMPT=1
GITHUB_RUN_ID=18825119046
GITHUB_RUN_NUMBER=1226
GITHUB_SERVER_URL=https://github.com
GITHUB_SHA=9f8bc79c084c206a1e2c6225b685230f1e69ae19
GITHUB_STATE=/home/runner/work/_temp/_runner_file_commands/save_state_6ea87555-e2e7-4490-9621-f89d987734f1
GITHUB_STEP_SUMMARY=/home/runner/work/_temp/_runner_file_commands/step_summary_6ea87555-e2e7-4490-9621-f89d987734f1
GITHUB_TRIGGERING_ACTOR=AlexBomber12
GITHUB_WORKFLOW=ci
GITHUB_WORKFLOW_REF=AlexBomber12/AWA-App/.github/workflows/ci.yml@refs/pull/454/merge
GITHUB_WORKFLOW_SHA=9f8bc79c084c206a1e2c6225b685230f1e69ae19
GITHUB_WORKSPACE=/home/runner/work/AWA-App/AWA-App
GOROOT_1_22_X64=/opt/hostedtoolcache/go/1.22.12/x64
GOROOT_1_23_X64=/opt/hostedtoolcache/go/1.23.12/x64
GOROOT_1_24_X64=/opt/hostedtoolcache/go/1.24.7/x64
GRADLE_HOME=/usr/share/gradle-9.1.0
HOME=/home/runner
HOMEBREW_CLEANUP_PERIODIC_FULL_DAYS=3650
HOMEBREW_NO_AUTO_UPDATE=1
INVOCATION_ID=b7d804ab152d4914a8edf688f9f81c7a
ImageOS=ubuntu24
ImageVersion=20250929.60.1
JAVA_HOME=/usr/lib/jvm/temurin-17-jdk-amd64
JAVA_HOME_11_X64=/usr/lib/jvm/temurin-11-jdk-amd64
JAVA_HOME_17_X64=/usr/lib/jvm/temurin-17-jdk-amd64
JAVA_HOME_21_X64=/usr/lib/jvm/temurin-21-jdk-amd64
JAVA_HOME_25_X64=/usr/lib/jvm/temurin-25-jdk-amd64
JAVA_HOME_8_X64=/usr/lib/jvm/temurin-8-jdk-amd64
JOURNAL_STREAM=9:12475
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
RUNNER_NAME=GitHub Actions 1000008456
RUNNER_OS=Linux
RUNNER_TEMP=/home/runner/work/_temp
RUNNER_TOOL_CACHE=/opt/hostedtoolcache
RUNNER_TRACKING_ID=github_07074e7e-95a9-4974-a34b-df0c54ddf6a4
RUNNER_WORKSPACE=/home/runner/work/AWA-App
SELENIUM_JAR_PATH=/usr/share/java/selenium-server.jar
SGX_AESM_ADDR=1
SHELL=/bin/bash
SHLVL=2
SWIFT_PATH=/usr/share/swift/usr/bin
SYSTEMD_EXEC_PID=1884
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
