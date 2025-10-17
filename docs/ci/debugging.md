# CI Debugging Guide

The CI pipeline now publishes the same diagnostics in three places so you can quickly triage failures without rerunning jobs.

## Artifacts

Each job uploads a `debug-bundle-<stage>-<run_id>-<attempt>.tar.gz` artifact. After downloading it you will find:

- `system.txt` containing sanitized environment variables, Git status, Docker diagnostics, and the workflow commit SHA.
- `compose-ps.txt` / `compose-logs.txt` snapshots captured at bundle time whenever Docker Compose is available.
- Test logs such as `unit.log`, `integ.log`, `vitest.log`, `tsc.log`, `eslint.log`, and `docker-build.log`.
- Alembic context in `migrations/alembic.txt` showing the current head and the last 20 entries.
- Optional files such as `preview-url.txt` if the preview stack exposed an external URL.

All commands that generate logs stream through `tee`, so the bundle always contains the latest output even when a step fails.

## PR Digest Comment

On repository pull requests the `mirror_logs` job updates a single comment marked with `<!-- AWA-CI-DIGEST -->`. The comment highlights:

- The short SHA that was tested.
- The preview URL for the stack (or `n/a` when tunnels are not configured).
- The mirror path inside the repository (`mirror-logs/pr-<number>/latest` for PRs, or `mirror-logs/branch-<name>/latest` for pushes).
- A compact list of the first detected errors across unit, integration, Compose, Docker build, and frontend logs.
- Collapsible tails for the same log set so you can see recent output without leaving the PR.

Log excerpts are sanitized to remove secrets and credentials before posting.

## Preview Environment

When the repository defines the `CLOUDFLARE_TUNNEL_TOKEN` and `CLOUDFLARE_TUNNEL_HOSTNAME` secrets the preview job publishes an external tunnel URL. The address is written to both the job summary and `preview-url.txt`, which is then surfaced in the digest comment and mirrored logs. Without these secrets the job still boots the stack locally and records readiness but lists the preview URL as `n/a`.

## Repository Mirror (`ci-logs` branch)

The same sanitized logs are pushed into the `ci-logs` branch so the most recent run is available without downloading artifacts. Paths follow the format:

- Pull requests: `mirror-logs/pr-<number>/sha-<shortsha>/...` with a `mirror-logs/pr-<number>/latest` copy.
- `main` pushes: `mirror-logs/branch-main/sha-<shortsha>/...` with a corresponding `latest` directory.

Each mirror commit includes `[skip ci]` to avoid triggering workflows from the mirrored branch. If there are no log changes the branch is left untouched.

## Fork Behaviour

When a pull request originates from a fork the workflow still uploads artifacts but intentionally skips the mirror push and the PR digest comment because forks do not have the required permissions. The job summary explicitly notes when this happens.

