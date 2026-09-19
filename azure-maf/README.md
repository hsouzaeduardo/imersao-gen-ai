# ARI, o estagiário da Aurora Fibra: versão Azure + Microsoft Agent Framework

A mesma história, os mesmos seis labs, a mesma base de dados,
agora com **Microsoft Agent Framework** rodando sobre **Azure**.

A empresa é a **Aurora Fibra**, provedor regional de internet com 400 mil assinantes.
O agente é o **ARI**, contratado como estagiário do suporte N1.
Cada lab existe porque o anterior falhou de um jeito específico.

Este repositório é irmão do laboratório em Google ADK.
Dá para ensinar só um dos dois, ou os dois em sequência,
e nesse caso [`MAPEAMENTO.md`](MAPEAMENTO.md) é o material mais valioso do curso:
a tabela de tradução conceito a conceito entre as duas pilhas.

---

## Mapa dos labs

| Lab | Capítulo | Conceito | Construto MAF | Recurso Azure |
|---|---|---|---|---|
| 1 | Primeiro dia, sem crachá | agente puro | `Agent` mais chat client | Azure OpenAI ou Foundry |
| 2a | O caderno de anotações | conversa | `AgentSession`, `RedisHistoryProvider` | Azure Cache for Redis |
| 2b | O prontuário do cliente | memória longa | tools próprias ou `context_providers` | Redis, Mem0, Memory do Foundry |
| 3 | O primeiro acesso ao sistema | tool externa | `@tool` mais function middleware | Container Apps |
| 4 | A chave do banco de dados | MCP | `MCPStreamableHTTPTool` | PostgreSQL Flexible Server mais Toolbox em Container Apps |
| 5 | Promovido a líder de equipe | multiagente | `HandoffBuilder`, `as_tool` | o mesmo modelo |
| 6 | O processo operacional | orquestração | `SequentialBuilder`, `ConcurrentBuilder`, loop | Application Insights para o trace |
| 7 | O agente que não é seu | A2A | `A2AAgent`, `A2AExecutor` | Container Apps, um por time |
| 8 | A prova de que funciona | avaliação | `evaluate_agent`, checks e juiz | a mesma massa em qualquer ambiente |

---

## Para quem vai dar a aula

- [`docs/roteiros/`](docs/roteiros/) — **um roteiro por lab**, detalhado: partes,
  falas, edições ao vivo com o desfazer, perguntas da turma e o gancho do próximo.
  É o que você abre enquanto dá a aula.
- [`docs/COMO_EXECUTAR.md`](docs/COMO_EXECUTAR.md) — passo a passo operacional de cada
  lab: o que precisa estar no ar, o comando, o resultado esperado e os erros comuns.
- [`docs/ROTEIRO_AULA_AZURE.md`](docs/ROTEIRO_AULA_AZURE.md) — grade dos dois
  encontros, as sete demos que não podem falhar, perguntas frequentes da turma
  e o checklist de véspera.
- [`docs/CONDUCAO_LAB_A_LAB.md`](docs/CONDUCAO_LAB_A_LAB.md) — cada lab parte a
  parte: o comando, a saída esperada, a fala de cada momento e o que fazer
  quando não sai como o previsto.

---

## Setup

### 1. Dependências

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Use o venv mesmo que você já tenha os pacotes no Python global. O
`requirements.txt` fixa versão de propósito: a API do Agent Framework
ainda se move, e sem pin o pip monta combinações que não funcionam
entre si. O porquê de cada pin está comentado no próprio arquivo.

### 2. Azure

```bash
az login
./infra/deploy.sh        # provisiona tudo e escreve o .env
```

Detalhes, custo e o que o script simplifica em relação a produção
estão em [`infra/README.md`](infra/README.md).

### 3. Plano B, sem Azure para a camada de dados

```bash
cp .env.example .env     # preencha só o endpoint e o deployment do modelo
docker compose -f docker-compose.local.yml up -d
```

Postgres, Toolbox, API de rede e Redis sobem no notebook.
Só o modelo continua vindo do Azure OpenAI.
Esse modo salva aula em rede corporativa restrita.

Existe ainda um meio-termo, com o banco no Azure e o resto no notebook:

```bash
docker compose -f docker-compose.azure-db.yml up -d
```

Esse arquivo lê `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER` e
`POSTGRES_PASSWORD` do `.env`, e falha na hora se faltar alguma, em vez de
subir um Toolbox que só quebra na primeira pergunta do aluno. Quem lê essas
variáveis é o Toolbox, nunca o agente: é esse o ponto do lab 04.

O `docker-compose.local.yml` ignora esse bloco de propósito e mantém valores
fixos. Ele é a rota de fuga do Azure, e não pode passar a depender do Azure
só porque o `.env` está preenchido.

### 4. Rodar

