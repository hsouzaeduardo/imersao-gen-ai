"""
DevUI com TODOS os agentes do curso.

    python -m ui
    python -m ui --port 8080

Abre em http://localhost:8080 e lista cada agente dos oito labs como uma
entidade. A turma escolhe um, conversa, e vê o trace da chamada. É o equivalente
ao `adk web` do laboratório em Google.

DE ONDE VÊM OS AGENTES

Deste arquivo, quase nada. Os agentes são importados dos próprios labs:
`montar_especialistas` do lab 05, `montar_papeis` e os pipelines do lab 06, as
tools do prontuário do lab 02b, o guardrail do lab 03, o agente remoto do 07.
Só as quatro instructions dos labs 01 a 04 são referenciadas por constante,
porque lá elas estão dentro do `main()`.

Isso é de propósito: se a UI tivesse cópias das instructions, editar um lab em
aula deixaria a UI mostrando a versão velha, e a turma veria dois agentes
diferentes com o mesmo nome. Aqui, mexeu no lab, mexeu na UI.

POR QUE NÃO `devui.serve()` DIRETO

O `serve()` monta o servidor e bloqueia. Não serve aqui porque metade dos
agentes segura conexões MCP, e conexão MCP precisa ficar aberta na MESMA task o
tempo todo — abrindo e fechando por chamada, o teardown estoura com
`Attempted to exit cancel scope in a different task`.

Então montamos o app com `DevServer.create_app()` e rodamos o uvicorn dentro do
nosso loop, com um `AsyncExitStack` segurando tudo enquanto o processo vive.

WORKFLOW NA UI

O DevUI reconhece workflow como entidade, mas um `Workflow` não tem `name` e
apareceria como "Workflow Workflow". Por isso os pipelines do lab 06 entram via
`.as_agent(nome, description=...)`, que os embrulha num agente com nome.

TOLERÂNCIA A SERVIÇO FORA DO AR

Sem Toolbox ou sem o agente A2A, a UI sobe assim mesmo, com o que dá para montar,
e diz o que ficou de fora. Em sala, uma UI que sobe pela metade vale mais do que
uma que não sobe.
"""

from __future__ import annotations

import asyncio
import os
import sys
from contextlib import AsyncExitStack

import httpx
import uvicorn
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework_devui import DevServer
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

from comum import (
    chat_client,
    consultar_status_rede,
    ligar_telemetria,
    middleware_habbo,
    reiniciar_roteador,
)

# As instructions e tools vêm dos labs, não de cópias.
from lab01_agente_puro.agent import INSTRUCTION_PROTOCOLO
from lab02_memoria.a_thread import INSTRUCTION as I_SESSAO
from lab02_memoria.b_memoria_longa import (
    INSTRUCTION as I_PRONTUARIO,
    gravar_no_prontuario,
    ler_prontuario,
)
from lab03_tool_externa.agent import (
    INSTRUCTION as I_REDE,
    guardrail_acao_destrutiva,
    registrar_autorizacao_reinicio,
)
from lab04_mcp_toolbox.agent import INSTRUCTION as I_DADOS

load_dotenv()

TOOLBOX_URL = os.getenv("TOOLBOX_MCP_URL", "http://localhost:5000/mcp")
AURORA_API = os.getenv("AURORA_API_URL", "http://localhost:8000")
A2A_URL = os.getenv("A2A_TECNICO_URL", "http://localhost:9000")

I_MAESTRO = """
Você é o ARI, coordenador do atendimento da Aurora Fibra.
Você tem consultores internos disponíveis como ferramentas. Consulte quantos
forem necessários ANTES de responder, e entregue uma resposta única e integrada,
em até 120 palavras. Nunca mencione que consultou ferramentas ou outros agentes.
"""


async def _no_ar(url: str, timeout: float = 3.0) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout) as cli:
            await cli.get(url)
        return True
    except Exception:
        return False


