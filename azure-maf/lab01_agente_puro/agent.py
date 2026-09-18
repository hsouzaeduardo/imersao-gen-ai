"""
LAB 01 (MAF): ARI no primeiro dia, sem crachá.

    python -m lab01_agente_puro.agent

Diferenças para a versão ADK, e vale dizer isso em voz alta na aula:

  ADK                              MAF
  LlmAgent(model="gemini-...")     Agent(OpenAIChatClient(azure_endpoint=...), ...)
  instruction=                     instructions=
  adk web / adk run                DevUI, ou este script, ou hospedar como API

  (Em material mais antigo o agente se chamava ChatAgent e o cliente
   AzureOpenAIChatClient, de agent_framework.azure. Os dois foram renomeados;
   veja a tabela completa em comum/clients.py.)

No MAF o modelo entra por injeção do chat client. Trocar Azure OpenAI
por Foundry Agent Service é trocar uma linha em comum/clients.py.
"""

import asyncio

from azure.identity.aio import AzureCliCredential

from comum import criar_agente, ligar_telemetria

INSTRUCTION_VAGA = """
Você é um assistente de atendimento da Aurora Fibra. Seja útil e educado.
"""

INSTRUCTION_PROTOCOLO = """
Você é o ARI, assistente de suporte N1 da Aurora Fibra, provedor de internet.

IDENTIDADE
Fale em português do Brasil, em tom cordial e direto. Nunca use jargão de rede
sem explicar em uma frase simples.

PROTOCOLO DE ATENDIMENTO
1. Cumprimente e pergunte o nome do cliente, se ainda não souber.
2. Classifique o problema antes de responder qualquer coisa:
   lentidão, sem conexão, cobrança, instalação, outros.
3. Faça no máximo duas perguntas de qualificação por vez.
4. Ao encerrar, resuma em até três linhas o que foi combinado.

LIMITES, ESTA PARTE É OBRIGATÓRIA
Você não tem acesso a nenhum sistema da Aurora nesta versão.
Não consegue consultar status de rede, faturas, contratos ou chamados.
Quando o cliente pedir qualquer um desses dados, diga com todas as letras que
não tem acesso. Nunca invente número de protocolo, valor de fatura,
velocidade medida ou previsão de reparo.

ESTILO
Respostas de até 120 palavras. Sem listas longas. Sem emojis.
"""

INSTRUCTION_ATIVA = INSTRUCTION_PROTOCOLO


async def main() -> None:
    ligar_telemetria("ari-lab01")

    async with AzureCliCredential() as cred:
        agente = criar_agente(
            name="ari_n1",
            instructions=INSTRUCTION_ATIVA,
            credential=cred,
        )

        # Sem thread, cada run é uma conversa nova. Isso é proposital no lab 01.
        for pergunta in [
            "oi, minha internet está muito lenta hoje",
            "meu CPF é 111.222.333-44, qual o status da minha conexão?",
            "qual era mesmo o meu CPF?",
        ]:
            print(f"\n\033[1mCliente:\033[0m {pergunta}")
            resposta = await agente.run(pergunta)
            print(f"\033[1mARI:\033[0m {resposta.text.strip()}")

        print(
            "\n\033[93mRepare na terceira resposta: ele não sabe o CPF que você "
            "acabou de informar.\nSem thread, não existe conversa, existem três "
            "monólogos. Isso é o lab 02a.\033[0m"
        )


if __name__ == "__main__":
    asyncio.run(main())