Sempre com `-m`, e sempre a partir da raiz do projeto:

```bash
python -m lab01_agente_puro.agent
python -m lab02_memoria.a_thread
python -m lab02_memoria.a_thread --continuar
python -m lab02_memoria.b_memoria_longa
python -m lab03_tool_externa.agent
python -m lab04_mcp_toolbox.agent
python -m lab05_handoff.agent
python -m lab05_handoff.agent --tools
python -m lab06_workflows.run comparar
python -m uvicorn lab07_a2a.servidor:app --port 9000   # noutro terminal
python -m lab07_a2a.agent
python -m lab08_avaliacao.avaliar --ab
```

### UI

```bash
python -m ui        # http://localhost:8080
```

Os agentes do curso no DevUI, a UI de desenvolvimento do MAF — o equivalente ao
`adk web` do laboratório em Google. Detalhes em [`ui/README.md`](ui/README.md).

Rodar o arquivo direto, `python lab01_agente_puro/agent.py`, falha com
`ModuleNotFoundError: No module named 'comum'`. Não é erro de instalação:
executar o arquivo põe a pasta dele no `sys.path` em vez da raiz do projeto,
e aí o pacote `comum` fica invisível. O `-m` resolve.

---

## Visualização ao vivo dos agentes (opcional)

A sala do [habbo-agents](https://github.com/hsouzaeduardo/habbo-agents) desenha
até 12 avatares com balão de fala. Preencha `HABBO_URL` e `HABBO_API_KEY` no
`.env` e cada agente dos labs passa a publicar o que está fazendo:

| Lab | O que a turma vê |
|---|---|
| 01 a 04 | a Ana sozinha, trocando de balão a cada tool |
| 05 | Felipe tria, e Bruno e Carla acendem quando são consultados |
| 06 concorrente | Diego, Elisa e Fábio acendem **ao mesmo tempo**, cada um com a sua consulta |

É a forma mais direta de mostrar concorrência sem pedir para a turma ler log.
Rode `lab06_workflows.run comparar` com a sala aberta num projetor: no modo
sequencial os avatares acendem um de cada vez, no concorrente acendem juntos.

Sem `HABBO_URL` tudo vira no-op. A publicação é disparada e esquecida, com
falha engolida de propósito: se o Habbo cair ou a rede da empresa bloquear,
o lab roda igual e o cronômetro do lab 06 continua medindo só o modelo.

Para esvaziar a sala entre demos:

```python
from comum import limpar_sala
await limpar_sala()
```

O mapa de agente para avatar está em `comum/habbo.py`, em `MAPA`.

---

## As três diferenças que mais confundem quem vem do ADK

**1. Estado de conversa é opt-in.**
Sem `AgentSession`, cada `run` é uma conversa nova. O lab 01 mostra isso doendo:
o agente esquece o CPF informado no turno anterior.

**2. Não existe `state`.**
O ADK tem um dicionário de sessão com escopos. O MAF tem histórico de mensagens
e context providers. Dado estruturado do atendimento vira armazenamento seu.
Isso é a refatoração real ao portar um agente de um framework para o outro.

**3. Não existe `LoopAgent`.**
Loop é seu: em Python, como no lab 06, ou como ciclo no `WorkflowBuilder`.
Em troca, o workflow do MAF faz grafo arbitrário, aresta condicional,
checkpoint e human in the loop, que o ADK não faz.

---

## O que a versão Azure acrescenta ao curso

Quatro blocos que não existem na versão Google e que valem tempo de aula,
principalmente em turma corporativa:

- **Identidade em vez de chave.** Entra ID no modelo, identidade gerenciada
  no Toolbox para falar com o Postgres, e nenhuma senha no `tools.yaml`.
- **Trace ponta a ponta.** O MAF emite OpenTelemetry com convenções GenAI.
  Com `ENABLE_OTEL=true`, o Application Insights mostra a árvore completa
  do atendimento: agente, chamada de modelo, tool, workflow, executor.
- **Cota como decisão de arquitetura.** TPM por deployment é o que quebra
  o lab 06 em sala. O aluno sente na pele que concorrência custa cota.
- **Foundry Agent Service como alternativa.** Uma variável de ambiente
  muda de agente no seu processo para agente gerenciado no serviço,
  com threads e políticas do lado do Azure. O código dos labs não muda.

---

## Aviso sobre versões

O Microsoft Agent Framework evolui rápido e alguns nomes de classe mudam
entre releases, principalmente nos pacotes de memória.
Onde isso é provável, o código tenta mais de um caminho de import
e diz o que fazer quando não encontra. Confira com `pip show` na véspera.

## Aviso sobre dados

Todos os CPFs, nomes, endereços e contratos em `data/seed_aurora.sql`
são fictícios, gerados para aula.