async def montar(stack: AsyncExitStack, cred) -> tuple[list, list[str]]:
    cliente = chat_client(cred)
    ents: list = []
    fora: list[str] = []

    def novo(nome, instrucoes, descricao, tools=None, extra_mw=None):
        return Agent(cliente, instrucoes, name=nome, description=descricao,
                     tools=tools or [],
                     middleware=[*middleware_habbo(nome), *(extra_mw or [])])

    # ---------------------------------------------------- labs 01 a 03
    ents += [
        novo("ari_n1", INSTRUCTION_PROTOCOLO,
             "Lab 01 · agente puro. Sem acesso a sistema nenhum: peça uma fatura "
             "e veja ele admitir que não tem."),
        novo("ari_com_caderno", I_SESSAO,
             "Lab 02a · com sessão. Informe algo e cobre depois: ele acompanha."),
        novo("ari_com_prontuario", I_PRONTUARIO,
             "Lab 02b · prontuário em disco. Diga uma preferência durável e abra "
             "o lab02_memoria/prontuarios.json depois.",
             tools=[gravar_no_prontuario, ler_prontuario]),
        novo("ari_com_acesso", I_REDE,
             "Lab 03 · painel de rede, com o guardrail de verdade. Peça o reinício "
             "direto e veja o middleware barrar.",
             tools=[consultar_status_rede, registrar_autorizacao_reinicio,
                    reiniciar_roteador],
             extra_mw=[guardrail_acao_destrutiva]),
    ]

    if not await _no_ar(AURORA_API + "/health"):
        fora.append(f"API de rede ({AURORA_API}) — o ari_com_acesso sobe, mas as "
                    f"consultas respondem 'indisponivel'")

    # ------------------------------------------- labs 04, 05 e 06 (Toolbox)
    if await _no_ar(TOOLBOX_URL.replace("/mcp", "/")):
        from lab05_handoff.especialistas import montar_especialistas
        from lab06_workflows.pipelines import (
            montar_papeis,
            pipeline_concorrente,
            pipeline_sequencial,
        )

        mcp_n1 = await stack.enter_async_context(
            MCPStreamableHTTPTool(name="toolbox_n1", url=TOOLBOX_URL,
                                  description="Consultas aprovadas da Aurora."))
        ents.append(novo("ari_com_dados", I_DADOS,
                         "Lab 04 · o banco, via MCP Toolbox. Informe um CPF "
                         "(111.222.333-44 ou 444.555.666-77).",
                         tools=[mcp_n1, consultar_status_rede]))

        # Os especialistas do lab 05, com as instructions e o isolamento de
        # tools do próprio lab — uma conexão MCP por papel.
        cobranca, tecnico, agendamento = await stack.enter_async_context(
            montar_especialistas(cred))
        for ag, lab in ((cobranca, "cobrança"), (tecnico, "técnico"),
                        (agendamento, "agendamento")):
            ag.description = f"Lab 05 · especialista de {lab}. {ag.description or ''}"[:300]
        ents += [cobranca, tecnico, agendamento]

        ents.append(novo(
            "ari_maestro", I_MAESTRO,
            "Lab 05 · o maestro, com os três especialistas como ferramentas. "
            "Pergunte algo que misture cobrança e problema técnico.",
            tools=[
                cobranca.as_tool(name="consultar_cobranca",
                                 description="Consulta a situação financeira do cliente."),
                tecnico.as_tool(name="consultar_tecnico",
                                description="Consulta a situação técnica da conexão."),
                agendamento.as_tool(name="consultar_agenda",
                                    description="Consulta visitas técnicas agendadas."),
            ]))

        # Os nove papéis do lab 06, cada um sozinho. Eles respondem JSON ou
        # texto de etapa, e não conversa: servem para depurar uma etapa isolada.
        papeis = await stack.enter_async_context(montar_papeis(cred))
        rotulos = {
            "triagem": "etapa 1 do POP: classifica o caso",
            "diagnostico": "etapa 2 do POP: hipótese técnica",
            "registro": "etapa 3 do POP: resposta e registro interno",
            "check_financeiro": "checagem paralela: bloqueio financeiro, responde JSON",
            "check_rede": "checagem paralela: incidente na região, responde JSON",
            "check_historico": "checagem paralela: reincidência, responde JSON",
            "consolidador": "junta as três checagens e decide a conduta",
            "redator": "reescreve resposta para o cliente",
            "critico": "aprova ou devolve o texto do redator",
        }
        for chave, agente in papeis.items():
            agente.description = f"Lab 06 · {rotulos.get(chave, chave)}"
            ents.append(agente)

        # Os pipelines, embrulhados como agentes para terem nome na lista.
        ents.append(pipeline_sequencial(papeis).as_agent(
            "pop_sequencial",
            description="Lab 06 · o POP inteiro em ordem fixa: triagem, diagnóstico, registro."))
        ents.append(pipeline_concorrente(papeis).as_agent(
            "checagens_concorrentes",
            description="Lab 06 · as três checagens em paralelo, com o agregador."))
    else:
        fora.append(f"Toolbox ({TOOLBOX_URL}) — ficam de fora os labs 04, 05 e 06")

    # ------------------------------------------------------------ lab 07
    if await _no_ar(f"{A2A_URL.rstrip('/')}/.well-known/agent-card.json"):
        from lab07_a2a.agent import tecnico_remoto

        remoto = tecnico_remoto()
        remoto.description = ("Lab 07 · especialista técnico de OUTRO processo, por A2A. "
                              "Na lista ele parece igual aos outros.")
        ents.append(remoto)
        ents.append(novo(
            "ari_maestro_a2a", I_MAESTRO,
            "Lab 07 · maestro cujo consultor técnico mora fora deste processo.",
            tools=[remoto.as_tool(
                name="consultar_tecnico",
                description="Consulta o especialista técnico sobre problemas de conexão.")]))
    else:
        fora.append(f"Agente A2A ({A2A_URL}) — fica de fora o lab 07. Suba com: "
                    f"python -m uvicorn lab07_a2a.servidor:app --port 9000")

    return ents, fora


async def main() -> None:
    ligar_telemetria("ari-devui")

    porta = 8080
    if "--port" in sys.argv:
        porta = int(sys.argv[sys.argv.index("--port") + 1])

    async with AsyncExitStack() as stack:
        cred = await stack.enter_async_context(AzureCliCredential())
        ents, fora = await montar(stack, cred)

        print(f"\n\033[1m{len(ents)} entidades registradas:\033[0m")
        for e in ents:
            print(f"  · {getattr(e, 'name', '?')}")
        if fora:
            print("\n\033[93mFora do ar, e o que isso custou:\033[0m")
            for f in fora:
                print(f"  · {f}")

        servidor = DevServer(port=porta, host="127.0.0.1", ui_enabled=True,
                             auth_enabled=False)
        servidor.register_entities(ents)

        print(f"\n\033[1mDevUI em http://localhost:{porta}\033[0m  (ctrl+c para parar)\n")
        config = uvicorn.Config(servidor.create_app(), host="127.0.0.1",
                                port=porta, log_level="warning")
        await uvicorn.Server(config).serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nencerrado.")
