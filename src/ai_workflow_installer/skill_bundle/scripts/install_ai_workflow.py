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

FRONTEND_REUSE_CANDIDATES = [
    "components",
    "src/components",
    "app/components",
    "components/ui",
    "src/components/ui",
    "ui",
    "src/ui",
    "shared/ui",
    "src/shared/ui",
    "hooks",
    "src/hooks",
    "styles",
    "src/styles",
    "theme",
    "src/theme",
    "tokens",
    "src/tokens",
    "design-system",
    "packages/ui",
    "packages/design-system",
    ".storybook",
    "storybook",
    "components.json",
    "tailwind.config.js",
    "tailwind.config.ts",
    "tailwind.config.mjs",
]

BRIEF_FIELDS = {
    "project": "O que é o projeto",
    "users": "Quem usa",
    "current_goal": "Objetivo atual",
    "sensitive_areas": "Áreas sensíveis",
    "must_not_break": "O que não pode quebrar",
    "known_pains": "Dores conhecidas",
}


@dataclass
class InstallMode:
    name: str
    label: str
    reason: str
    existing_docs: list[str] = field(default_factory=list)
    auto_refresh_existing: bool = False


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
    frontend_reuse: list[str] = field(default_factory=list)
    sensitive_hints: set[str] = field(default_factory=set)
    readme_excerpt: str | None = None


AI_DOC_PATHS = [
    "AGENTS.md",
    "CLAUDE.md",
    "AI_CONTEXT.md",
    "FEATURE_STATUS.md",
    "PROJECT_MEMORY.md",
    "TECH_DEBT.md",
    "docs/ia/README.md",
]

CUSTOM_AGENT_DOC_PATHS = [
    "GEMINI.md",
    ".cursorrules",
    ".windsurfrules",
    ".cursor/rules",
    ".github/copilot-instructions.md",
]

PROJECT_MARKER_PATHS = [
    "README.md",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "go.mod",
    "Cargo.toml",
    "composer.json",
    "Gemfile",
    "src",
    "app",
    "apps",
    "packages",
]

KIT_MARKERS = [
    "Fonte canônica do método de trabalho com IA",
    "docs/ia/PADROES_FRONTEND.md",
    "docs/ia/DESCOBERTA_E_PLANEJAMENTO.md",
]


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


def detect_install_mode(root: Path) -> InstallMode:
    existing_ai_docs = [path for path in AI_DOC_PATHS if (root / path).exists()]
    existing_custom_docs = [path for path in CUSTOM_AGENT_DOC_PATHS if (root / path).exists()]

    agents_text = read_text(root / "AGENTS.md", 12000) if (root / "AGENTS.md").exists() else ""
    has_docs_ia = (root / "docs" / "ia").exists()
    has_kit = bool(has_docs_ia and (root / "AI_CONTEXT.md").exists() and any(marker in agents_text for marker in KIT_MARKERS))
    has_project_files = any((root / path).exists() for path in PROJECT_MARKER_PATHS)

    existing_docs = sorted(set(existing_ai_docs + existing_custom_docs))

    if has_kit:
        return InstallMode(
            name="update",
            label="update",
            reason="Kit ai-workflow já detectado; atualizar workflow existente.",
            existing_docs=existing_docs,
            auto_refresh_existing=True,
        )
    if existing_docs:
        return InstallMode(
            name="migration",
            label="migration",
            reason="Documentos de IA/customizados detectados; arquivar e migrar para o kit.",
            existing_docs=existing_docs,
            auto_refresh_existing=True,
        )
    if has_project_files:
        return InstallMode(
            name="existing-project-onboarding",
            label="existing-project onboarding",
            reason="Projeto existente sem workflow de IA detectado; gerar contexto inicial.",
        )
    return InstallMode(
        name="fresh",
        label="fresh",
        reason="Nenhum workflow de IA ou estrutura de projeto detectada; instalar base limpa.",
    )


def install_mode_lines(install_mode: InstallMode) -> list[str]:
    lines = [
        f"- Modo: `{install_mode.label}`. Fonte: detecção automática.",
        f"- Motivo: {install_mode.reason}",
    ]
    if install_mode.existing_docs:
        lines.append(f"- Docs existentes detectados: {', '.join(install_mode.existing_docs[:12])}.")
    if install_mode.auto_refresh_existing:
        lines.append("- Ação padrão: arquivar docs existentes e atualizar o kit.")
    return lines


def add_frontend_reuse_hint(discovery: Discovery, relative: str) -> None:
    parts = relative.split("/")
    markers = {"components", "ui", "hooks", "styles", "theme", "tokens", ".storybook", "storybook"}
    frontend_suffixes = {".css", ".scss", ".sass", ".less", ".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte"}
    if Path(relative).suffix and Path(relative).suffix not in frontend_suffixes:
        return
    for index, part in enumerate(parts[:-1]):
        if part not in markers:
            continue
        end = index + 1
        if part == "components" and end < len(parts) - 1 and parts[end] == "ui":
            end += 1
        discovery.frontend_reuse.append("/".join(parts[:end]))
        return


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
    discovery.frontend_reuse = [
        candidate for candidate in FRONTEND_REUSE_CANDIDATES if (root / candidate).exists()
    ]

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
        add_frontend_reuse_hint(discovery, relative)

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
    discovery.frontend_reuse = sorted(set(discovery.frontend_reuse))[:30]
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
5. Leia `docs/ia/TRIAGEM_E_INTAKE.md` para classificar tarefa, risco, lacunas e evidências esperadas.
6. Para frontend/UI, leia `docs/ia/PADROES_FRONTEND.md` e `docs/context/frontend.md` antes de implementar.
7. Para pedido vago de melhoria, leia `docs/ia/DESCOBERTA_E_PLANEJAMENTO.md`, converse com o humano e aguarde aprovação antes de implementar.
8. Para pesquisa externa, API, scraping, dependência ou solução desconhecida, leia `docs/ia/PESQUISA_E_REFERENCIAS.md`.
9. Para segurança, privacidade, auth, dados sensíveis ou dependência externa, leia `docs/ia/PADROES_SEGURANCA.md`.
10. Quando a ferramenta suportar agentes/subagentes reais e o humano autorizar, leia `docs/ia/ORQUESTRACAO_DE_AGENTES.md`.
11. Para UI relevante, leia `docs/ia/VALIDACAO_VISUAL_E_RUNTIME.md` antes de finalizar.
12. Antes de confiar em contexto antigo, leia `docs/ia/SINCRONIA_DE_CONTEXTO.md`.
13. Para qualquer custo real ou potencial, leia `docs/ia/CUSTO_E_APROVACAO.md` e aguarde aprovação humana.
14. Para fechar trabalho, leia `docs/ia/EVIDENCIAS_E_VALIDACAO.md`.
15. Leia ADRs em `docs/decisions/` somente quando a tarefa tocar uma decisão arquitetural.

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
- Pedido vago de melhoria, UX, "deixar melhor" ou "modernizar": Agente De Descoberta antes de qualquer implementação.
- UI relevante, tela nova ou componente compartilhado: Produto + Curador De UI + Design QA + Testador.
- Ambiguidade visual, solução externa, API open source ou scraping: Agente de Pesquisa antes da implementação.
- Subagentes reais/paralelos: somente quando a ferramenta suportar, a tarefa puder ser dividida sem conflito e houver autorização humana explícita.
- Validação visual relevante: runtime/browser obrigatório quando viável; se ambiente não subir, registrar bloqueio e fallback.
- Contexto desatualizado ou contraditório: Sincronia de Contexto antes de decidir.
- Qualquer custo real ou potencial: Planejador De Custo + aprovação humana explícita.
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
- pedidos vagos transformados em plano aprovado antes de implementar;
- verificações relevantes rodadas, ou motivo registrado;
- evidências registradas para as afirmações de entrega;
- contexto consultado foi considerado atual ou a divergência foi registrada;
- validação visual/runtime feita em UI relevante, ou bloqueio/fallback registrado;
- estados loading/empty/error considerados em UI;
- reuso de componentes/tokens/padrões existentes considerado em UI;
- baseline de segurança verificado quando tocar auth, dados, secrets, API externa, upload ou dependência;
- custo real ou potencial aprovado pelo humano antes da implementação;
- validação/auth/audit considerados em API sensível;
- ADR, `FEATURE_STATUS.md`, `TECH_DEBT.md` ou `CHANGELOG.md` atualizados quando houver decisão, status, débito ou entrega relevante.
"""


def render_ai_context(
    project_name: str,
    brief: dict[str, str],
    discovery: Discovery | None,
    install_mode: InstallMode,
) -> str:
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

## Modo De Instalação

{chr(10).join(install_mode_lines(install_mode))}

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

## Frescor Do Contexto

- Gerado na instalação do workflow.
- Conferir contra código/configs antes de decisões relevantes.
- Se algo divergir, seguir `docs/ia/SINCRONIA_DE_CONTEXTO.md`.
"""


