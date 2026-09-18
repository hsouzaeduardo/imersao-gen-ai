"""
Runner do lab 06.

    python -m lab06_workflows.run sequencial
    python -m lab06_workflows.run concorrente
    python -m lab06_workflows.run loop
    python -m lab06_workflows.run comparar     # cronômetro: sequência x concorrência
    python -m lab06_workflows.run completo
"""

from __future__ import annotations

import asyncio
import sys
import time

from agent_framework.orchestrations import SequentialBuilder
from azure.identity.aio import AzureCliCredential

from comum import ligar_telemetria, rodar_workflow
from lab06_workflows.pipelines import (
    loop_de_qualidade,
    montar_papeis,
    pipeline_concorrente,
    pipeline_sequencial,
)

CASO = (
    "Meu CPF é 44455566677. Minha internet não funciona há dois dias "
    "e eu já liguei antes sobre isso."
)


async def main() -> None:
    ligar_telemetria("ari-lab06")
    modo = sys.argv[1] if len(sys.argv) > 1 else "sequencial"

    async with AzureCliCredential() as cred:
        async with montar_papeis(cred) as papeis:

            if modo == "sequencial":
                print("\033[94m=== POP: triagem, diagnóstico, registro ===\033[0m")
                await rodar_workflow(pipeline_sequencial(papeis), CASO)

            elif modo == "concorrente":
                print("\033[94m=== Três verificações em paralelo ===\033[0m")
                saidas = await rodar_workflow(pipeline_concorrente(papeis), CASO)
                print("\n\033[94m=== Consolidação ===\033[0m")
                conduta = await papeis["consolidador"].run("\n\n".join(saidas))
                print(conduta.text.strip())

            elif modo == "loop":
                print("\033[94m=== Loop de qualidade ===\033[0m")
                rascunho = (
                    "Prezado cliente, identificamos degradação de OLT com perda de "
                    "pacotes e latência elevada no seu PON. O LOS do ONU indica falha "
                    "no enlace. Assim que possível a equipe atuará."
                )
                print(f"\n\033[90m[rascunho]\033[0m {rascunho}")
                final, voltas = await loop_de_qualidade(papeis, rascunho)
                print(f"\n\033[1m[aprovada em {voltas} iteração(ões)]\033[0m {final}")

            elif modo == "comparar":
                sequencia = SequentialBuilder(
                    participants=[
                        papeis["check_financeiro"],
                        papeis["check_rede"],
                        papeis["check_historico"],
                    ]
                ).build()

                print("\033[94m=== SEQUENCIAL ===\033[0m")
                t0 = time.perf_counter()
                await rodar_workflow(sequencia, CASO, mostrar_intermediarios=False)
                t_seq = time.perf_counter() - t0
                print(f"\033[93mTempo: {t_seq:.1f}s\033[0m")

                print("\n\033[94m=== CONCORRENTE ===\033[0m")
                t0 = time.perf_counter()
                await rodar_workflow(pipeline_concorrente(papeis), CASO, mostrar_intermediarios=False)
                t_par = time.perf_counter() - t0
                print(f"\033[93mTempo: {t_par:.1f}s\033[0m")

                print("\n" + "=" * 52)
                print(f"Sequencial: {t_seq:.1f}s")
                print(f"Concorrente: {t_par:.1f}s")
                if t_par > 0:
                    print(f"Ganho: {t_seq / t_par:.1f}x")
                print("=" * 52)

            elif modo == "completo":
                print("\033[94m=== 1. Verificações em paralelo ===\033[0m")
                saidas = await rodar_workflow(
                    pipeline_concorrente(papeis), CASO, mostrar_intermediarios=False
                )
                conduta = (await papeis["consolidador"].run("\n\n".join(saidas))).text.strip()
                print(conduta)

                print("\n\033[94m=== 2. POP em ordem fixa ===\033[0m")
                etapas = await rodar_workflow(
                    pipeline_sequencial(papeis), CASO, mostrar_intermediarios=False
                )
                rascunho = etapas[-1] if etapas else conduta

                print("\n\033[94m=== 3. Loop de qualidade ===\033[0m")
                final, voltas = await loop_de_qualidade(papeis, rascunho)
                print(f"\n\033[1m[aprovada em {voltas} iteração(ões)]\033[0m {final}")

            else:
                print(f"Modo desconhecido: {modo}")
                print("Use: sequencial | concorrente | loop | comparar | completo")


if __name__ == "__main__":
    asyncio.run(main())
