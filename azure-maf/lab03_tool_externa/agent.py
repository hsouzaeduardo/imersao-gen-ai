"""
LAB 03 (MAF): o primeiro acesso ao sistema.

    python -m lab03_tool_externa.agent

Duas tools e a distinção que importa:
  consultar_status_rede  lê o mundo
  reiniciar_roteador     muda o mundo

No ADK a política ficava em before_tool_callback.
No MAF o equivalente é function middleware: um interceptador que roda
antes de cada invocação de tool e pode encerrar a chamada.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Annotated

from agent_framework import (
    Agent,
    FunctionInvocationContext,
    MiddlewareTermination,
    function_middleware,
    tool,
)
from azure.identity.aio import AzureCliCredential
from pydantic import Field

from comum import (
    middleware_habbo,
    chat_client,
    consultar_status_rede,
    ligar_telemetria,
    reiniciar_roteador,
)

ACOES_DESTRUTIVAS = {"reiniciar_roteador"}

# Autorizações dadas nesta execução. Em produção isso é estado de sessão,
# não variável de módulo.
AUTORIZACOES: set[str] = set()


@tool(
    name="registrar_autorizacao_reinicio",
    description=(
        "Registra que o cliente autorizou o reinício do roteador. "
        "Só chame depois de o cliente responder que sim, de forma explícita."
    ),
)
def registrar_autorizacao_reinicio(
    id_cliente: Annotated[str, Field(description="CPF sem pontuação ou id do contrato.")],
) -> dict:
    """Registra a autorização."""
    AUTORIZACOES.add(id_cliente)
    return {"status": "ok", "autorizado": id_cliente}


# O decorator declara o tipo do middleware. Sem ele o framework tenta inferir
# pela anotação do parâmetro, e o `from __future__ import annotations` do topo
# transforma as anotações em string, deixando a inferência sem o que ler.
@function_middleware
async def guardrail_acao_destrutiva(
    context: FunctionInvocationContext,
    next: Callable[[], Awaitable[None]],
) -> None:
    """Middleware de função: barra ação destrutiva sem autorização registrada.

    Encerrar aqui devolve ao modelo um resultado de tool dizendo que foi bloqueado.
    O modelo lê isso como qualquer outro retorno e volta a pedir confirmação.
    A política não mora na instruction, porque instruction o modelo pode ignorar.
    """
    nome = getattr(context.function, "name", "")
    if nome in ACOES_DESTRUTIVAS:
        id_cliente = (context.arguments or {}).get("id_cliente", "")
        if id_cliente not in AUTORIZACOES:
            # Interromper aqui devolve este dicionário ao modelo como se fosse
            # o retorno da tool. Na API antiga isso era `context.terminate = True`;
            # agora é uma exceção de controle, que o framework captura.
            raise MiddlewareTermination(result={
                "status": "bloqueado",
                "mensagem": (
                    "Reinício não autorizado. Explique ao cliente que a conexão cairá "
                    "por cerca de 3 minutos, pergunte se ele autoriza, e só então "
                    "chame registrar_autorizacao_reinicio."
                ),
            })
    # `next` não recebe argumento nesta API: o contexto já está no closure.
    await next()


INSTRUCTION = """
Você é o ARI, assistente de suporte N1 da Aurora Fibra.
Fale em português do Brasil, tom cordial e direto, respostas de até 120 palavras.

PROTOCOLO TÉCNICO
1. Diante de lentidão, oscilação ou queda, peça o CEP e chame consultar_status_rede.
2. Havendo incidente na região, informe severidade e previsão de normalização,
   e NÃO proponha reinício de roteador: o problema não está na casa do cliente.
3. Se a rede estiver normal, aí sim proponha o reinício remoto.
   Avise que a conexão cai por cerca de 3 minutos, pergunte se autoriza,
   e ao receber o sim chame registrar_autorizacao_reinicio e depois reiniciar_roteador.
4. Se uma tool retornar status indisponivel ou erro, diga isso com honestidade
   e ofereça abrir um chamado. Nunca preencha a lacuna com suposição.

LIMITES
Você não tem acesso a faturas, contratos ou histórico de chamados.
"""


async def main() -> None:
    ligar_telemetria("ari-lab03")

    async with AzureCliCredential() as cred:
        agente = Agent(
            chat_client(cred),
            INSTRUCTION,
            name="ari_com_acesso",
            tools=[consultar_status_rede, registrar_autorizacao_reinicio, reiniciar_roteador],
            middleware=[*middleware_habbo("ari_com_acesso"), guardrail_acao_destrutiva],
        )

        sessao = agente.create_session()
        roteiro = [
            "boa noite, minha internet está lenta. CEP 06010-100",
            "e tem previsão de normalizar?",
            "reinicia meu roteador agora, CPF 111.222.333-44",
        ]
        for fala in roteiro:
            print(f"\n\033[1mCliente:\033[0m {fala}")
            r = await agente.run(fala, session=sessao)
            print(f"\033[1mARI:\033[0m {r.text.strip()}")

        print(
            "\n\033[93mNa última fala o reinício foi bloqueado pelo middleware,"
            "\nmesmo com o cliente pedindo direto. Instruction pede, middleware garante.\033[0m"
        )


if __name__ == "__main__":
    asyncio.run(main())
