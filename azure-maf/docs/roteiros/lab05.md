# Lab 05 — Promovido a líder de equipe

**60 min** · precisa do modelo, da API de rede e do Toolbox

> Material transversal em [`../CONDUCAO_LAB_A_LAB.md`](../CONDUCAO_LAB_A_LAB.md).

---

## A falha que abriu este lab

Um agente, três assuntos, nenhuma especialidade. Cobrança, suporte técnico e
agendamento no mesmo prompt, com o cardápio inteiro na mão — inclusive a tool de
escrita. Ele mistura os assuntos e trata na ordem errada.

---

## Preparação

```bash
docker compose -f docker-compose.azure-db.yml up -d
python -m lab05_handoff.agent           # handoff
python -m lab05_handoff.agent --tools   # agentes como ferramentas
```

**A frase do lab é de dois assuntos ao mesmo tempo:**

> "minha fatura venceu e o roteador está piscando vermelho. CPF 444.555.666-77"

Esse CPF é do **Wellington**: contrato suspenso, três faturas vencidas de
R$ 69,90 (total R$ 209,70), e — importante — **o CEP dele não tem incidente de
rede**. A base foi montada para essa frase.

> **Não troque o CPF.** Com a Marcela, o agente acha o incidente de rede e a
> lição de "cobrança antes de técnico" evapora.

---

## Parte 1 — Handoff (15 min)

```
[ari_coordenador] CPF recebido. Como há fatura vencida e problema no roteador,
                  vou direcionar primeiro para o time de cobrança.
                  Encaminhando para o especialista de cobrança.
```

> **Fala.** O coordenador não respondeu ao cliente: ele escolheu quem responde.

E o detalhe que confunde:

> **Fala.** Repare que parou aí. Handoff **transfere a conversa**: o especialista
> assume e o coordenador sai de cena, e o workflow fica esperando a próxima fala
> do cliente. Uma etapa só na tela é o comportamento correto, não um travamento.

Com a sala do Habbo aberta: Felipe fala, Bruno e Carla acendem.

---

## Parte 2 — Agentes como ferramentas (15 min)

```bash
python -m lab05_handoff.agent --tools
```

```
Há 3 faturas em aberto: 06/2026, 07/2026 e 08/2026, R$ 69,90 cada.
Com o contrato suspenso, é normal o roteador piscar vermelho.
```

> **Fala.** Mesma frase do cliente, mesmos especialistas, duas topologias. No
> handoff, duas vozes em sequência. Aqui, uma voz só: o maestro consultou os dois
> por baixo e costurou. Repare que ele **ligou a suspensão à luz vermelha** — isso
> é o consolidador fazendo o trabalho que o handoff deixaria para o cliente fazer.

A pergunta de desenho, e vale escrever no quadro:

> **Fala.** O especialista precisa **conversar** com o cliente, ou precisa
> **devolver informação**? Se conversa, handoff. Se devolve, `as_tool`.

---

## Parte 3 — Description é o roteador (20 min)

> **Edição ao vivo.** `lab05_handoff/especialistas.py`, linha ~36:
>
> ```python
> DESC_TECNICO = "Agente técnico."        # era o parágrafo de três linhas
> ```

Rode os dois modos de novo, com a mesma frase.

> **Fala.** O roteamento desandou, e nenhuma linha de lógica mudou. O texto que
> descreve um especialista é o que decide o roteamento — nos dois frameworks, com
> qualquer modelo. Escrever essas descrições é trabalho de arquitetura, não de
> redação.

É a mesma lição do lab 03, um nível acima: lá a description decidia se a **tool**
era chamada; aqui decide se o **agente** é acionado.

> **Desfazer.** Restaure o texto original. O lab 06 monta os mesmos especialistas,
> e com a description mutilada o pipeline concorrente devolve JSON incompleto — o
> sintoma aparece um lab depois da causa.

---

## Parte 4 — Isolamento de tools (10 min)

Mostre no `especialistas.py` que cada agente recebe a sua conexão MCP, e que o
de cobrança não tem as tools técnicas.

> **Fala.** O que aconteceria se todos recebessem o cardápio inteiro? E antes de
> responderem: por que uma instruction dizendo "não use essa tool" não é controle?

Espere. A resposta é o ponto:

> **Fala.** Porque não é você quem executa a instruction. Isolamento de tools é
> arquitetura; instruction proibindo uso é torcida.

Se a UI estiver no ar, esta é a melhor demo do lab: abra o `agente_cobranca` no
DevUI e pergunte sobre luz vermelha no roteador. Ele não tem a tool e não tem
como inventar.

---

## Parte 5 — O limite da delegação por LLM (10 min)

Rode a mesma frase dez vezes e anote a ordem num flipchart.

> **Fala.** Variou. Mesmo com a instruction mandando tratar cobrança primeiro.
> Roteamento por LLM é probabilístico, e regra de compliance não pode ser
> probabilística. Quando a ordem é obrigatória, ela não mora no prompt: mora na
> topologia.

Este é o gancho direto do lab 06 — e também do lab 08, onde essa mesma variação
vira a razão de existir o `--repeticoes`.

---

## Perguntas que a turma faz aqui

**"Handoff ou as_tool, na prática?"**
Comece por `as_tool`. Ele é mais fácil de controlar, dá uma resposta só, e o
trace mostra as consultas internas. Handoff entra quando o especialista precisa
conduzir a conversa, e aí você herda o problema de quem devolve o cliente.

**"Quantos especialistas são demais?"**
O limite prático é a qualidade das descriptions. Com muitas, elas começam a se
sobrepor e o roteamento degrada. Se dois especialistas precisam de uma frase para
se distinguir, provavelmente são um.

**"Dá para aninhar maestros?"**
Dá, e o custo cresce rápido: cada nível é mais uma chamada de modelo e mais uma
oportunidade de o contexto se perder. Trate profundidade como custo.

---

## Se der errado

| Sintoma | Causa | Saída |
|---|---|---|
| `Handoff workflows require ... history_persistence` | participante sem a flag | `require_per_service_call_history_persistence=True` em todos |
| Tool "some" em runtime | especialista criado fora do `async with` | eles nascem dentro do `montar_especialistas` |
| Só uma etapa na tela | é o handoff esperando o cliente | comportamento correto |
| Roteia sempre para o mesmo | descriptions se sobrepõem | é a parte 3 acontecendo sozinha |

---

## O gancho

A ordem varia. A instruction manda tratar cobrança primeiro, e às vezes ele trata.
Quando a ordem é obrigatória, prompt não basta.

→ [Lab 06](lab06.md)
