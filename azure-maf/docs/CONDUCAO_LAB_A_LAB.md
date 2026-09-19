# Condução lab a lab: o que rodar, o que aparece, o que dizer

Complemento do [`ROTEIRO_AULA_AZURE.md`](ROTEIRO_AULA_AZURE.md), que traz a
grade de horários e as falas de abertura. Aqui está o nível abaixo: cada lab
quebrado em partes, com o comando, o que vai aparecer na tela, a fala que
sustenta aquele momento e o que fazer quando não sai como o esperado.

As saídas transcritas são de execuções reais contra o Azure, não inventadas.
Os números vão variar, o formato não.

---

## Antes de tudo: o pré-voo de 3 minutos

Rode isto com a turma ainda se acomodando. Se algo aqui falhar, você descobre
antes de ter 30 pessoas olhando.

```bash
cd <raiz do projeto>
.venv\Scripts\Activate.ps1          # Windows
az account show --query name -o tsv  # tem que devolver a subscription certa
python -m lab01_agente_puro.agent    # o menor caminho até o modelo
```

Para os labs 03 em diante, suba também a API de rede; para o 04 em diante, o Toolbox:

```bash
docker compose -f docker-compose.azure-db.yml up -d   # Toolbox + API + Redis, banco no Azure
curl http://localhost:5000/         # Toolbox
curl http://localhost:8000/health   # API de rede
```

**Sempre com `-m`, sempre da raiz.** `python lab01_agente_puro/agent.py` falha
com `ModuleNotFoundError: No module named 'comum'`. Não é instalação quebrada:
rodar o arquivo põe a pasta dele no `sys.path` em vez da raiz do projeto.
Vai acontecer com algum aluno, e saber a resposta de cabeça vale a aula.

### A sala do Habbo, se for usar

Com `HABBO_URL` e `HABBO_API_KEY` no `.env`, cada agente publica o que está
fazendo numa sala com 12 avatares. Abra num segundo monitor ou projetor.
Entre demos, esvazie a sala:

```python
import asyncio
from comum import limpar_sala
asyncio.run(limpar_sala())
```

O mapa de agente para avatar está em `MAPA`, em `comum/habbo.py`.

---

## O elenco: quem é quem na base

Trocar o CPF mata a demo. Se for imprimir uma página deste documento, imprima esta.

| CPF | Quem | CEP | Contrato | Em aberto | Chamados | Visita |
|---|---|---|---|---|---|---|
| `111.222.333-44` | Marcela Tavares | 06010-100 | ativo | 1 × R$ 129,90 | 2 | — |
| `222.333.444-55` | Rogério Santana | 06320-250 | ativo | 1 × R$ 89,90 | 1 | 23/08, realizada |
| `333.444.555-66` | Ana Beatriz | 06455-030 | ativo | 1 × R$ 179,90 | 1 | **16/09 manhã, agendada** |
| `444.555.666-77` | Wellington Farias | 06018-090 | **suspenso** | **3 × R$ 209,70** | 1 | — |
| `555.666.777-88` | Cláudia Mendes | 06501-010 | ativo | nenhuma | 0 | — |
| `666.777.888-99` | Itamar Gonçalves | 06700-000 | ativo | nenhuma | 0 | — |
| `777.888.999-00` | Priscila Amaral | 06110-045 | ativo | 1 × R$ 179,90 | 1 | **15/09 tarde, agendada** |
| `888.999.000-11` | Nelson Batista | 06600-100 | **cancelado** | nenhuma | 0 | — |

**Rede:** só **dois** CEPs têm incidente ativo no painel — o da Marcela
(`06010-100`, severidade média, degradação de OLT, 1.840 afetados) e o da
Priscila (`06110-045`, severidade alta, rompimento de fibra, 6.120 afetados).
Todos os outros respondem `normal`.

### Qual persona para qual demo

| Quero mostrar | Use |
|---|---|
| Incidente na região | Marcela `111.222.333-44` (média) ou Priscila `777.888.999-00` (alta) |
| Reincidência: dois chamados de lentidão | Marcela `111.222.333-44` |
| Cobrança travando o atendimento técnico | Wellington `444.555.666-77` |
| "Já existe visita agendada, não marque outra" | Ana Beatriz `333.444.555-66` |
| Cliente sem pendência nenhuma | Cláudia `555.666.777-88` |
| Contrato cancelado, caso de borda | Nelson `888.999.000-11` |
| CPF que não existe na base | `000.000.000-00` |

### Duas armadilhas que a base esconde

**O CEP do Wellington não tem incidente, e isso é de propósito.** Os labs 05 e 06
precisam que o problema dele seja financeiro. Se você usar a Marcela ali, o agente
acha o incidente de rede e a lição — cobrança antes de técnico — evapora.

**A Marcela não tem visita agendada.** Se quiser demonstrar "já existe visita
marcada, informe em vez de agendar outra", é a Ana Beatriz. Com a Marcela o agente
responde corretamente que não encontrou nada, e parece que a tool falhou.

---

## Os roteiros, um por lab

O detalhe de cada lab — partes, falas, edições ao vivo com o desfazer, perguntas
da turma e o que fazer se der errado — está em um arquivo por lab, em
[`roteiros/`](roteiros/). Abra só o do lab que você vai dar.

