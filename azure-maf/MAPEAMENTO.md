# ADK para MAF, e Google Cloud para Azure

A tabela de tradução do mesmo cenário entre as duas pilhas.
Use como material de apoio e como slide de fechamento do curso:
quem entende as duas colunas entende agentes, não entende um framework.

---

## 0. Atenção: os nomes do MAF mudaram

A API do Microsoft Agent Framework foi renomeada depois que boa parte do
material da internet foi escrita. As tabelas abaixo usam os nomes **atuais**.
Se você encontrar um tutorial com a coluna da esquerda, é material antigo:

| Nome antigo | Nome atual |
|---|---|
| `ChatAgent` | `Agent` |
| `AgentThread` | `AgentSession` |
| `agente.get_new_thread()` | `agente.create_session(session_id=...)` |
| `agente.run(x, thread=...)` | `agente.run(x, session=...)` |
| `@ai_function` | `@tool` |
| `chat_message_store_factory=` | `context_providers=[...]` |
| `workflow.run_stream(x)` | `workflow.run(x, stream=True)` |
| `context.terminate = True` | `raise MiddlewareTermination(result=...)` |
| `await next(context)` no middleware | `await next()`, sem argumento |
| `agent_framework.azure.AzureOpenAIChatClient` | `agent_framework_openai.OpenAIChatClient` |
| `agent_framework.azure.AzureAIAgentClient` | `agent_framework_foundry.FoundryChatClient` |

O pacote `agent-framework-azure-ai` foi descontinuado. Quem o substitui é
`agent-framework-openai` e `agent-framework-foundry`. É por isso que o
`requirements.txt` fixa versão: sem pin, o pip monta combinações que não
funcionam entre si.

---

## 1. Conceitos de agente

| Conceito | Google ADK | Microsoft Agent Framework |
|---|---|---|
| Agente | `LlmAgent(model="gemini-2.5-flash", instruction=...)` | `Agent(client, instructions=...)` |
| Modelo | declarado no agente | injetado pelo chat client |
| Trocar de provedor | trocar a string do modelo | trocar a classe do cliente |
| UI de desenvolvimento | `adk web`, com trace embutido | DevUI, ou hospedar o agente como API |
| Executar | `Runner` com serviços injetados | `await agente.run(...)`, sem runner obrigatório |
| Streaming | `run_async` com eventos | `run(..., stream=True)` |
| Interceptar | callbacks: before/after agent, model, tool | middleware em três níveis: agente, chat, função |

## 2. Memória

| Conceito | ADK | MAF |
|---|---|---|
| Conversa atual | `Session` criada pelo `SessionService` | `AgentSession`, criada e passada por você |
| Dado estruturado do atendimento | `state` com escopos `user:`, `app:`, `temp:` | **não existe equivalente direto** |
| Persistir a conversa | `DatabaseSessionService`, `VertexAiSessionService` | `context_providers=[RedisHistoryProvider(...)]`, Redis ou Cosmos DB |
| Memória de longo prazo | `MemoryService` mais tool `load_memory` | `context_providers` |
| Backend gerenciado | Vertex AI Memory Bank | Memory no Foundry Agent Service, Mem0, Redis |
| Escrita da memória | `add_session_to_memory`, chamada por você | o provider grava, ou você grava com tool própria |

**A lacuna que importa:** o `state` do ADK não tem correspondente no MAF.
Se o seu agente ADK guarda um dicionário de atendimento em `state`,
ao portar para MAF esse dado vai para um armazenamento seu,
para o shared state do workflow, ou para um context provider.
Isso é refatoração real, não troca de import.

## 3. Ferramentas

