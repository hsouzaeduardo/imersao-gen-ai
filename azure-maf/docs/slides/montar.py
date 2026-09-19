"""
Monta um deck.html autônomo a partir dos slides versionados.

    python docs/slides/montar.py

Lê `deck.json` e os arquivos de `slides/`, e escreve `deck.html`: um arquivo só,
que abre em qualquer navegador, sem servidor e sem internet — exceto pelas
fontes do Google, que caem para as básicas se a rede estiver bloqueada.

Por que existe: a versão viva do deck é um Artifact no claude.ai, e ela é melhor
(transições, exportação, comentários). Este aqui é o plano B de sala — projetor
sem internet, máquina de terceiros, ou a necessidade de abrir o deck daqui a
dois anos sem depender de nenhuma conta.

Navegação: setas, espaço, ou clique. Tecla N mostra as notas do apresentador.
"""

from __future__ import annotations

import json
import pathlib
import re

AQUI = pathlib.Path(__file__).parent
INDICE = json.loads((AQUI / "deck.json").read_text(encoding="utf-8"))
SLIDES = AQUI / "slides"

# As fontes declaradas no índice viram <link>, uma por família.
links = "\n  ".join(
    f'<link rel="stylesheet" href="{f["href"]}">'
    for f in INDICE.get("faces", {}).values()
    if f.get("href")
)

folhas, notas = [], []
for i, sid in enumerate(INDICE["order"]):
    bruto = (SLIDES / f"{sid}.html").read_text(encoding="utf-8").strip()

    # As notas saem do <aside> e vão para o painel; no palco elas não entram.
    m = re.search(r"<aside>(.*?)</aside>", bruto, re.S)
    notas.append(re.sub(r"\s+", " ", m.group(1)).strip() if m else "")
    bruto = re.sub(r"<aside>.*?</aside>", "", bruto, flags=re.S)

    folhas.append(f'<div class="folha" data-i="{i}">\n{bruto}\n</div>')

HTML = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>{INDICE["title"]}</title>
  {links}
  <style>
    html, body {{ margin:0; height:100%; background:#0d1117; overflow:hidden;
                  font-family:'IBM Plex Sans', Verdana, sans-serif }}
    #palco {{ position:fixed; inset:0; display:grid; place-items:center }}
    .folha {{ width:1920px; height:1080px; display:none; position:relative;
              box-shadow:0 24px 80px rgba(0,0,0,.6) }}
    .folha.ativa {{ display:block }}
    .folha > section {{ position:relative; width:1920px; height:1080px;
                        box-sizing:border-box }}
    /* x-connector é um elemento do runtime do Artifact. Aqui vira uma linha
       simples, sem ponta de seta: o desenho continua legível. */
    x-connector {{ display:inline-block; height:3px; background:currentColor;
                   align-self:center; min-width:60px }}
    #barra {{ position:fixed; left:0; right:0; bottom:0; height:34px;
              display:flex; align-items:center; gap:18px; padding:0 18px;
              background:rgba(13,17,23,.92); color:#8b98a5; font-size:13px }}
    #notas {{ position:fixed; left:0; right:0; bottom:34px; max-height:38vh;
              overflow:auto; padding:20px 26px; background:rgba(13,17,23,.97);
              color:#c9d4e0; font-size:16px; line-height:1.55; display:none;
              border-top:1px solid #2e3f52 }}
    #notas.aberto {{ display:block }}
  </style>
</head>
<body>
  <div id="palco"><div id="pilha">
{chr(10).join(folhas)}
  </div></div>
  <div id="notas"></div>
  <div id="barra">
    <span id="pos"></span>
    <span>← →  navegar</span><span>N  notas</span><span>F  tela cheia</span>
  </div>
<script>
const NOTAS = {json.dumps(notas, ensure_ascii=False)};
const folhas = [...document.querySelectorAll('.folha')];
const pilha = document.getElementById('pilha');
let i = 0;

function escalar() {{
  const e = Math.min(innerWidth / 1920, (innerHeight - 34) / 1080);
  pilha.style.transform = `scale(${{e}})`;
  pilha.style.width = '1920px';
  pilha.style.height = '1080px';
}}

function mostrar(n) {{
  i = Math.max(0, Math.min(folhas.length - 1, n));
  folhas.forEach((f, k) => f.classList.toggle('ativa', k === i));
  document.getElementById('pos').textContent = `${{i + 1}} / ${{folhas.length}}`;
  document.getElementById('notas').textContent = NOTAS[i] || '(sem notas)';
  location.hash = i + 1;
}}

addEventListener('resize', escalar);
addEventListener('keydown', e => {{
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') mostrar(i + 1);
  else if (e.key === 'ArrowLeft' || e.key === 'PageUp') mostrar(i - 1);
  else if (e.key === 'Home') mostrar(0);
  else if (e.key === 'End') mostrar(folhas.length - 1);
  else if (e.key.toLowerCase() === 'n') document.getElementById('notas').classList.toggle('aberto');
  else if (e.key.toLowerCase() === 'f') {{
    document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
  }}
}});
addEventListener('click', e => {{ if (!e.target.closest('#notas')) mostrar(i + 1); }});

escalar();
mostrar(Math.max(0, (parseInt(location.hash.slice(1)) || 1) - 1));
</script>
</body>
</html>
"""

destino = AQUI / "deck.html"
destino.write_text(HTML, encoding="utf-8")
print(f"{destino.name}: {len(folhas)} slides, {destino.stat().st_size // 1024} KB")
