# Discovery Reference

The installer detects the install mode and performs a read-only repo scan before generating docs unless `--no-discover` is passed.
It also synthesizes existing Markdown context before archive/update, so projects with prior memory or docs can seed the new files automatically.

## Install Mode Detection

- `fresh`: no AI workflow docs or project markers detected.
- `existing-project onboarding`: project markers exist, but no AI workflow docs were found.
- `update`: this kit is already installed and should be refreshed.
- `migration`: old/custom AI docs such as `AGENTS.md`, `CLAUDE.md`, `PROJECT_MEMORY.md`, `TECH_DEBT.md`, `GEMINI.md`, Cursor/Windsurf/Copilot instructions, or `docs/ia/` were found.

In `update` and `migration`, existing AI docs are archived and refreshed by default. Use `--no-auto-force` to only create missing files.

## Detect

- Manifests: `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`, `composer.json`, `Gemfile`.
- Package manager: `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `bun.lock*`.
- Frameworks/libs: common frontend, backend, DB/ORM, validation, auth, queue, and infra dependencies.
- Frontend reuse points: shared `components/`, `ui/`, `styles/`, `theme/`, `tokens/`, Storybook, design-system docs, icon sets, and shared hooks.
- Commands: install, dev, build, test, lint, typecheck, format.
- Structure: `apps/`, `packages/`, `src/`, `infra/`, `docs/`, `.github/`.
- Tests: `test/`, `tests/`, `__tests__/`, `*.test.*`, `*.spec.*`, Go/Python test naming.
- Infra: Dockerfiles, Compose files, `infra/`, `.github/workflows`.
- DB/migrations: `migrations/`, `drizzle/`, `prisma/`.
- Env/secrets: `.env.example`, `env.example`.
- Frontend reuse: component directories, UI libraries, theme/tokens/style folders, Storybook, and Tailwind/component configs.
- Existing docs: README and `docs/**`.
- Existing Markdown context: README, AI docs, context docs, ADRs, debt docs, changelog, feature status and other project Markdown.

## Output

The discovery report can be printed or saved:

```bash
python scripts/install_ai_workflow.py /path/to/repo --discovery-report
python scripts/install_ai_workflow.py /path/to/repo --discovery-report docs/ia/DISCOVERY_REPORT.md
```

Use the report to review generated context and replace `A confirmar` entries with verified facts.
Review the automatic Markdown synthesis: it preserves source paths and should be treated as useful signal, not absolute truth.
For frontend projects, use the frontend reuse section to confirm which components and visual tokens agents should reuse first.
If the project uses an external design system, add its GitHub URL/package/version, branch/tag, public/private status, `gh` access notes and fallback snapshot path to `docs/context/frontend.md`.
Confirm the dev server/runtime command for visual validation and add it to `docs/context/frontend.md` when discoverable.
For security-sensitive projects, review `docs/context/seguranca.md` and `docs/ia/PADROES_SEGURANCA.md` to confirm auth, PII, secrets, external API, upload and dependency assumptions.
For every project, confirm `docs/ia/TRIAGEM_E_INTAKE.md`, `docs/ia/SINCRONIA_DE_CONTEXTO.md`, `docs/ia/VALIDACAO_VISUAL_E_RUNTIME.md` and `docs/ia/EVIDENCIAS_E_VALIDACAO.md` match the team's desired rigor.