def render_feature_status(brief: dict[str, str], discovery: Discovery | None, install_mode: InstallMode) -> str:
    confirmed: list[str] = []
    inferred: list[str] = []
    confirm: list[str] = []

    if discovery:
        confirmed.append(f"Modo de instalação detectado: `{install_mode.label}`. Fonte: detecção automática.")
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
        if discovery.frontend_reuse:
            confirmed.append(f"Pontos de reuso frontend detectados: {', '.join(discovery.frontend_reuse[:8])}. Fonte: repo.")
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

## Frescor Do Status

- Revisar após mudança relevante de produto, UI, API, DB, infra ou fluxo.
- Não assumir que feature está pronta sem conferir código/teste/rota relacionada.
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
2. `TRIAGEM_E_INTAKE.md`
3. `MATRIZ_DE_RISCO.md`
4. `PAPEIS_DOS_AGENTES.md`
5. `FLUXOS.md`
6. `DESCOBERTA_E_PLANEJAMENTO.md` quando o pedido for vago ou subjetivo
7. `PADROES_FRONTEND.md` quando tocar UI/frontend
8. `PESQUISA_E_REFERENCIAS.md` quando houver ambiguidade, API, scraping, dependência ou solução externa
9. `PADROES_SEGURANCA.md` quando tocar auth, dados, secrets, dependências, APIs externas ou uploads
10. `ORQUESTRACAO_DE_AGENTES.md` quando houver subagentes reais, paralelismo ou delegação
11. `VALIDACAO_VISUAL_E_RUNTIME.md` quando tocar UI relevante
12. `SINCRONIA_DE_CONTEXTO.md` quando o contexto puder estar desatualizado
13. `CUSTO_E_APROVACAO.md` quando houver custo real ou potencial
14. `EVIDENCIAS_E_VALIDACAO.md`
15. `DEFINICAO_DE_PRONTO.md`
16. `PADROES_DE_FALHA.md`

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
Também é alto risco qualquer escolha que crie custo real ou potencial sem aprovação humana.

Fluxo: Orquestrador -> Checkpoint de Orquestração -> especialistas obrigatórios -> Dev -> Testador -> Revisor -> Release quando aplicável.

## Emergência

Produção quebrada, vazamento, cobrança duplicada, login/API fora ou erro 500 em massa.

Fluxo: Orquestrador -> Leitor -> Dev -> Revisor -> Testador. Depois do hotfix, registrar débito residual e padrão de falha.
""",
    "TRIAGEM_E_INTAKE.md": """# Triagem E Intake

Todo trabalho começa por triagem leve. O objetivo é sair do pedido bruto para um plano executável sem transformar descoberta em burocracia.

## Regra Central

- Descobrir no repositório tudo que puder ser descoberto lendo código, docs, rotas, testes e padrões existentes.
- Perguntar ao humano somente quando a resposta mudar escopo, risco, critério de aceite, custo, comportamento de produto ou decisão visual.
- Não implementar quando a tarefa estiver vaga, custosa ou arriscada demais para execução direta.

## Classificação Inicial

Antes de editar arquivos, registrar mentalmente ou no resumo de trabalho:

- tipo da tarefa: bugfix, UI, API, DB, infra, segurança, docs, pesquisa, planejamento ou processo;
- objetivo e critério de aceite;
- risco: baixo, médio, alto ou emergência;
- áreas e arquivos prováveis;
- especialistas obrigatórios;
- lacunas que precisam de pergunta humana;
- evidências esperadas para provar a entrega.

## Quando Perguntar

Pergunte quando faltar:

- resultado esperado ou critério de aceite;
- público, jornada ou prioridade de uma mudança de produto/UX;
- autorização para custo real ou potencial;
- decisão entre alternativas com trade-off real;
- permissão para mexer em área sensível;
- confirmação de comportamento que o código não revela.

Evite perguntar sobre stack, comandos, estrutura, padrões de componente, testes ou rotas quando isso puder ser lido no projeto.

## Roteamento

- Pedido vago ou subjetivo: acionar `DESCOBERTA_E_PLANEJAMENTO.md`.
- UI/frontend: acionar `PADROES_FRONTEND.md` e `docs/context/frontend.md`.
- UI relevante: acionar `VALIDACAO_VISUAL_E_RUNTIME.md` antes de finalizar.
- API externa, scraping, biblioteca ou problema desconhecido: acionar `PESQUISA_E_REFERENCIAS.md`.
- Auth, dados, secrets, upload, dependência ou integração externa: acionar `PADROES_SEGURANCA.md`.
- Contexto antigo, genérico ou divergente: acionar `SINCRONIA_DE_CONTEXTO.md`.
- Subagentes reais/paralelos: acionar `ORQUESTRACAO_DE_AGENTES.md` e pedir autorização quando necessário.
- Custo real ou potencial: acionar `CUSTO_E_APROVACAO.md` antes de implementar.
- Qualquer entrega relevante: fechar com `EVIDENCIAS_E_VALIDACAO.md`.

