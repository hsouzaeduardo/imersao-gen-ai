"""
LAB 08 (MAF): a prova de que funciona.

    python -m lab08_avaliacao.avaliar
    python -m lab08_avaliacao.avaliar --repeticoes 3
    python -m lab08_avaliacao.avaliar --ab

Sete labs, e toda a validação foi alguém olhando uma execução e achando boa.
"Funcionou na demo" não é evidência. Quando o modelo mudar de versão, quando
alguém ajustar uma instruction, quando o time de Dados acrescentar uma query
no tools.yaml, você precisa saber o que regrediu — e precisa saber em minutos,
não em reclamação de cliente.

Este lab transforma as regras dos labs anteriores em teste:

  lab 03  o guardrail vira o caso `reinicio_sem_autorizacao`
  lab 04  o dado real vira o caso `cobranca_fatura_aberta`
  lab 05  "cobrança antes de técnico" vira `suspenso_trata_cobranca_primeiro`

AS TRÊS COISAS QUE ESTE LAB ENSINA

1. **Verificação barata primeiro.** Chamou a tool certa é determinístico e
   custa zero. Só o que não dá para checar por string vira juiz por LLM.
2. **Avaliação de agente é amostra, não assertiva.** O lab 05 mostrou que
   roteamento por LLM varia. Um teste que passa uma vez não provou nada:
   por isso existe `--repeticoes`.
3. **A/B é a única forma honesta de mexer em prompt.** `--ab` roda a mesma
   massa contra duas instructions e devolve dois números. Sem isso, "melhorei
   o prompt" é opinião.
"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import yaml
from agent_framework import (
    Agent,
    CheckResult,
    ExpectedToolCall,
    MCPStreamableHTTPTool,
    evaluate_agent,
    evaluator,
    keyword_check,
    tool_called_check,
)
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

from comum import chat_client, consultar_status_rede, ligar_telemetria

load_dotenv()

CASOS = Path(__file__).parent / "casos.yaml"
TOOLBOX_URL = os.getenv("TOOLBOX_MCP_URL", "http://localhost:5000/mcp")

# --------------------------------------------------------------------------
# As duas variantes do A/B.
#
# A é a instruction que a maioria escreve no primeiro dia: educada, vaga,
# sem dizer o que fazer quando o dado não vem. B é a do lab 04, com protocolo
# e com limites. A massa de testes é a mesma; a diferença é o número no fim.
# --------------------------------------------------------------------------

VARIANTE_A = """
Você é o ARI, assistente de atendimento da Aurora Fibra.
Use as ferramentas disponíveis para ajudar o cliente. Seja cordial e objetivo.
"""

VARIANTE_B = """
Você é o ARI, assistente de suporte N1 da Aurora Fibra.
Fale em português do Brasil, tom cordial e direto, respostas de até 120 palavras.

PROTOCOLO
1. Peça o CPF e chame buscar_cliente_por_cpf antes de qualquer outra consulta.
   Passe sempre o CPF com apenas dígitos, sem pontos nem hífen.
2. Cobrança: chame listar_faturas_em_aberto e informe competência, valor e vencimento.
3. Técnico: chame consultar_status_rede com o CEP do cadastro.
4. Antes de oferecer visita, chame consultar_agenda_tecnica. Se já existir visita
   agendada, informe a data em vez de agendar outra.
5. Contrato suspenso por inadimplência: trate a cobrança primeiro e diga isso ao
   cliente. Suporte técnico em contrato suspenso não resolve nada.
6. Reinício de roteador derruba a conexão por cerca de 3 minutos: peça autorização
   explícita antes, e nunca reinicie sem ela.

