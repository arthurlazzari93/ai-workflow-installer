---
name: ai-workflow-installer
description: Install or update a reusable AI-agent workflow documentation kit in software repositories. Use when Codex needs to bootstrap AGENTS.md, AI_CONTEXT.md, FEATURE_STATUS.md, TECH_DEBT.md, docs/ia workflows, risk matrix, agent roles, definition of done, failure patterns, ADR/debt structure, or migrate an existing repo to a more reliable AI-assisted development process.
---

# AI Workflow Installer

Use this skill to install or update a reusable AI-assisted development workflow in a repository, including existing projects that have no `AGENTS.md`, `CLAUDE.md`, or organized AI context yet.

## Workflow

1. Inspect the target repo first:
   - root docs: `AGENTS.md`, `CLAUDE.md`, `AI_CONTEXT.md`, `PROJECT_MEMORY.md`, `TECH_DEBT.md`, `README.md`
   - existing `docs/`, `apps/`, `packages/`, `src/`, `infra/`, `.github/`
   - package manager and formatter commands
2. Choose an install mode:
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
   - keep `AGENTS.md` short and route details to `docs/ia/`
6. Preserve existing user/project knowledge:
   - archive long docs before replacing them
   - keep compatibility indexes at old root paths
   - do not delete decisions, debts, or project-specific process rules
7. Validate:
   - run formatter/check command if discoverable
   - confirm `AGENTS.md` stays short
   - confirm `CLAUDE.md` is a compatibility bridge, not a duplicate protocol

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
```

Discovery is enabled by default. Generated docs use PT-BR by default and mark information sources:

- `Fonte: brief` for user-provided context
- `Fonte: repo` for repository inspection
- `A confirmar` for inference or missing information

The script creates:

- `AGENTS.md`
- `CLAUDE.md`
- `AI_CONTEXT.md`
- `FEATURE_STATUS.md`
- `TECH_DEBT.md`
- `CHANGELOG.md`
- `PROJECT_MEMORY.md`
- `docs/ia/*`
- `docs/context/*`
- `docs/decisions/README.md`
- `docs/debt/README.md`

## Customization Reference

Read `references/customization.md` when adapting the generated kit to a specific stack or when migrating existing long-form memory/debt documents.

Read `references/intake.md` for the standard brief and `references/discovery.md` for the repository discovery checklist.
