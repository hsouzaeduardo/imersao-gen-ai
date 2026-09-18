"""
LAB 06 (MAF): o processo operacional.

Três topologias, os mesmos papéis da versão ADK:

  ADK                    MAF
  SequentialAgent        SequentialBuilder
  ParallelAgent          ConcurrentBuilder, que já monta o fan-out e o fan-in
  LoopAgent              não existe pronto: o loop é seu, em código ou em grafo cíclico
  output_key + {chave}   a conversa inteira é passada adiante entre os participantes

Essa última linha é a diferença mais importante e a que mais confunde
quem vem do ADK: no MAF os participantes de um workflow sequencial
trocam a conversa, não um dicionário de chaves. Se você quer estado
estruturado entre etapas, use shared state do workflow ou seus próprios
executores, não um `state` implícito.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.orchestrations import ConcurrentBuilder, SequentialBuilder
from dotenv import load_dotenv

from comum import middleware_habbo, chat_client, consultar_status_rede, listar_eventos_massivos

load_dotenv()

MCP_URL = os.getenv("TOOLBOX_MCP_URL", "http://localhost:5000/mcp")

CRITERIOS = """
CRITÉRIOS DE QUALIDADE DA AURORA
1. Até 100 palavras.
2. Zero jargão técnico sem explicação: OLT, ONU, LOS, latência, pacote.
3. Diz claramente qual é o próximo passo e de quem é a responsabilidade.
4. Nenhuma promessa de prazo que não veio de uma tool.
5. Tom cordial, sem pedir desculpas mais de uma vez.
"""


@asynccontextmanager
async def montar_papeis(credential):
    """Cria os agentes usados pelas três topologias."""
    async with MCPStreamableHTTPTool(
        name="toolbox", url=MCP_URL, description="Consultas aprovadas da Aurora."
    ) as toolbox:
        cli = chat_client(credential)

        papeis = {}

        # ---------- etapas do POP ----------
        papeis["triagem"] = Agent(
            client=cli,
            name="etapa_triagem",
            description="Classifica o chamado e identifica o cliente.",
            instructions="""
Você é a triagem da Aurora Fibra.
1. Chame buscar_cliente_por_cpf com o CPF informado, em dígitos.
2. Classifique em lentidao, sem_conexao, cobranca ou instalacao.
Responda APENAS com JSON, sem crase:
{"cpf": "...", "nome": "...", "cep": "...", "categoria": "...", "relato": "..."}
""",
            tools=[toolbox],
            middleware=middleware_habbo("etapa_triagem"),
        )

        papeis["diagnostico"] = Agent(
            client=cli,
            name="etapa_diagnostico",
            description="Investiga a causa provável usando rede e histórico.",
            instructions="""
Você é o diagnóstico técnico da Aurora Fibra.
A triagem já veio na conversa acima, use o CPF e o CEP que estão lá.
1. Chame consultar_status_rede com o CEP.
2. Chame listar_chamados_recentes com o CPF.
3. Conclua a causa provável.
Responda APENAS com JSON:
{"causa": "...", "escopo": "rede|individual|financeiro", "evidencias": ["..."]}
""",
            tools=[toolbox, consultar_status_rede],
            middleware=middleware_habbo("etapa_diagnostico"),
        )

        papeis["registro"] = Agent(
            client=cli,
            name="etapa_registro",
            description="Redige a resposta ao cliente e o registro interno.",
            instructions="""
Você é o registro do atendimento da Aurora Fibra.
Use a triagem e o diagnóstico que estão na conversa acima.

Produza duas partes, com estes títulos exatos:

RESPOSTA AO CLIENTE
Até 100 palavras, português claro, sem jargão, com o próximo passo.

REGISTRO INTERNO
Três linhas: categoria, causa provável e ação tomada.
""",
            middleware=middleware_habbo("etapa_registro"),
        )

        # ---------- verificações independentes ----------
        papeis["check_financeiro"] = Agent(
            client=cli,
            name="checagem_financeira",
            description="Verifica bloqueio financeiro.",
            instructions="""
Chame buscar_cliente_por_cpf e listar_faturas_em_aberto para o CPF informado.
Responda APENAS com JSON:
{"bloqueio_financeiro": true, "faturas_vencidas": 0, "detalhe": "..."}
""",
            tools=[toolbox],
            middleware=middleware_habbo("checagem_financeira"),
        )

        papeis["check_rede"] = Agent(
            client=cli,
            name="checagem_rede",
            description="Verifica incidente de rede na região.",
            instructions="""
