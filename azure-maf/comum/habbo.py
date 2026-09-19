"""
Publica no Habbo o que cada agente está fazendo, para a turma ver ao vivo.

A sala em https://github.com/hsouzaeduardo/habbo-agents desenha até 12 avatares
com um balão de fala. Aqui os avatares são os agentes dos labs: quando o
coordenador tria, o Felipe fala; quando as três checagens do lab 06 rodam em
paralelo, três avatares falam ao mesmo tempo. É a única forma que eu conheço de
mostrar concorrência de agente sem pedir para a turma ler log.

TRÊS REGRAS QUE ESTE MÓDULO NÃO PODE QUEBRAR

1. Nunca derrubar um lab. Isto é enfeite de aula: se o Habbo estiver fora,
   com chave errada ou a rede da empresa bloquear, o lab segue igual. Toda
   falha é engolida de propósito, e o silêncio aqui é a feature.
2. Nunca atrasar um lab. A publicação é disparada e esquecida, sem esperar
   resposta. O cronômetro do lab 06 mede o modelo, não o Habbo.
3. Ser opcional. Sem HABBO_URL no .env, tudo vira no-op e nenhum lab muda.

Ligar: preencha HABBO_URL e HABBO_API_KEY no .env.
"""

from __future__ import annotations

import asyncio
import os

import httpx
from agent_framework import AgentContext, FunctionInvocationContext, agent_middleware, function_middleware

URL = (os.getenv("HABBO_URL") or "").rstrip("/")
CHAVE = os.getenv("HABBO_API_KEY") or ""
TIMEOUT = 3.0
LIMITE_FALA = 140  # a API corta acima disso

# Nome do agente no lab -> avatar na sala.
# Os nomes vêm do `name=` de cada Agent. Quem não estiver aqui não aparece,
# o que é melhor que aparecer no avatar de outro e confundir a leitura.
MAPA: dict[str, int] = {
    # A sala tem 12 avatares, e o curso tem 19 agentes. O critério do rateio é
    # um só: quem pode aparecer AO MESMO TEMPO precisa de avatar diferente.
    # Quem nunca divide a tela pode dividir o avatar.
    #
    # Labs 01 a 04: um por avatar, porque cada um roda sozinho.
    "ari_n1": 1,
    "ari_com_caderno": 2,
    "ari_com_prontuario": 3,
    "ari_com_acesso": 4,
    "ari_com_dados": 5,
    # Quem coordena. Os três nunca rodam juntos.
    "ari_coordenador": 6,
    "ari_maestro": 6,
    "ari_maestro_a2a": 6,
    # Os três especialistas do lab 05, as três checagens paralelas do lab 06 e
    # as três etapas do POP caem nos mesmos 7, 8 e 9. É a fileira que a turma
    # olha quando você compara sequencial e concorrente, e por isso ela precisa
    # de três avatares distintos — nunca junte duas destas linhas no mesmo id.
    "agente_cobranca": 7,
    "checagem_financeira": 7,
    "etapa_triagem": 7,
    "agente_tecnico": 8,
    "checagem_rede": 8,
    "etapa_diagnostico": 8,
    "tecnico_aurora": 8,
    "agente_agendamento": 9,
    "checagem_historico": 9,
    "etapa_registro": 9,
    # O fecho do lab 06.
    "consolidador": 10,
    "redator": 11,
    "critico": 12,
}

