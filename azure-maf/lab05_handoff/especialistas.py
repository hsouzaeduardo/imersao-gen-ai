"""
Os três especialistas da Aurora, em MAF.

Diferença estrutural para o ADK: lá, o isolamento de tools vinha do
`toolset_name` de cada agente. Aqui, o servidor MCP é o mesmo e o recorte
é feito na conexão: um MCP tool por toolset, cada agente recebe o seu.

Como MCP tool é conexão viva, os agentes são construídos dentro de um
contexto assíncrono, e não no import do módulo.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from agent_framework import Agent, MCPStreamableHTTPTool
from dotenv import load_dotenv

from comum import middleware_habbo, chat_client, consultar_status_rede

load_dotenv()

MCP_URL = os.getenv("TOOLBOX_MCP_URL", "http://localhost:5000/mcp")


DESC_COBRANCA = (
    "Trata assuntos financeiros do cliente: faturas em aberto ou vencidas, valores, "
    "vencimentos, segunda via, contestação de cobrança e contrato suspenso por "
    "inadimplência. Acione sempre que houver menção a pagamento, boleto, fatura, "
    "conta, débito ou bloqueio por falta de pagamento."
)

DESC_TECNICO = (
    "Trata problemas de conexão: lentidão, oscilação, queda de sinal, luz vermelha no "
    "roteador, ping alto, Wi-Fi fraco. Verifica incidentes na região, consulta "
    "histórico de chamados e abre chamado quando necessário."
)

DESC_AGENDAMENTO = (
    "Trata visitas técnicas: consulta visitas marcadas, informa data, turno e técnico, "
    "e orienta sobre remarcação. Acione quando o cliente falar em visita, técnico na "
    "casa, horário presencial ou remarcar."
)


@asynccontextmanager
async def montar_especialistas(credential):
    """Abre as conexões MCP e devolve os três especialistas prontos.

    Uso:
        async with montar_especialistas(cred) as (cobranca, tecnico, agenda):
            ...
    """
    async with (
        MCPStreamableHTTPTool(
            name="toolbox_cobranca", url=MCP_URL, description="Consultas de cobrança."
        ) as mcp_cobranca,
        MCPStreamableHTTPTool(
            name="toolbox_tecnico", url=MCP_URL, description="Consultas técnicas."
        ) as mcp_tecnico,
    ):
        cliente = chat_client(credential)

        cobranca = Agent(
            client=cliente,
            name="agente_cobranca",
            description=DESC_COBRANCA,
            instructions="""
Você é o especialista de cobrança da Aurora Fibra.

1. Chame buscar_cliente_por_cpf com o CPF em dígitos.
2. Chame listar_faturas_em_aberto e informe competência, valor e vencimento.
3. Contrato suspenso: explique que a religação ocorre após a compensação
   do pagamento, em até 24 horas úteis.
4. Não negocie desconto, não perdoe multa, não prometa data de baixa.

Até 100 palavras. Se o assunto sair de cobrança, devolva para o coordenador.
""",
            tools=[mcp_cobranca],
            # Exigido pelo HandoffBuilder: mantém o histórico local
            # coerente com o serviço quando o handoff curto-circuita
            # a chamada de tool.
            require_per_service_call_history_persistence=True,
            middleware=middleware_habbo("agente_cobranca"),
        )

        tecnico = Agent(
            client=cliente,
            name="agente_tecnico",
            description=DESC_TECNICO,
            instructions="""
Você é o especialista técnico N2 da Aurora Fibra.

1. Chame buscar_cliente_por_cpf para obter o CEP do cadastro.
2. Chame consultar_status_rede com esse CEP. Havendo incidente na região,
   informe severidade e previsão e não abra chamado individual.
3. Rede normal: chame listar_chamados_recentes para ver reincidência.
4. Havendo reincidência ou sintoma não explicado, confirme o resumo
   com o cliente e só então chame abrir_chamado.

Até 100 palavras. Se o assunto virar cobrança ou agenda, devolva para o coordenador.
""",
            tools=[mcp_tecnico, consultar_status_rede],
            # Exigido pelo HandoffBuilder: mantém o histórico local
            # coerente com o serviço quando o handoff curto-circuita
            # a chamada de tool.
            require_per_service_call_history_persistence=True,
            middleware=middleware_habbo("agente_tecnico"),
        )

        agendamento = Agent(
            client=cliente,
            name="agente_agendamento",
            description=DESC_AGENDAMENTO,
            instructions="""
Você é o especialista de agenda técnica da Aurora Fibra.

1. Chame buscar_cliente_por_cpf e depois consultar_agenda_tecnica.
2. Existindo visita agendada, informe data, turno e técnico,
   e não ofereça novo agendamento.
3. Turnos: manhã das 8h às 12h, tarde das 13h às 18h.
4. Confirme se o cliente estará no endereço de instalação.

Até 100 palavras.
""",
            tools=[mcp_tecnico],
            # Exigido pelo HandoffBuilder: mantém o histórico local
            # coerente com o serviço quando o handoff curto-circuita
            # a chamada de tool.
            require_per_service_call_history_persistence=True,
            middleware=middleware_habbo("agente_agendamento"),
        )

        yield cobranca, tecnico, agendamento
