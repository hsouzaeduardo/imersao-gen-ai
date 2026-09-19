# UI: todos os agentes do curso no DevUI

```bash
python -m ui                 # http://localhost:8080
python -m ui --port 9090
```

O `agent-framework-devui` é a UI de desenvolvimento do MAF: lista agentes, abre
um chat com cada um e mostra o trace da chamada. É o equivalente ao `adk web` do
laboratório em Google, e é por isso que ele está aqui — quem faz os dois cursos
reconhece a tela.

Este módulo não reimplementa nada. Com tudo no ar são **22 entidades**.

## O que aparece na tela

| Lab | Entidades |
|---|---|
| 01 | `ari_n1` |
| 02a | `ari_com_caderno` |
| 02b | `ari_com_prontuario` |
| 03 | `ari_com_acesso` (com o guardrail de verdade) |
| 04 | `ari_com_dados` |
| 05 | `agente_cobranca`, `agente_tecnico`, `agente_agendamento`, `ari_maestro` |
| 06 | os 9 papéis, mais `pop_sequencial` e `checagens_concorrentes` |
| 07 | `tecnico_aurora` (outro processo), `ari_maestro_a2a` |

## Os agentes vêm dos labs, não de cópias

Deste arquivo, quase nada. `montar_especialistas` vem do lab 05,
`montar_papeis` e os pipelines do lab 06, as tools do prontuário do lab 02b, o
`guardrail_acao_destrutiva` do lab 03, o `tecnico_remoto` do lab 07. Só as quatro
instructions dos labs 01 a 04 entram por constante, porque lá elas moram dentro
do `main()`.

Isso é deliberado: se a UI tivesse cópias das instructions, editar um lab em aula
deixaria a UI mostrando a versão velha, e a turma veria dois agentes diferentes
com o mesmo nome. **Mexeu no lab, mexeu na UI.**

## Workflow na lista

O DevUI reconhece workflow como entidade — ele testa se o objeto tem
`get_executors_list`. Mas um `Workflow` não tem `name`, e apareceria na lista
como "Workflow Workflow". Por isso os pipelines do lab 06 entram via
`.as_agent(nome, description=...)`, que os embrulha num agente com nome.

Funciona de verdade: chamar `pop_sequencial` na UI devolve as três etapas do POP
em sequência, cada uma com o seu JSON ou texto.

## Três demos que esta tela permite e o terminal não

**O esquecimento, lado a lado.** Abra `ari_n1` e `ari_com_caderno` e mande a
mesma sequência. Um esquece, o outro não, na mesma janela.

**Isolamento de tools visto de fora.** Abra `agente_cobranca` e pergunte sobre
luz vermelha no roteador. Ele não tem a tool e não tem como inventar. Depois
faça a mesma pergunta ao `agente_tecnico`.

**A etapa isolada.** Abra `checagem_financeira` sozinho e mande um CPF. Ele
responde JSON, porque é peça de pipeline e não atendente. É a melhor forma de
mostrar que "agente" no lab 06 não quer dizer "conversa".

## Serviço fora do ar

A UI sobe com o que der, e diz o que ficou de fora:

```
4 entidades registradas:
  · ari_n1
  · ari_com_caderno
  · ari_com_prontuario
  · ari_com_acesso

Fora do ar, e o que isso custou:
  · Toolbox (http://localhost:5000/mcp) — ficam de fora os labs 04, 05 e 06
```

Para ter as 22:

```bash
docker compose -f docker-compose.azure-db.yml up -d          # Toolbox + API de rede
python -m uvicorn lab07_a2a.servidor:app --port 9000         # o agente do lab 07
```

## Por que não `devui.serve()` direto

O `serve()` monta o servidor e bloqueia, e isso não serve aqui: metade dos
agentes segura conexões MCP, e conexão MCP precisa ficar aberta na **mesma task**
o tempo todo. Abrindo e fechando por chamada, o teardown estoura com
`Attempted to exit cancel scope in a different task` — funciona uma vez e vaza
depois.

Então o módulo monta o app com `DevServer.create_app()` e roda o uvicorn dentro
do próprio loop, com um `AsyncExitStack` segurando as conexões enquanto o
processo vive. É o mesmo motivo pelo qual o `lab07_a2a/servidor.py` não usa
`async with`: servidor não tem "fim do atendimento".

## Gotchas

- **Sem autenticação.** O módulo sobe com `auth_enabled=False`, ligado a
  `127.0.0.1`. É ferramenta de desenvolvimento: não exponha essa porta.
- **A sessão é da UI.** O `ari_n1` "esquece" dentro de um `run`, não entre as
  mensagens do chat — o DevUI mantém o histórico. Para ver o esquecimento cru do
  lab 01, o terminal continua sendo o lugar.
- **Porta ocupada mata em silêncio.** Se já houver algo na 8080, o processo morre
  sem mensagem visível e você acaba olhando uma UI antiga com os agentes de
  antes. Ao trocar de versão, confira que a lista impressa no terminal bate com
  o que a tela mostra.
- **Muitas conexões MCP.** Os especialistas do lab 05 e os papéis do lab 06 abrem
  cada um a sua, contra o mesmo Toolbox. É de propósito — isolamento de tools é
  arquitetura —, mas são várias conexões vivas enquanto a UI roda.
- **`--port` colide.** API de rede 8000, Toolbox 5000, A2A 9000, DevUI 8080.