## Saída Esperada

Para tarefas simples, a triagem pode ficar implícita no plano curto do agente. Para tarefas médias/altas, devolver ou manter claro:

- entendimento do pedido;
- plano de execução;
- riscos e gates;
- perguntas indispensáveis;
- validações que serão feitas;
- ponto onde aprovação humana é necessária.
""",
    "PAPEIS_DOS_AGENTES.md": """# Papéis Dos Agentes

- Orquestrador: classifica tipo, risco, lacunas, especialistas, possibilidade de subagentes reais e evidências esperadas; não implementa.
- Leitor: mapeia código existente, contratos, comandos, testes e padrões locais.
- Agente De Descoberta: entra quando o pedido humano é vago, lê o produto/tela/código, conversa para clarificar intenção, aciona Pesquisa quando útil e retorna opções de implementação para aprovação.
- Produto/PM: valida valor, escopo, experiência, copy, consentimento e trade-offs.
- Agente de Pesquisa: busca referências visuais, docs oficiais, APIs open source, exemplos de mercado e soluções técnicas quando há ambiguidade ou dependência externa.
- Planejador De Custo: identifica custo real ou potencial, estima impacto, propõe alternativas gratuitas e bloqueia implementação até aprovação humana explícita.
- Arquiteto: escolhe abordagem quando há trade-off técnico ou impacto entre áreas.
- Curador De UI: mapeia componentes, telas parecidas, tokens, hooks, estilos e padrões reutilizáveis antes de nova UI.
- Dev Frontend/Mobile: implementa UI/client reaproveitando padrões existentes antes de criar novos.
- Dev API: implementa rotas, services, validação, jobs e contratos.
- Dev DB: cuida de schema, migrations, índices, constraints, seed e ownership/RLS.
- Dev Infra/SRE: cuida de Docker, CI/CD, deploy, observabilidade, backups e healthchecks.
- Design QA: verifica fidelidade visual, consistência com componentes existentes, responsividade, acessibilidade, estados e overlap.
- Segurança/Privacidade: aplica baseline de segurança para auth, autorização, PII, secrets, logs, dependências, APIs externas e privacidade/legal.
- Testador: verifica golden path, edge, erro, regressões relevantes, runtime visual quando aplicável e evidências de validação.
- Revisor Código: revisa diff, async, tipos, imports, edge cases, escopo, duplicação e aderência aos padrões.
- Documentação: atualiza contexto, ADRs, status, debt e changelog quando aplicável.
- Release Manager: gerencia PR, deploy, rollback e validação pós-deploy.
""",
    "ORQUESTRACAO_DE_AGENTES.md": """# Orquestração De Agentes

Esta skill define papéis lógicos. Ela não cria agentes reais sozinha em toda ferramenta. Quando a ferramenta suportar subagentes reais e o humano autorizar, o Orquestrador pode delegar trabalho paralelo com controle explícito.

## Regra Central

- Usar subagentes reais somente quando houver benefício claro de paralelismo, pesquisa independente, revisão isolada ou implementação em áreas sem conflito.
- Não delegar trabalho bloqueante se o próximo passo depende diretamente dele.
- Não criar subagentes quando a ferramenta, permissão ou política atual não permitir.
- Se subagente real não estiver disponível, executar os papéis em sequência no mesmo agente e registrar a limitação.

## Quando Pedir Autorização

Peça autorização humana antes de acionar subagentes reais quando:

- a ferramenta exigir permissão explícita;
- houver risco de edição paralela nos mesmos arquivos;
- o trabalho puder consumir recursos pagos;
- a delegação depender de acesso externo, GitHub privado, APIs ou credenciais;
- o resultado precisar ser integrado no mesmo diff.

## Divisão Segura

Delegue apenas tarefas com escopo claro:

- Pesquisa: fontes, APIs, referência visual, docs oficiais, benchmarking.
- Curadoria de UI: mapear componentes, tokens, telas parecidas e padrões locais.
- Design QA: revisar screenshots, responsividade, overlap, estados e consistência.
- Testes: rodar validações, investigar falhas, propor cobertura.
- Implementação: somente quando cada agente tiver arquivos/módulos próprios e não conflitantes.

## Brief Para Subagente

```md
Papel:

Objetivo:

Arquivos/áreas sob sua responsabilidade:

Arquivos que você não deve alterar:

Contexto mínimo:

Critérios de aceite:

Evidência esperada:

Ao finalizar, retorne:
- resumo;
- arquivos alterados ou analisados;
- validações;
- riscos e dúvidas.
```

## Fan-In

Antes de finalizar:

- integrar resultados sem sobrescrever trabalho de outro agente;
- revisar conflitos de escopo;
- confirmar evidências;
- registrar limitações quando algum papel foi executado sequencialmente por falta de subagente real.
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

## Todo Trabalho

Orquestrador -> Triagem e intake -> especialistas conforme risco -> implementação -> validação/evidências -> revisão.

Triagem deve identificar objetivo, critério de aceite, risco, áreas afetadas, gates, custo potencial e evidências esperadas. Se faltar informação que muda escopo ou aprovação, pare para perguntar.

Antes de confiar em contexto antigo, acionar `SINCRONIA_DE_CONTEXTO.md` quando houver divergência, `A confirmar`, docs genéricas ou mudança recente no repo.

## Subagentes Reais Quando Suportado

Orquestrador -> autorização humana quando necessária -> briefs independentes -> agentes/subagentes -> fan-in -> revisão integrada.

Usar `ORQUESTRACAO_DE_AGENTES.md`. Se a ferramenta não suportar subagentes reais, executar os papéis em sequência e registrar essa limitação.

## Bugfix Local

Orquestrador -> Leitor leve -> Dev da área -> Revisor -> verificação mínima.

## UI Relevante

Orquestrador -> Produto -> Agente de Pesquisa se houver ambiguidade visual ou referência externa -> Curador De UI -> contrato de UX -> Dev Frontend/Mobile -> Design QA -> Testador -> Revisor.

O contrato de UX deve registrar tarefa principal, público, padrão visual escolhido, componentes/tokens reutilizados, estados obrigatórios e evidência visual esperada.

Antes de finalizar UI relevante, executar `VALIDACAO_VISUAL_E_RUNTIME.md`: subir runtime quando viável, validar navegador/viewport/estados, ou registrar bloqueio e fallback.

