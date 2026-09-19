# Lab 07 (Azure + MAF): o agente que não é seu

```bash
# terminal 1: o outro time
python -m uvicorn lab07_a2a.servidor:app --port 9000

# terminal 2: você
python -m lab07_a2a.agent --card      # descoberta: o contrato publicado
python -m lab07_a2a.agent --direto    # fala direto com o agente remoto
python -m lab07_a2a.agent             # o maestro do lab 05, com um participante externo
```

## A falha que abriu este lab

No lab 05 o ARI ganhou três especialistas, e no 06 eles viraram um processo.
Todos eram **seus**: no seu processo, no seu `requirements.txt`, no seu deploy.

Na Aurora real, o especialista técnico pertence ao time de Operações de Rede.
Versiona sozinho, sobe quando quer, e pode nem ser Python. Você não tem como
`import` a classe dele, e pedir para ele virar uma biblioteca no seu repositório
é pedir para dois times passarem a subir junto.

## A simetria com o lab 04

É o mesmo movimento, um nível acima:

| | Fronteira | Antes | Depois |
|---|---|---|---|
| Lab 04 | acesso a **dado** | o agente fala com o banco | o agente fala com um servidor MCP |
| Lab 07 | acesso a **agente** | você importa o especialista | você fala com um endpoint A2A |

Nos dois casos o ganho é o mesmo: a coisa do outro lado passa a ter ciclo de vida
próprio, e o contrato deixa de ser código compartilhado.

## O que muda no código

Nada, e esse é o ponto.

```python
remoto = A2AAgent(name="tecnico_aurora", url="http://localhost:9000", description="...")

maestro = Agent(cliente, INSTRUCTION, tools=[
    remoto.as_tool(name="consultar_tecnico", description="..."),
])
```

`A2AAgent` expõe `run`, `create_session` e `as_tool` — a mesma superfície de um
agente local. A linha do `as_tool` é idêntica à do lab 05. O maestro não tem como
saber que o especialista atravessou a rede, e é justamente isso que você quer.

## O agent card é o contrato

```
GET /.well-known/agent-card.json
```

```json
{
  "name": "especialista_tecnico_aurora",
  "description": "Diagnostica problemas de conexão da Aurora Fibra: lentidão,
                  oscilação, queda de sinal... Não trata cobrança nem agendamento.",
  "version": "1.0.0",
  "skills": [{ "id": "diagnostico_conexao", "description": "..." }]
}
```

É tudo o que você recebe do outro time. Sem código, sem biblioteca, sem acordo de
linguagem. Repare no formato: nome, descrição, e o que entra e sai — a mesma
estrutura da tool do lab 03, e pelo mesmo motivo. **A descrição é o que decide se
o agente vai ser consultado**, aqui como lá.

Note também a frase `Não trata cobrança nem agendamento`. Escopo declarado no
cartão é o equivalente A2A do isolamento de tools do lab 05.

## Roteiro

1. **Descoberta** (10 min): rode `--card` antes de qualquer código. É o momento em
   que o agente remoto deixa de ser uma URL e vira uma capacidade com contrato.
   Mostre que nada ali revela implementação.
2. **A chamada crua** (10 min): rode `--direto`. O `run` é idêntico ao de um agente
   local; a única pista de que atravessou a rede é a latência.
3. **O participante externo** (20 min): rode o modo padrão e ponha lado a lado com
   o `lab05_handoff/agent.py --tools`. A linha do `as_tool` é a mesma.
4. **Derrube o servidor** (10 min): pare o terminal 1 e rode de novo. Agora o
   especialista é uma dependência de rede, com tudo o que isso implica.
5. **Edite a description do cartão** (10 min): troque por "Agente técnico." em
   `servidor.py`, reinicie **só o servidor**, e veja o maestro deixar de consultar.
   Mesma lição do lab 03 e do lab 05, agora atravessando a fronteira do time.

## Gotchas

- **O `url` do `A2AAgent` é a raiz, não o caminho do cartão.** A biblioteca acrescenta
  `/.well-known/agent-card.json` sozinha. Apontar para o cartão direto não conecta.
- **O `url` dentro do cartão precisa ser o endereço público real.** No `servidor.py`
  ele vem de `A2A_TECNICO_URL`. Se o servidor está atrás de um proxy ou num Container
  App, o `localhost:9000` do default manda o cliente para o lugar errado.
- **Sem `async with` no servidor.** Nos outros labs a credencial vive dentro de um
  bloco, porque o atendimento acaba. Um servidor não acaba: a credencial vive
  enquanto o processo vive.
- **A2A não é MCP.** MCP publica *tools* para um agente usar; A2A publica *um agente*
  para outro agente conversar. Quem tem uma query publica MCP. Quem tem julgamento,
  instruction e tools próprias publica A2A. A pergunta que separa: o outro lado
  precisa raciocinar, ou só executar?
- **Autenticação fica de fora deste lab.** O `A2AAgent` aceita `auth_interceptor`, e
  em produção esse parâmetro não é opcional: um endpoint A2A aberto é um agente seu
  respondendo para qualquer um, com a sua cota.
- **Versões em movimento.** O `a2a-sdk` mudou o caminho do servidor entre releases —
  nesta versão são `create_agent_card_routes` e `add_a2a_routes_to_fastapi`, e material
  mais antigo mostra `A2AStarletteApplication`, que não existe mais aqui. O
  `requirements.txt` fixa as duas versões por isso.
