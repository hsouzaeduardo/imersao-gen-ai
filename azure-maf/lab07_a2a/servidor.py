"""
LAB 07, lado servidor: o especialista técnico publicado por A2A.

    python -m uvicorn lab07_a2a.servidor:app --port 9000

Este arquivo representa **o outro time**. Finja que ele está noutro
repositório, noutra linguagem, com outro ciclo de release, e que você não tem
acesso ao código. Tudo o que você vai receber é a URL.

O que um servidor A2A publica:

  GET  /.well-known/agent-card.json    quem eu sou e o que sei fazer
  POST /                               fale comigo (JSON-RPC)

O agent card é o contrato. É ele que o cliente lê para descobrir o agente, do
mesmo jeito que o modelo lê a description de uma tool para decidir chamá-la.
Repare que a estrutura é a mesma do lab 03: nome, descrição, e o que entra e sai.
"""

from __future__ import annotations

import os

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from agent_framework import Agent
from agent_framework_a2a import A2AExecutor
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv
from fastapi import FastAPI

from comum import chat_client

load_dotenv()

URL_PUBLICA = os.getenv("A2A_TECNICO_URL", "http://localhost:9000")

INSTRUCTION = """
Você é o especialista técnico da Aurora Fibra, consultado por outros agentes.

Responda em português do Brasil, em até 50 palavras, direto ao ponto.
Classifique o problema e diga o próximo passo concreto.
Você não tem acesso ao cadastro do cliente: se precisar de dado cadastral,
diga qual dado falta em vez de supor.
"""

# O cartão é o contrato publicado. Quem consome nunca vê este arquivo:
# vê só o que está aqui dentro.
CARTAO = AgentCard(
    name="especialista_tecnico_aurora",
    description=(
        "Diagnostica problemas de conexão da Aurora Fibra: lentidão, oscilação, "
        "queda de sinal, luz vermelha no roteador e ping alto. "
        "Não trata cobrança nem agendamento."
    ),
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    supported_interfaces=[AgentInterface(url=URL_PUBLICA, protocol_binding="JSONRPC")],
    skills=[
        AgentSkill(
            id="diagnostico_conexao",
            name="Diagnóstico de conexão",
            description="Classifica o problema relatado e indica o próximo passo.",
            tags=["rede", "suporte", "n2"],
            examples=["Luz vermelha LOS acesa desde a madrugada."],
        )
    ],
)

app = FastAPI(title="Aurora Fibra · especialista técnico (A2A)")

# A credencial vive enquanto o processo vive. Num servidor não há `async with`
# envolvendo tudo, como nos outros labs, porque não existe "fim do atendimento":
# o processo fica de pé atendendo chamadas de quem aparecer.
_credencial = AzureCliCredential()

_agente = Agent(
    chat_client(_credencial),
    INSTRUCTION,
    name="especialista_tecnico",
    description=CARTAO.description,
)

# A2AExecutor é o adaptador: pega um Agent do MAF e o expõe no formato que o
# protocolo espera. O agente não sabe que está sendo servido por A2A, do mesmo
# jeito que no lab 04 o Postgres não sabia que estava sendo servido por MCP.
_handler = DefaultRequestHandler(
    agent_executor=A2AExecutor(_agente),
    task_store=InMemoryTaskStore(),
    agent_card=CARTAO,
)

add_a2a_routes_to_fastapi(
    app,
    agent_card_routes=create_agent_card_routes(CARTAO),
    jsonrpc_routes=create_jsonrpc_routes(_handler, rpc_url="/"),
)