## Pedido Vago De Melhoria

Orquestrador -> Agente De Descoberta -> Leitor/Curador De UI conforme área -> Agente de Pesquisa quando ajudar -> proposta com opções -> aprovação humana -> fluxo normal de implementação.

Exemplos: "melhorar UX", "deixar mais moderno", "melhorar tela principal", "melhorar performance", "organizar dashboard" sem critério claro.

Enquanto não houver plano aprovado, não implementar.

## Reuso De UI

Curador De UI -> Dev Frontend/Mobile. Antes de criar componente novo, mapear componentes, telas parecidas, tokens, estilos, hooks e estados existentes. Criar novo padrão só com justificativa.

## Pesquisa Externa, API Ou Scraping

Orquestrador -> Agente de Pesquisa -> Arquiteto/Produto conforme impacto -> Planejador De Custo se houver cobrança -> Dev da área.

## Custo Real Ou Potencial

Orquestrador -> Planejador De Custo -> aprovação humana explícita -> Dev da área. Sem aprovação, registrar alternativa gratuita ou bloquear a implementação.

## API

Orquestrador -> Leitor -> Dev API -> Testador -> Revisor. Incluir Arquiteto se contrato público mudar.

## Segurança Ou Privacidade

Orquestrador -> Segurança/Privacidade -> Arquiteto/Produto quando houver trade-off -> Dev da área -> Testador -> Revisor.

Aplicar baseline de `PADROES_SEGURANCA.md` sempre que tocar auth, autorização, dados pessoais, secrets, upload, webhook, API externa, dependência, logs ou cobrança.

## DB Ou Schema

Orquestrador -> Arquiteto -> Dev DB -> Dev API se necessário -> Testador -> Revisor.

## Auth, Privacidade, Parceiro Ou Pagamento

Orquestrador -> Checkpoint -> Produto -> Arquiteto -> Segurança/Privacidade -> Devs necessários -> Testador -> Revisor -> Release quando aplicável.

## Infra, CI/CD Ou Deploy

Orquestrador -> Infra/SRE -> Release -> Testador smoke -> Revisor.

## Fechamento Com Evidências

Antes de finalizar, o agente deve declarar o que mudou, quais validações foram feitas, quais evidências sustentam a entrega e qual risco residual permaneceu.
""",
    "DEFINICAO_DE_PRONTO.md": """# Definição De Pronto

## Toda Mudança

- Critérios de aceite conferidos.
- Triagem feita: tipo, risco, área, lacunas, gates e evidências esperadas.
- Pedido vago, subjetivo ou amplo foi clarificado e aprovado antes da implementação.
- Contexto vivo conferido quando havia `A confirmar`, divergência ou docs antigas.
- Subagentes reais, quando usados, tiveram brief, escopo de arquivos e fan-in registrados.
- Sem mudança fora de escopo.
- Sem TODO/stub novo sem debt.
- Verificações relevantes rodadas, ou motivo registrado.
- Evidências registradas para as afirmações principais da entrega.
- Documentação viva atualizada somente quando houver decisão, status, débito ou entrega relevante.

## UI

- Estados loading, empty, error e populated considerados.
- Componentes, telas parecidas, tokens, estilos e hooks existentes foram procurados antes de criar UI nova.
- Contrato de UX considerado: tarefa principal, público, padrão local, estados e restrições.
- Componente novo tem motivo claro: falta de equivalente, variação legítima ou abstração reutilizável.
- Copy combina com idioma/tom do projeto.
- Sem violar tokens/design system quando houver.
- Sem overlap incoerente.
- Evidência visual/runtime feita quando a mudança visual for relevante, ou bloqueio/fallback registrado.

## API/DB

- Entrada validada.
- Business logic fora de handlers finos.
- Erros tipados quando aplicável.
- Golden path, edge e erro cobertos quando houver lógica nova.

## Segurança/Privacidade

- Endpoints sensíveis exigem auth.
- Autorização checada no servidor, não apenas no cliente.
- PII não vaza por logs, push payloads, respostas públicas ou screenshots.
- Secrets não entram em commit.
- Dependências, APIs externas, uploads e integrações passam pelo baseline de `PADROES_SEGURANCA.md`.

## Custo

- Nenhuma API paga, SaaS, infra, scraping pago, modelo pago, storage, fila, observabilidade ou dependência com cobrança foi implementada sem aprovação humana explícita.
""",
    "DESCOBERTA_E_PLANEJAMENTO.md": """# Descoberta E Planejamento

Use este fluxo quando o pedido humano for vago, subjetivo ou amplo demais para implementação direta.

## Quando Acionar

- "Melhorar UX", "deixar mais bonito", "modernizar", "melhorar tela principal" ou pedido equivalente.
- Pedido sem tela, público, problema, métrica, prioridade ou critério de aceite claro.
- Mudança que pode virar redesign, refactor amplo, alteração de comportamento ou custo.
- Ideia visual difícil de explicar pelo usuário humano.

## Responsabilidade Do Agente De Descoberta

- Entrar em modo de planejamento/conversa antes de qualquer edição.
- Ler o que a tela, fluxo ou módulo faz hoje usando código, docs, rotas, screenshots ou contexto disponível.
- Explicar de forma curta o entendimento atual e as lacunas.
- Fazer poucas perguntas de alto impacto para transformar pedido genérico em objetivo implementável.
- Perguntar uma a três coisas por vez, priorizando respostas que mudam direção, risco, custo ou aceite.
- Evitar perguntar o que pode ser descoberto no repositório.
- Acionar Agente de Pesquisa quando referências, benchmark, padrão de UX ou solução técnica externa puderem ajudar.
- Acionar Curador De UI quando o assunto tocar frontend para mapear componentes e padrões existentes.
- Acionar Planejador De Custo se qualquer opção tiver custo real ou potencial.
- Retornar opções concretas de implementação e aguardar aprovação humana.

## Perguntas Boas

- Qual resultado concreto você quer que o usuário perceba?
- Quem usa essa tela e qual tarefa principal precisa ficar melhor?
- O problema é clareza, velocidade, confiança, conversão, estética, acessibilidade ou erro?
- Existe alguma referência visual ou produto que se aproxima do esperado?
- O que não pode mudar nesta tela ou fluxo?
- Qual opção você aprova implementar agora?

## Saída Esperada

Antes de implementar, devolver ao humano:

- entendimento da tela/fluxo atual;
- problema provável e tarefa principal do usuário;
- 2 ou 3 opções de melhoria, com impacto, esforço relativo e evidência necessária;
- riscos, dependências e custo quando houver;
- recomendação objetiva;
- pergunta final pedindo aprovação da opção escolhida.

