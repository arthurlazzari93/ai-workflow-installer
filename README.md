# AI Workflow Installer

Um kit para padronizar o jeito que times usam IA no desenvolvimento de software.

Ele instala uma skill do Codex e um conjunto de documentos operacionais que ajudam agentes de IA a entenderem um projeto, classificarem risco, chamarem os especialistas certos e evitarem repetir bugs.
Também orienta pedidos vagos por uma etapa de descoberta e aprovação, trabalhos de frontend com reuso de componentes, pesquisa de referências quando houver ambiguidade e bloqueio de qualquer custo real sem aprovação humana.

> A ideia central: **IA boa precisa de contexto bom, processo leve e gates fortes onde existe risco.**

## O Que Este Projeto Resolve

Projetos em andamento quase sempre têm o mesmo problema quando começam a usar IA:

- não existe `AGENTS.md`;
- o contexto está espalhado em README, issues, código e cabeça das pessoas;
- a IA não sabe o que está pronto, parcial ou stubado;
- decisões arquiteturais ficam misturadas com changelog;
- bugs escapados não viram aprendizado durável;
- cada dev usa IA de um jeito diferente.

O `ai-workflow-installer` cria uma base comum para resolver isso.

## O Que Ele Instala

No assistente de IA usado pelo dev:

- uma skill chamada `ai-workflow-installer`;
- comandos CLI para instalar e atualizar o workflow em qualquer repo;
- suporte para times mistos usando Codex e Claude Code.

Dentro do projeto alvo:

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
  decisions/
  debt/
```

## Como Funciona

O fluxo padrão para projetos existentes é:

1. você roda `ai-workflow .` no projeto;
2. o instalador identifica automaticamente se é instalação nova, onboarding de projeto existente, atualização ou migração;
3. ele investiga o repositório;
4. ele detecta stack, scripts, docs, CI/CD, Docker, testes, migrations, áreas sensíveis e pontos de reuso frontend;
5. ele gera ou atualiza os documentos;
6. docs antigas de IA são arquivadas antes de atualização/migração;
7. tudo que veio do usuário fica marcado como `Fonte: brief`;
8. tudo que veio do repo fica marcado como `Fonte: repo`;
9. o modo de instalação fica marcado como `Fonte: detecção automática`;
10. inferências e lacunas ficam marcadas como `A confirmar`;
11. todo trabalho ganha triagem/intake leve para classificar risco, especialistas e evidências esperadas;
12. quando a ferramenta suportar subagentes reais, o fluxo orienta autorização, divisão segura, brief e fan-in;
13. pedidos vagos como "melhorar UX" viram descoberta, perguntas e plano aprovado antes de implementação;
14. trabalhos de UI passam a seguir reuso obrigatório de componentes, tokens, layouts, design system oficial e padrões existentes;
15. UI relevante exige validação visual/runtime quando viável, ou bloqueio/fallback explícito;
16. pesquisa entra quando houver ambiguidade visual, API, scraping, dependência ou problema técnico desconhecido;
17. segurança passa a ter baseline prático para auth, autorização, PII, secrets, APIs externas, uploads e dependências;
18. contexto vivo evita decisão ruim quando docs estão antigas, genéricas ou contraditórias com o repo;
19. entregas relevantes precisam registrar evidências de validação;
20. se um design system externo no GitHub for necessário, o agente solicita link/branch/tag/versão, valida acesso com `gh` e nunca pede token no chat;
21. se um design system externo não puder ser acessado, o agente informa o bloqueio e sugere uma ou duas formas de consumo;
22. qualquer custo real ou potencial exige aprovação humana antes da implementação.

Isso evita o pior erro possível: a IA fingir que sabe o que não sabe.

## Instalação

O pacote Python é o mesmo para todo mundo. Depois da instalação, cada dev registra a skill no assistente que usa: Codex, Claude Code ou os dois.

Pré-requisito: Python 3.11+.

Instale `pipx`:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Feche e reabra o terminal.

Instale o pacote:

```bash
pipx install git+https://github.com/arthurlazzari93/ai-workflow-installer.git
```

### Para Devs Que Usam Codex

Registre a skill no Codex:

```bash
ai-skills install ai-workflow-installer
```

Abra uma nova sessão do Codex para a skill aparecer no contexto.

### Para Devs Que Usam Claude Code

Registre a skill no Claude Code:

```bash
ai-skills install ai-workflow-installer --codex-home ~/.claude --force
```

Isso instala a skill em:

```bash
~/.claude/skills/ai-workflow-installer
```

O parâmetro `--codex-home` é histórico: ele aponta para a pasta base onde a CLI deve criar `skills/`. Para Claude Code, essa pasta base é `~/.claude`.

Reinicie o Claude Code para a skill aparecer. Depois, você pode chamar a skill pelo nome ou pedir em linguagem natural:

```txt
Use a skill ai-workflow-installer para instalar o workflow de IA neste projeto.
```

### Para Devs Que Usam Codex E Claude Code

Instale nos dois ambientes:

```bash
ai-skills install ai-workflow-installer
ai-skills install ai-workflow-installer --codex-home ~/.claude --force
```

Reinicie os dois assistentes depois da instalação.

## Uso Básico

Dentro do projeto onde você quer aplicar o método:

```bash
cd /caminho/do/projeto
ai-workflow .
```

O comando detecta automaticamente o modo:

- `fresh`: projeto sem workflow de IA;
- `existing-project onboarding`: projeto existente sem instruções de IA;
- `update`: projeto já tem este kit;
- `migration`: projeto tem docs antigas/customizadas de IA.

Se você quiser enriquecer o contexto inicial com respostas humanas, use:

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

Depois disso, o instalador escaneia o repo e cria os documentos.

## Projetos Que Já Têm Docs Antigos

Se o projeto já tem `AGENTS.md`, `CLAUDE.md`, `PROJECT_MEMORY.md`, `TECH_DEBT.md` ou docs antigas de IA, use:

```bash
ai-workflow .
```

O instalador detecta `migration` ou `update` automaticamente. Arquivos existentes são arquivados antes de serem substituídos:

```txt
docs/archive/
```

Nada importante deve ser apagado sem cópia histórica.

Para apenas criar arquivos faltantes sem atualizar docs existentes, use:

```bash
ai-workflow . --no-auto-force
```

## Gerar Relatório De Descoberta

Para revisar o que foi detectado:

```bash
ai-workflow . --interactive --discovery-report docs/ia/DISCOVERY_REPORT.md
```

Esse relatório ajuda o time a validar as inferências e substituir `A confirmar` por fatos reais.

## Usar Brief Em Arquivo

Você também pode passar um brief pronto:

```bash
ai-workflow . --brief-file brief.md
```

Modelo:

```md
## O que é o projeto

