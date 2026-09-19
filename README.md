# Imersão Gen AI

Laboratórios de agentes construídos sobre o mesmo cenário, em pilhas diferentes.

A empresa é a **Aurora Fibra**, provedor regional de internet com 400 mil
assinantes. O agente é o **ARI**, contratado como estagiário do suporte N1.
São oito labs, e cada um existe porque o anterior falhou de um jeito específico.

## Labs

| Pasta | Pilha | Estado |
|---|---|---|
| [`azure-maf/`](azure-maf/) | Microsoft Agent Framework sobre Azure | pronto |
| `google-adk/` | Google ADK sobre Google Cloud | a publicar |

Os dois percorrem os mesmos capítulos, com a mesma base de dados e o mesmo
`tools.yaml`. Dá para ensinar só um, ou os dois em sequência — e nesse caso o
[`MAPEAMENTO.md`](azure-maf/MAPEAMENTO.md) é o material mais valioso do curso:
a tabela de tradução conceito a conceito entre as duas pilhas.

## Os seis capítulos

| Lab | Capítulo | Conceito |
|---|---|---|
| 1 | Primeiro dia, sem crachá | agente puro |
| 2a | O caderno de anotações | conversa |
| 2b | O prontuário do cliente | memória longa |
| 3 | O primeiro acesso ao sistema | tool externa |
| 4 | A chave do banco de dados | MCP |
| 5 | Promovido a líder de equipe | multiagente |
| 6 | O processo operacional | orquestração |
| 7 | O agente que não é seu | A2A |
| 8 | A prova de que funciona | avaliação e A/B |

## Para quem vai dar a aula

Em `azure-maf/docs/`:

- [`slides/`](azure-maf/docs/slides/) — o deck do curso, para abrir no navegador.
- [`roteiros/`](azure-maf/docs/roteiros/) — um roteiro detalhado por lab, com as
  falas e as edições ao vivo. É o que se abre durante a aula.
- [`COMO_EXECUTAR.md`](azure-maf/docs/COMO_EXECUTAR.md) — passo a passo de execução de
  cada lab: pré-requisitos, comandos, resultado esperado e erros comuns.
- [`ROTEIRO_AULA_AZURE.md`](azure-maf/docs/ROTEIRO_AULA_AZURE.md) — grade dos
  dois encontros de 4 horas, as demos que não podem falhar, perguntas
  frequentes da turma e o checklist de véspera.
- [`CONDUCAO_LAB_A_LAB.md`](azure-maf/docs/CONDUCAO_LAB_A_LAB.md) — cada lab
  parte a parte: o comando, a saída esperada, a fala de cada momento e o que
  fazer quando não sai como o previsto.

## Aviso sobre dados

Todos os CPFs, nomes, endereços e contratos das bases de seed são fictícios,
gerados para aula.

## Aviso sobre credenciais

Nenhum `.env` é versionado. Cada lab traz um `.env.example` com os campos em
branco: preencha localmente com os seus endpoints e as suas chaves.
