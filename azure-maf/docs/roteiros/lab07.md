# Lab 07 — O agente que não é seu

**45 min** · precisa do modelo e de **dois terminais** · não usa Toolbox nem API de rede

> Material transversal em [`../CONDUCAO_LAB_A_LAB.md`](../CONDUCAO_LAB_A_LAB.md).

---

## A falha que abriu este lab

Todos os agentes eram seus. No lab 05 eles viraram especialistas, no 06 viraram um
processo — e os sete moravam no mesmo `requirements.txt`. Na Aurora real o
especialista técnico pertence a Operações de Rede: versiona sozinho, sobe quando
quer, pode nem ser Python.

---

## Preparação

**Terminal 1**, o "outro time":

```bash
python -m uvicorn lab07_a2a.servidor:app --port 9000
curl http://localhost:9000/.well-known/agent-card.json
```

**Terminal 2**, você:

```bash
python -m lab07_a2a.agent --card
python -m lab07_a2a.agent --direto
python -m lab07_a2a.agent
```

Os dois terminais precisam do venv ativado e rodar da raiz do projeto.

---

## Parte 1 — A descoberta (15 min)

Rode `--card` **antes** de mostrar qualquer código.

```
nome:       especialista_tecnico_aurora
descrição:  Diagnostica problemas de conexão da Aurora Fibra: lentidão,
            oscilação, queda de sinal... Não trata cobrança nem agendamento.
versão:     1.0.0
skill:      diagnostico_conexao — Classifica o problema e indica o próximo passo.
```

> **Fala.** Isto é tudo o que o outro time te entregou: um nome, uma descrição,
> uma versão e uma lista de habilidades. Sem código, sem biblioteca, sem acordo de
> linguagem.

E a observação que amarra o curso:

> **Fala.** Repare no formato — nome, descrição, o que entra e o que sai. É a
> mesma estrutura da tool do lab 03, e pelo mesmo motivo: a descrição é o que
> decide se vão te consultar.

Aponte a frase "Não trata cobrança nem agendamento":

> **Fala.** Escopo declarado no cartão. É o isolamento de tools do lab 05, agora
> atravessando a fronteira do time.

---

## Parte 2 — A chamada crua (10 min)

```bash
python -m lab07_a2a.agent --direto
```

> **Fala.** Esse `run` é idêntico ao de um agente local. A única pista de que ele
> atravessou a rede é a latência.

Mostre o código:

```python
remoto = A2AAgent(name="tecnico_aurora", url="http://localhost:9000", description="...")
r = await remoto.run(pergunta)
```

---

## Parte 3 — O participante externo (20 min)

Rode o modo padrão com o `lab05_handoff/agent.py` aberto ao lado.

```python
Agent(cliente, INSTRUCTION, tools=[
    remoto.as_tool(name="consultar_tecnico", description="..."),
])
```

> **Fala.** A linha do `as_tool` é a mesma do lab 05. Byte a byte. O que mudou foi
> onde o especialista mora, e o maestro não tem como saber.

E a simetria que fecha o desenho do curso — vale desenhar no quadro:

| | Fronteira | Antes | Depois |
|---|---|---|---|
| Lab 04 | acesso a **dado** | o agente fala com o banco | fala com um servidor MCP |
| Lab 07 | acesso a **agente** | você importa o especialista | fala com um endpoint A2A |

> **Fala.** É o mesmo movimento, um nível acima. Nos dois casos o outro lado passa
> a ter ciclo de vida próprio, e o contrato deixa de ser código compartilhado.

---

## Parte 4 — Derrube o outro time (15 min)

Pare o terminal 1 e rode de novo.

> **Fala.** Agora o especialista é uma dependência de rede, com tudo o que isso
> implica: timeout, retry, versão, janela de manutenção, e alguém de plantão que
> não é você. Foi exatamente isso que vocês compraram ao parar de importar a
> classe dele.

E a pergunta de arquitetura, que é o fechamento do lab:

> **Fala.** A pergunta não é se A2A é melhor. É se essa fronteira já existe na
> organização de vocês. Se existe, o protocolo só a torna honesta.

**Variação opcional:** troque a `description` do `CARTAO` em `servidor.py` por
"Agente técnico.", reinicie **só o servidor**, e veja o maestro deixar de
consultar. É a terceira vez que a mesma lição aparece — labs 03, 05 e agora 07 —
e é de propósito.

> **Desfazer.** Restaure a descrição do cartão.

---

## Perguntas que a turma faz aqui

**"Qual a diferença entre MCP e A2A?"**
MCP publica **tools** para um agente usar. A2A publica **um agente** para outro
agente conversar. A pergunta que separa: o outro lado precisa raciocinar, ou só
executar? Quem tem uma query publica MCP. Quem tem julgamento, instruction e
tools próprias publica A2A.

**"E a autenticação?"**
Ficou de fora deste lab de propósito, e o README diz isso. O `A2AAgent` aceita
`auth_interceptor`, e em produção esse parâmetro não é opcional: um endpoint A2A
aberto é um agente seu respondendo para qualquer um, com a sua cota.

**"Isso não é só uma API REST com outro nome?"**
É uma API REST com um contrato padronizado para agentes: descoberta pelo agent
card, formato de mensagem, e tarefas de longa duração. O ganho é o mesmo do MCP:
não negociar formato a cada integração.

---

## Se der errado

| Sintoma | Causa | Saída |
|---|---|---|
| "Não consegui ler o cartão" | terminal 1 não está de pé | suba o servidor |
| Conecta mas responde errado | `url` apontando para o cartão | o `url` é a raiz; a lib acrescenta o caminho |
| Cliente vai para o lugar errado | `url` dentro do cartão | ajuste `A2A_TECNICO_URL` no `.env` |
| `ImportError` no `a2a` | versão do SDK | `A2AStarletteApplication` não existe na 1.1.4; use as rotas |

---

## O gancho

Sete labs, e toda a validação foi alguém olhando uma execução e achando boa.
"Funcionou na demo" não é evidência.

→ [Lab 08](lab08.md)
