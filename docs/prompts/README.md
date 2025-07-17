# Prompt Scaffolding

This folder stores discussions that guided the AWA-App architecture.
To scaffold a new service:
1. Create a package under `services/` with `Dockerfile`, `requirements.txt` and tests.
2. List runtime dependencies in `requirements.txt` and any tooling in `requirements-dev.txt`.
3. Update CI so the new service builds and its tests run.
