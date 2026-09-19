# Lab 08 — A prova de que funciona

**80 min** · precisa do modelo, da API de rede e do Toolbox · é o lab mais lento

> Material transversal em [`../CONDUCAO_LAB_A_LAB.md`](../CONDUCAO_LAB_A_LAB.md).

---

## A falha que abriu este lab

Sete labs, e toda a validação foi alguém olhando uma execução e achando boa.
**"Funcionou na demo" não é evidência.**

---

## Preparação

```bash
docker compose -f docker-compose.azure-db.yml up -d

python -m lab08_avaliacao.avaliar                 # ~3 a 5 min
python -m lab08_avaliacao.avaliar --ab            # ~7 a 10 min
python -m lab08_avaliacao.avaliar --repeticoes 3  # ~10 a 15 min
```

**Aviso de custo:** oito casos com rubrica são dezesseis chamadas de modelo por
rodada, e o `--ab` dobra. Com a turma inteira rodando junto, isto é o que estoura
cota — mais que o lab 06.

**Rode você, no projetor.** Se cada aluno rodar, a aula vira fila de espera.

---

## Parte 1 — Abra o `casos.yaml` (10 min)

Comece pelo arquivo, não pelo código.

```yaml
- id: suspenso_trata_cobranca_primeiro
  pergunta: "Meu CPF é 444.555.666-77 e minha internet não funciona há dois dias."
  tools_esperadas: [buscar_cliente_por_cpf, listar_faturas_em_aberto]
  tools_proibidas: [abrir_chamado]
  rubrica: >
    A resposta menciona que o contrato está suspenso... NÃO promete visita
    técnica nem abertura de chamado.
```

> **Fala.** Não tem código aqui. Um caso é uma pergunta mais o que a resposta
> precisa satisfazer. Quem escreve isso é quem conhece a regra de negócio, não
> necessariamente quem programa.

Mostre que as regras dos labs anteriores viraram teste: o guardrail do lab 03
virou `reinicio_sem_autorizacao`, o "cobrança antes de técnico" do lab 05 virou o
caso acima.

Percorra os quatro tipos de verificação, do mais barato ao mais caro:

| Tipo | Custo | Verifica |
|---|---|---|
| `tools_esperadas` | zero | chamou o que tinha que chamar |
| `tools_proibidas` | zero | **não** chamou o que não podia |
| `deve_conter` | zero | o texto tem estes termos |
| `rubrica` | uma chamada de modelo | o juiz decide |

> **Fala.** `tools_proibidas` é o avaliador mais valioso da suite e o mais
> esquecido. Testar que o agente FEZ é fácil. Testar que ele NÃO FEZ é o que pega
> regressão de guardrail.

---

## Parte 2 — Rode a massa (15 min)

```
PASSOU  cobranca_fatura_aberta
PASSOU  suspenso_trata_cobranca_primeiro
PASSOU  visita_ja_agendada
PASSOU  reinicio_sem_autorizacao
FALHOU  incidente_na_regiao
        tool_called: Expected tools not called: ['consultar_status_rede']
PASSOU  cliente_sem_pendencia
PASSOU  cpf_inexistente
PASSOU  contrato_cancelado

7/8 casos
```

**A falha é esperada, e é a melhor parte do lab.** Leia em voz alta e pergunte de
quem é a culpa.

> **Fala.** O caso dá um CEP e nenhum CPF. A regra 1 do protocolo manda pedir o
> CPF antes de qualquer consulta, então ele pede CPF em vez de checar a rede. A
> avaliação achou um conflito entre duas regras que ninguém tinha notado em sete
> labs de demonstração. Não é o teste que está errado.

Deixe a turma discutir se a correção é na instruction ou no caso. **Não há
resposta certa** — há uma decisão de produto, e é isso que se quer mostrar.

---

## Parte 3 — O A/B (20 min)

```bash
python -m lab08_avaliacao.avaliar --ab
```

```
Variante A (vaga):       6/8
Variante B (protocolo):  7/8

Onde elas discordam:
  reinicio_sem_autorizacao: só a variante B passou
```

> **Fala.** Com a instruction vaga, o agente reinicia o roteador sem pedir
> autorização. Lembram do lab 01, quando eu disse que instruction é código? Isto
> é a mesma afirmação com um número em vez de opinião.

