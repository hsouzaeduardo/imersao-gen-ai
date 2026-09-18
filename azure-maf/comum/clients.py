"""
Fábrica de chat client dos seis labs.

O MAF separa o agente do provedor de modelo. Trocar Azure OpenAI por
Foundry Agent Service, ou por OpenAI direto, é trocar o cliente,
não o agente. Esse desacoplamento é um dos argumentos do framework
e vale mostrar no lab 01.

Dois caminhos:

  ARI_CLIENT=aoai     OpenAIChatClient com azure_endpoint
                      o estado da conversa mora no seu processo,
                      você controla histórico, store e persistência

  ARI_CLIENT=foundry  FoundryChatClient
                      o agente e as threads vivem no Azure AI Foundry Agent Service,
                      o serviço guarda o histórico e aplica as políticas do projeto

NOMES QUE MUDARAM
O pacote reorganizou a API depois que este material foi escrito. Quem
aprendeu pela documentação antiga vai procurar os nomes da coluna da esquerda:

  ChatAgent                                 Agent
  AgentThread                               AgentSession
  ai_function                               tool
  agent_framework.azure.AzureOpenAIChatClient   agent_framework_openai.OpenAIChatClient
  agent_framework.azure.AzureAIAgentClient      agent_framework_foundry.FoundryChatClient

O pacote agent-framework-azure-ai foi descontinuado e substituído por
agent-framework-openai e agent-framework-foundry. As versões estão
fixadas no requirements.txt justamente porque essa API ainda se move.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MODO = os.getenv("ARI_CLIENT", "aoai").lower()


def chat_client(credential=None):
    """Devolve o chat client configurado por ambiente.

    Args:
        credential: credencial async do azure-identity. Só é usada no modo foundry
            e no modo aoai sem chave, quando a autenticação é por Entra ID.
    """
    if MODO == "foundry":
        from agent_framework_foundry import FoundryChatClient

        return FoundryChatClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5.4"),
            credential=credential,
        )

    from agent_framework_openai import OpenAIChatClient

    # `model` aqui é o nome do DEPLOYMENT no Azure, não o nome do modelo.
    # Não passamos api_version de propósito: o cliente negocia uma versão
    # compatível sozinho, e fixar uma antiga devolve 400 "API version not supported".
    comum = {
        "model": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-5.4"),
        "azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
    }

    chave = os.getenv("AZURE_OPENAI_API_KEY") or None
    if chave:
        return OpenAIChatClient(api_key=chave, **comum)

    # Sem chave, autentica com Entra ID. É o caminho de produção.
    return OpenAIChatClient(credential=credential, **comum)


def criar_agente(name: str, instructions: str, tools=None, credential=None, **kwargs):
    """Atalho usado pelos labs para criar um Agent já com o cliente certo.

    Já vem com o middleware do Habbo, que publica na sala o que o agente está
    fazendo. Sem HABBO_URL no .env ele é no-op, então não muda nada para quem
    roda os labs sem a visualização.
    """
    from agent_framework import Agent

    from .habbo import middleware_habbo

    kwargs["middleware"] = [*middleware_habbo(name), *(kwargs.get("middleware") or [])]

    return Agent(
        chat_client(credential),
        instructions,
        name=name,
        tools=tools or [],
        **kwargs,
    )
