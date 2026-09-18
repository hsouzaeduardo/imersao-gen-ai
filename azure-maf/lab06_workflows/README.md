# Lab 06 (Azure + MAF): o processo operacional

```bash
python -m lab06_workflows.run sequencial
python -m lab06_workflows.run concorrente
python -m lab06_workflows.run comparar
python -m lab06_workflows.run loop
python -m lab06_workflows.run completo
```

## O que muda em relação ao ADK

| ADK | MAF |
|---|---|
| `SequentialAgent(sub_agents=[...])` | `SequentialBuilder(participants=[...]).build()` |
| `ParallelAgent(sub_agents=[...])` | `ConcurrentBuilder(participants=[...]).build()`, com dispatcher, fan-out, fan-in e agregador prontos |
| `LoopAgent(max_iterations=n)` | não existe pronto: loop em Python ou ciclo no `WorkflowBuilder` |
| `output_key` mais `{chave}` na instruction | os participantes recebem a conversa acumulada |
| workflow agent é um agente | workflow é um grafo de executores, com checkpoint e visualização |

Duas diferenças que exigem atenção na hora de portar código:

**1. Não existe `output_key`.** No ADK, cada etapa gravava numa chave e a
seguinte lia com `{chave}`. No `SequentialBuilder`, o que trafega é a conversa.
Por isso as instructions deste lab dizem "use o que veio na conversa acima"
em vez de interpolar variável. Para estado estruturado entre etapas,
o caminho é shared state do workflow ou executores próprios.

**2. Não existe `LoopAgent`.** Isso assusta quem vem do ADK e não deveria:
o `WorkflowBuilder` aceita ciclos, com aresta condicional voltando ao redator.
Neste lab o loop está em Python porque é mais legível em sala,
e porque deixa explícito que a condição de parada é decisão sua.

## Roteiro

1. **Sequencial** (25 min): rode dez vezes e compare com o lab 05.
   Ordem idêntica nas dez. Inverta dois participantes e mostre a saída degradar.
2. **Concorrente e o cronômetro** (25 min): `run comparar`, os dois tempos na tela.
   Depois explique o modelo de supersteps: dentro de um superstep tudo roda junto,
   e o workflow só avança quando todos terminam. Isso define o ganho real.
3. **Loop** (20 min): `run loop`. O rascunho começa cheio de jargão,
   o crítico aponta os critérios, o redator corrige.
   Aumente `max_iteracoes` e mostre o custo subindo com ele.
4. **Completo** (10 min): as três topologias no mesmo atendimento.

## Gotchas

- **Supersteps criam barreira de sincronização.** Em fan-out, um ramo lento
  segura os outros até o fim do superstep. Ramo com várias etapas encadeadas
  deve virar um executor só, senão o paralelismo rende menos do que parece.
- **Ramo paralelo não enxerga o irmão.** A consolidação é etapa separada,
  exatamente como na versão ADK.
- **Concorrência multiplica TPM.** Três ramos simultâneos batem no rate limit
  do deployment. Em Azure, isso é cota por deployment, e é a causa mais comum
  de erro 429 em demo ao vivo.
- **Loop sem limite é fatura.** Condição de parada mais teto de iterações, sempre.
- **Checkpointing existe e resolve processo longo.** Workflow com checkpoint
  sobrevive a reinício do host. É o que viabiliza atendimento que espera
  aprovação humana por horas.