## Quem usa

## Objetivo atual

## Áreas sensíveis

## O que não pode quebrar

## Dores conhecidas
```

JSON também funciona:

```json
{
  "project": "Sistema interno de vendas",
  "users": "Time comercial e gestores",
  "current_goal": "Reduzir retrabalho no fluxo de propostas",
  "sensitive_areas": "Dados de clientes, permissões e integrações de pagamento",
  "must_not_break": "Login, geração de propostas e webhooks",
  "known_pains": "Testes fracos e documentação desatualizada"
}
```

## Comandos

```bash
# Instala workflow no repo atual
ai-workflow .

# Instala workflow coletando brief humano
ai-workflow . --interactive

# Migra/atualiza docs existentes automaticamente, arquivando versões anteriores
ai-workflow .

# Cria só arquivos ausentes, sem atualizar docs existentes
ai-workflow . --no-auto-force

# Instala sem investigação automática
ai-workflow . --no-discover

# Gera relatório de descoberta
ai-workflow . --discovery-report docs/ia/DISCOVERY_REPORT.md

# Lista skills instaladas no Codex
ai-skills list

# Instala ou atualiza a skill no Codex
ai-skills install ai-workflow-installer --force

# Instala ou atualiza a skill no Claude Code
ai-skills install ai-workflow-installer --codex-home ~/.claude --force

# Mostra a pasta de skills do Codex
ai-skills path

# Mostra a pasta de skills usada para o Claude Code
ai-skills path --codex-home ~/.claude
```

## Atualização

Codex:

```bash
pipx upgrade ai-workflow-installer
ai-skills install ai-workflow-installer --force
```

Claude Code:

```bash
pipx upgrade ai-workflow-installer
ai-skills install ai-workflow-installer --codex-home ~/.claude --force
```

Codex e Claude Code:

```bash
pipx upgrade ai-workflow-installer
ai-skills install ai-workflow-installer --force
ai-skills install ai-workflow-installer --codex-home ~/.claude --force
```

## Desinstalação

Remover o pacote:

```bash
pipx uninstall ai-workflow-installer
```

Remover a skill do Codex manualmente:

```bash
rm -rf ~/.codex/skills/ai-workflow-installer
```

Se você usa `CODEX_HOME`, a pasta será:

```bash
$CODEX_HOME/skills/ai-workflow-installer
```

Remover a skill do Claude Code manualmente:

```bash
rm -rf ~/.claude/skills/ai-workflow-installer
```

## Filosofia

Este kit segue algumas regras simples:

- contexto curto vence documento gigante;
- especialistas entram por risco, não por ritual;
- decisões arquiteturais viram ADR;
- entrega vira changelog;
- estado atual vira feature status;
- dívida técnica precisa de impacto, contexto e gatilho;
- bug escapado precisa virar barreira durável;
- pedido vago precisa virar plano aprovado antes de código;
- frontend premium começa por reutilizar componentes, tokens e padrões existentes;
- pesquisa transforma ambiguidade visual ou técnica em opções implementáveis;
- custo real ou potencial exige aprovação humana explícita antes da implementação;
- `CLAUDE.md` não deve duplicar `AGENTS.md`;
- a IA deve marcar incerteza como `A confirmar`.

## Estrutura Do Repositório

```txt
SKILL.md                         # skill do Codex
agents/openai.yaml               # metadata da skill
references/                      # referências carregadas sob demanda
scripts/install_ai_workflow.py   # wrapper local para dev
src/ai_workflow_installer/       # pacote Python e CLIs
```

## Desenvolvimento Local

```bash
git clone https://github.com/arthurlazzari93/ai-workflow-installer.git
cd ai-workflow-installer
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Validar a skill:

```bash
python /caminho/para/quick_validate.py .
```

Testar em um projeto temporário:

```bash
mkdir /tmp/ai-workflow-demo
ai-workflow /tmp/ai-workflow-demo --project-name "Demo" --discovery-report /tmp/ai-workflow-demo/report.md
```

## Licença

MIT.