| Lab | Tempo | Precisa no ar | Roteiro |
|---|---|---|---|
| 01 · Primeiro dia, sem crachá | 45 min | só o modelo | [lab01](roteiros/lab01.md) |
| 02a · O caderno de anotações | 50 min | Redis (opcional) | [lab02a](roteiros/lab02a.md) |
| 02b · O prontuário do cliente | 50 min | só o modelo | [lab02b](roteiros/lab02b.md) |
| 03 · O primeiro acesso ao sistema | 60 min | API de rede | [lab03](roteiros/lab03.md) |
| 04 · A chave do banco de dados | 80 min | Toolbox + API | [lab04](roteiros/lab04.md) |
| 05 · Promovido a líder de equipe | 60 min | Toolbox + API | [lab05](roteiros/lab05.md) |
| 06 · O processo operacional | 70 min | Toolbox + API | [lab06](roteiros/lab06.md) |
| 07 · O agente que não é seu | 45 min | dois terminais | [lab07](roteiros/lab07.md) |
| 08 · A prova de que funciona | 80 min | Toolbox + API | [lab08](roteiros/lab08.md) |

O que ficou neste arquivo é o material transversal: o elenco da base, o ritmo,
a cola de uma página e os erros comuns.

---


## Fechamento

> **Fala.** Vocês viram o mesmo problema resolvido em dois frameworks. O que
> mudou foram nomes de classe — e olhem a seção 0 do MAPEAMENTO, mudaram até
> dentro do mesmo framework, entre versões. O que não mudou foi o raciocínio:
> o que é determinístico, o que é julgamento, onde mora a política, quem paga
> a conta do paralelismo. Framework é detalhe de implementação disso.

---

## Ritmo: quanto cada coisa demora

Nenhum lab é instantâneo, e o silêncio do terminal assusta quem está conduzindo.
Medições reais contra o Azure, com `gpt-5.4`:

| Comando | Tempo |
|---|---|
| `lab01` (3 turnos) | 30 a 60 s |
| `lab02a` (3 falas) | 30 a 50 s |
| `lab02b` (2 atendimentos, 4 falas) | 1 a 2 min |
| `lab03` (3 falas com tools) | 1 a 2 min |
| `lab04` (3 falas com banco) | 1 a 2 min |
| `lab05 --tools` | 40 a 70 s |
| `lab06 comparar` | 20 a 30 s |
| `lab06 completo` | 2 a 3 min |
| `lab07` (qualquer modo) | 10 a 40 s |

Fale enquanto roda. O `lab06 comparar` é o único que vale assistir em silêncio,
porque o número é a demo.

---

## Cola de uma página

**Pré-voo**

```bash
cd azure-maf && .venv\Scripts\Activate.ps1
az account show --query name -o tsv
docker compose -f docker-compose.azure-db.yml up -d
python -m uvicorn lab07_a2a.servidor:app --port 9000     # se for dar o lab 07
```

**Portas** — Toolbox 5000 · API de rede 8000 · DevUI 8080 · A2A 9000

**Os quatro CPFs que importam**

```
111.222.333-44  Marcela      incidente na rede, 1 vencida, 2 chamados, sem visita
444.555.666-77  Wellington   SUSPENSO, 3 vencidas, rede normal   <- labs 05 e 06
333.444.555-66  Ana Beatriz  visita agendada 16/09 manhã
555.666.777-88  Cláudia      sem pendência nenhuma
```

**Os comandos**

```bash
python -m lab01_agente_puro.agent
python -m lab02_memoria.a_thread [--continuar]
python -m lab02_memoria.b_memoria_longa
python -m lab03_tool_externa.agent
python -m lab04_mcp_toolbox.agent
python -m lab05_handoff.agent [--tools]
python -m lab06_workflows.run sequencial|concorrente|loop|comparar|completo
python -m lab07_a2a.agent [--card|--direto]
python -m ui                                              # DevUI, 8080
```

**As quatro edições ao vivo, e o desfazer**

| Lab | Arquivo | Troque | Desfaça antes de |
|---|---|---|---|
| 01 | `lab01_agente_puro/agent.py` | `INSTRUCTION_ATIVA` para `INSTRUCTION_VAGA` | o lab 02a |
| 03 | `comum/tools_rede.py` | a `description` por "Consulta coisas" | o lab 04 |
| 03 | `lab03_tool_externa/agent.py` | comentar `MiddlewareTermination` | o lab 05 |
| 05 | `lab05_handoff/especialistas.py` | `DESC_TECNICO` por "Agente técnico." | o lab 06 |

**Os três números**

- **1,7×** — ganho do concorrente sobre o sequencial no lab 06 (12,8 s → 7,4 s)
- **5** — queries no cardápio do Toolbox. É o blast radius inteiro
- **R$ 209,70** — as três faturas do Wellington, o gancho de cobrança do lab 05

**Antes de encerrar**

```bash
docker compose -f docker-compose.azure-db.yml down
rm lab02_memoria/prontuarios.json
git diff --stat                    # nenhuma edição ao vivo esquecida?
```

Esse `git diff` no fim é o que separa uma aula da próxima. Se aparecer algo, era
edição de demo que ficou para trás.

---

## Quando algo dá errado

| Sintoma | Causa quase certa |
|---|---|
| `ModuleNotFoundError: No module named 'comum'` | rodou o arquivo em vez de `-m`, ou fora da raiz |
| `ImportError: cannot import name 'ChatAgent'` | Python global em vez do `.venv` |
| 404 no modelo, mensagem pouco útil | `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` é o nome do **deployment**, não do modelo |
| `API version not supported` | alguém fixou `api_version` no chat client; deixe o default |
| Tool "some" em runtime | MCP criado fora do `async with` |
| Toolbox não sobe, `password: null` | `POSTGRES_PASSWORD` vazio, ou senha comida pelo shell ao exportar o `.env` |
| Lab 02a não lembra com `--continuar` | Redis fora do ar; o lab avisa no começo e cai para memória |
| Lab 06 estoura cota | TPM do deployment; é conteúdo, não acidente |
