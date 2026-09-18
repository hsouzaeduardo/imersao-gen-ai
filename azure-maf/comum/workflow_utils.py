"""
Utilitários para rodar workflows do MAF na aula.

Os tipos de evento do workflow mudam entre versões. Em vez de amarrar os
labs a um formato específico, este helper extrai o que der de cada evento
e imprime de forma legível. Em produção você trata os eventos por tipo.

Um workflow em streaming emite muito evento: numa execução do lab 05 são
147 eventos, e 113 deles são pedaços de texto do mesmo parágrafo sendo
gerado token a token. Imprimir tudo transforma a demo em cachoeira e
esconde o que a aula quer mostrar, que é quem fez o quê e em que ordem.
Por isso o padrão aqui é ficar com os eventos de etapa concluída.
"""

from __future__ import annotations

# O texto real vem picado nos eventos `output`, um pedaço por vez.
# O `executor_completed` só carrega os objetos internos da etapa, com texto
# vazio, então ele não serve como fonte: serve como sinal de "acabou",
# o momento de descarregar o que foi acumulado daquele executor.
EVENTO_TEXTO = "output"
EVENTO_FIM = "executor_completed"


def extrair_texto(objeto) -> str:
    """Tenta obter texto legível de um evento, resposta ou mensagem do workflow."""
    if objeto is None:
        return ""

    if isinstance(objeto, str):
        return objeto.strip()

    # executor_completed entrega uma lista de mensagens: interessa a última
    # com conteúdo, que é a fala final daquele executor.
    if isinstance(objeto, (list, tuple)):
        for item in reversed(objeto):
            texto = extrair_texto(item)
            if texto:
                return texto
        return ""

    for atributo in ("text", "message", "content"):
        valor = getattr(objeto, atributo, None)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()

    dados = getattr(objeto, "data", None)
    if dados is not None and dados is not objeto:
        interno = extrair_texto(dados)
        if interno:
            return interno

    resposta = getattr(objeto, "agent_run_response", None)
    if resposta is not None:
        texto = getattr(resposta, "text", None)
        if texto:
            return texto.strip()

    mensagens = getattr(objeto, "messages", None)
    if mensagens:
        return extrair_texto(list(mensagens))

    return ""


async def rodar_workflow(workflow, entrada, mostrar_intermediarios: bool = True) -> list[str]:
    """Roda o workflow em streaming e imprime o que cada etapa produziu.

    Returns:
        A lista de textos capturados, na ordem em que apareceram.
    """
    capturados: list[str] = []
    buffer: dict[str, list[str]] = {}

    def descarregar(quem: str) -> None:
        texto = "".join(buffer.pop(quem, [])).strip()
        # O mesmo texto reaparece quando o workflow propaga o resultado
        # adiante. Repetir na tela só confunde a turma.
        if not texto or (capturados and texto == capturados[-1]):
            return
        capturados.append(texto)
        if mostrar_intermediarios:
            print(f"\n\033[90m[{quem}]\033[0m {texto[:700]}")

    # Em versões anteriores isto era `workflow.run_stream(entrada)`, que ainda
    # aparece em material antigo. Hoje o streaming é um parâmetro do run.
    async for evento in workflow.run(entrada, stream=True):
        tipo = str(getattr(evento, "type", ""))
        quem = str(getattr(evento, "executor_id", "") or "etapa")

        if tipo == EVENTO_TEXTO:
            # Sem strip aqui: o espaço entre as palavras chega como borda do
            # pedaço, e limpar cada um cola o parágrafo inteiro sem espaços.
            pedaco = getattr(getattr(evento, "data", None), "text", None)
            if isinstance(pedaco, str) and pedaco:
                buffer.setdefault(quem, []).append(pedaco)
        elif tipo == EVENTO_FIM:
            descarregar(quem)

    # Um executor pode terminar sem emitir o evento de fim.
    for quem in list(buffer):
        descarregar(quem)

    return capturados
