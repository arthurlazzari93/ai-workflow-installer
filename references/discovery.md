# Discovery Reference

The installer performs a read-only repo scan before generating docs unless `--no-discover` is passed.

## Detect

- Manifests: `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`, `composer.json`, `Gemfile`.
- Package manager: `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `bun.lock*`.
- Frameworks/libs: common frontend, backend, DB/ORM, validation, auth, queue, and infra dependencies.
- Commands: install, dev, build, test, lint, typecheck, format.
- Structure: `apps/`, `packages/`, `src/`, `infra/`, `docs/`, `.github/`.
- Tests: `test/`, `tests/`, `__tests__/`, `*.test.*`, `*.spec.*`, Go/Python test naming.
- Infra: Dockerfiles, Compose files, `infra/`, `.github/workflows`.
- DB/migrations: `migrations/`, `drizzle/`, `prisma/`.
- Env/secrets: `.env.example`, `env.example`.
- Existing docs: README and `docs/**`.

## Output

The discovery report can be printed or saved:

```bash
python scripts/install_ai_workflow.py /path/to/repo --discovery-report
python scripts/install_ai_workflow.py /path/to/repo --discovery-report docs/ia/DISCOVERY_REPORT.md
```

Use the report to review generated context and replace `A confirmar` entries with verified facts.
