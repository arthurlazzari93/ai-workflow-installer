#!/usr/bin/env python3
"""Install a reusable AI workflow documentation kit into a repository."""

from __future__ import annotations

import argparse
import json
import shutil
import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".expo",
    ".venv",
    "venv",
    "target",
    "coverage",
    "__pycache__",
}

BRIEF_FIELDS = {
    "project": "O que é o projeto",
    "users": "Quem usa",
    "current_goal": "Objetivo atual",
    "sensitive_areas": "Áreas sensíveis",
    "must_not_break": "O que não pode quebrar",
    "known_pains": "Dores conhecidas",
}


@dataclass
class Discovery:
    root: Path
    project_name: str
    package_manager: str | None = None
    languages: set[str] = field(default_factory=set)
    frameworks: set[str] = field(default_factory=set)
    commands: dict[str, str] = field(default_factory=dict)
    top_level_dirs: list[str] = field(default_factory=list)
    manifests: list[str] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)
    ci: list[str] = field(default_factory=list)
    docker: list[str] = field(default_factory=list)
    env_examples: list[str] = field(default_factory=list)
    migrations: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    sensitive_hints: set[str] = field(default_factory=set)
    readme_excerpt: str | None = None


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def walk_files(root: Path, max_files: int = 5000) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if len(files) >= max_files:
            break
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def read_text(path: Path, limit: int = 8000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def detect_package_manager(root: Path) -> str | None:
    lockfiles = [
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("package-lock.json", "npm"),
        ("bun.lockb", "bun"),
        ("bun.lock", "bun"),
    ]
    for filename, manager in lockfiles:
        if (root / filename).exists():
            return manager
    return None


def add_package_json_discovery(path: Path, root: Path, discovery: Discovery) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    discovery.languages.add("JavaScript/TypeScript")
    discovery.manifests.append(rel(path, root))
    scripts = data.get("scripts", {})
    if isinstance(scripts, dict):
        manager = discovery.package_manager or "npm"
        for name in ["install", "dev", "build", "test", "lint", "typecheck", "format", "format:check"]:
            if name == "install":
                discovery.commands.setdefault("install", f"{manager} install")
            elif name in scripts:
                discovery.commands[name] = f"{manager} run {name}"

    deps: dict[str, Any] = {}
    for key in ["dependencies", "devDependencies", "peerDependencies"]:
        value = data.get(key)
        if isinstance(value, dict):
            deps.update(value)

    framework_map = {
        "next": "Next.js",
        "react": "React",
        "react-native": "React Native",
        "expo": "Expo",
        "vue": "Vue",
        "nuxt": "Nuxt",
        "svelte": "Svelte",
        "@sveltejs/kit": "SvelteKit",
        "vite": "Vite",
        "hono": "Hono",
        "express": "Express",
        "fastify": "Fastify",
        "@nestjs/core": "NestJS",
        "drizzle-orm": "Drizzle",
        "prisma": "Prisma",
        "typeorm": "TypeORM",
        "sequelize": "Sequelize",
        "zod": "Zod",
        "typescript": "TypeScript",
    }
    for dep, label in framework_map.items():
        if dep in deps:
            discovery.frameworks.add(label)

    sensitive_deps = {
        "better-auth": "auth",
        "next-auth": "auth",
        "@auth/core": "auth",
        "stripe": "pagamento",
        "mercadopago": "pagamento",
        "aws-sdk": "cloud/secrets",
        "@aws-sdk/client-s3": "cloud/secrets",
        "bullmq": "workers/fila",
        "ioredis": "Redis",
        "pg": "Postgres",
        "postgres": "Postgres",
    }
    for dep, hint in sensitive_deps.items():
        if dep in deps:
            discovery.sensitive_hints.add(hint)


def add_pyproject_discovery(path: Path, root: Path, discovery: Discovery) -> None:
    discovery.languages.add("Python")
    discovery.manifests.append(rel(path, root))
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        data = {}
    project = data.get("project", {}) if isinstance(data, dict) else {}
    deps = project.get("dependencies", []) if isinstance(project, dict) else []
    text = "\n".join(str(dep).lower() for dep in deps) + "\n" + read_text(path).lower()
    if "django" in text:
        discovery.frameworks.add("Django")
    if "fastapi" in text:
        discovery.frameworks.add("FastAPI")
    if "flask" in text:
        discovery.frameworks.add("Flask")
    if "pytest" in text:
        discovery.commands.setdefault("test", "pytest")
        discovery.tests.append(rel(path, root))
    if "ruff" in text:
        discovery.commands.setdefault("lint", "ruff check .")


def discover_repo(root: Path, project_name: str) -> Discovery:
    discovery = Discovery(root=root, project_name=project_name)
    discovery.package_manager = detect_package_manager(root)
    discovery.top_level_dirs = sorted([path.name for path in root.iterdir() if path.is_dir() and path.name not in SKIP_DIRS])

    readme = next((root / name for name in ["README.md", "README.rst", "README.txt"] if (root / name).exists()), None)
    if readme:
        discovery.docs.append(rel(readme, root))
        lines = [line.strip() for line in read_text(readme, 3000).splitlines() if line.strip()]
        discovery.readme_excerpt = " ".join(lines[:4])[:700] if lines else None

    files = walk_files(root)
    for path in files:
        relative = rel(path, root)
        name = path.name
        lower = relative.lower()

        if name == "package.json":
            add_package_json_discovery(path, root, discovery)
        elif name == "pyproject.toml":
            add_pyproject_discovery(path, root, discovery)
        elif name == "requirements.txt":
            discovery.languages.add("Python")
            discovery.manifests.append(relative)
        elif name == "go.mod":
            discovery.languages.add("Go")
            discovery.manifests.append(relative)
            discovery.commands.setdefault("test", "go test ./...")
        elif name == "Cargo.toml":
            discovery.languages.add("Rust")
            discovery.manifests.append(relative)
            discovery.commands.setdefault("test", "cargo test")
        elif name in {"composer.json"}:
            discovery.languages.add("PHP")
            discovery.manifests.append(relative)
        elif name in {"Gemfile"}:
            discovery.languages.add("Ruby")
            discovery.manifests.append(relative)

        if ".github/workflows/" in lower:
            discovery.ci.append(relative)
        if name in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"} or lower.startswith("docker/") or lower.startswith("infra/"):
            discovery.docker.append(relative)
            discovery.sensitive_hints.add("infra/deploy")
        if name.endswith(".env.example") or name in {".env.example", "env.example"}:
            discovery.env_examples.append(relative)
            discovery.sensitive_hints.add("secrets/env")
        if "migration" in lower or "migrations/" in lower or "drizzle/" in lower or "prisma/" in lower:
            discovery.migrations.append(relative)
            discovery.sensitive_hints.add("DB/migrations")
        if any(part in {"test", "tests", "__tests__"} for part in path.parts) or name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx", "_test.go", "_test.py")):
            discovery.tests.append(relative)
        if lower.startswith("docs/") and relative not in discovery.docs:
            discovery.docs.append(relative)

    if discovery.ci:
        discovery.sensitive_hints.add("CI/CD")
    if discovery.env_examples:
        discovery.sensitive_hints.add("secrets")
    if "Drizzle" in discovery.frameworks or "Prisma" in discovery.frameworks:
        discovery.sensitive_hints.add("DB/schema")
    if {"Next.js", "React", "Vue", "Svelte", "Expo", "React Native"} & discovery.frameworks:
        discovery.sensitive_hints.add("frontend/UI")
    if {"Hono", "Express", "Fastify", "NestJS", "Django", "FastAPI", "Flask"} & discovery.frameworks:
        discovery.sensitive_hints.add("API/backend")

    discovery.docs = sorted(set(discovery.docs))[:40]
    discovery.ci = sorted(set(discovery.ci))[:30]
    discovery.docker = sorted(set(discovery.docker))[:30]
    discovery.env_examples = sorted(set(discovery.env_examples))[:20]
    discovery.migrations = sorted(set(discovery.migrations))[:30]
    discovery.tests = sorted(set(discovery.tests))[:30]
    discovery.manifests = sorted(set(discovery.manifests))
    return discovery


def parse_brief_file(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        return {str(key): str(value).strip() for key, value in data.items() if str(value).strip()}

    brief: dict[str, str] = {}
    aliases = {
        "projeto": "project",
        "o que é o projeto": "project",
        "produto": "project",
        "quem usa": "users",
        "usuarios": "users",
        "usuários": "users",
        "objetivo atual": "current_goal",
        "objetivo": "current_goal",
        "áreas sensíveis": "sensitive_areas",
        "areas sensiveis": "sensitive_areas",
        "o que não pode quebrar": "must_not_break",
        "o que nao pode quebrar": "must_not_break",
        "dores conhecidas": "known_pains",
        "dores": "known_pains",
    }
    current: str | None = None
    buffer: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        heading = line.lstrip("#").strip().lower() if line.startswith("#") else ""
        key = aliases.get(heading)
        if key:
            if current and buffer:
                brief[current] = "\n".join(buffer).strip()
            current = key
            buffer = []
            continue
        if ":" in line and not current:
            left, right = line.split(":", 1)
            key = aliases.get(left.strip().lower())
            if key and right.strip():
                brief[key] = right.strip()
            continue
        if current:
            buffer.append(raw_line)
    if current and buffer:
        brief[current] = "\n".join(buffer).strip()
    if not brief and text.strip():
        brief["project"] = text.strip()
    return brief


def ask_interactive() -> dict[str, str]:
    print("Brief inicial do projeto. Deixe em branco se não souber.")
    brief: dict[str, str] = {}
    for key, prompt in BRIEF_FIELDS.items():
        value = input(f"{prompt}: ").strip()
        if value:
            brief[key] = value
    return brief


def bullet(values: list[str] | set[str], empty: str = "A confirmar.") -> str:
    items = sorted(values) if isinstance(values, set) else values
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def brief_value(brief: dict[str, str], key: str, fallback: str = "A confirmar.") -> str:
    value = brief.get(key, "").strip()
    return value if value else fallback


def command_lines(discovery: Discovery | None) -> list[str]:
    if not discovery or not discovery.commands:
        return ["- A confirmar: comandos canônicos do projeto."]
    return [f"- `{cmd}` — Fonte: repo" for _, cmd in sorted(discovery.commands.items())]


def stack_lines(discovery: Discovery | None) -> list[str]:
    if not discovery:
        return ["- A confirmar: stack não investigada (`--no-discover`)."]
    lines: list[str] = []
    if discovery.languages:
        lines.append(f"- Linguagens: {', '.join(sorted(discovery.languages))}. Fonte: repo.")
    if discovery.frameworks:
        lines.append(f"- Frameworks/libs detectados: {', '.join(sorted(discovery.frameworks))}. Fonte: repo.")
    if discovery.package_manager:
        lines.append(f"- Package manager: `{discovery.package_manager}`. Fonte: repo.")
    if discovery.manifests:
        lines.append(f"- Manifests: {', '.join(discovery.manifests[:8])}. Fonte: repo.")
    return lines or ["- A confirmar: stack não detectada automaticamente."]


def render_agents(project_name: str) -> str:
    return f"""# AGENTS.md

Fonte canônica do método de trabalho com IA em **{project_name}**.

## Leitura Inicial

1. Leia `AI_CONTEXT.md` sempre.
2. Leia `FEATURE_STATUS.md` quando a tarefa tocar produto, UI, API ou comportamento existente.
3. Leia `TECH_DEBT.md` quando houver risco de stub, simplificação, bug conhecido ou decisão de adiar algo.
4. Leia contexto específico em `docs/context/` conforme a área afetada.
5. Leia ADRs em `docs/decisions/` somente quando a tarefa tocar uma decisão arquitetural.

Se `AI_CONTEXT.md`, `FEATURE_STATUS.md` ou `TECH_DEBT.md` não existirem, pare e avise.

## Orquestração

Todo trabalho começa por triagem do Orquestrador:

- objetivo e critérios de aceite;
- risco: baixo, médio, alto ou emergência;
- áreas afetadas;
- especialistas necessários;
- confiança da classificação;
- verificações obrigatórias.

O Orquestrador roteia o trabalho; ele não implementa.

## Matriz De Risco

Use `docs/ia/MATRIZ_DE_RISCO.md` como fonte detalhada.

- Baixo: copy, docs simples, ajuste visual isolado, bug local claro.
- Médio: lógica pequena, endpoint simples, tela nova, refactor entre poucos arquivos.
- Alto: auth, permissão, privacidade/legal, pagamento, DB/schema, workers, infra, CI/CD, secrets, dependência nova ou arquivos de processo.
- Emergência: produção quebrada, vazamento, cobrança duplicada, login/API fora ou erro 500 em massa.

## Gates Obrigatórios

- Auth/sessão/permissão: Segurança/Privacidade + Testador.
- DB/schema/migration/query crítica: Arquiteto + DB + Testador.
- Dados pessoais/privacidade/legal: Produto + Segurança/Privacidade.
- Pagamento: Produto + Segurança/Privacidade + Release.
- Docker/CI/CD/deploy/env/secrets: Infra/SRE + Release.
- Dependência nova: Arquiteto + Segurança quando runtime ou supply chain forem afetados.
- `AGENTS.md`, `CLAUDE.md`, `docs/ia/*`, workflows ou scripts de build: Checkpoint de Processo + revisão humana.

## Política De Modelos

Quando a ferramenta permitir escolher modelo, use o modelo mais inteligente disponível, independentemente de custo, latência ou simplicidade da tarefa.

- OpenAI/Codex: preferir GPT-5.5 com maior reasoning disponível, preferencialmente `xhigh`.
- Claude: preferir Opus mais avançado disponível com contexto máximo, preferencialmente Max/1M.
- Se houver fallback, registre modelo pretendido, modelo usado e motivo.

## Definition Of Done

Antes de finalizar:

- critérios de aceite conferidos;
- diff sem mudança fora de escopo;
- verificações relevantes rodadas, ou motivo registrado;
- estados loading/empty/error considerados em UI;
- validação/auth/audit considerados em API sensível;
- ADR, `FEATURE_STATUS.md`, `TECH_DEBT.md` ou `CHANGELOG.md` atualizados quando houver decisão, status, débito ou entrega relevante.
"""


def render_ai_context(project_name: str, brief: dict[str, str], discovery: Discovery | None) -> str:
    product_source = "Fonte: brief." if brief.get("project") else "A confirmar."
    users_source = "Fonte: brief." if brief.get("users") else "A confirmar."
    readme_line = ""
    if discovery and discovery.readme_excerpt and not brief.get("project"):
        readme_line = f"\n\nResumo inferido do README: {discovery.readme_excerpt}\n\nA confirmar: validar se o resumo acima descreve corretamente o produto."

    sensitive: set[str] = set()
    if discovery:
        sensitive.update(discovery.sensitive_hints)
    if brief.get("sensitive_areas"):
        sensitive.add(f"{brief['sensitive_areas']} (Fonte: brief)")

    anti_patterns = [
        "Duplicar protocolo entre `AGENTS.md` e `CLAUDE.md`.",
        "Sobrescrever conhecimento existente sem archive.",
    ]
    if discovery and discovery.migrations:
        anti_patterns.append("Alterar schema/migrations sem plano e validação.")
    if discovery and discovery.env_examples:
        anti_patterns.append("Comitar secrets ou arquivos `.env` reais.")

    return f"""# AI_CONTEXT.md

Contexto curto e sempre lido do projeto **{project_name}**.

## Produto

{brief_value(brief, "project")} {product_source}{readme_line}

## Usuários

{brief_value(brief, "users")} {users_source}

## Objetivo Atual

{brief_value(brief, "current_goal")} {"Fonte: brief." if brief.get("current_goal") else "A confirmar."}

## Stack Atual

{chr(10).join(stack_lines(discovery))}

## Documentos Vivos

- `AGENTS.md`: entrypoint do método de trabalho com IA.
- `FEATURE_STATUS.md`: o que está pronto, parcial, stubado ou pendente.
- `TECH_DEBT.md`: índice de débitos por área.
- `PROJECT_MEMORY.md`: índice de ADRs e decisões históricas.
- `docs/ia/`: matriz de risco, papéis, fluxos, DoD, modelos e falhas aprendidas.
- `docs/context/`: contexto curto por área.
- `docs/decisions/`: ADRs por tema.
- `docs/debt/`: débitos detalhados por área.

## Comandos Canônicos

{chr(10).join(command_lines(discovery))}

## Áreas Sensíveis

{bullet(sensitive)}

## O Que Não Pode Quebrar

{brief_value(brief, "must_not_break")} {"Fonte: brief." if brief.get("must_not_break") else "A confirmar."}

## Anti-Patterns Iniciais

{bullet(anti_patterns)}
"""


def render_feature_status(brief: dict[str, str], discovery: Discovery | None) -> str:
    confirmed: list[str] = []
    inferred: list[str] = []
    confirm: list[str] = []

    if discovery:
        if discovery.top_level_dirs:
            confirmed.append(f"Estrutura detectada: {', '.join(discovery.top_level_dirs[:12])}. Fonte: repo.")
        if discovery.commands:
            confirmed.append(f"Comandos detectados: {', '.join(f'`{cmd}`' for cmd in discovery.commands.values())}. Fonte: repo.")
        if discovery.tests:
            confirmed.append("Há estrutura/arquivos de teste detectados. Fonte: repo.")
        if discovery.ci:
            confirmed.append("Há CI/CD em `.github/workflows`. Fonte: repo.")
        if discovery.docker:
            confirmed.append("Há Docker/infra detectado. Fonte: repo.")
        if discovery.frameworks:
            inferred.append(f"Capacidades associadas à stack: {', '.join(sorted(discovery.frameworks))}. Fonte: repo; A confirmar escopo real.")
    else:
        confirm.append("Stack e estrutura do repo não foram investigadas porque `--no-discover` foi usado.")

    if brief.get("known_pains"):
        confirm.append(f"Dores conhecidas informadas: {brief['known_pains']}. Fonte: brief.")
    confirm.append("Listar manualmente features prontas, parciais, stubadas e bloqueadas após primeira revisão humana.")

    return f"""# FEATURE_STATUS.md

Mapa operacional do que existe, o que está parcial e o que ainda é stub.

## Confirmado

{bullet(confirmed)}

## Inferido

{bullet(inferred)}

## A Confirmar

{bullet(confirm)}
"""


def render_project_memory() -> str:
    return """# PROJECT_MEMORY.md

Índice de compatibilidade das decisões arquiteturais.

## Onde Registrar

- Decisão arquitetural nova: criar/atualizar ADR em `docs/decisions/`.
- Entrega ou PR concluído: registrar em `CHANGELOG.md`.
- Estado pronto/parcial/stub: atualizar `FEATURE_STATUS.md`.
- Débito ou simplificação consciente: atualizar `TECH_DEBT.md` e `docs/debt/`.

## ADRs

- [docs/decisions/README.md](docs/decisions/README.md)
"""


def render_tech_debt() -> str:
    return """# TECH_DEBT.md

Índice curto dos débitos técnicos. Entradas detalhadas vivem em `docs/debt/`.

## Como Usar

- Novo débito entra no arquivo por área em `docs/debt/`.
- Débito resolvido vai para `docs/debt/resolvidos.md`.
- Bug escapado que indicar falha de processo também entra em `docs/ia/PADROES_DE_FALHA.md`.

## Áreas

- [Produto e integrações](docs/debt/produto-integracoes.md)
- [Segurança e privacidade](docs/debt/seguranca.md)
- [Infra e observabilidade](docs/debt/infra-observabilidade.md)
- [Backend e DB](docs/debt/backend-db.md)
- [Frontend e UX](docs/debt/frontend-ux.md)
- [Qualidade e testes](docs/debt/qualidade-testes.md)
- [Resolvidos](docs/debt/resolvidos.md)
"""


def render_changelog() -> str:
    return """# CHANGELOG.md

Histórico resumido de entregas. Decisões arquiteturais ficam em `docs/decisions/`; status atual fica em `FEATURE_STATUS.md`.

## Não Lançado

- A confirmar.
"""


DOCS_IA = {
    "README.md": """# IA Workflow

Esta pasta guarda o método de trabalho com agentes de IA. `AGENTS.md` continua sendo o entrypoint.

## Ordem De Leitura

1. `AI_CONTEXT.md`
2. `MATRIZ_DE_RISCO.md`
3. `PAPEIS_DOS_AGENTES.md`
4. `FLUXOS.md`
5. `DEFINICAO_DE_PRONTO.md`
6. `PADROES_DE_FALHA.md`

O processo deve acionar especialistas por risco e área afetada, não por ritual fixo.
""",
    "MATRIZ_DE_RISCO.md": """# Matriz De Risco

## Baixo

Copy, docs simples, ajuste visual isolado, typo, refactor local sem mudança de comportamento.

Fluxo: Orquestrador -> Dev da área -> Revisor rápido.

## Médio

Lógica pequena, contrato interno, endpoint simples, tela nova simples, hook compartilhado, service pequeno.

Fluxo: Orquestrador -> Leitor -> Arquiteto se houver trade-off -> Dev da área -> Testador -> Revisor.

## Alto

Auth, permissão, privacidade/legal, dados pessoais, pagamento, DB/schema, migrations, workers, deploy, CI/CD, secrets, dependências ou arquivos de processo.

Fluxo: Orquestrador -> Checkpoint de Orquestração -> especialistas obrigatórios -> Dev -> Testador -> Revisor -> Release quando aplicável.

## Emergência

Produção quebrada, vazamento, cobrança duplicada, login/API fora ou erro 500 em massa.

Fluxo: Orquestrador -> Leitor -> Dev -> Revisor -> Testador. Depois do hotfix, registrar débito residual e padrão de falha.
""",
    "PAPEIS_DOS_AGENTES.md": """# Papéis Dos Agentes

- Orquestrador: classifica risco, escolhe especialistas, define critérios de aceite, não implementa.
- Leitor: mapeia código existente e padrões locais.
- Produto/PM: valida valor, escopo, experiência, copy, consentimento e trade-offs.
- Arquiteto: escolhe abordagem quando há trade-off técnico ou impacto entre áreas.
- Dev Frontend/Mobile: implementa UI/client.
- Dev API: implementa rotas, services, validação, jobs e contratos.
- Dev DB: cuida de schema, migrations, índices, constraints, seed e ownership/RLS.
- Dev Infra/SRE: cuida de Docker, CI/CD, deploy, observabilidade, backups e healthchecks.
- Design QA: verifica fidelidade visual, responsividade, acessibilidade e overlap.
- Segurança/Privacidade: verifica auth, PII, secrets, autorização, logs e privacidade/legal.
- Testador: verifica golden path, edge e erro sem enfraquecer testes.
- Revisor Código: revisa diff, async, tipos, imports, edge cases e escopo.
- Documentação: atualiza contexto, ADRs, status, debt e changelog quando aplicável.
- Release Manager: gerencia PR, deploy, rollback e validação pós-deploy.
""",
    "POLITICA_DE_MODELOS.md": """# Política De Modelos

Preferir capacidade máxima a custo ou velocidade.

## OpenAI / Codex

- Preferir GPT-5.5.
- Usar o maior reasoning disponível, preferencialmente `xhigh`.

## Claude

- Preferir o Opus mais avançado disponível.
- Usar contexto máximo, preferencialmente Max/1M quando suportado.

## Fallback

Se o modelo extremo não estiver disponível, registrar modelo pretendido, modelo usado, motivo e risco residual.
""",
    "FLUXOS.md": """# Fluxos

## Bugfix Local

Orquestrador -> Leitor leve -> Dev da área -> Revisor -> verificação mínima.

## UI Relevante

Orquestrador -> Produto -> Design QA -> Dev Frontend/Mobile -> Testador -> Revisor.

## API

Orquestrador -> Leitor -> Dev API -> Testador -> Revisor. Incluir Arquiteto se contrato público mudar.

## DB Ou Schema

Orquestrador -> Arquiteto -> Dev DB -> Dev API se necessário -> Testador -> Revisor.

## Auth, Privacidade, Parceiro Ou Pagamento

Orquestrador -> Checkpoint -> Produto -> Arquiteto -> Segurança/Privacidade -> Devs necessários -> Testador -> Revisor -> Release quando aplicável.

## Infra, CI/CD Ou Deploy

Orquestrador -> Infra/SRE -> Release -> Testador smoke -> Revisor.
""",
    "DEFINICAO_DE_PRONTO.md": """# Definição De Pronto

## Toda Mudança

- Critérios de aceite conferidos.
- Sem mudança fora de escopo.
- Sem TODO/stub novo sem debt.
- Verificações relevantes rodadas, ou motivo registrado.
- Documentação viva atualizada somente quando houver decisão, status, débito ou entrega relevante.

## UI

- Estados loading, empty, error e populated considerados.
- Copy combina com idioma/tom do projeto.
- Sem violar tokens/design system quando houver.
- Sem overlap incoerente.

## API/DB

- Entrada validada.
- Business logic fora de handlers finos.
- Erros tipados quando aplicável.
- Golden path, edge e erro cobertos quando houver lógica nova.

## Segurança/Privacidade

- Endpoints sensíveis exigem auth.
- PII não vaza por logs, push payloads, respostas públicas ou screenshots.
- Secrets não entram em commit.
""",
    "PADROES_DE_FALHA.md": """# Padrões De Falha

Registre bugs escapados e a barreira durável que impede repetição.

## Template

```md
## FP-000 — Título curto

Detectado em:
- PR/tela/endpoint/data

Problema:
- O que estava errado ou faltando.

Por que passou:
- Critério, teste, agente, gate ou profundidade de review ausente.

Barreira nova:
- Teste, checklist, lint, gate, matriz de risco ou documentação.

Aplica a:
- Agentes/áreas afetadas.
```
""",
}


def context_docs(discovery: Discovery | None, brief: dict[str, str]) -> dict[str, str]:
    docs: dict[str, str] = {
        "produto.md": f"""# Contexto Produto

## Fonte: brief

- Projeto: {brief_value(brief, "project")}
- Quem usa: {brief_value(brief, "users")}
- Objetivo atual: {brief_value(brief, "current_goal")}
- Dores conhecidas: {brief_value(brief, "known_pains")}

## A Confirmar

- Jornada principal do usuário.
- Métricas de sucesso.
- Linguagem/tom padrão.
""",
        "seguranca.md": f"""# Contexto Segurança E Privacidade

## Fonte: brief

- Áreas sensíveis: {brief_value(brief, "sensitive_areas")}
- O que não pode quebrar: {brief_value(brief, "must_not_break")}

## Fonte: repo

{bullet(discovery.sensitive_hints if discovery else set())}

## A Confirmar

- Política de secrets.
- Dados pessoais ou regulados.
- Requisitos de auth/autorização.
""",
    }
    frameworks = discovery.frameworks if discovery else set()
    if not discovery or {"Next.js", "React", "Vue", "Svelte", "SvelteKit", "Expo", "React Native", "Vite"} & frameworks:
        docs["frontend.md"] = f"""# Contexto Frontend

## Fonte: repo

{bullet(sorted({"Next.js", "React", "Vue", "Svelte", "SvelteKit", "Expo", "React Native", "Vite"} & frameworks) if discovery else [])}

## A Confirmar

- Design system.
- Estados loading/empty/error.
- Acessibilidade e responsividade.
"""
    if not discovery or {"Hono", "Express", "Fastify", "NestJS", "Django", "FastAPI", "Flask"} & frameworks:
        docs["backend.md"] = f"""# Contexto Backend

## Fonte: repo

{bullet(sorted({"Hono", "Express", "Fastify", "NestJS", "Django", "FastAPI", "Flask"} & frameworks) if discovery else [])}

## A Confirmar

- Formato de erro.
- Validação de entrada.
- Boundaries entre handlers/controllers e services.
"""
    if not discovery or discovery.migrations or {"Drizzle", "Prisma", "TypeORM", "Sequelize"} & frameworks:
        docs["db.md"] = f"""# Contexto DB

## Fonte: repo

{bullet(discovery.migrations[:12] if discovery else [])}

## A Confirmar

- Source of truth do schema.
- Política de migrations/rollback.
- Seeds e dados de teste.
"""
    if not discovery or discovery.docker or discovery.ci:
        docs["infra.md"] = f"""# Contexto Infra

## Fonte: repo

### Docker/infra
{bullet(discovery.docker[:12] if discovery else [])}

### CI/CD
{bullet(discovery.ci[:12] if discovery else [])}

## A Confirmar

- Deploy target.
- Rollback.
- Observabilidade.
"""
    return docs


DEBT_DOCS = {
    "README.md": """# Debt

Débitos técnicos por área. `TECH_DEBT.md` na raiz é apenas o índice curto.

## Template

```md
### Título curto Impacto

**Identificado em:** data / PR / contexto
**Descrição:** o que foi adiado ou simplificado.
**Impacto:** alto, médio ou baixo.
**Contexto:** por que foi aceito agora.
**Gatilho:** evento objetivo que torna o débito prioridade.
```
""",
    "produto-integracoes.md": "# Produto E Integrações\n\n",
    "seguranca.md": "# Segurança E Privacidade\n\n",
    "infra-observabilidade.md": "# Infra E Observabilidade\n\n",
    "backend-db.md": "# Backend E DB\n\n",
    "frontend-ux.md": "# Frontend E UX\n\n",
    "qualidade-testes.md": "# Qualidade E Testes\n\n",
    "resolvidos.md": "# Resolvidos\n\n",
}


def decision_docs() -> dict[str, str]:
    return {
        "README.md": """# Decisions

ADRs por tema. Detalhes de entrega ficam em `CHANGELOG.md`; estado atual fica em `FEATURE_STATUS.md`.

## Template

```md
# ADR-0001 — Título

Status: accepted
Data: YYYY-MM-DD

## Contexto

## Decisão

## Consequências
```
"""
    }


def discovery_report(discovery: Discovery | None, brief: dict[str, str]) -> str:
    if not discovery:
        return "# Relatório De Descoberta\n\nDescoberta desativada por `--no-discover`.\n"
    brief_lines = [f"- {label}: {brief.get(key, 'A confirmar.')}" for key, label in BRIEF_FIELDS.items()]
    return f"""# Relatório De Descoberta

## Brief

{chr(10).join(brief_lines)}

## Estrutura

{bullet(discovery.top_level_dirs)}

## Stack

{chr(10).join(stack_lines(discovery))}

## Comandos

{chr(10).join(command_lines(discovery))}

## Docs Existentes

{bullet(discovery.docs[:20])}

## Testes

{bullet(discovery.tests[:20])}

## Infra / Docker

{bullet(discovery.docker[:20])}

## CI/CD

{bullet(discovery.ci[:20])}

## Env / Secrets

{bullet(discovery.env_examples[:20])}

## Migrations / DB

{bullet(discovery.migrations[:20])}

## Áreas Sensíveis Inferidas

{bullet(discovery.sensitive_hints)}
"""


def archive_existing(path: Path, archive_root: Path, repo_root: Path) -> None:
    if not path.exists():
        return
    archive_root.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    relative_name = path.relative_to(repo_root).as_posix().replace("/", "__")
    target = archive_root / f"{relative_name}.{stamp}"
    counter = 1
    while target.exists():
        target = archive_root / f"{relative_name}.{stamp}.{counter}"
        counter += 1
    shutil.copy2(path, target)


def write_file(
    path: Path,
    content: str,
    *,
    force: bool,
    archive: bool,
    archive_root: Path,
    repo_root: Path,
) -> str:
    if path.exists() and not force:
        return f"skip existing {path}"
    if path.exists() and archive:
        archive_existing(path, archive_root, repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return f"write {path}"


def install(
    target: Path,
    project_name: str,
    force: bool,
    archive: bool,
    brief: dict[str, str],
    discovery: Discovery | None,
) -> list[str]:
    target = target.resolve()
    archive_root = target / "docs" / "archive"
    actions: list[str] = []

    root_docs = {
        "AGENTS.md": render_agents(project_name),
        "CLAUDE.md": f"""# CLAUDE.md

A fonte canônica do método de trabalho deste repositório é [`AGENTS.md`](AGENTS.md).

Antes de trabalhar aqui, leia:

1. [`AGENTS.md`](AGENTS.md)
2. [`AI_CONTEXT.md`](AI_CONTEXT.md)
3. Os documentos indicados pelo Orquestrador em `docs/ia/` e `docs/context/`

Este arquivo existe apenas para compatibilidade com ferramentas que procuram `CLAUDE.md`. Não duplique regras aqui.
""",
        "AI_CONTEXT.md": render_ai_context(project_name, brief, discovery),
        "FEATURE_STATUS.md": render_feature_status(brief, discovery),
        "PROJECT_MEMORY.md": render_project_memory(),
        "TECH_DEBT.md": render_tech_debt(),
        "CHANGELOG.md": render_changelog(),
    }

    groups = [
        ("", root_docs),
        ("docs/ia", DOCS_IA),
        ("docs/context", context_docs(discovery, brief)),
        ("docs/decisions", decision_docs()),
        ("docs/debt", DEBT_DOCS),
    ]

    for prefix, files in groups:
        for relative, content in files.items():
            path = target / prefix / relative if prefix else target / relative
            actions.append(
                write_file(
                    path,
                    content,
                    force=force,
                    archive=archive,
                    archive_root=archive_root,
                    repo_root=target,
                )
            )
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Install AI workflow documentation kit.")
    parser.add_argument("target_repo", type=Path)
    parser.add_argument("--project-name", default=None)
    parser.add_argument("--force", action="store_true", help="Overwrite existing files after archiving them.")
    parser.add_argument("--no-archive", action="store_true", help="Do not archive overwritten files.")
    parser.add_argument("--interactive", action="store_true", help="Collect a short project brief in the terminal.")
    parser.add_argument("--brief-file", type=Path, help="Read project brief from a JSON or Markdown file.")
    parser.add_argument("--discover", dest="discover", action="store_true", default=True, help="Inspect repo files before generating docs. Enabled by default.")
    parser.add_argument("--no-discover", dest="discover", action="store_false", help="Skip repo discovery and generate generic docs.")
    parser.add_argument(
        "--discovery-report",
        nargs="?",
        const="-",
        help="Print discovery report to stdout when omitted or '-' is used, otherwise write it to this path.",
    )
    args = parser.parse_args()

    if not args.target_repo.exists() or not args.target_repo.is_dir():
        parser.error(f"target repo does not exist or is not a directory: {args.target_repo}")

    brief: dict[str, str] = {}
    if args.brief_file:
        brief.update(parse_brief_file(args.brief_file))
    if args.interactive:
        brief.update(ask_interactive())

    target = args.target_repo.resolve()
    project_name = args.project_name or brief.get("project") or target.name
    discovery = discover_repo(target, project_name) if args.discover else None

    report = discovery_report(discovery, brief)
    if args.discovery_report is not None:
        if args.discovery_report == "-":
            print(report)
        else:
            report_path = Path(args.discovery_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report, encoding="utf-8")

    actions = install(target, project_name, args.force, not args.no_archive, brief, discovery)
    for action in actions:
        print(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
