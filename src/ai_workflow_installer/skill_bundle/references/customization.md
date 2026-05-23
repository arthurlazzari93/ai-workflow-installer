# Customization Reference

Use this reference after the base installer runs.

## What Must Be Project-Specific

- `AI_CONTEXT.md`: product, stack, commands, sensitive areas, anti-patterns.
- `FEATURE_STATUS.md`: real ready/partial/stub map.
- `docs/context/*.md`: area-specific rules and conventions.
- `docs/context/frontend.md`: real component libraries, reusable UI patterns, tokens, design system, Storybook/docs, and frontend validation commands.
- For external design systems, record the official GitHub link/package, version/branch/tag, public/private status, `gh` access requirements, and fallback snapshot location if agents cannot consume the source directly.
- `TECH_DEBT.md` and `docs/debt/*`: real debt, impact, context, trigger.
- `PROJECT_MEMORY.md` and `docs/decisions/*`: real ADR IDs and architecture decisions.

The installer now seeds these files from existing Markdown when available. Keep useful synthesized lines, remove stale lines, and replace `A confirmar` with verified facts after human review.

## What Should Stay Mostly Generic

- `docs/ia/MATRIZ_DE_RISCO.md`
- `docs/ia/TRIAGEM_E_INTAKE.md`
- `docs/ia/ORQUESTRACAO_DE_AGENTES.md`
- `docs/ia/PAPEIS_DOS_AGENTES.md`
- `docs/ia/POLITICA_DE_MODELOS.md`
- `docs/ia/FLUXOS.md`
- `docs/ia/DEFINICAO_DE_PRONTO.md`
- `docs/ia/DESCOBERTA_E_PLANEJAMENTO.md`
- `docs/ia/PADROES_FRONTEND.md`
- `docs/ia/VALIDACAO_VISUAL_E_RUNTIME.md`
- `docs/ia/PESQUISA_E_REFERENCIAS.md`
- `docs/ia/PADROES_SEGURANCA.md`
- `docs/ia/SINCRONIA_DE_CONTEXTO.md`
- `docs/ia/CUSTO_E_APROVACAO.md`
- `docs/ia/EVIDENCIAS_E_VALIDACAO.md`
- `docs/ia/PADROES_DE_FALHA.md`

## Migration Rules

- If `CLAUDE.md` duplicates `AGENTS.md`, keep `AGENTS.md` canonical and turn `CLAUDE.md` into a bridge.
- If `PROJECT_MEMORY.md` is long, archive it and replace it with an index to ADRs.
- If `TECH_DEBT.md` is long, archive it and replace it with an index to `docs/debt/`.
- Preserve all IDs and historical references when possible.
- Do not overwrite project-specific knowledge without an archive.

## Quality Checks

- `AGENTS.md` should be below roughly 180 lines.
- `AI_CONTEXT.md` should be below roughly 200 lines.
- `CLAUDE.md` should not duplicate protocol rules.
- Vague improvement requests should produce discovery questions, implementation options, and explicit human approval before code changes.
- Frontend work should reuse existing components, tokens, layouts, hooks, and visual patterns before creating new UI.
- If an external design system cannot be accessed, the agent should tell the human what failed and suggest one or two ways to consume it: run `gh auth login`, grant GitHub access, install the package, attach/export a snapshot, or copy minimal tokens/components into the repo.
- Agents must not ask for GitHub tokens or credentials in chat; authentication must happen through `gh`, secret manager, or another approved secure flow.
- Triage/intake should classify risk, specialists, questions and expected evidence before implementation.
- Real subagents should only be used when the tool supports them, the human authorizes when needed, and write scopes do not conflict.
- Visual UI changes should use runtime/browser validation when feasible, with explicit fallback when the environment cannot run.
- Context docs should be checked against code/configs when they are stale, generic or contradicted by the repo.
- Security/privacy work should follow the practical baseline for auth, authorization, PII, secrets, external APIs, uploads and dependencies.
- Delivery summaries should include validation evidence or an explicit reason validation could not run.
- Any real or potential cost must have explicit human approval before implementation.
- Every bug escape should create a durable barrier: test, checklist, gate, debt entry, or failure pattern.
