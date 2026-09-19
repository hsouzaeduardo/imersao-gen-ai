# Lab 06 — O processo operacional

**70 min** · precisa do modelo, da API de rede e do Toolbox

> Material transversal em [`../CONDUCAO_LAB_A_LAB.md`](../CONDUCAO_LAB_A_LAB.md).

---

## A falha que abriu este lab

Roteamento por LLM é probabilístico. Dez execuções da mesma frase, ordens
diferentes, mesmo com a instruction mandando tratar cobrança primeiro. Regra de
compliance não pode ser probabilística.

---

## Preparação

```bash
docker compose -f docker-compose.azure-db.yml up -d

python -m lab06_workflows.run sequencial
python -m lab06_workflows.run concorrente
python -m lab06_workflows.run comparar
python -m lab06_workflows.run loop
python -m lab06_workflows.run completo
```

O caso fixo do lab usa o Wellington (`44455566677`): contrato suspenso, três
faturas vencidas, rede normal.

---

## Parte 1 — Ordem fixa (15 min)

```bash
python -m lab06_workflows.run sequencial
```

Triagem → diagnóstico → registro, sempre nessa ordem.

> **Fala.** Não tem modelo decidindo a sequência. Quando o processo é obrigatório,
> tirar a decisão do LLM não é limitação: é o requisito.

Nota para quem vem do ADK, e vale dizer explicitamente:

> **Fala.** Não existe `output_key` aqui. No ADK cada etapa gravava numa chave e a
> seguinte lia com `{chave}`. No `SequentialBuilder`, o que trafega é a conversa
> acumulada — por isso as instructions deste lab dizem "use o que veio na conversa
> acima" em vez de interpolar variável. Para estado estruturado entre etapas, o
> caminho é shared state do workflow ou executores próprios.

---

## Parte 2 — Paralelo (15 min)

```bash
python -m lab06_workflows.run concorrente
```

As três verificações rodam juntas e o agregador junta:

```json
{"bloqueio_financeiro":true,"faturas_vencidas":3,...}
{"incidente_regiao": false, "severidade": "nenhuma", ...}
{"reincidente":true,"chamados_90d":1,...}
```

> **Fala.** As três checagens não dependem uma da outra, então não há motivo para
> esperar. O `ConcurrentBuilder` já monta o dispatcher, o fan-out e o fan-in. No
> ADK isso era o `ParallelAgent`.

Com a sala do Habbo aberta, esta é a melhor demo visual do curso: Diego, Elisa e
Fábio acendem **ao mesmo tempo**, cada um com a sua consulta.

Repare que cada checagem responde **JSON**, não conversa. Vale dizer:

> **Fala.** Estes não são atendentes, são peças de pipeline. "Agente" aqui não
> quer dizer "conversa".

---

## Parte 3 — O cronômetro (20 min)

```bash
python -m lab06_workflows.run comparar
```

```
Sequencial:  12,8s
Concorrente:  7,4s
Ganho:        1,7x
```

Este é o único momento do curso em que vale assistir em silêncio — o número é a
demo.

> **Fala.** 1,7 vez mais rápido. Agora a outra metade da conta: vocês fizeram o
> mesmo número de chamadas ao modelo, no mesmo intervalo, em vez de espalhadas.
> Latência caiu, custo não mudou, e pressão de cota triplicou no mesmo instante.

E o momento que vale provocar:

> **Fala.** Numa turma de 30 pessoas rodando isto ao mesmo tempo, o deployment
> estoura TPM. Se estourar agora, ao vivo, melhor ainda: é a aula acontecendo
> sozinha.

**Os números variam** com a latência do deployment. A ordem de grandeza, não.

---

## Parte 4 — Loop (15 min)

```bash
python -m lab06_workflows.run loop
```

O rascunho entra cheio de jargão — "degradação de OLT", "LOS do ONU" — e sai em
português de gente:

```
[aprovada em 3 iteração(ões)]
Identificamos instabilidade em um equipamento da nossa rede na sua região...
```

> **Fala.** No MAF não existe `LoopAgent`. O loop é seu, em Python, ou um ciclo no
> grafo do `WorkflowBuilder`. E olhem a condição de parada: um crítico aprovando.
> Todo loop com LLM precisa de um teto de iterações, porque a condição de saída é
> opinião.

Se travar no teto, é conteúdo e não defeito: o crítico está exigente demais.

---

## Parte 5 — Tudo junto (15 min)

```bash
python -m lab06_workflows.run completo
```

Concorrente para levantar o caso, sequencial para conduzir o processo, loop para
revisar a resposta.

> **Fala.** Três topologias no mesmo atendimento, cada uma onde faz sentido. Não
> existe "o padrão certo": existe a pergunta certa, que é o que precisa ser
> determinístico e o que é julgamento.

---

## Perguntas que a turma faz aqui

**"Quando usar workflow em vez de multiagente?"**
Quando a ordem é requisito. Se o processo está escrito num POP que alguém assina,
ele não pode depender de o modelo escolher bem naquele turno.

**"O paralelo não fica mais barato?"**
Não. Fica mais rápido. Mesmo número de tokens, distribuídos em menos tempo — e
é isso que estoura cota. Latência e custo são eixos diferentes.

**"Dá para retomar um workflow interrompido?"**
Dá: o MAF tem checkpoint e hidratação, e o ADK não. É uma das coisas que o
`WorkflowBuilder` faz e a árvore de agentes do ADK não faz.

---

## Se der errado

| Sintoma | Causa | Saída |
|---|---|---|
| `429` / cota estourada | TPM do deployment | é conteúdo; espere e rode de novo |
| JSON incompleto nas checagens | alguma description foi mutilada no lab 05 | `git diff` |
| Saída picada, ilegível | helper de eventos filtrando errado | `comum/workflow_utils.py` acumula deltas por executor |
| Loop sempre no teto | crítico exigente | conteúdo: a condição de saída é opinião |

---

## O gancho

Todos os agentes são seus: no seu processo, no seu `requirements.txt`, no seu
deploy. O especialista real é de outro time.

→ [Lab 07](lab07.md)
