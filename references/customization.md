# Customization Reference

Use this reference after the base installer runs.

## What Must Be Project-Specific

- `AI_CONTEXT.md`: product, stack, commands, sensitive areas, anti-patterns.
- `FEATURE_STATUS.md`: real ready/partial/stub map.
- `docs/context/*.md`: area-specific rules and conventions.
- `docs/context/frontend.md`: real component libraries, reusable UI patterns, tokens, design system, Storybook/docs, and frontend validation commands.
- `TECH_DEBT.md` and `docs/debt/*`: real debt, impact, context, trigger.
- `PROJECT_MEMORY.md` and `docs/decisions/*`: real ADR IDs and architecture decisions.

## What Should Stay Mostly Generic

- `docs/ia/MATRIZ_DE_RISCO.md`
- `docs/ia/PAPEIS_DOS_AGENTES.md`
- `docs/ia/POLITICA_DE_MODELOS.md`
- `docs/ia/FLUXOS.md`
- `docs/ia/DEFINICAO_DE_PRONTO.md`
- `docs/ia/DESCOBERTA_E_PLANEJAMENTO.md`
- `docs/ia/PADROES_FRONTEND.md`
- `docs/ia/PESQUISA_E_REFERENCIAS.md`
- `docs/ia/CUSTO_E_APROVACAO.md`
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
- Any real or potential cost must have explicit human approval before implementation.
- Every bug escape should create a durable barrier: test, checklist, gate, debt entry, or failure pattern.
