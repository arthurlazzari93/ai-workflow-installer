# Intake Reference

Use this brief before installing the workflow in an existing project without AI instructions.

Ask only what materially improves the initial context. Keep it short; the repo inspection will fill discoverable facts.

## Standard Brief

```md
## O que é o projeto

## Quem usa

## Objetivo atual

## Áreas sensíveis

## O que não pode quebrar

## Dores conhecidas
```

## CLI Options

Interactive:

```bash
python scripts/install_ai_workflow.py /path/to/repo --interactive
```

Brief file:

```bash
python scripts/install_ai_workflow.py /path/to/repo --brief-file brief.md
python scripts/install_ai_workflow.py /path/to/repo --brief-file brief.json
```

## Source Policy

- User answers become `Fonte: brief`.
- Repo inspection becomes `Fonte: repo`.
- Anything inferred or missing must be marked `A confirmar`.
