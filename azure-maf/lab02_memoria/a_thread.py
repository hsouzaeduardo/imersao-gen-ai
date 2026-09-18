"""
LAB 02a (MAF): o caderno de anotações.

    python -m lab02_memoria.a_thread
    python -m lab02_memoria.a_thread --continuar

No ADK, o runner criava a sessão e o state vinha junto.
No MAF, memória de trabalho é explícita: você cria uma AgentSession e passa
em cada run. Sem sessão, não existe conversa.

E onde essa sessão mora é decisão sua:
  - padrão: na memória do processo, morre no restart
  - RedisHistoryProvider: sobrevive ao restart e serve várias réplicas
  - modo foundry: as threads vivem no Azure AI Foundry Agent Service

NOMES QUE MUDARAM
  AgentThread                    AgentSession
  agente.get_new_thread()        agente.create_session(session_id=...)
  agente.run(x, thread=...)      agente.run(x, session=...)
  chat_message_store_factory=    context_providers=[RedisHistoryProvider(...)]

O `session_id` é o que faz a memória durar: reabrir a sessão com o mesmo id
é o que permite ao --continuar reencontrar a conversa no Redis.
"""

from __future__ import annotations

import asyncio
import os
import sys

from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

from comum import criar_agente, ligar_telemetria

load_dotenv()

SESSION_ID = "aurora:atendimento:001"

INSTRUCTION = """
Você é o ARI, assistente de suporte N1 da Aurora Fibra.
Fale em português do Brasil, tom cordial e direto, respostas de até 120 palavras.

Nunca pergunte de novo algo que o cliente já informou nesta conversa.
Você ainda não tem acesso a status de rede, faturas ou chamados,
e nunca inventa esses dados.
"""


def history_provider():
    """Devolve o provider de histórico em Redis, se houver Redis de pé.

    Só a variável estar preenchida não basta: em sala o container cai, e um
    agente que estoura no meio da demo ensina menos que um que avisa e segue.
    Por isso testamos a conexão antes, e caímos para o histórico em memória,
    que é o padrão do MAF, quando o Redis não responde.
    """
    url = os.getenv("REDIS_URL")
    if not url:
        return None

    try:
        import redis as redis_sync

        redis_sync.from_url(url, socket_connect_timeout=2).ping()
    except Exception as e:
        print(f"\033[93mRedis configurado em {url} mas não respondeu ({type(e).__name__}).")
        print("Seguindo com o histórico em memória: o --continuar vai esquecer.\033[0m")
        return None

    from agent_framework_redis import RedisHistoryProvider

    # ssl=False porque o Redis local do docker-compose fala redis://, sem TLS.
    # Para o Azure Cache (rediss://, porta 10000) o default ssl=True é o certo.
    return RedisHistoryProvider(redis_url=url, ssl=url.startswith("rediss://"))


async def main() -> None:
    ligar_telemetria("ari-lab02a")
    continuar = "--continuar" in sys.argv

    async with AzureCliCredential() as cred:
        provider = history_provider()
        extras = {"context_providers": [provider]} if provider else {}

        agente = criar_agente(
            name="ari_com_caderno",
            instructions=INSTRUCTION,
            credential=cred,
            **extras,
        )

        # Mesmo id nas duas execuções: é isso que o --continuar reaproveita.
        sessao = agente.create_session(session_id=SESSION_ID)

        if not continuar:
            falas = [
                "boa tarde, minha internet está muito lenta à noite",
                "meu nome é Marcela Tavares Pinto e meu CPF é 111.222.333-44",
                "além disso, ontem caiu tudo por umas duas horas",
            ]
        else:
            falas = ["você ainda lembra do meu CPF e do que eu reclamei?"]

        for fala in falas:
            print(f"\n\033[1mCliente:\033[0m {fala}")
            resposta = await agente.run(fala, session=sessao)
            print(f"\033[1mARI:\033[0m {resposta.text.strip()}")

        if not continuar:
            print(
                "\n\033[93mAgora rode com --continuar."
                "\nCom Redis configurado, ele lembra: a sessão está no Redis."
                "\nSem Redis, ele esquece: a sessão morreu com o processo."
                "\nEsse contraste é o lab inteiro.\033[0m"
            )


if __name__ == "__main__":
    asyncio.run(main())
