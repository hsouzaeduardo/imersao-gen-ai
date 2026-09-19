# Lab 03 — O primeiro acesso ao sistema

**60 min** · precisa do modelo e da API de rede

> Material transversal em [`../CONDUCAO_LAB_A_LAB.md`](../CONDUCAO_LAB_A_LAB.md).

---

## A falha que abriu este lab

O ARI lembra de tudo e não sabe de nada. Nenhum sistema da Aurora está ao alcance
dele, e agente sem dado corporativo é demonstração, não atendimento.

---

## Preparação

```bash
docker compose -f docker-compose.azure-db.yml up -d mock_api
curl http://localhost:8000/health            # {"status":"ok",...}
python -m lab03_tool_externa.agent
```

Sem Docker:

```bash
python -m uvicorn mock_api.main:app --port 8000
```

**Dados deste lab:** o CEP `06010-100` (Marcela) tem incidente de severidade
média, degradação de OLT, 1.840 afetados. O `06110-045` (Priscila) tem incidente
alto. Qualquer outro CEP responde `normal`.

---

## Parte 1 — O agente com acesso (10 min)

Primeira fala: "minha internet está lenta. CEP 06010-100". Ele consulta o painel
e acha o incidente na OLT Osasco Centro.

> **Fala.** Primeira vez no curso que ele fala de um dado que não estava na
> pergunta. Uma função Python decorada com `@tool`, e o contrato com o modelo é o
> nome, a descrição e os tipos dos parâmetros. Mais nada.

Mostre o decorator em `comum/tools_rede.py`:

```python
@tool(
    name="consultar_status_rede",
    description=("Consulta o painel de rede da Aurora e retorna a situação de um CEP. "
                 "Use sempre que o cliente relatar lentidão, oscilação ou falta de "
                 "conexão, antes de qualquer diagnóstico. Não use para cobrança."),
)
```

> **Fala.** Repare na última frase: "não use para cobrança". Descrição de tool
> também serve para dizer quando NÃO chamar.

---

## Parte 2 — A descrição é o contrato (20 min)

> **Edição ao vivo.** `comum/tools_rede.py`, linha ~24:
>
> ```python
> description=("Consulta coisas"),        # era o parágrafo inteiro
> ```

Rode a mesma frase de novo.

> **Fala.** O código da tool não mudou nenhum caractere. O que mudou foi a frase
> que descreve ela, e agora ele chama na hora errada, ou não chama. Essa descrição
> não é documentação para humano. É o único material que o modelo tem para
> decidir. Quando a tool de vocês não é chamada, o problema quase nunca está no
> código dela.

> **Desfazer.** Restaure o texto original. Essa tool é usada também nos labs 04,
> 05, 06 e na UI — deixar "Consulta coisas" quebra o agente técnico do lab 05 de
> um jeito que não parece ter relação com o que você mexeu.

---

## Parte 3 — O guardrail (15 min)

Terceira fala do roteiro: "reinicia meu roteador agora, CPF 111.222.333-44".

```
Cliente:    reinicia meu roteador agora
middleware: bloqueado — sem autorização registrada
ARI:        ...antes preciso da sua autorização explícita.
```

> **Fala.** Ele pediu direto, e não aconteceu. O middleware interceptou antes da
> execução e devolveu ao modelo um resultado dizendo que foi bloqueado. O modelo
> lê isso como qualquer outro retorno de tool e volta a pedir confirmação. Repare
> onde mora a política: não está na instruction. Instruction o modelo pode
> ignorar, e num dia ruim vai.

> **Edição ao vivo.** `lab03_tool_externa/agent.py`: comente o
> `raise MiddlewareTermination(...)` e rode de novo. O roteador do cliente é
> reiniciado sem confirmação nenhuma.

> **Fala.** Essa é a diferença entre pedir e garantir. Em ambiente regulado, esse
> middleware é o ponto de auditoria: todo efeito colateral passa por ali, e é ali
> que se registra quem autorizou o quê.

> **Desfazer.** Descomente. É o mais fácil de esquecer, porque o lab continua
> "funcionando" sem o guardrail — só que a política sumiu, e o lab 08 vai acusar.

**Detalhe de implementação que vale citar:** o middleware precisa do decorator
`@function_middleware`, porque o arquivo tem `from __future__ import annotations`
e isso transforma as anotações em string, deixando a inferência de tipo do
framework sem o que ler. E o `next` **não recebe argumento**: é `await next()`.

---

## Parte 4 — A dependência cai (10 min)

```bash
docker compose -f docker-compose.azure-db.yml stop mock_api
```

Rode de novo.

> **Fala.** A tool devolve `indisponivel` e a instruction manda admitir. Sem esse
> caminho, o modelo preenche a lacuna com o que soa plausível, que é o pior
> resultado possível: errado e confiante. Toda tool de vocês precisa de um retorno
> para o caso de falha, escrito para o modelo ler.

Mostre o `except httpx.ConnectError` no arquivo — a mensagem de erro é escrita
em português, para o modelo, e não é um stack trace.

Suba a API de novo antes de seguir.

---

## Parte 5 — A falha planejada (5 min)

Peça a fatura de agosto. Ele não tem como saber.

> **Fala.** O painel de rede não sabe de fatura. E a pergunta que abre o próximo
> lab não é técnica, é organizacional: quem entrega acesso a banco de produção
> para um agente, e em que formato?

**Segure a pergunta no ar** antes de encerrar o bloco.

---

## Perguntas que a turma faz aqui

**"Middleware em qual nível?"**
Três no MAF: agente, chamada ao modelo e invocação de tool. Guardrail de ação
destrutiva é no nível de tool. Política de conteúdo é no nível de chat. Auditoria
costuma ser no nível de agente.

**"Não seria melhor aprovação humana?"**
Seria, e o MAF tem fluxo nativo de aprovação de tool. Este middleware caseiro
existe para mostrar o mecanismo. Em produção, a diferença entre bloquear e pedir
aprovação é de produto.

**"E se o modelo chamar a tool com argumento errado?"**
O middleware vê os argumentos antes da execução: `context.arguments`. Validar ali
é o mesmo padrão de validar entrada numa API.

---

## Se der errado

| Sintoma | Causa | Saída |
|---|---|---|
| "não consegui consultar o status da rede" | API fora do ar, ou `AURORA_API_URL` errado | `curl localhost:8000/health` |
| `TypeError` no middleware | `await next(context)` em vez de `await next()` | o `next` não recebe argumento |
| `MiddlewareException: cannot determine type` | falta o `@function_middleware` | o decorator é obrigatório aqui |

---

## O gancho

Fatura, contrato, chamado e agenda estão no banco. E o agente não tem a chave.

→ [Lab 04](lab04.md)
