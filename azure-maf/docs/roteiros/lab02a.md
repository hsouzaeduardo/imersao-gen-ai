# Lab 02a — O caderno de anotações

**50 min** · precisa do modelo · Redis opcional, e é ele que faz a demo

> Material transversal em [`../CONDUCAO_LAB_A_LAB.md`](../CONDUCAO_LAB_A_LAB.md).

---

## A falha que abriu este lab

O ARI esquece o CPF do turno anterior. Sem `AgentSession`, cada `run` é uma
conversa nova: existem três monólogos, não um atendimento.

---

## Preparação

```bash
python -m lab02_memoria.a_thread
python -m lab02_memoria.a_thread --continuar
```

Para a parte 3, o Redis precisa estar no ar e `REDIS_URL` preenchido:

```bash
docker compose -f docker-compose.azure-db.yml up -d redis
docker exec -it aurora-redis redis-cli PING     # tem que responder PONG
```

No `.env`: `REDIS_URL=redis://localhost:6379` (local) ou
`rediss://<nome>.redis.azure.net:10000` com `REDIS_PASSWORD` (Azure Cache).

---

## Parte 1 — Com sessão, ele acompanha (10 min)

A primeira execução tem três falas. Na terceira o cliente diz "além disso, ontem
caiu tudo por umas duas horas", e o ARI responde acumulando:

```
ARI: Entendi. Vou incluir também que ontem a conexão ficou totalmente
     indisponível por cerca de 2 horas.
```

> **Fala.** Comparem com o lab 01. A mudança no código são duas linhas:
> `create_session`, e passar `session=` em cada `run`. A palavra "também" nessa
> resposta é a sessão funcionando.

Mostre as duas linhas no arquivo:

```python
sessao = agente.create_session(session_id="aurora:atendimento:001")
resposta = await agente.run(fala, session=sessao)
```

> **Fala.** Repare no `session_id` fixo. É ele que faz o `--continuar` reencontrar
> a conversa. Em produção esse id vem do protocolo de atendimento, não de uma
> constante no código.

---

## Parte 2 — Sem Redis, morre com o processo (15 min)

Deixe `REDIS_URL` vazio no `.env` e rode com `--continuar`.

> **Fala.** Processo novo, sessão nova, cliente novo. Para ele, essa pessoa nunca
> ligou. Em desenvolvimento isso não incomoda porque o processo fica de pé. Em
> produção, com três réplicas atrás de um balanceador, o cliente troca de
> atendente a cada frase.

Vale desenhar no quadro: três caixas de processo, uma sessão dentro de cada.

---

## Parte 3 — Com Redis, sobrevive (20 min)

Preencha `REDIS_URL`, rode sem `--continuar`, depois com.

> **Fala.** Mesmo código. O que mudou foi um `context_providers` apontando para o
> Redis. A sessão deixou de morar na memória do processo e passou a morar num
> lugar que as três réplicas enxergam.

Agora abra o banco e mostre o que está gravado:

```bash
docker exec -it aurora-redis redis-cli KEYS '*'
docker exec -it aurora-redis redis-cli LRANGE <a chave que apareceu> 0 -1
```

> **Fala.** Olhem o que está gravado: as mensagens, cruas. Não tem mágica, não tem
> embedding, não tem índice. Memória de conversa é uma lista de mensagens num
> banco, e quem escolhe o banco é você.

**Esse momento é o mais valioso do lab.** Ele mata a ideia de que memória de
agente é uma capacidade cognitiva do modelo.

---

## Detalhe que vale mostrar no código

O lab **testa a conexão antes** de usar o Redis:

```python
redis_sync.from_url(url, socket_connect_timeout=2).ping()
```

> **Fala.** Repare que ele não confia na variável estar preenchida. Em sala o
> container cai, e um agente que estoura no meio da demo ensina menos que um que
> avisa e segue. Isso não é capricho: é a mesma decisão do lab 03 sobre o que uma
> tool devolve quando a dependência some.

---

## Perguntas que a turma faz aqui

**"Qual a diferença para o `state` do ADK?"**
Não existe `state` no MAF. O que existe é histórico de mensagens mais context
providers. Dado estruturado do atendimento vira armazenamento seu — é o lab 02b.
Esta é a lacuna que mais dá trabalho ao portar um agente de ADK para MAF.

**"O histórico cresce para sempre?"**
Cresce, e vira custo de token em todo turno. O framework tem
`compaction_strategy` para isso. Mencione, não demonstre: é assunto do dia
seguinte em projeto real, não de aula introdutória.

**"Dá para usar Cosmos DB em vez de Redis?"**
Dá. A troca é a mesma linha do `context_providers`. O argumento de escolha é
latência contra durabilidade, e não capacidade.

---

## Se der errado

| Sintoma | Causa | Saída |
|---|---|---|
| `--continuar` não lembra | Redis fora do ar | o lab avisa no começo; suba o container |
| timeout sem mensagem clara | Azure Cache exige TLS e porta 10000 | a URL começa com `rediss://` |
| `PONG` não responde | container não subiu | `docker compose ... up -d redis` |

Se o Redis não subir, você perde a parte 3 e não perde a aula. O lab cai para
memória de processo e avisa.

---

## O gancho

Ele lembra da conversa de hoje. Mas o atendimento de amanhã começa do zero — e
"prefiro visita de manhã" não é uma informação de hoje.

→ [Lab 02b](lab02b.md)