## Formato Sugerido

```md
Entendimento:
- ...

Opções:
1. ...
2. ...
3. ...

Recomendação:
- ...

Preciso da sua aprovação para implementar a opção N.
```

## Regra De Bloqueio

Sem aprovação humana de uma opção concreta, o agente não implementa. Ele pode apenas pesquisar, ler o código, levantar alternativas e refinar o plano.
""",
    "PADROES_FRONTEND.md": """# Padrões Frontend

O objetivo é entregar UI premium sem fragmentar o produto. Reuso vem antes de criação.

## Antes De Implementar

- Entender objetivo, público, jornada, restrições e critérios de aceite.
- Acionar Agente De Descoberta se o pedido for vago, subjetivo ou amplo demais para implementação direta.
- Procurar telas parecidas, componentes compartilhados, design system, tokens, estilos, hooks e utilitários existentes.
- Identificar estados obrigatórios: loading, empty, error, populated, disabled e permissões quando aplicável.
- Acionar Agente de Pesquisa quando a intenção visual estiver ambígua, faltar referência ou houver padrão de mercado relevante.
- Acionar Planejador De Custo antes de usar asset, serviço, API, biblioteca ou ferramenta com cobrança real ou potencial.

## Design System Externo

Se o projeto declarar um design system oficial por link, pacote ou repositório:

- Tratar essa fonte como referência prioritária depois dos componentes locais já existentes no projeto.
- Consultar tokens, componentes, layouts, exemplos e regras de acessibilidade antes de criar UI nova.
- Registrar a versão, branch, tag, pacote ou data de consulta quando a decisão depender dessa fonte.
- Se a fonte ainda não estiver registrada, pedir ao humano: link do GitHub/repositório, branch/tag/versão, se é público ou privado, pacote oficial quando existir e prioridade entre design system externo e padrões locais.
- Quando o design system estiver no GitHub, validar acesso com `gh auth status` e leitura do repositório com `gh repo view ORG/REPO` ou comando equivalente.
- Se `gh` não estiver autenticado ou autorizado, não pedir token/credencial no chat. Orientar o humano a autenticar com `gh auth login`, liberar acesso ao repositório, instalar o pacote oficial, anexar um snapshot dos docs/tokens/componentes ou copiar um recorte mínimo para `docs/context/frontend.md`.
- Depois de acessar, registrar em `docs/context/frontend.md`: URL, branch/tag/versão, pacote, forma de consumo, prioridade, fallback e data de validação.
- Sem acesso ao design system externo, não inventar divergência visual; usar padrões locais detectados e marcar a lacuna como `A confirmar`.

## Contrato De UX

Antes de codar UI relevante, o agente deve ter clareza sobre:

- tarefa principal do usuário na tela;
- público e frequência de uso;
- problema que a mudança resolve: clareza, velocidade, confiança, conversão, estética, acessibilidade ou erro;
- tela, componente ou padrão local que será usado como referência;
- componentes, tokens, estilos, hooks e estados que serão reaproveitados;
- restrições: o que não pode mudar;
- evidência esperada: screenshot, validação no navegador, teste ou checklist.

Se algum item mudar a direção da implementação e não puder ser descoberto no projeto, volte para `DESCOBERTA_E_PLANEJAMENTO.md`.

## Reuso Obrigatório

- Preferir componente existente a componente novo.
- Preferir token/design system existente a valor visual manual.
- Preferir layout/padrão já usado em tela parecida a composição nova.
- Não duplicar botões, cards, inputs, modais, tabelas, badges, tabs, empty states, toasts ou feedback visual quando houver equivalente.
- Se a UI nova revelar padrão recorrente, sugerir extração para componente compartilhado.

## Quando Criar Componente Novo

Crie componente novo somente quando:

- não existe equivalente local;
- a variação é legítima e não cabe como prop/configuração limpa;
- a abstração será reutilizável em mais de um ponto;
- criar o componente reduz duplicação real sem esconder regra de negócio.

Registre no resumo da entrega o motivo da criação e onde o componente deve ser reutilizado.

## Qualidade Visual

- Seguir densidade, espaçamento, tipografia, bordas, sombras, ícones e linguagem visual já existentes.
- Evitar layouts decorativos quando o produto for ferramenta operacional; priorizar clareza, escaneabilidade e eficiência.
- Garantir que textos não estourem botões, cards, tabelas ou menus em mobile e desktop.
- Garantir ausência de overlap incoerente entre elementos.
- Usar assets reais ou imagens adequadas quando a tela depende de inspeção visual do produto, pessoa, lugar ou objeto.

## UX E Estados

- Toda tela interativa precisa ter estados loading, empty, error e sucesso quando aplicável.
- Ações destrutivas ou custosas exigem confirmação compatível com o risco.
- Erros devem orientar recuperação, não apenas mostrar falha genérica.
- Inputs precisam de label, validação, feedback e estado disabled quando necessário.

## Acessibilidade E Responsividade

- Navegação por teclado preservada em controles interativos.
- Contraste, foco visível, labels e aria quando necessário.
- Layout validado nos breakpoints relevantes do projeto.
- Elementos fixos, toolbars, grids e cards devem ter dimensões estáveis para evitar shift visual.

## Validação

- Seguir `VALIDACAO_VISUAL_E_RUNTIME.md` para mudança visual relevante.
- Validar no navegador quando houver mudança visual relevante.
- Conferir desktop e mobile quando a UI for responsiva.
- Testar golden path, estados loading/empty/error e pelo menos um erro realista.
- Registrar componentes/tokens reutilizados ou justificar componente novo.
- Revisor Código confirma que não houve duplicação desnecessária nem quebra de padrão visual.
""",
    "VALIDACAO_VISUAL_E_RUNTIME.md": """# Validação Visual E Runtime

Mudança visual relevante precisa ser validada no produto rodando quando isso for viável. Se o ambiente não subir, o agente não deve fingir validação: deve registrar o bloqueio e usar fallback proporcional.

## Antes De Validar

- Descobrir comando de dev/build/test em `AI_CONTEXT.md`, `package.json`, `pyproject.toml` ou docs do projeto.
- Verificar se dependências já estão instaladas.
- Não instalar dependências, subir serviço pago, criar infra ou consumir API paga sem aprovação humana quando houver custo real ou potencial.
- Identificar rota/tela, viewport desktop e mobile, estado de dados e login necessário.

## Fluxo Preferido

1. Rodar typecheck/lint/test relevante quando existir.
2. Subir servidor local com comando do projeto.
3. Abrir a rota no navegador.
4. Validar desktop e mobile quando responsivo.
5. Verificar console, loading, empty, error, disabled e populated quando aplicável.
6. Capturar evidência: screenshot, observação objetiva ou log de validação.