| Conceito | ADK | MAF |
|---|---|---|
| Function tool | função Python com docstring e type hints | `@tool` com `Annotated[..., Field(description=...)]` |
| Contrato com o modelo | docstring | parâmetro `description` |
| Guardrail antes da execução | `before_tool_callback` | function middleware com `MiddlewareTermination` |
| Aprovação humana | implementada por você | fluxo de aprovação de tool nativo |
| MCP | `MCPToolset`, `ToolboxToolset` | `MCPStreamableHTTPTool`, `MCPStdioTool`, `MCPWebsocketTool` |
| Tools hospedadas | busca e execução de código do Gemini | busca, code interpreter, file search, MCP hospedado, conforme o cliente |

## 4. Multiagente

| Conceito | ADK | MAF |
|---|---|---|
| Delegar conversa | `sub_agents=[...]` | `HandoffBuilder().participants([...])` |
| Consultar e voltar | `AgentTool(agent=...)` | `agente.as_tool(...)` |
| O que decide o roteamento | `description` do sub agente | `description` do participante |
| Modelo mental | árvore, um agente tem um pai | grafo de participantes |
| Padrões adicionais | nenhum pronto | group chat, Magentic |

## 5. Orquestração determinística

| Conceito | ADK | MAF |
|---|---|---|
| Ordem fixa | `SequentialAgent` | `SequentialBuilder` |
| Paralelo | `ParallelAgent` | `ConcurrentBuilder`, com dispatcher, fan-out, fan-in e agregador |
| Loop | `LoopAgent(max_iterations=n)` | **não existe pronto**: loop em Python ou ciclo no `WorkflowBuilder` |
| Passagem entre etapas | `output_key` mais `{chave}` na instruction | a conversa acumulada, ou shared state do workflow |
| Sair do loop | `tool_context.actions.escalate = True` | condição sua |
| Execução | árvore de agentes | grafo de executores com supersteps |
| Retomar processo longo | não nativo | checkpointing e hidratação |

**As duas lacunas que dão trabalho ao portar:** `output_key` e `LoopAgent`.
Em compensação, `WorkflowBuilder` faz coisas que o ADK não faz:
grafo arbitrário, aresta condicional, sub-workflow, checkpoint,
human in the loop e visualização.

## 6. Serviços de plataforma

| Papel | Google Cloud | Azure |
|---|---|---|
| Modelo | Gemini via AI Studio ou Vertex AI | Azure OpenAI ou Azure AI Foundry |
| Runtime gerenciado de agente | Vertex AI Agent Engine | Azure AI Foundry Agent Service |
| Memória gerenciada | Vertex AI Memory Bank | Memory no Foundry Agent Service, ou Redis, ou Mem0 |
| Banco relacional | Cloud SQL para PostgreSQL | Azure Database for PostgreSQL Flexible Server |
| Servidor MCP de dados | MCP Toolbox for Databases | o mesmo, em Container Apps |
| Hospedar contêiner | Cloud Run | Azure Container Apps |
| Identidade | Service Account, Workload Identity | Entra ID, identidade gerenciada |
| Segredos | Secret Manager | Key Vault |
| Observabilidade | Cloud Trace e Cloud Logging | Application Insights e Log Analytics |
| Rede privada | VPC com Private Service Connect | VNet com private endpoint |

Repare na linha do MCP Toolbox: é a única que não muda.
O `tools.yaml` deste repositório é idêntico ao do laboratório em ADK.
Padronizar acesso a dado em MCP antes de escolher framework
é a decisão com maior meia-vida das três.

## 7. O que sobrevive à troca

Sete coisas seguem idênticas entre as duas pilhas, e são elas que
o curso ensina de verdade:

1. Instruction bem escrita vale mais do que instruction longa.
2. A descrição da tool é o contrato com o modelo, nos dois frameworks.
3. Política de ação destrutiva mora no interceptador, não na instruction.
4. Isolamento de tools por papel é arquitetura, e instruction proibindo uso é torcida.
5. O texto que descreve um especialista é o que decide o roteamento.
6. Roteamento por LLM é probabilístico, e regra de compliance precisa de topologia.
7. Paralelismo reduz latência e multiplica custo e pressão de cota no mesmo instante.

Framework é detalhe de implementação desses sete pontos.
