# AWA Documentation

The AWA App monorepo bundles the operational agents, services, and supporting runbooks that keep the wholesale automation stack running. This site centralizes the most requested workflows so you can jump straight to the diagram, agent, or troubleshooting guide you need.

## Start here
- [Architecture Blueprint](blueprint.md) — systems diagram plus service map.
- [Agents](agents.md) — container list, run modes, and log-driven debugging contract.
- [Testing](TESTING.md) — unit vs. integration responsibilities and how CI enforces them.
- [Dry-run Specification](dry_run.md) — shared contract for reversible runs.
- [Local HTTPS](local_https.md) — mkcert workflow for trusted certificates.
- [CI Debug](CI_debug.md) — mirror-log recipe for reproducing pipeline failures.
- [LLM Microservice](llm_microservice.md) — FastAPI wrapper shipped with the repo.

## Working with the docs
The site is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). Run `pip install mkdocs mkdocs-material` once, then use:

```bash
mkdocs serve     # local preview with live reload
mkdocs build     # validates links during CI
```

All markdown files live under `docs/`. Keep new content close to the relevant section and add a link in the navigation so teammates can discover it quickly.
