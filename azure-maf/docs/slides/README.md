# Slides: "A evolução do ARI"

24 slides que contam o curso como uma corrente de falhas: fundo claro é a peça
que o lab entrega, fundo escuro é a falha que ela ainda não resolve.

```
deck.json          o índice: ordem, seções e as fontes
slides/*.html      um arquivo por slide, com as notas no <aside>
deck.html          gerado — abra este no navegador
montar.py          regenera o deck.html a partir dos dois acima
```

## Ver

Abra `deck.html` direto no navegador. Não precisa de servidor.

- **setas, espaço ou clique** — navegar
- **N** — notas do apresentador
- **F** — tela cheia

O número do slide vai para o `#hash` da URL, então dá para mandar um link para
um slide específico ou recarregar sem perder o lugar.

## Editar

Cada slide é um `<section>` isolado, com todo o estilo inline, numa tela fixa de
1920×1080. As notas do apresentador ficam no `<aside>`, sempre o último filho.
Edite o arquivo do slide e regenere:

```bash
python docs/slides/montar.py
```

Para mudar a ordem, acrescentar ou remover um slide, mexa no `order` do
`deck.json`.

## Duas versões, e qual usar

A versão **viva** é um Artifact no claude.ai, e ela é melhor para apresentar:
transições, exportação para PDF e PowerPoint, comentários. É de lá que estes
arquivos saíram.

Este `deck.html` é o **plano B de sala**: projetor sem internet, máquina de
terceiros, ou a necessidade de abrir o deck daqui a dois anos sem depender de
conta nenhuma. E é o que dá para versionar e revisar em pull request.

## Limites conhecidos

- **Sem transições.** O `data-transition` dos slides é lido pelo runtime do
  Artifact, não por este viewer.
- **`x-connector` vira uma linha simples.** É um elemento do runtime do Artifact;
  aqui ele aparece como um traço sem ponta de seta. Afeta um slide, o
  `lab04-blast`, e o desenho continua legível.
- **As fontes vêm do Google.** Sem internet, o navegador cai para as básicas
  declaradas em cada `font-family`. O layout aguenta; o texto muda de cara.
- **Este arquivo foi validado por estrutura, não visualmente.** HTML bem formado,
  script sem erro de sintaxe, 24 slides na ordem do índice e 24 blocos de notas.
  Abra uma vez antes da aula.
