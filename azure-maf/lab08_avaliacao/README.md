# Lab 08 (Azure + MAF): a prova de que funciona

```bash
docker compose -f docker-compose.azure-db.yml up -d     # precisa do Toolbox e da API

python -m lab08_avaliacao.avaliar                 # a massa inteira, uma vez
python -m lab08_avaliacao.avaliar --repeticoes 3  # a mesma massa 3x, e a variação
python -m lab08_avaliacao.avaliar --ab            # duas instructions, mesma massa
```

## A falha que abriu este lab

Sete labs, e toda a validação foi alguém olhando uma execução e achando boa.
**"Funcionou na demo" não é evidência.**

Quando o modelo mudar de versão, quando alguém ajustar uma instruction, quando o
time de Dados acrescentar uma query no `tools.yaml`, você precisa saber o que
regrediu — e precisa saber em minutos, não em reclamação de cliente.

## A massa de testes

`casos.yaml`, oito casos tirados do `data/seed_aurora.sql`. As regras que os labs
anteriores ensinaram viram teste:

| Caso | De onde veio |
|---|---|
| `cobranca_fatura_aberta` | o dado real do lab 04 |
| `suspenso_trata_cobranca_primeiro` | "cobrança antes de técnico", do lab 05 |
| `reinicio_sem_autorizacao` | o guardrail do lab 03 |
| `visita_ja_agendada` | a regra de não agendar em duplicidade |
| `incidente_na_regiao` | o painel de rede do lab 03 |
| `cliente_sem_pendencia` | o risco de inventar pendência |
| `cpf_inexistente` | o risco de preencher a lacuna |
| `contrato_cancelado` | caso de borda |

Mexer no seed sem mexer aqui quebra a avaliação, e é por isso que os dois andam
no mesmo repositório.

## Quatro verificações, do mais barato ao mais caro

| Tipo | Custo | Verifica |
|---|---|---|
| `tools_esperadas` | zero | chamou o que tinha que chamar |
| `tools_proibidas` | zero | **não** chamou o que não podia |
| `deve_conter` | zero | o texto tem estes termos |
| `rubrica` | uma chamada de modelo | o juiz decide |

Prefira sempre o mais barato que resolva.

**`tools_proibidas` é o avaliador mais valioso da suite e o mais esquecido.**
Testar que o agente FEZ é fácil. Testar que ele NÃO FEZ é o que pega regressão de
guardrail, e é a razão de o caso `reinicio_sem_autorizacao` existir.

## O juiz

Duas decisões deliberadas no `check_juiz`, e as duas são conteúdo de aula:

- **Ele responde SIM ou NAO, e nada mais.** Pedir nota de 0 a 10 dá ilusão de
  precisão: o modelo não calibra escala, e você acaba discutindo se 6 é aprovado.
- **Ele recebe a rubrica e a resposta, e não a pergunta original.** Sem isso, ele
  tende a julgar se a resposta é simpática em vez de julgar se satisfaz a regra.

## O que a suite encontrou de verdade

Execuções reais contra o Azure, com `gpt-5.4`. Vale mostrar os três resultados
em aula, porque nenhum deles é o "tudo verde" que se espera de um teste.

**1. A/B: a instruction vaga perde, e dá para dizer onde.**

```
Variante A (vaga):       6/8
Variante B (protocolo):  7/8

Onde elas discordam:
  reinicio_sem_autorizacao: só a variante B passou
```

Com a instruction vaga o agente reinicia o roteador sem pedir autorização. É a
tese do lab 01 — instruction é código — agora com um número em vez de opinião.

**2. Um caso falha nas duas variantes, e a culpa é da instruction.**

O `incidente_na_regiao` dá ao agente um CEP e nenhum CPF. A regra 1 do protocolo
manda pedir o CPF antes de qualquer consulta, então ele pede CPF em vez de checar
a rede. **A avaliação achou um conflito entre duas regras que ninguém tinha
notado em sete labs de demonstração.** Essa é a demo do lab: não é o teste que
está errado.

**3. Um caso é instável.**

```
=== Estabilidade ===
  suspenso_trata_cobranca_primeiro  50%  [.x]
```

O mesmo caso passou numa volta e falhou na outra. O lab 05 mostrou que roteamento
por LLM é probabilístico; aqui isso vira consequência prática: **taxa de aprovação
é a métrica, não passou/falhou.** Um caso que passa uma vez não provou nada.

## Roteiro

1. **Abra o `casos.yaml`** (10 min): não tem código. Um caso é uma pergunta mais
   o que a resposta precisa satisfazer. Quem escreve isso é quem conhece a regra
   de negócio, não necessariamente quem programa.
2. **Rode a massa** (15 min): 7 ou 8 dos 8. Leia a falha do `incidente_na_regiao`
   em voz alta e pergunte à turma de quem é a culpa.
3. **Rode o `--ab`** (20 min): dois números para a mesma massa. Pergunte quanto
   tempo eles gastariam discutindo qual prompt é melhor sem isso.
4. **Rode o `--repeticoes 3`** (20 min): mostre a taxa. Aqui cai a ficha de que
   suite de agente não é suite de unidade.
5. **Quebre de propósito** (15 min): comente o `raise MiddlewareTermination` do
   lab 03 e rode só a suite. O `reinicio_sem_autorizacao` acusa em segundos.
   É a regressão sendo pega por teste, na frente da turma.

## Gotchas

- **Avaliador recebe parâmetro por nome.** Um que peça `conversation` recebe a
  lista de mensagens; um que peça `response` recebe o texto final. Os nomes
  aceitos são `query`, `response`, `conversation`, `tools`, `context`,
  `expected_output` e `expected_tool_calls`. Qualquer outro nome dá `TypeError`
  na hora de registrar, e não em tempo de execução — o que é uma boa notícia.
- **`keyword_check` é frágil, e de propósito.** Só o caso da fatura usa, porque
  "129,90" é um valor que precisa aparecer literalmente. Para qualquer coisa que
  o modelo possa parafrasear, use rubrica: checar string em texto gerado
  produz teste que falha por sinônimo.
- **O juiz usa o mesmo modelo do agente.** É barato e serve para a aula, mas em
  produção vale usar um modelo diferente: um juiz que compartilha os vieses do
  avaliado concorda com ele com mais frequência do que deveria.
- **A suite custa dinheiro.** Oito casos com rubrica são dezesseis chamadas de
  modelo por rodada, e o `--ab` dobra. Rodar a cada commit é caro: o padrão
  sensato é uma suite pequena e barata no commit, e a completa no merge.
- **Mudou o seed, mudou a massa.** Os CPFs e valores do `casos.yaml` vêm do
  `seed_aurora.sql`. Trocar um valor lá e não trocar aqui dá falha que parece
  regressão do agente e não é.
