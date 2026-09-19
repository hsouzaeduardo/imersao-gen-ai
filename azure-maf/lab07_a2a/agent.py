"""
LAB 07 (MAF): o agente que não é seu.

    python -m uvicorn lab07_a2a.servidor:app --port 9000    # noutro terminal
    python -m lab07_a2a.agent --card
    python -m lab07_a2a.agent --direto
    python -m lab07_a2a.agent

No lab 05 o ARI ganhou especialistas. Todos eram seus: no seu processo, no seu
requirements.txt, no seu deploy. Na Aurora real, o especialista técnico é de
outro time, que versiona sozinho e sobe quando quer. Você não pode importar a
classe dele.

A2A resolve isso do mesmo jeito que o MCP resolveu o acesso a dado no lab 04:
padronizando a fronteira. Lá, o agente parou de falar com o banco e passou a
falar com um servidor de tools. Aqui, o agente para de importar o especialista
e passa a falar com um endpoint.

E repare no que NÃO muda: `A2AAgent` tem `run`, `create_session` e `as_tool`,
a mesma superfície de um agente local. O maestro do lab 05 continua idêntico.
A fronteira de processo virou detalhe de construção.
"""

from __future__ import annotations

import asyncio
import os
import sys

import httpx
from agent_framework import Agent
from agent_framework_a2a import A2AAgent
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

from comum import chat_client, ligar_telemetria, middleware_habbo

load_dotenv()

URL_TECNICO = os.getenv("A2A_TECNICO_URL", "http://localhost:9000")

PERGUNTA = (
    "Minha internet caiu ontem à noite e o roteador está com uma luz vermelha "
    "acesa. Já tirei da tomada e não resolveu."
)

INSTRUCTION_MAESTRO = """
Você é o ARI, do atendimento da Aurora Fibra.

Você tem um consultor técnico externo disponível como ferramenta.
Consulte-o antes de responder qualquer coisa sobre conexão.
Entregue ao cliente uma resposta única e integrada, de até 80 palavras.
Nunca mencione que consultou outro agente, e nunca diga que ele é externo.
"""


async def mostrar_cartao() -> None:
    """Busca e imprime o agent card, que é a descoberta do protocolo.

    Vale rodar isto antes de qualquer código: é o momento em que o agente remoto
    deixa de ser uma URL e passa a ser uma capacidade com contrato.
    """
    url = f"{URL_TECNICO.rstrip('/')}/.well-known/agent-card.json"
    print(f"\n\033[90mGET {url}\033[0m")
    try:
        async with httpx.AsyncClient(timeout=10.0) as cli:
            r = await cli.get(url)
        r.raise_for_status()
    except httpx.HTTPError as e:
        print(f"\033[93mNão consegui ler o cartão ({type(e).__name__}).")
        print("O servidor está de pé? python -m uvicorn lab07_a2a.servidor:app --port 9000\033[0m")
        return

    cartao = r.json()
    print(f"\n\033[1mnome:\033[0m       {cartao.get('name')}")
    print(f"\033[1mdescrição:\033[0m  {cartao.get('description')}")
    print(f"\033[1mversão:\033[0m     {cartao.get('version')}")
    for s in cartao.get("skills", []):
        print(f"\033[1mskill:\033[0m      {s.get('id')} — {s.get('description')}")
    print(
        "\n\033[93mIsso é tudo o que você recebe do outro time. Sem código, sem "
        "biblioteca,\nsem acordo de linguagem. A descrição aqui é o contrato, "
        "igual à da tool no lab 03.\033[0m"
    )


def tecnico_remoto() -> A2AAgent:
    """O especialista de outro time, como se fosse local.

    A description é a mesma coisa que no lab 05: é ela que o modelo lê para
    decidir consultar. Só que agora ela vem do agent card do outro time, e não
    de uma constante no seu repositório.
    """
    return A2AAgent(
        name="tecnico_aurora",
        url=URL_TECNICO,
        description=(
            "Especialista técnico da Aurora Fibra. Diagnostica lentidão, "
            "oscilação, queda de sinal e luz vermelha no roteador."
        ),
    )


async def modo_direto() -> None:
    """Fala com o agente remoto sem intermediário nenhum."""
    remoto = tecnico_remoto()
    print(f"\n\033[1mCliente:\033[0m {PERGUNTA}")
    r = await remoto.run(PERGUNTA)
    print(f"\033[1mTécnico (outro processo):\033[0m {r.text.strip()}")
    print(
        "\n\033[93mEsse `run` é idêntico ao de um agente local. A única pista de "
        "que\nele atravessou a rede é a latência.\033[0m"
    )


async def modo_maestro(cred) -> None:
    """O maestro do lab 05, com um participante que não é seu."""
    remoto = tecnico_remoto()
    maestro = Agent(
        chat_client(cred),
        INSTRUCTION_MAESTRO,
        name="ari_maestro_a2a",
        tools=[
            remoto.as_tool(
                name="consultar_tecnico",
                description="Consulta o especialista técnico sobre problemas de conexão.",
            )
        ],
        middleware=middleware_habbo("ari_maestro_a2a"),
    )
    print(f"\n\033[1mCliente:\033[0m {PERGUNTA}")
    r = await maestro.run(PERGUNTA)
    print(f"\033[1mARI:\033[0m {r.text.strip()}")
    print(
        "\n\033[93mCompare com o lab 05: a linha do `as_tool` é a mesma. O que mudou "
        "foi\nonde o especialista mora, e o maestro não tem como saber.\033[0m"
    )


async def main() -> None:
    ligar_telemetria("ari-lab07")

    if "--card" in sys.argv:
        await mostrar_cartao()
        return

    async with AzureCliCredential() as cred:
        if "--direto" in sys.argv:
            await modo_direto()
        else:
            await modo_maestro(cred)


if __name__ == "__main__":
    asyncio.run(main())
