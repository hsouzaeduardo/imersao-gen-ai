"""
API interna da Aurora Fibra, versão de aula.

Representa o painel de status da rede que o suporte N1 consulta.
No lab 03 o ARI ganha acesso somente leitura a /status-rede,
e depois um acesso com efeito colateral em /roteador/reiniciar.

Rodar isolado:
    uvicorn mock_api.main:app --reload --port 8000
"""

from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Aurora Fibra - Painel de Rede", version="1.0.0")

# CEPs com incidente ativo. O 06010-100 é o da Marcela, usado na demo.
INCIDENTES = {
    "06010100": {
        "severidade": "media",
        "causa": "degradacao_olt",
        "descricao": "Degradação na OLT Osasco Centro afetando o período noturno.",
        "previsao_normalizacao": "2026-09-15T22:00:00",
        "clientes_afetados": 1840,
    },
    "06110045": {
        "severidade": "alta",
        "causa": "rompimento_fibra",
        "descricao": "Rompimento de fibra na Av. dos Autonomistas, equipe em campo.",
        "previsao_normalizacao": "2026-09-14T18:00:00",
        "clientes_afetados": 6120,
    },
}


class ReinicioRequest(BaseModel):
    id_cliente: str


def _normalizar_cep(cep: str) -> str:
    return "".join(ch for ch in cep if ch.isdigit())


@app.get("/health")
def health():
    return {"status": "ok", "servico": "painel-rede-aurora"}


@app.get("/status-rede/{cep}")
def status_rede(cep: str):
    """Status da rede para um CEP. Este é o endpoint do lab 03."""
    chave = _normalizar_cep(cep)
    if len(chave) != 8:
        raise HTTPException(status_code=400, detail="CEP inválido, use 8 dígitos.")

    incidente = INCIDENTES.get(chave)
    if incidente:
        return {
            "cep": cep,
            "situacao": "incidente",
            "consultado_em": datetime.now().isoformat(timespec="seconds"),
            **incidente,
        }

    return {
        "cep": cep,
        "situacao": "normal",
        "consultado_em": datetime.now().isoformat(timespec="seconds"),
        "latencia_media_ms": 12,
        "perda_pacotes_pct": 0.2,
        "clientes_afetados": 0,
    }


@app.post("/roteador/reiniciar")
def reiniciar_roteador(req: ReinicioRequest):
    """Ação com efeito colateral. É o gatilho do guardrail no lab 03."""
    if not req.id_cliente:
        raise HTTPException(status_code=400, detail="id_cliente é obrigatório.")

    return {
        "id_cliente": req.id_cliente,
        "resultado": "reinicio_agendado",
        "janela": "imediata",
        "previsao_retorno": (datetime.now() + timedelta(minutes=4)).isoformat(timespec="seconds"),
        "aviso": "A conexão do cliente ficará indisponível por cerca de 3 minutos.",
    }


@app.get("/eventos-massivos")
def eventos_massivos():
    """Usado no lab 06 como uma das verificações paralelas."""
    return {
        "consultado_em": datetime.now().isoformat(timespec="seconds"),
        "total": len(INCIDENTES),
        "eventos": [
            {"cep": cep, "severidade": i["severidade"], "descricao": i["descricao"]}
            for cep, i in INCIDENTES.items()
        ],
    }