Chame buscar_cliente_por_cpf para obter o CEP, depois consultar_status_rede
e listar_eventos_massivos.
Responda APENAS com JSON:
{"incidente_regiao": true, "severidade": "...", "previsao": "..."}
""",
            tools=[toolbox, consultar_status_rede, listar_eventos_massivos],
            middleware=middleware_habbo("checagem_rede"),
        )

        papeis["check_historico"] = Agent(
            client=cli,
            name="checagem_historico",
            description="Verifica reincidência nos últimos 90 dias.",
            instructions="""
Chame listar_chamados_recentes para o CPF informado.
Responda APENAS com JSON:
{"reincidente": true, "chamados_90d": 0, "ultimo": "..."}
""",
            tools=[toolbox],
            middleware=middleware_habbo("checagem_historico"),
        )

        papeis["consolidador"] = Agent(
            client=cli,
            name="consolidador",
            description="Junta as verificações e define a conduta.",
            instructions="""
Você consolida a abertura do atendimento da Aurora Fibra.
As três verificações vieram no texto acima, em JSON.

Precedência das condutas:
1. Bloqueio financeiro: trate cobrança primeiro, o resto não resolve.
2. Incidente na região: informe severidade e previsão, sem chamado individual.
3. Reincidência sem incidente de rede: encaminhe para N2 com prioridade.
4. Nada disso: roteiro padrão de diagnóstico.

Responda ao cliente em até 100 palavras, sem jargão,
e diga qual das quatro condutas foi aplicada.
""",
            middleware=middleware_habbo("consolidador"),
        )

        # ---------- loop de qualidade ----------
        papeis["redator"] = Agent(
            client=cli,
            name="redator",
            description="Escreve ou reescreve a resposta ao cliente.",
            instructions=f"""
Você redige a resposta final ao cliente da Aurora Fibra.
Se houver uma crítica no texto recebido, reescreva corrigindo exatamente
o que foi apontado. Caso contrário, escreva a primeira versão.
{CRITERIOS}
Responda apenas com o texto da resposta ao cliente.
""",
            middleware=middleware_habbo("redator"),
        )

        papeis["critico"] = Agent(
            client=cli,
            name="critico",
            description="Avalia a resposta contra os critérios de qualidade.",
            instructions=f"""
Você é o revisor de qualidade da Aurora Fibra.
{CRITERIOS}
Se a resposta cumprir todos os critérios, responda exatamente: APROVADA
Caso contrário, liste os problemas, um por linha, citando o número do critério
e a palavra ou frase que precisa mudar. Não reescreva o texto.
""",
            middleware=middleware_habbo("critico"),
        )

        yield papeis


# ---------------------------------------------------------------------------
# Topologias
# ---------------------------------------------------------------------------
def pipeline_sequencial(papeis) -> "object":
    """POP da Aurora: triagem, diagnóstico, registro, sempre nessa ordem."""
    return SequentialBuilder(
        participants=[papeis["triagem"], papeis["diagnostico"], papeis["registro"]],
        intermediate_output_from=[papeis["triagem"], papeis["diagnostico"]],
    ).build()


def pipeline_concorrente(papeis) -> "object":
    """As três verificações de abertura, em paralelo.

    O ConcurrentBuilder monta o dispatcher, o fan-out, o fan-in e um agregador
    padrão. A consolidação com regra de negócio fica no agente consolidador,
    chamado depois, porque cada ramo roda isolado e não enxerga os irmãos.
    """
    return ConcurrentBuilder(
        participants=[
            papeis["check_financeiro"],
            papeis["check_rede"],
            papeis["check_historico"],
        ]
    ).build()


async def loop_de_qualidade(papeis, rascunho: str, max_iteracoes: int = 3) -> tuple[str, int]:
    """Refina a resposta até o crítico aprovar ou até bater o limite.

    O MAF não tem um LoopAgent pronto como o ADK. O loop é seu:
    ou em Python, como aqui, ou como ciclo no grafo do WorkflowBuilder,
    com uma aresta condicional voltando para o redator.

    Returns:
        A resposta final e o número de iterações gastas.
    """
    texto = rascunho
    for iteracao in range(1, max_iteracoes + 1):
        critica = (await papeis["critico"].run(texto)).text.strip()
        if critica.upper().startswith("APROVADA"):
            return texto, iteracao

        pedido = f"Texto atual:\n{texto}\n\nCrítica a corrigir:\n{critica}"
        texto = (await papeis["redator"].run(pedido)).text.strip()

    return texto, max_iteracoes
