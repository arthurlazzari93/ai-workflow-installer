# AI Workflow Installer

Skill e CLI para instalar um workflow de desenvolvimento com IA dentro de projetos de software.

## 1. O Que A Skill Resolve

O `ai-workflow-installer` resolve o problema de usar Codex em projetos sem contexto operacional confiável.

Sem um método claro, o agente tende a trabalhar com contexto incompleto: não sabe o que está pronto, o que é stub, onde estão os riscos, quais padrões de frontend reutilizar, quais decisões já foram tomadas, quais comandos validar ou quando precisa parar para pedir aprovação humana.

A skill cria uma base de trabalho para o Codex:

- `AGENTS.md` curto como entrypoint;
- contexto vivo do projeto;
- matriz de risco;
- papéis lógicos de agentes;
- fluxo para pedidos vagos;
- padrões premium de frontend;
- reuso obrigatório de componentes, tokens e design system;
- pesquisa para referências, APIs, scraping e problemas técnicos;
- baseline de segurança;
- gate de custo com aprovação humana;
- validação visual/runtime;
- sincronia de contexto para evitar decisões com docs desatualizadas;
- evidências de validação antes de finalizar.

A ideia central: o humano continua aprovando direção, custo e risco; o Codex ganha um processo claro para executar com mais consistência.

## 2. Cenários De Projeto

### Projeto Sem Contexto De IA

Este é o caso em que o projeto não tem `AGENTS.md`, `AI_CONTEXT.md`, `FEATURE_STATUS.md`, `TECH_DEBT.md` ou documentação própria para orientar agentes.

O que a skill faz:

1. Detecta que o projeto ainda não tem workflow de IA.
2. Inspeciona o repositório.
3. Detecta stack, scripts, testes, Docker, CI/CD, migrations, docs e pontos de reuso frontend.
4. Cria os arquivos base.
5. Marca informações detectadas como `Fonte: repo`.
6. Marca informações ausentes ou inferidas como `A confirmar`.
7. Cria um processo inicial para o Codex trabalhar com triagem, risco, validação e evidência.

### Projeto Com Contexto De IA Fora Do Padrão

Este é o caso em que o projeto já tem alguma documentação, mas espalhada, duplicada, longa demais ou fora de um formato operacional. Exemplos:

- `AGENTS.md` muito grande;
- `CLAUDE.md` duplicando regras;
- `PROJECT_MEMORY.md` misturando decisão, histórico e changelog;
- `TECH_DEBT.md` sem impacto, contexto ou gatilho;
- instruções antigas para Cursor, Copilot, Windsurf, Gemini ou Claude;
- docs de IA sem matriz de risco, papéis, DoD ou gates.

O que a skill faz:

1. Detecta `migration` ou `update`.
2. Arquiva documentos antigos em `docs/archive/` antes de substituir.
3. Mantém `AGENTS.md` como fonte canônica curta.
4. Transforma `CLAUDE.md` em ponte de compatibilidade.
5. Reorganiza memória, dívida técnica, decisões e contexto em arquivos próprios.
6. Preserva histórico em vez de apagar conhecimento.
7. Atualiza o projeto para o formato da skill.

### Projeto Que Já Usa Esta Skill

Quando o projeto já tem este workflow instalado, o instalador detecta `update`.

O que a skill faz:

1. Atualiza os documentos do kit.
2. Arquiva versões anteriores antes de sobrescrever.
3. Mantém o formato compatível com as melhorias mais recentes.
4. Permite usar `--no-auto-force` quando você quiser apenas criar arquivos faltantes.

## 3. Estrutura Criada No Projeto

Ao rodar `ai-workflow .`, a skill cria ou atualiza esta estrutura dentro do projeto alvo:

```txt
AGENTS.md
CLAUDE.md
AI_CONTEXT.md
FEATURE_STATUS.md
PROJECT_MEMORY.md
TECH_DEBT.md
CHANGELOG.md

docs/
  ia/
    README.md
    MATRIZ_DE_RISCO.md
    TRIAGEM_E_INTAKE.md
    ORQUESTRACAO_DE_AGENTES.md
    PAPEIS_DOS_AGENTES.md
    POLITICA_DE_MODELOS.md
    FLUXOS.md
    DESCOBERTA_E_PLANEJAMENTO.md
    DEFINICAO_DE_PRONTO.md
    PADROES_FRONTEND.md
    VALIDACAO_VISUAL_E_RUNTIME.md
    PESQUISA_E_REFERENCIAS.md
    PADROES_SEGURANCA.md
    SINCRONIA_DE_CONTEXTO.md
    CUSTO_E_APROVACAO.md
    EVIDENCIAS_E_VALIDACAO.md
    PADROES_DE_FALHA.md
  context/
    produto.md
    seguranca.md
    frontend.md
    backend.md
    db.md
    infra.md
  decisions/
    README.md
  debt/
    README.md
    produto-integracoes.md
    seguranca.md
    infra-observabilidade.md
    backend-db.md
    frontend-ux.md
    qualidade-testes.md
    resolvidos.md
```