## Quando O Runtime Não Sobe

Registrar:

- comando tentado;
- erro principal;
- hipótese provável;
- se falta dependência, env, banco, seed, login, segredo, serviço externo ou porta;
- o que seria necessário para desbloquear;
- fallback usado.

Fallbacks aceitáveis:

- build/typecheck/lint/test;
- inspeção de componentes e estilos;
- Storybook ou preview isolado quando existir;
- screenshot de estado estático se a ferramenta permitir;
- checklist manual com risco residual explícito.

## Evidência Mínima Para UI

- Rota/tela validada.
- Viewports usadas.
- Estados verificados.
- Componentes/tokens reutilizados.
- Problemas visuais encontrados ou confirmação de ausência de overlap/texto estourado.
- Limitações de ambiente.
""",
    "PESQUISA_E_REFERENCIAS.md": """# Pesquisa E Referências

Use pesquisa para reduzir incerteza antes da implementação, não para justificar complexidade desnecessária.

## Quando Acionar

- Ideia visual difícil de descrever ou sem referência clara.
- Apoio ao Agente De Descoberta para transformar pedidos vagos em opções implementáveis.
- Necessidade de inspiração de mercado, benchmark ou padrão de UX.
- Web scraping, API open source, SDK, biblioteca ou integração externa.
- Problema técnico desconhecido ou erro que exige solução atualizada.
- Mudança dependente de documentação oficial ou comportamento recente.

## Como Pesquisar

- Priorizar documentação oficial, repositórios mantidos, exemplos do próprio projeto e fontes primárias.
- Verificar data, versão, licença, manutenção e sinais de abandono quando a decisão depender de fonte externa.
- Para frontend, coletar padrões concretos: layout, comportamento, estados, hierarquia visual e restrições.
- Para design system externo no GitHub ou pacote versionado, tentar consumir docs, tokens, componentes e exemplos antes de propor UI nova.
- Quando o design system estiver no GitHub, solicitar link/branch/tag/versão ao humano se isso ainda não estiver documentado e validar acesso com `gh auth status` e `gh repo view ORG/REPO` ou equivalente.
- Para API/scraping, verificar termos de uso, autenticação, rate limits, paginação, estabilidade e custo.
- Separar fato verificado de inferência.
- Registrar links, data de consulta quando relevante e recomendação objetiva.

## Fonte Externa Inacessível

Se o agente não conseguir acessar ou consumir uma fonte externa necessária, ele deve informar o humano com objetividade:

- qual fonte falhou;
- por que ela é necessária;
- o que foi tentado;
- uma ou duas formas de desbloquear, por exemplo autenticar com `gh auth login`, liberar permissão/acesso ao GitHub, instalar o pacote oficial, anexar um export/snapshot ou copiar os tokens/componentes mínimos para o repositório.

O agente não deve pedir token ou credencial no chat. Credenciais precisam passar por fluxo seguro da ferramenta, CLI, secret manager ou canal aprovado pelo projeto.

Enquanto a fonte estiver inacessível, o agente pode seguir apenas com padrões locais já verificados ou aguardar o desbloqueio quando a decisão depender da fonte.

## Entrega Para Frontend

O Agente de Pesquisa deve transformar ambiguidade em opções implementáveis:

- 2 ou 3 direções visuais concretas quando houver escolha de UX.
- referências de interação, não apenas estética;
- relação entre a referência externa e componentes/padrões já existentes no projeto;
- riscos de acessibilidade, responsividade ou performance;
- recomendação alinhada ao produto e aos componentes existentes.

Quando atuar junto com o Agente De Descoberta, entregar insumos curtos que ajudem o humano a escolher uma direção, não um relatório longo.

## Restrições

- Não adicionar dependência externa sem avaliar manutenção, licença, segurança e custo.
- Não usar scraping sem validar permissão, limites e impacto operacional.
- Não implementar caminho com custo real ou potencial antes do Planejador De Custo e aprovação humana.
""",
    "CUSTO_E_APROVACAO.md": """# Custo E Aprovação

Nada que gere custo real ou potencial pode ser implementado sem aprovação humana explícita.

## O Que Conta Como Custo

- API paga, plano SaaS, assinatura, marketplace ou serviço externo cobrado.
- Infra, deploy, storage, banco, fila, cache, logs, tracing, observabilidade ou CDN com cobrança.
- Modelos pagos, créditos, tokens, geração de mídia ou processamento por uso.
- Scraping pago, proxy, captcha solver, dados licenciados ou rate limit pago.
- Dependência que exige licença comercial ou cria custo operacional relevante.

## Responsabilidade Do Planejador De Custo

- Identificar custo direto, recorrente, por uso e custo oculto de manutenção.
- Estimar ordem de grandeza quando possível.
- Apontar alternativa gratuita ou já disponível no projeto.
- Registrar risco residual se a estimativa for incerta.
- Bloquear implementação até aprovação humana explícita.

## Aprovação Humana

A aprovação precisa citar o item aprovado e o limite conhecido, por exemplo:

```md
Aprovado usar API X para o fluxo Y, até o plano gratuito / até R$ N por mês / apenas em ambiente de teste.
```

Silêncio, aprovação genérica ou plano gratuito sem limite claro não contam como aprovação para custo real. Sem aprovação, o agente deve propor alternativa sem custo ou parar a implementação.
""",
    "SINCRONIA_DE_CONTEXTO.md": """# Sincronia De Contexto

Contexto desatualizado gera decisão ruim. Antes de confiar em docs antigas, o agente deve checar se o repositório confirma o que está escrito.

## Regra Central

- Código, testes, configs e manifests atuais têm prioridade sobre contexto antigo.
- Docs de contexto orientam, mas não substituem inspeção do repo quando a tarefa toca comportamento real.
- Se houver divergência entre docs e código, registrar a divergência e usar o código como fonte operacional até o humano confirmar.

## Quando Acionar

- `AI_CONTEXT.md`, `FEATURE_STATUS.md`, `TECH_DEBT.md` ou `docs/context/*` parecem genéricos, antigos ou contraditórios.
- A tarefa toca área marcada como `A confirmar`.
- O repo mudou desde a última atualização de contexto.
- O agente encontra stub, TODO, comportamento parcial ou comando que não bate com a documentação.
- O pedido humano depende de estado atual de produto, tela, API, DB, infra ou feature.

## Checklist De Frescor

- Ler `git status --short` para entender mudanças locais antes de editar.
- Conferir manifests e scripts atuais.
- Conferir arquivos diretamente afetados.
- Conferir testes ou rotas relacionadas.
- Conferir `FEATURE_STATUS.md` antes de assumir que algo está pronto.
- Conferir `TECH_DEBT.md` antes de mexer em área com débito conhecido.
- Conferir `docs/context/frontend.md` antes de UI e `docs/context/seguranca.md` antes de área sensível.

