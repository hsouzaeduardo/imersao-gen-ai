"""
Tools de rede da Aurora, em MAF.

Diferença para o ADK: aqui a tool é decorada com @tool (era @ai_function na API antiga), e a
descrição de cada parâmetro vem de Annotated[..., Field(description=...)].
O contrato com o modelo continua sendo o mesmo, só muda a forma de declarar.
"""

from __future__ import annotations

import os
from typing import Annotated

import httpx
from agent_framework import tool
from pydantic import Field

API = os.getenv("AURORA_API_URL", "http://localhost:8000")
TIMEOUT = 8.0


@tool(
    name="consultar_status_rede",
    description=(
        "Consulta o painel de rede da Aurora e retorna a situação de um CEP. "
        "Use sempre que o cliente relatar lentidão, oscilação ou falta de conexão, "
        "antes de qualquer diagnóstico. Não use para assuntos de cobrança."
    ),
)
async def consultar_status_rede(
    cep: Annotated[str, Field(description="CEP da instalação, com ou sem hífen. Ex: 06010-100")],
) -> dict:
    """Situação da rede para um CEP."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
            r = await cli.get(f"{API}/status-rede/{cep}")
        if r.status_code == 400:
            return {"status": "erro", "mensagem": "CEP inválido. Peça o CEP com 8 dígitos."}
        r.raise_for_status()
        return {"status": "ok", "dados": r.json()}
    except httpx.ConnectError:
        return {
            "status": "indisponivel",
            "mensagem": "Painel de rede fora do ar. Informe o cliente e não invente diagnóstico.",
        }
    except httpx.HTTPError as e:
        return {"status": "erro", "mensagem": f"Falha ao consultar o painel: {e}"}


@tool(
    name="reiniciar_roteador",
    description=(
        "Envia comando de reinício remoto para o roteador do cliente. "
        "AÇÃO COM EFEITO COLATERAL: derruba a conexão por cerca de 3 minutos. "
        "Só chame depois de o cliente autorizar explicitamente."
    ),
)
async def reiniciar_roteador(
    id_cliente: Annotated[str, Field(description="CPF sem pontuação ou id do contrato.")],
) -> dict:
    """Reinício remoto do roteador."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
            r = await cli.post(f"{API}/roteador/reiniciar", json={"id_cliente": id_cliente})
        r.raise_for_status()
        return {"status": "ok", "dados": r.json()}
    except httpx.HTTPError as e:
        return {"status": "erro", "mensagem": f"Falha ao reiniciar: {e}"}


@tool(
    name="listar_eventos_massivos",
    description="Lista os incidentes de rede ativos na base da Aurora.",
)
async def listar_eventos_massivos() -> dict:
    """Incidentes ativos."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
            r = await cli.get(f"{API}/eventos-massivos")
        r.raise_for_status()
        return {"status": "ok", "dados": r.json()}
    except httpx.HTTPError as e:
        return {"status": "erro", "mensagem": f"Falha: {e}"}