Principais arquivos:

- `AGENTS.md`: leitura inicial do Codex dentro do projeto.
- `AI_CONTEXT.md`: contexto curto e sempre lido.
- `FEATURE_STATUS.md`: mapa do que está pronto, parcial, stubado ou bloqueado.
- `TECH_DEBT.md`: índice curto de dívida técnica.
- `PROJECT_MEMORY.md`: índice de decisões históricas.
- `docs/ia/`: método de trabalho dos agentes.
- `docs/context/`: contexto por área.
- `docs/decisions/`: ADRs.
- `docs/debt/`: débitos detalhados.

## 4. Instalação E Uso Passo A Passo

Pré-requisito: Python 3.11+.

### Windows

Abra o PowerShell.

Instale o `pipx`:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

Feche e reabra o PowerShell.

Instale o pacote:

```powershell
pipx install git+https://github.com/arthurlazzari93/ai-workflow-installer.git
```

Registre a skill no Codex:

```powershell
ai-skills install ai-workflow-installer
```

Abra uma nova sessão do Codex para a skill aparecer.

### Linux

Instale o `pipx`:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Feche e reabra o terminal.

Instale o pacote:

```bash
pipx install git+https://github.com/arthurlazzari93/ai-workflow-installer.git
```

Registre a skill no Codex:

```bash
ai-skills install ai-workflow-installer
```

Abra uma nova sessão do Codex para a skill aparecer.

### Opcional: Claude Code

Se o time também usa Claude Code:

```bash
ai-skills install ai-workflow-installer --codex-home ~/.claude --force
```

Isso instala a skill em:

```txt
~/.claude/skills/ai-workflow-installer
```

### Como Usar Depois Da Instalação

Entre no repositório do projeto:

```bash
cd /caminho/do/projeto
```

Instale o workflow:

```bash
ai-workflow .
```

Para enriquecer o contexto inicial com respostas humanas:

```bash
ai-workflow . --interactive
```

O modo interativo pergunta:

- o que é o projeto;
- quem usa;
- objetivo atual;
- áreas sensíveis;
- o que não pode quebrar;
- dores conhecidas.

Depois disso, abra o projeto no Codex e peça:

```txt
Use a skill ai-workflow-installer neste projeto.
```

Ou trabalhe normalmente. O Codex passará a ler `AGENTS.md` e os documentos indicados conforme o tipo da tarefa.

## 5. Comandos

### Workflow No Projeto

```bash
# Instala ou atualiza o workflow no repo atual
ai-workflow .

# Instala coletando brief humano
ai-workflow . --interactive

# Define nome do projeto manualmente
ai-workflow . --project-name "Meu Produto"

# Cria apenas arquivos ausentes, sem atualizar docs existentes
ai-workflow . --no-auto-force

# Instala sem investigação automática do repo
ai-workflow . --no-discover

# Não arquiva arquivos substituídos
ai-workflow . --no-archive

# Gera relatório de descoberta no stdout
ai-workflow . --discovery-report

# Gera relatório de descoberta em arquivo
ai-workflow . --discovery-report docs/ia/DISCOVERY_REPORT.md

# Usa brief em Markdown ou JSON
ai-workflow . --brief-file brief.md
ai-workflow . --brief-file brief.json
```

### Skill No Codex

```bash
# Lista skills instaladas
ai-skills list

# Instala a skill
ai-skills install ai-workflow-installer

# Reinstala/atualiza a skill
ai-skills install ai-workflow-installer --force

# Mostra a pasta de skills do Codex
ai-skills path
```

### Skill No Claude Code

```bash
# Instala a skill no Claude Code
ai-skills install ai-workflow-installer --codex-home ~/.claude --force

# Mostra a pasta de skills usada para Claude Code
ai-skills path --codex-home ~/.claude
```

### Atualização Do Pacote

```bash
pipx upgrade ai-workflow-installer
ai-skills install ai-workflow-installer --force
```

### Desinstalação

```bash
pipx uninstall ai-workflow-installer
```

Remover a skill do Codex manualmente:

```bash
rm -rf ~/.codex/skills/ai-workflow-installer
```

Remover a skill do Claude Code manualmente:

```bash
rm -rf ~/.claude/skills/ai-workflow-installer
```