## Como Atualizar

Atualize contexto somente quando a mudança for real e útil para próximas sessões:

- `AI_CONTEXT.md`: stack, comandos, arquitetura, áreas sensíveis.
- `FEATURE_STATUS.md`: pronto, parcial, stub, bloqueado.
- `TECH_DEBT.md` e `docs/debt/*`: débito aceito, impacto, gatilho.
- `docs/context/*`: padrões locais, design system, validação, auth, DB, infra.
- `docs/decisions/*`: decisão arquitetural durável.

Não transformar todo diff em documentação. Atualize apenas quando o contexto futuro ficaria errado sem isso.

## Saída Esperada

Quando houver divergência:

```md
Contexto divergente:
- doc dizia: ...
- repo mostrou: ...
- decisão operacional: ...
- atualização feita/pendente: ...
```
""",
    "EVIDENCIAS_E_VALIDACAO.md": """# Evidências E Validação

Toda entrega precisa de evidência proporcional ao risco. O agente deve provar as afirmações principais antes de finalizar.

## Regra Central

- Não afirmar que algo funciona sem validação ou motivo claro para não validar.
- Preferir evidência executada no projeto: teste, typecheck, lint, build, screenshot, navegador, log de comando ou revisão de diff.
- Se não puder validar, registrar o bloqueio e o risco residual.

## Matriz De Evidência

### UI / Frontend

- Navegador aberto quando houver mudança visual relevante.
- Runtime local iniciado quando viável; se não subir, registrar comando, erro, bloqueio e fallback.
- Desktop e mobile quando a tela for responsiva.
- Golden path e estados loading, empty, error, disabled e populated quando aplicável.
- Evidência de reuso: componentes, tokens, telas parecidas ou justificativa para componente novo.
- Sem overlap, texto estourado ou layout shift incoerente.

### API / Regra De Negócio

- Teste automatizado quando houver lógica nova ou correção de bug.
- Smoke/manual documentado quando teste automatizado não for viável.
- Entrada inválida, não autorizado e caso de sucesso considerados.
- Contrato de resposta/erro preservado ou mudança documentada.

### DB / Migration

- Migration, rollback ou plano de reversão considerado.
- Índices, constraints, ownership/RLS e impacto em dados existentes avaliados quando aplicável.
- Seed/dados de teste ajustados quando necessário.

### Segurança / Privacidade

- Auth e autorização verificadas em endpoints ou telas sensíveis.
- PII, tokens, secrets e dados privados não aparecem em logs, console, screenshots ou respostas públicas.
- Dependência, API externa, upload ou scraping passam pelo baseline de `PADROES_SEGURANCA.md`.

### Infra / Dependências

- Build, CI, Docker, env e rollback considerados quando forem afetados.
- Licença, manutenção, segurança e custo avaliados para dependência nova.

### Docs / Processo

- `AGENTS.md` continua curto.
- Docs detalhados ficam em `docs/ia/` ou `docs/context/`.
- Decisões, débitos e status são atualizados somente quando houver mudança real.
- Contexto antigo foi conferido contra código/configs quando a tarefa dependia dele.
- Delegações/subagentes, quando usados, têm brief e fan-in claros.

## Cartão De Resultado

Use este formato no fechamento de tarefas médias ou altas:

```md
Resultado:
- ...

Evidências:
- ...

Riscos residuais:
- ...

Custo:
- nenhum / aprovado por ...

Próximos passos:
- ...
```
""",
    "PADROES_SEGURANCA.md": """# Padrões De Segurança

Este é o baseline prático para tarefas que tocam segurança, privacidade, dados, autenticação, autorização, dependências, uploads, scraping ou integrações externas.

## Regra Central

- Segurança relevante é risco alto.
- Não confiar no frontend para proteger dado ou ação.
- Não expor segredo, token, dado pessoal ou informação interna em log, erro, console, screenshot ou resposta pública.
- Qualquer custo, API externa, serviço pago ou dependência comercial também passa por `CUSTO_E_APROVACAO.md`.

## Auth E Autorização

- Endpoint sensível exige autenticação.
- Autorização deve ser checada no servidor para o recurso específico.
- Validar acesso negado, usuário sem permissão e tentativa de acessar dado de outro usuário/tenant.
- Não usar apenas esconder botão ou rota no frontend como controle de segurança.
- Alteração de sessão, permissão, reset de senha, convite ou troca de ownership exige revisão de Segurança/Privacidade.

## Dados Pessoais E Privacidade

- Coletar e exibir somente o dado necessário para a tarefa.
- Mascarar PII quando a visualização completa não for necessária.
- Não enviar PII para analytics, logs, tracing, erro de frontend ou ferramenta externa sem base clara.
- Não incluir dados reais sensíveis em seed, fixture, screenshot ou documentação.
- Exportação, exclusão e retenção de dados precisam de Produto + Segurança quando afetarem usuário real.

## Secrets E Configuração

- Secrets nunca entram em commit, log, screenshot ou mensagem de erro.
- Usar `.env.example` sem valores reais.
- Validar que novas integrações documentam variáveis necessárias sem vazar credenciais.
- Rotação/revogação deve ser considerada se um secret foi exposto.

## APIs, Webhooks E Integrações

- Validar entrada no servidor com schema ou regra explícita.
- Definir timeout, tratamento de erro e retry quando chamar serviço externo.
- Verificar autenticação, rate limit, paginação, termos de uso, licença e custo.
- Webhook precisa de verificação de assinatura ou segredo quando a fonte suportar.
- Não persistir payload externo sensível sem necessidade.

## Uploads E Arquivos

- Validar tipo, tamanho e origem do arquivo no servidor.
- Não confiar apenas em extensão ou MIME enviado pelo cliente.
- Evitar servir upload executável no mesmo domínio quando houver risco.
- Considerar antivírus/sandbox quando o produto aceitar arquivos de usuários externos.

## Dependências E Supply Chain

- Preferir dependência já existente no projeto.
- Antes de adicionar dependência nova, verificar manutenção, licença, popularidade, superfície de ataque e custo.
- Dependência que roda em runtime, build, CI ou manipula dados sensíveis exige revisão de Arquiteto ou Segurança.
- Não adicionar biblioteca grande para resolver problema pequeno sem justificativa.

## Frontend

- Sanitizar conteúdo dinâmico quando houver HTML, markdown ou rich text.
- Evitar armazenar token sensível em localStorage quando houver alternativa mais segura no projeto.
- Não colocar regras de autorização apenas no cliente.
- Erros visíveis ao usuário não devem revelar stack, query, token, segredo ou dado de outro usuário.

## Evidência Mínima

Ao finalizar tarefa de segurança, registrar:

