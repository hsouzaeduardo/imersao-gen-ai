"""
LAB 04 (MAF): a chave do banco de dados.

    python -m lab04_mcp_toolbox.agent

O mesmo MCP Toolbox for Databases do laboratório em ADK, sem mudar
uma linha do tools.yaml. É esse o ponto do MCP: o servidor de tools
não sabe nem se importa com qual framework está do outro lado.

O que muda é só o cliente:
  ADK: ToolboxToolset(server_url=...)
  MAF: MCPStreamableHTTPTool(url=".../mcp")

Em Azure, o Toolbox roda em Container Apps apontando para um
Azure Database for PostgreSQL Flexible Server.
"""

from __future__ import annotations

import asyncio
import os

from agent_framework import Agent, MCPStreamableHTTPTool
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

from comum import middleware_habbo, chat_client, consultar_status_rede, ligar_telemetria

load_dotenv()

TOOLBOX_MCP_URL = os.getenv("TOOLBOX_MCP_URL", "http://localhost:5000/mcp")

INSTRUCTION = """
Você é o ARI, assistente de suporte N1 da Aurora Fibra.
Fale em português do Brasil, tom cordial e direto, respostas de até 120 palavras.

PROTOCOLO
1. Peça o CPF e chame buscar_cliente_por_cpf antes de qualquer outra consulta.
   Passe sempre o CPF com apenas dígitos, sem pontos nem hífen.
2. Cobrança: chame listar_faturas_em_aberto e informe competência, valor e vencimento.
   Não negocie desconto, não prometa prazo de baixa.
3. Técnico: chame consultar_status_rede com o CEP do cadastro e
   listar_chamados_recentes para verificar reincidência.
4. Antes de oferecer visita, chame consultar_agenda_tecnica.
   Se já existir visita agendada, informe a data em vez de agendar outra.
5. Contrato suspenso por inadimplência: trate a cobrança primeiro.
   Suporte técnico em contrato suspenso não resolve nada.

LIMITES
Use exclusivamente o que as tools retornarem. Se vier vazio, diga que não localizou.
"""


async def main() -> None:
    ligar_telemetria("ari-lab04")

    async with AzureCliCredential() as cred:
        # O MCP tool é um recurso com ciclo de vida: abre a conexão,
        # descobre as tools publicadas pelo servidor, e fecha no fim.
        async with MCPStreamableHTTPTool(
            name="aurora_toolbox",
            url=TOOLBOX_MCP_URL,
            description="Consultas aprovadas da base de clientes da Aurora Fibra.",
            # Em Container Apps com autenticação, o token entra aqui:
            # headers={"Authorization": f"Bearer {token}"},
        ) as toolbox:
            agente = Agent(
                chat_client(cred),
                INSTRUCTION,
                name="ari_com_dados",
                tools=[toolbox, consultar_status_rede],
                middleware=middleware_habbo("ari_com_dados"),
            )

            sessao = agente.create_session()
            roteiro = [
                "oi, meu CPF é 111.222.333-44, tenho alguma fatura em aberto?",
                "e a minha internet, tem algum problema na região?",
                "tem visita técnica marcada pra mim?",
            ]
            for fala in roteiro:
                print(f"\n\033[1mCliente:\033[0m {fala}")
                r = await agente.run(fala, session=sessao)
                print(f"\033[1mARI:\033[0m {r.text.strip()}")

            print(
                "\n\033[93mAgora edite o tools.yaml, reinicie só o Toolbox,"
                "\ne faça a mesma pergunta. O agente mudou sem deploy de agente.\033[0m"
            )


if __name__ == "__main__":
    asyncio.run(main())
