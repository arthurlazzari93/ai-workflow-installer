---
name: ai-workflow-installer
description: Install or update a reusable AI-agent workflow documentation kit in software repositories. Use when Codex needs to bootstrap AGENTS.md, AI_CONTEXT.md, FEATURE_STATUS.md, TECH_DEBT.md, docs/ia workflows, risk matrix, agent roles, discovery/planning for vague requests, frontend premium standards, UI component reuse, research/reference workflows, cost approval gates, definition of done, failure patterns, ADR/debt structure, or migrate an existing repo to a more reliable AI-assisted development process.
---

# AI Workflow Installer

Use this skill to install or update a reusable AI-assisted development workflow in a repository, including existing projects that have no `AGENTS.md`, `CLAUDE.md`, or organized AI context yet.

## Workflow

1. Inspect the target repo first:
   - root docs: `AGENTS.md`, `CLAUDE.md`, `AI_CONTEXT.md`, `PROJECT_MEMORY.md`, `TECH_DEBT.md`, `README.md`
   - existing `docs/`, `apps/`, `packages/`, `src/`, `infra/`, `.github/`
   - frontend/component areas such as `components/`, `ui/`, `styles/`, `theme/`, `tokens/`, design system docs, Storybook, and shared hooks
   - package manager and formatter commands
2. Let the installer detect the install mode automatically:
   - **fresh**: repo has no AI workflow docs
   - **update**: repo already has this kit and needs refresh
   - **migration**: repo has long `PROJECT_MEMORY.md`, `TECH_DEBT.md`, `CLAUDE.md`, or custom agent docs that must be archived and indexed
   - **existing-project onboarding**: repo is already in progress but has no AI instructions; collect a short user brief, inspect the repo, then generate initial context from both sources
3. For existing-project onboarding, collect only the minimum brief before installing:
   - what the project is
   - who uses it
   - current goal
   - sensitive areas
   - what must not break
   - known pains
4. Prefer running `scripts/install_ai_workflow.py <target-repo>` for deterministic file creation.
5. Customize generated placeholders:
   - fill `AI_CONTEXT.md` with the actual stack, commands, and sensitive areas
   - fill `FEATURE_STATUS.md` with real ready/partial/stub status
   - fill `docs/context/frontend.md` with real component libraries, tokens, UI conventions, and reusable patterns
   - review `docs/ia/DESCOBERTA_E_PLANEJAMENTO.md`, `docs/ia/PADROES_FRONTEND.md`, `docs/ia/PESQUISA_E_REFERENCIAS.md`, and `docs/ia/CUSTO_E_APROVACAO.md` against project needs
   - keep `AGENTS.md` short and route details to `docs/ia/`
6. Preserve existing user/project knowledge:
   - archive long docs before replacing them
   - keep compatibility indexes at old root paths
   - do not delete decisions, debts, or project-specific process rules
7. Validate:
   - run formatter/check command if discoverable
   - confirm `AGENTS.md` stays short
   - confirm `CLAUDE.md` is a compatibility bridge, not a duplicate protocol
   - confirm vague improvement requests require discovery/planning and human approval before implementation
   - confirm frontend rules require component/token/pattern reuse before new UI
   - confirm cost-bearing work requires explicit human approval before implementation

## Installer Script

Run:

```bash
python scripts/install_ai_workflow.py /path/to/repo
```

Useful flags:

```bash
python scripts/install_ai_workflow.py /path/to/repo --force
python scripts/install_ai_workflow.py /path/to/repo --project-name "Meu Produto"
python scripts/install_ai_workflow.py /path/to/repo --interactive
python scripts/install_ai_workflow.py /path/to/repo --brief-file brief.md
python scripts/install_ai_workflow.py /path/to/repo --discovery-report report.md
python scripts/install_ai_workflow.py /path/to/repo --no-discover
python scripts/install_ai_workflow.py /path/to/repo --no-archive
python scripts/install_ai_workflow.py /path/to/repo --no-auto-force
```

Install mode detection and discovery are enabled by default. In update/migration mode, existing AI workflow docs are archived and refreshed automatically unless `--no-auto-force` is passed. Generated docs use PT-BR by default and mark information sources:

- `Fonte: brief` for user-provided context
- `Fonte: repo` for repository inspection
- `Fonte: detecção automática` for install mode
- `A confirmar` for inference or missing information

The script creates:

- `AGENTS.md`
- `CLAUDE.md`
- `AI_CONTEXT.md`
- `FEATURE_STATUS.md`
- `TECH_DEBT.md`
- `CHANGELOG.md`
- `PROJECT_MEMORY.md`
- `docs/ia/*`, including discovery/planning for vague requests, frontend standards, research/reference workflow, and cost approval gate
- `docs/context/*`
- `docs/decisions/README.md`
- `docs/debt/README.md`

## Customization Reference

Read `references/customization.md` when adapting the generated kit to a specific stack or when migrating existing long-form memory/debt documents.

Read `references/intake.md` for the standard brief and `references/discovery.md` for the repository discovery checklist.
