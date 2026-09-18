# Lab 03 (Azure + MAF): o primeiro acesso ao sistema

```bash
# API da Aurora local
docker compose -f docker-compose.local.yml up -d mock_api
# ou no Azure: AURORA_API_URL apontando para o Container App

python -m lab03_tool_externa.agent
```

## O que muda em relação ao ADK

| ADK | MAF |
|---|---|
| função Python com docstring e type hints | `@tool` com `Annotated[..., Field(description=...)]` |
| `before_tool_callback` | function middleware, com `MiddlewareTermination` |
| retorno `dict` lido pelo modelo | igual |
| limite de combinar built-in tools | no MAF depende do cliente: Responses e Foundry suportam tools hospedadas junto de function tools |

O contrato com o modelo é o mesmo nos dois frameworks: nome, descrição e
tipos dos parâmetros. Muda a sintaxe de declarar, não o conceito.

## Roteiro

1. **A descrição é o contrato** (20 min): em `comum/tools_rede.py`, troque a
   `description` de `consultar_status_rede` por "Consulta coisas" e rode a mesma frase.
   O modelo passa a chamar na hora errada ou não chamar.
2. **Ler versus agir** (20 min): rode o roteiro completo. A terceira fala pede
   reinício direto e o middleware bloqueia. Comente o `raise MiddlewareTermination(...)`
   e veja o roteador do cliente ser reiniciado sem confirmação nenhuma.
3. **Falha da dependência** (10 min): pare a API (`docker compose stop mock_api`).
   A tool devolve `indisponivel` e a instruction manda admitir. Sem isso,
   o modelo preenche a lacuna, que é o pior resultado possível.
4. **A falha planejada** (10 min): peça a fatura de agosto. Ele não tem como saber.

## Gotchas

- **Middleware tem três níveis no MAF**: agente, chamada ao modelo e invocação de tool.
  Guardrail de ação destrutiva é no nível de tool. Política de conteúdo é no nível
  de chat. Auditoria costuma ser no nível de agente.
- **A assinatura do middleware varia entre versões.** O contrato é `(context, next)`,
  mas `next` não recebe argumento: `await next()`, não `await next(context)`.
  E o decorator `@function_middleware` é obrigatório quando o arquivo tem
  `from __future__ import annotations`, porque aí as anotações viram string
  e a inferência de tipo do framework fica sem o que ler.
- **Aprovação humana existe nativa.** Para ações críticas em produção, o MAF tem
  fluxo de aprovação de tool, que é mais adequado do que este middleware caseiro.
  Vale mencionar em aula corporativa: a diferença entre bloquear e pedir aprovação.
- **Em regulado, esse middleware é o ponto de auditoria.** Todo efeito colateral
  passa por ali, e é ali que você registra quem autorizou o quê.