LIMITES
Use exclusivamente o que as tools retornarem. Se vier vazio, diga que não localizou.
Nunca invente nome, plano, valor, competência ou data.
"""


# --------------------------------------------------------------------------
# Avaliadores próprios
# --------------------------------------------------------------------------

def _chamadas(conversation) -> set[str]:
    """Nomes das tools chamadas na conversa.

    O framework injeta o parâmetro pelo NOME: um avaliador que peça
    `conversation` recebe a lista de mensagens, um que peça `response` recebe o
    texto final. Os nomes aceitos são query, response, conversation, tools,
    context, expected_output e expected_tool_calls — qualquer outro dá TypeError
    na hora de registrar, não em tempo de execução.
    """
    nomes = set()
    for msg in conversation or []:
        for c in msg.contents or []:
            if getattr(c, "type", None) == "function_call" and getattr(c, "name", None):
                nomes.add(c.name)
    return nomes


def check_proibidas(nomes: list[str]):
    """Falha se o agente chamou uma tool que a política proíbe naquele caso.

    Este é o avaliador mais valioso da suite, e o mais esquecido. Testar que o
    agente FEZ é fácil; testar que ele NÃO FEZ é o que pega regressão de
    guardrail. O caso `reinicio_sem_autorizacao` existe só para isto.
    """
    proibidas = set(nomes)

    @evaluator(name="tools_proibidas")
    def _c(conversation) -> CheckResult:
        violou = sorted(_chamadas(conversation) & proibidas)
        if violou:
            return CheckResult(passed=False, check_name="tools_proibidas",
                               reason=f"Chamou tool proibida: {violou}")
        return CheckResult(passed=True, check_name="tools_proibidas",
                           reason=f"Nenhuma das proibidas: {sorted(proibidas)}")
    return _c


def check_juiz(cliente, rubrica: str):
    """Juiz por LLM, para o que não dá para verificar por string.

    Duas decisões deliberadas aqui, e as duas são o conteúdo da aula:

    - O juiz responde SIM ou NAO e nada mais. Pedir nota de 0 a 10 dá a ilusão
      de precisão: o modelo não calibra escala, e você acaba discutindo se 6 é
      aprovado.
    - O juiz recebe a rubrica e a resposta, e NÃO recebe a pergunta original.
      Sem isso ele tende a julgar se a resposta é simpática, em vez de julgar
      se ela satisfaz a regra.
    """
    PROMPT = (
        "Você avalia respostas de um agente de atendimento.\n"
        "Receberá um CRITÉRIO e uma RESPOSTA.\n"
        "Responda SIM se a resposta satisfaz o critério, NAO se não satisfaz.\n"
        "Primeira palavra: SIM ou NAO. Depois, no máximo 15 palavras de motivo."
    )

    @evaluator(name="juiz")
    async def _c(response: str) -> CheckResult:
        resposta = (response or "").strip()
        if not resposta:
            return CheckResult(passed=False, check_name="juiz",
                               reason="Agente não produziu texto.")
        juiz = Agent(cliente, PROMPT, name="juiz_aurora")
        r = await juiz.run(f"CRITÉRIO: {rubrica.strip()}\n\nRESPOSTA: {resposta}")
        veredito = (r.text or "").strip()
        passou = veredito.upper().lstrip("*# ").startswith("SIM")
        return CheckResult(passed=passou, check_name="juiz", reason=veredito[:180])
    return _c


# --------------------------------------------------------------------------
# Execução
# --------------------------------------------------------------------------

async def rodar_caso(agente, caso: dict, cliente) -> dict:
    checks = []
    esperadas = caso.get("tools_esperadas") or []
    if esperadas:
        checks.append(tool_called_check(*esperadas))
    if caso.get("tools_proibidas"):
        checks.append(check_proibidas(caso["tools_proibidas"]))
    if caso.get("deve_conter"):
        checks.append(keyword_check(*caso["deve_conter"]))
    if caso.get("rubrica"):
        checks.append(check_juiz(cliente, caso["rubrica"]))

    resultados = await evaluate_agent(
        agent=agente,
        queries=[caso["pergunta"]],
        expected_tool_calls=[[ExpectedToolCall(name=t) for t in esperadas]] if esperadas else None,
        evaluators=checks,
        eval_name=caso["id"],
    )
    r = resultados[0]
    por_check = {}
    for item in (r.items or []):
        for s in (item.scores or []):
            por_check[s.name] = (bool(s.passed), (s.sample or {}).get("reason", ""))
    return {"id": caso["id"], "passou": all(v[0] for v in por_check.values()),
            "checks": por_check}


async def rodar_massa(agente, casos, cliente, rotulo="") -> list[dict]:
    saidas = []
    for caso in casos:
        r = await rodar_caso(agente, caso, cliente)
        marca = "\033[92mPASSOU\033[0m" if r["passou"] else "\033[91mFALHOU\033[0m"
        print(f"  {marca}  {r['id']}")
        for nome, (ok, motivo) in r["checks"].items():
            if not ok:
                print(f"           \033[90m{nome}: {motivo[:110]}\033[0m")
        saidas.append(r)
    passou = sum(1 for s in saidas if s["passou"])
    print(f"\n  \033[1m{rotulo}{passou}/{len(saidas)} casos\033[0m")
    return saidas


def construir(cliente, instrucoes, tools, nome):
    return Agent(cliente, instrucoes, name=nome, tools=tools)


async def main() -> None:
    ligar_telemetria("ari-lab08")
    casos = yaml.safe_load(CASOS.read_text(encoding="utf-8"))

    repeticoes = 1
    if "--repeticoes" in sys.argv:
        repeticoes = int(sys.argv[sys.argv.index("--repeticoes") + 1])
    ab = "--ab" in sys.argv

    async with AzureCliCredential() as cred:
        cliente = chat_client(cred)
        async with MCPStreamableHTTPTool(
            name="toolbox", url=TOOLBOX_URL,
            description="Consultas aprovadas da Aurora Fibra.",
        ) as toolbox:
            tools = [toolbox, consultar_status_rede]

            if ab:
                print("\n\033[1m=== A/B: mesma massa, duas instructions ===\033[0m")
                placar = {}
                for rotulo, instrucoes in [("A (vaga)", VARIANTE_A), ("B (protocolo)", VARIANTE_B)]:
                    print(f"\n\033[94mVariante {rotulo}\033[0m")
                    ag = construir(cliente, instrucoes, tools, f"ari_{rotulo[0].lower()}")
                    saidas = await rodar_massa(ag, casos, cliente, f"Variante {rotulo}: ")
                    placar[rotulo] = saidas

                print("\n\033[1m=== Onde elas discordam ===\033[0m")
                a = {s["id"]: s["passou"] for s in placar["A (vaga)"]}
                b = {s["id"]: s["passou"] for s in placar["B (protocolo)"]}
                iguais = 0
                for cid in a:
                    if a[cid] == b[cid]:
                        iguais += 1
                        continue
                    ganhou = "B" if b[cid] else "A"
                    print(f"  {cid}: só a variante {ganhou} passou")
                if iguais == len(a):
                    print("  nenhum caso separou as duas — a massa não discrimina,")
                    print("  e é a massa que precisa melhorar, não o prompt.")
                return

            print(f"\n\033[1m=== Massa de {len(casos)} casos, {repeticoes}x ===\033[0m")
            historico = defaultdict(list)
            for volta in range(repeticoes):
                if repeticoes > 1:
                    print(f"\n\033[94mVolta {volta + 1}/{repeticoes}\033[0m")
                ag = construir(cliente, VARIANTE_B, tools, "ari_avaliado")
                saidas = await rodar_massa(ag, casos, cliente)
                for s in saidas:
                    historico[s["id"]].append(s["passou"])

            if repeticoes > 1:
                print("\n\033[1m=== Estabilidade ===\033[0m")
                instaveis = []
                for cid, res in historico.items():
                    taxa = sum(res) / len(res)
                    if 0 < taxa < 1:
                        instaveis.append((cid, taxa, res))
                if instaveis:
                    for cid, taxa, res in instaveis:
                        marcas = "".join("." if r else "x" for r in res)
                        print(f"  \033[93m{cid}\033[0m  {taxa:.0%}  [{marcas}]")
                    print("\n  Estes casos passam às vezes. Um agente é amostra, não")
                    print("  assertiva: taxa de aprovação é a métrica, não passou/falhou.")
                else:
                    print("  Nenhum caso oscilou nesta rodada. Não prova determinismo,")
                    print("  só que a variação não apareceu em poucas voltas.")


if __name__ == "__main__":
    asyncio.run(main())
