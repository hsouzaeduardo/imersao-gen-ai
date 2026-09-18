"""
LAB 02b (MAF): o prontuário do cliente.

    python -m lab02_memoria.b_memoria_longa

Sessão é a conversa de hoje. Prontuário é o que vale para sempre.
No MAF isso se chama context provider: um componente que injeta contexto
antes de cada chamada ao modelo e pode gravar o que aprendeu depois.

Este lab implementa a memória de duas formas, e a diferença entre elas
é justamente o conteúdo da aula:

  A) explícita, com duas tools: o modelo decide quando gravar e quando buscar
  B) nativa, com um context provider (Redis, Mem0 ou Memory do Foundry):
     a injeção acontece sozinha, em todo turno

A versão A roda em qualquer máquina e é o que usamos ao vivo.
A versão B está no fim do arquivo e é o caminho de produção em Azure.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Annotated

from agent_framework import tool
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv
from pydantic import Field

from comum import criar_agente, ligar_telemetria

load_dotenv()

ARQUIVO = os.path.join(os.path.dirname(__file__), "prontuarios.json")


def _carregar() -> dict:
    if not os.path.exists(ARQUIVO):
        return {}
    with open(ARQUIVO, encoding="utf-8") as f:
        return json.load(f)


def _salvar(dados: dict) -> None:
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


@tool(
    name="gravar_no_prontuario",
    description=(
        "Grava no prontuário do cliente um fato durável: preferência de horário, "
        "canal de contato preferido, particularidade da instalação. "
        "Não grave o problema do dia, grave só o que vale para os próximos contatos."
    ),
)
def gravar_no_prontuario(
    cpf: Annotated[str, Field(description="CPF do cliente, somente dígitos.")],
    fato: Annotated[str, Field(description="O fato durável, em uma frase.")],
) -> dict:
    """Escreve no prontuário."""
    dados = _carregar()
    fatos = dados.setdefault(cpf, [])
    if fato not in fatos:
        fatos.append(fato)
    _salvar(dados)
    return {"status": "ok", "prontuario": fatos}


@tool(
    name="ler_prontuario",
    description=(
        "Lê o prontuário do cliente com o que já foi aprendido em contatos anteriores. "
        "Chame no primeiro turno de todo atendimento, antes de perguntar qualquer coisa."
    ),
)
def ler_prontuario(
    cpf: Annotated[str, Field(description="CPF do cliente, somente dígitos.")],
) -> dict:
    """Lê o prontuário."""
    fatos = _carregar().get(cpf, [])
    return {"status": "ok", "prontuario": fatos, "vazio": not fatos}


INSTRUCTION = """
Você é o ARI, assistente de suporte N1 da Aurora Fibra.
Fale em português do Brasil, tom cordial e direto, respostas de até 120 palavras.

USO DO PRONTUÁRIO, PARTE OBRIGATÓRIA DO PROTOCOLO
1. Assim que souber o CPF, chame ler_prontuario antes de perguntar qualquer coisa.
2. Se o prontuário trouxer preferências, use sem perguntar de novo.
3. Sempre que o cliente informar algo durável, preferência de horário,
   canal de contato, particularidade do imóvel, chame gravar_no_prontuario.
4. Prontuário vazio não é problema: siga o atendimento e não invente histórico.

LIMITES
Você ainda não tem acesso a status de rede, faturas ou chamados.
"""


async def main() -> None:
    ligar_telemetria("ari-lab02b")

    async with AzureCliCredential() as cred:
        agente = criar_agente(
            name="ari_com_prontuario",
            instructions=INSTRUCTION,
            tools=[ler_prontuario, gravar_no_prontuario],
            credential=cred,
        )

        print("\033[94m=== ATENDIMENTO 1, terça-feira ===\033[0m")
        t1 = agente.create_session()
        for fala in [
            "oi, sou a Marcela, CPF 111.222.333-44, internet lenta à noite",
            "se precisar de visita técnica, só de manhã, e me avise por WhatsApp, nunca por telefone",
        ]:
            print(f"\n\033[1mCliente:\033[0m {fala}")
            r = await agente.run(fala, session=t1)
            print(f"\033[1mARI:\033[0m {r.text.strip()}")

        print("\n\033[94m=== ATENDIMENTO 2, três semanas depois, sessão nova ===\033[0m")
        t2 = agente.create_session()
        for fala in [
            "oi, aqui é a Marcela de novo, CPF 111.222.333-44, voltou a ficar lenta",
            "dá pra mandar um técnico? vocês já sabem meu horário, né?",
        ]:
            print(f"\n\033[1mCliente:\033[0m {fala}")
            r = await agente.run(fala, session=t2)
            print(f"\033[1mARI:\033[0m {r.text.strip()}")

        print(
            "\n\033[93mVerificação: ele propôs manhã e WhatsApp sem perguntar?"
            f"\nO prontuário está em {ARQUIVO}, abra e mostre para a turma."
            "\nApague o arquivo e rode de novo: ele volta a perguntar tudo.\033[0m"
        )


# ---------------------------------------------------------------------------
# VERSÃO B: context provider nativo, o caminho de produção em Azure
# ---------------------------------------------------------------------------
# A diferença prática: some a tool call do trace. A injeção do contexto
# acontece antes de cada chamada ao modelo, e a extração dos fatos é feita
# pelo provider, não pelo prompt.
#
# Com Azure Managed Redis:
#
#   from agent_framework_redis import RedisContextProvider
#   agente = Agent(
#       chat_client(cred),
#       INSTRUCTION,
#       context_providers=[RedisContextProvider(
#           redis_url=os.environ["REDIS_URL"],
#           application_id="aurora",
#           agent_id="cpf:11122233344",    # escopo, isso é isolamento de dado pessoal
#       )],
#   )
#
# Com Mem0, que faz extração e deduplicação dos fatos:
#
#   from agent_framework_mem0 import Mem0Provider
#   agente = Agent(..., context_providers=[Mem0Provider(user_id="cpf:11122233344")])
#
# Com Foundry Agent Service, a memória é serviço gerenciado do projeto:
# o agente e as threads vivem no Azure AI Foundry e a memória é configurada lá.
#
# ATENÇÃO: o nome das classes e dos parâmetros muda entre versões destes pacotes.
# Confira com `pip show agent-framework-redis` antes da aula.
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    asyncio.run(main())