# Nome da tool -> frase legível. Sem isto o balão mostra identificador de
# código, que não diz nada para quem está assistindo.
FALA_TOOL: dict[str, str] = {
    "buscar_cliente_por_cpf": "Buscando o cadastro do cliente",
    "listar_faturas_em_aberto": "Consultando faturas em aberto",
    "listar_chamados_recentes": "Verificando chamados recentes",
    "consultar_agenda_tecnica": "Olhando a agenda técnica",
    "abrir_chamado": "Abrindo um chamado",
    "consultar_status_rede": "Checando o status da rede",
    "reiniciar_roteador": "Reiniciando o roteador",
    "listar_eventos_massivos": "Listando incidentes ativos",
    "registrar_autorizacao_reinicio": "Registrando a autorização do cliente",
    "gravar_no_prontuario": "Anotando no prontuário",
    "ler_prontuario": "Lendo o prontuário",
    "consultar_cobranca": "Consultando o especialista de cobrança",
    "consultar_tecnico": "Consultando o especialista técnico",
    "consultar_agenda": "Consultando o especialista de agendamento",
}

ligado = bool(URL)

# O asyncio só mantém referência fraca das tasks: sem guardar aqui, o coletor
# de lixo pode matar a publicação antes de ela sair.
_pendentes: set[asyncio.Task] = set()


def _cabecalhos() -> dict[str, str]:
    cab = {"Content-Type": "application/json"}
    if CHAVE:
        cab["x-api-key"] = CHAVE
    return cab


async def _enviar(metodo: str, caminho: str, corpo: dict | None = None) -> None:
    """Uma chamada ao Habbo. Engole qualquer falha: ver a regra 1 do topo."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
            await cli.request(metodo, f"{URL}{caminho}", headers=_cabecalhos(), json=corpo)
    except Exception:
        pass


def _disparar(corotina) -> None:
    """Agenda sem esperar. Fora de um event loop, desiste em silêncio."""
    try:
        tarefa = asyncio.get_running_loop().create_task(corotina)
    except RuntimeError:
        corotina.close()
        return
    _pendentes.add(tarefa)
    tarefa.add_done_callback(_pendentes.discard)


def publicar(agente: str, atividade: str) -> None:
    """Coloca `agente` na sala com uma fala. Silencioso se o módulo está desligado."""
    if not ligado:
        return
    avatar = MAPA.get(agente)
    if avatar is None:
        return
    _disparar(_enviar("POST", "/api/activity",
                      {"agentID": avatar, "activity": atividade[:LIMITE_FALA]}))


async def limpar_sala() -> None:
    """Tira todos os avatares da sala. Use antes e depois de uma demo.

    Diferente das publicações, aqui esperamos de fato: chamar isto no fim de um
    lab e deixar como tarefa solta faria o processo morrer antes de a sala
    esvaziar, e a próxima demo começaria suja.
    """
    if not ligado:
        return
    await asyncio.gather(*(_enviar("DELETE", f"/api/agent/{i}")
                           for i in sorted(set(MAPA.values()))))


def middleware_habbo(nome: str) -> list:
    """Middlewares que publicam na sala em nome de `nome`.

    O nome entra por parâmetro, e não é lido do contexto em tempo de execução,
    por um motivo que só apareceu testando: o `FunctionInvocationContext` não
    carrega o agente, só a função. A primeira versão disto guardava o agente do
    turno num ContextVar, e no lab 05 as consultas ao banco feitas pelo
    especialista de cobrança apareciam no balão do maestro. O framework cria
    tasks internas entre o middleware de agente e o de função, e um ContextVar
    setado depois da criação da task não chega lá dentro.

    Fechar o nome por closure, um middleware por agente, elimina a dúvida:
    cada avatar só fala do que ele mesmo fez.
    """

    @agent_middleware
    async def habbo_agente(context: AgentContext, next) -> None:
        publicar(nome, "Assumindo o atendimento")
        await next()

    @function_middleware
    async def habbo_tool(context: FunctionInvocationContext, next) -> None:
        # É este que dá a granularidade de aula: sem ele o avatar fica parado
        # em "Assumindo o atendimento" durante três consultas ao banco, e quem
        # assiste não vê nada acontecer.
        ferramenta = getattr(context.function, "name", "") or ""
        publicar(nome, FALA_TOOL.get(ferramenta, f"Executando {ferramenta}"))
        await next()

    return [habbo_agente, habbo_tool]