- cenário protegido;
- como auth/autorização foram verificados;
- onde PII/secrets/logs foram considerados;
- testes ou validações executadas;
- risco residual, se houver.
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

## Frescor Do Contexto

- Última revisão humana: A confirmar.
- Última conferência contra o repo: gerado na instalação; revisar quando houver mudança relevante.
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
- APIs externas, uploads, dependências e integrações que exigem baseline de segurança.

## Frescor Do Contexto

- Última revisão humana: A confirmar.
- Última conferência contra o repo: gerado na instalação; revisar quando auth, dados, secrets, integrações ou dependências mudarem.
""",
    }
    frameworks = discovery.frameworks if discovery else set()
    if not discovery or {"Next.js", "React", "Vue", "Svelte", "SvelteKit", "Expo", "React Native", "Vite"} & frameworks:
        docs["frontend.md"] = f"""# Contexto Frontend

## Fonte: repo

{bullet(sorted({"Next.js", "React", "Vue", "Svelte", "SvelteKit", "Expo", "React Native", "Vite"} & frameworks) if discovery else [])}

## Padrões Reutilizáveis Detectados

{bullet(discovery.frontend_reuse if discovery else [])}

## Reuso Obrigatório

- Antes de criar UI, procurar componentes compartilhados, telas parecidas, tokens, estilos, hooks e utilitários existentes.
- Antes de UI relevante, definir contrato de UX: tarefa principal, público, padrão local, estados e evidência esperada.
- Se houver design system oficial externo, registrar link/pacote/versão e como o agente deve acessá-lo.
- Se o design system estiver no GitHub e ainda não estiver registrado, pedir link, branch/tag/versão e se é público ou privado.
- Validar acesso via `gh auth status` e `gh repo view ORG/REPO` quando GitHub for necessário.
- Se o agente não conseguir acessar o design system externo, ele deve avisar o humano e sugerir uma ou duas formas de consumo: `gh auth login`, liberar acesso, instalar pacote, anexar snapshot ou copiar tokens/componentes mínimos para este repositório.
- Não pedir token ou credencial no chat.
- Registrar no resumo da entrega quando um componente novo for necessário e por quê.
- Preferir consistência visual do produto a composições novas sem justificativa.

## Design System Oficial

- GitHub/repositório: A confirmar.
- Branch/tag/versão: A confirmar.
- Pacote oficial: A confirmar.
- Público ou privado: A confirmar.
- Forma de acesso: A confirmar.
- Prioridade: componentes locais primeiro, depois design system oficial, salvo regra diferente do projeto.
- Fallback quando inacessível: snapshot/export em `docs/context/`, pacote instalado ou tokens/componentes mínimos copiados para o repo.
- Última validação de acesso: A confirmar.

## A Confirmar

- Design system local ou externo.
- Link, pacote, versão, branch ou tag do design system oficial.
- Biblioteca de componentes.
- Tokens de cor, espaçamento, tipografia e radius.
- Convenções para ícones, tabelas, formulários, modais, cards e empty states.
- Estados loading/empty/error.
- Acessibilidade e responsividade.
- Comando de runtime/dev server para validação visual.

## Frescor Do Contexto

- Última revisão humana: A confirmar.
- Última conferência contra o repo: gerado na instalação; revisar quando componentes, tokens, design system, rotas ou comandos mudarem.
"""
    if not discovery or {"Hono", "Express", "Fastify", "NestJS", "Django", "FastAPI", "Flask"} & frameworks:
        docs["backend.md"] = f"""# Contexto Backend

## Fonte: repo

{bullet(sorted({"Hono", "Express", "Fastify", "NestJS", "Django", "FastAPI", "Flask"} & frameworks) if discovery else [])}

## A Confirmar

- Formato de erro.
- Validação de entrada.
- Boundaries entre handlers/controllers e services.

## Frescor Do Contexto

- Última revisão humana: A confirmar.
- Última conferência contra o repo: gerado na instalação; revisar quando rotas, contratos, validações ou services mudarem.
"""
    if not discovery or discovery.migrations or {"Drizzle", "Prisma", "TypeORM", "Sequelize"} & frameworks:
        docs["db.md"] = f"""# Contexto DB

## Fonte: repo

{bullet(discovery.migrations[:12] if discovery else [])}

## A Confirmar

- Source of truth do schema.
- Política de migrations/rollback.
- Seeds e dados de teste.

## Frescor Do Contexto

- Última revisão humana: A confirmar.
- Última conferência contra o repo: gerado na instalação; revisar quando schema, migrations, seeds ou índices mudarem.
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

## Frescor Do Contexto

- Última revisão humana: A confirmar.
- Última conferência contra o repo: gerado na instalação; revisar quando Docker, CI/CD, env, deploy ou observabilidade mudarem.
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


def discovery_report(discovery: Discovery | None, brief: dict[str, str], install_mode: InstallMode) -> str:
    if not discovery:
        return f"""# Relatório De Descoberta

## Modo De Instalação

{chr(10).join(install_mode_lines(install_mode))}

Descoberta de repo desativada por `--no-discover`.
"""
    brief_lines = [f"- {label}: {brief.get(key, 'A confirmar.')}" for key, label in BRIEF_FIELDS.items()]
    return f"""# Relatório De Descoberta

## Modo De Instalação

{chr(10).join(install_mode_lines(install_mode))}

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

## Frontend / Reuso

{bullet(discovery.frontend_reuse[:20])}

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
    install_mode: InstallMode,
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
        "AI_CONTEXT.md": render_ai_context(project_name, brief, discovery, install_mode),
        "FEATURE_STATUS.md": render_feature_status(brief, discovery, install_mode),
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
    parser.add_argument(
        "--no-auto-force",
        action="store_true",
        help="Do not automatically refresh existing AI docs in update/migration modes; existing files are skipped unless --force is passed.",
    )
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
    install_mode = detect_install_mode(target)
    project_name = args.project_name or brief.get("project") or target.name
    discovery = discover_repo(target, project_name) if args.discover else None

    report = discovery_report(discovery, brief, install_mode)
    if args.discovery_report is not None:
        if args.discovery_report == "-":
            print(report)
        else:
            report_path = Path(args.discovery_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report, encoding="utf-8")

    effective_force = args.force or (install_mode.auto_refresh_existing and not args.no_auto_force)
    print(f"modo detectado: {install_mode.label} — {install_mode.reason}")
    if effective_force and not args.force and install_mode.auto_refresh_existing:
        print("auto-refresh: docs existentes serão arquivados e atualizados. Use --no-auto-force para apenas criar arquivos ausentes.")

    actions = install(target, project_name, effective_force, not args.no_archive, brief, discovery, install_mode)
    for action in actions:
        print(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