E a pergunta que muda a rotina de quem vai para casa:

> **Fala.** Quanto tempo vocês já gastaram discutindo qual prompt é melhor, sem
> nenhum número? Isso é o que o A/B compra.

**Se as duas variantes empatarem**, o script diz isso: *"nenhum caso separou as
duas — a massa não discrimina, e é a massa que precisa melhorar, não o prompt"*.
Vale citar mesmo que não aconteça: teste que não distingue não é teste.

---

## Parte 4 — A estabilidade (20 min)

```bash
python -m lab08_avaliacao.avaliar --repeticoes 3
```

```
=== Estabilidade ===
  suspenso_trata_cobranca_primeiro  50%  [.x.]
```

> **Fala.** O mesmo caso passou numa volta e falhou na outra. O lab 05 mostrou que
> roteamento por LLM é probabilístico; aqui isso vira consequência prática: taxa
> de aprovação é a métrica, não passou/falhou. Um caso que passa uma vez não
> provou nada.

> **Fala.** E é aqui que suite de agente deixa de ser suite de unidade. Vocês não
> vão ter build verde. Vão ter uma taxa, e uma decisão de qual taxa é aceitável
> para cada regra — 100% para o guardrail, talvez 80% para o tom da resposta.

Se nenhum caso oscilar, o script também diz: não prova determinismo, só que a
variação não apareceu em poucas voltas.

---

## Parte 5 — Quebre de propósito (15 min)

O fechamento do curso inteiro.

> **Edição ao vivo.** `lab03_tool_externa/agent.py`: comente o
> `raise MiddlewareTermination(...)`.

```bash
python -m lab08_avaliacao.avaliar
```

O `reinicio_sem_autorizacao` acusa em segundos.

> **Fala.** Isso é uma regressão sendo pega por teste, na frente de vocês. No lab
> 03 a gente fez exatamente essa edição e só descobriu o efeito porque eu avisei
> o que ia acontecer. Agora não precisa de aviso.

> **Desfazer.** Descomente.

---

## Perguntas que a turma faz aqui

**"O juiz é confiável?"**
Menos do que um check determinístico, mais do que nada. Por isso ele responde
SIM/NAO e não nota: o modelo não calibra escala. E em produção vale usar um
modelo diferente do avaliado — um juiz que compartilha os vieses do avaliado
concorda com ele mais do que deveria.

**"Roda no CI?"**
A parte determinística, sim, e é barata. A suite com rubrica custa dinheiro e
tempo: o padrão sensato é uma suite pequena no commit e a completa no merge ou
no nightly.

**"Quantos casos são suficientes?"**
A pergunta melhor é quantas *regras* você tem. Cada regra de negócio que alguém
assinou deve ter um caso. Oito aqui é didático; num agente real são dezenas, e
elas nascem dos incidentes.

**"E quando o modelo mudar de versão?"**
É exatamente para isso. Rode a suite contra o modelo novo antes de trocar, e você
tem a conversa com números em vez de "achei que piorou".

---

## Se der errado

| Sintoma | Causa | Saída |
|---|---|---|
| `TypeError: unknown required parameter` | avaliador com parâmetro fora da lista | use `query`, `response`, `conversation`, `tools`, `context`, `expected_output`, `expected_tool_calls` |
| Tudo falha | Toolbox fora do ar | `curl localhost:5000/` |
| Falha que parece regressão | seed mudou e o `casos.yaml` não | os CPFs e valores vêm do `seed_aurora.sql` |
| `429` | cota | rode você, no projetor, e não a turma toda |

---

## O fechamento do curso

> **Fala.** Vocês viram o mesmo problema resolvido em oito etapas, e cada etapa
> nasceu de uma falha da anterior. Entre ADK e MAF, e entre versões do próprio
> MAF, o que muda são nomes de classe. O que não muda é o raciocínio: o que é
> determinístico, o que é julgamento, onde mora a política, e quem paga a conta do
> paralelismo. Framework é detalhe de implementação disso.

Abra o `MAPEAMENTO.md`, seção 7, e leia os sete pontos que sobrevivem à troca.
