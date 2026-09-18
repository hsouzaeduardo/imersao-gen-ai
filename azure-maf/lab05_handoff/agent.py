"""
LAB 05 (MAF): ARI promovido a coordenador.

    python -m lab05_handoff.agent            # handoff
    python -m lab05_handoff.agent --tools    # agentes como ferramentas

Duas formas, o mesmo debate da versão ADK com outros nomes:

  HandoffBuilder   equivale a sub_agents do ADK
                   o especialista assume a conversa e fala com o cliente

  agent.as_tool()  equivale a AgentTool do ADK
                   o coordenador consulta e redige a resposta final

E, como no ADK, quem decide o roteamento é o texto da `description`
de cada especialista, não a instruction dele.
"""

from __future__ import annotations

import asyncio
import sys

from agent_framework import Agent
from agent_framework.orchestrations import HandoffBuilder
from azure.identity.aio import AzureCliCredential

from comum import middleware_habbo, chat_client, ligar_telemetria, rodar_workflow
from lab05_handoff.especialistas import montar_especialistas

PERGUNTA = "minha fatura venceu e o roteador está piscando vermelho. CPF 444.555.666-77"

INSTRUCTION_COORDENADOR = """
Você é o ARI, coordenador do atendimento da Aurora Fibra.

SEU TRABALHO É ROTEAR, NÃO RESOLVER.
Você não consulta fatura, não consulta rede, não abre chamado.

1. Peça o CPF, se ainda não tiver.
2. Identifique o assunto e encaminhe para o especialista correto.
3. Dois assuntos no mesmo pedido: trate a pendência financeira primeiro,
   porque suporte técnico em contrato suspenso não resolve nada.
4. Não dando para classificar, faça UMA pergunta de esclarecimento.

Nunca narre o procedimento interno nem peça desculpa pelo encaminhamento.
Até 60 palavras.
"""


async def modo_handoff(cred) -> None:
    async with montar_especialistas(cred) as (cobranca, tecnico, agendamento):
        triagem = Agent(
            client=chat_client(cred),
            name="ari_coordenador",
            description="Coordenador do atendimento da Aurora Fibra.",
            instructions=INSTRUCTION_COORDENADOR,
            require_per_service_call_history_persistence=True,
            middleware=middleware_habbo("ari_coordenador"),
        )

        workflow = (
            HandoffBuilder()
            .participants([triagem, cobranca, tecnico, agendamento])
            .with_start_agent(triagem)
            .build()
        )

        print(f"\n\033[1mCliente:\033[0m {PERGUNTA}")
        await rodar_workflow(workflow, PERGUNTA)


async def modo_agentes_como_tools(cred) -> None:
    async with montar_especialistas(cred) as (cobranca, tecnico, agendamento):
        maestro = Agent(
            client=chat_client(cred),
            name="ari_maestro",
            instructions="""
Você é o ARI, coordenador do atendimento da Aurora Fibra.

Você tem três consultores internos disponíveis como ferramentas.
Consulte quantos forem necessários ANTES de responder, e entregue ao cliente
uma resposta única e integrada, em até 120 palavras.

Problema financeiro e técnico juntos: consulte os dois e explique a relação,
por exemplo contrato suspenso derrubando o serviço.

Nunca mencione que consultou ferramentas ou outros agentes.
""",
            tools=[
                cobranca.as_tool(
                    name="consultar_cobranca",
                    description="Consulta a situação financeira do cliente.",
                ),
                tecnico.as_tool(
                    name="consultar_tecnico",
                    description="Consulta a situação técnica da conexão do cliente.",
                ),
                agendamento.as_tool(
                    name="consultar_agenda",
                    description="Consulta visitas técnicas agendadas.",
                ),
            ],
            middleware=middleware_habbo("ari_maestro"),
        )

        print(f"\n\033[1mCliente:\033[0m {PERGUNTA}")
        r = await maestro.run(PERGUNTA)
        print(f"\033[1mARI:\033[0m {r.text.strip()}")


async def main() -> None:
    ligar_telemetria("ari-lab05")
    async with AzureCliCredential() as cred:
        if "--tools" in sys.argv:
            await modo_agentes_como_tools(cred)
        else:
            await modo_handoff(cred)


if __name__ == "__main__":
    asyncio.run(main())
