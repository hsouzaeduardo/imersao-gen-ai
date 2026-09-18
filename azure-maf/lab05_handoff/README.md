# Lab 05 (Azure + MAF): promovido a líder de equipe

```bash
python -m lab05_handoff.agent           # handoff, o especialista assume
python -m lab05_handoff.agent --tools   # agentes como ferramentas
```

## O que muda em relação ao ADK

| ADK | MAF |
|---|---|
| `sub_agents=[...]` no `LlmAgent` | `HandoffBuilder().participants([...]).with_start_agent(...)` |
| transferência implícita, decidida pelo LLM | handoff explícito, também decidido pelo LLM |
| `AgentTool(agent=...)` | `agente.as_tool(name=..., description=...)` |
| isolamento por `toolset_name` | uma conexão MCP por papel |
| hierarquia: um agente tem um pai | grafo: o handoff é um workflow, não uma árvore |

A diferença conceitual que vale a aula: no ADK, delegação é uma propriedade
do agente. No MAF, delegação é um workflow com participantes.
O ADK é mais direto para hierarquia simples. O MAF deixa a topologia explícita,
e isso importa quando o desenho deixa de ser uma árvore.

## Roteiro

1. **Description é o roteador** (25 min): em `especialistas.py`, troque
   `DESC_TECNICO` por "Agente técnico." e rode de novo. O roteamento desanda.
   Mesmo experimento da versão ADK, mesma lição.
2. **Isolamento de tools** (10 min): o agente de cobrança recebe a conexão MCP
   de cobrança. Pergunte à turma o que aconteceria se todos recebessem o toolset
   completo, e por que instruction dizendo "não use essa tool" não é controle.
3. **Handoff versus as_tool** (20 min): rode os dois modos com a mesma frase.
   No handoff aparecem duas vozes em sequência. Com `as_tool`, uma voz só,
   integrada, e o trace mostra as consultas internas.
4. **O limite da delegação por LLM** (15 min): rode dez vezes a frase de dois
   assuntos e anote a ordem. Ela varia, mesmo com a instruction mandando
   tratar cobrança primeiro. Esse é o gancho do lab 06.

## Gotchas

- **MCP tool precisa estar conectado quando o agente roda.** Por isso os
  especialistas nascem dentro de um `async with`, e não no import do módulo.
  Criar fora do contexto é o erro mais comum aqui, e o sintoma é tool que some.
- **`as_tool` esconde o especialista do cliente.** Isso é ótimo para consolidar
  resposta e péssimo quando o especialista precisa fazer perguntas de qualificação.
- **O MAF tem mais padrões de orquestração do que o ADK**: além de handoff,
  existem group chat e Magentic. Não use Magentic em aula introdutória:
  ele resolve um problema que a turma ainda não tem.
- **Nome e descrição dos participantes entram no prompt de roteamento.** Vale o mesmo
  cuidado do ADK.
