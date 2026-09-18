"""
Observabilidade: o MAF emite spans OpenTelemetry seguindo as convenções GenAI.

Ligue isso no lab 01 e deixe ligado até o 06. No fim do curso,
o Application Insights mostra a árvore inteira de um atendimento:
agente, chamada de modelo, tool, workflow, executor.

Esse é um ganho de plataforma que vale mostrar cedo, porque muda
a conversa com a área de operações.
"""

import os


def ligar_telemetria(nome_servico: str = "ari-aurora") -> bool:
    """Liga o envio de traces para o Application Insights, se configurado.

    Returns:
        True se a telemetria foi ligada, False se ficou desligada.
    """
    if os.getenv("ENABLE_OTEL", "false").lower() != "true":
        return False

    conn = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not conn:
        print("ENABLE_OTEL=true mas falta APPLICATIONINSIGHTS_CONNECTION_STRING.")
        return False

    from azure.monitor.opentelemetry import configure_azure_monitor

    os.environ.setdefault("OTEL_SERVICE_NAME", nome_servico)
    # Sem isso os spans vêm sem o conteúdo das mensagens.
    os.environ.setdefault("ENABLE_SENSITIVE_DATA", "true")
    configure_azure_monitor(connection_string=conn)
    return True
