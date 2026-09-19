# Lab 01 — Primeiro dia, sem crachá

**45 min** · precisa só do modelo · nenhum serviço local

> Material transversal — elenco da base, ritmo e cola — em
> [`../CONDUCAO_LAB_A_LAB.md`](../CONDUCAO_LAB_A_LAB.md).

---

## Por que este lab existe

É o ponto de partida. Não tem falha anterior para consertar: o que ele faz é
estabelecer o menor agente possível, para que tudo nos próximos sete labs seja
visivelmente um **acréscimo** com um custo nomeável.

E termina criando a primeira falha do curso, que abre o lab 02a.

---

## Preparação

```bash
cd azure-maf
.venv\Scripts\Activate.ps1
az account show --query name -o tsv     # tem que devolver a subscription certa
python -m lab01_agente_puro.agent
```

Nada precisa estar no ar além do endpoint do Azure OpenAI. **É o lab que roda com
a rede corporativa bloqueando tudo**, e é por isso que ele abre o curso: se o
resto falhar na véspera, você ainda tem aula.

Se der `ModuleNotFoundError: No module named 'comum'`, você rodou o arquivo em
vez do módulo. Sempre `-m`, sempre da raiz.

---

## Parte 1 — Anatomia de um turno (10 min)

Rode e deixe as três respostas na tela.

```python
Agent(
    OpenAIChatClient(azure_endpoint=...),
    INSTRUCTION,
    name="ari_n1",
)
```

> **Fala.** Isto aqui é um agente inteiro. Um cliente de modelo, uma instruction,
> e um `run`. Não tem runner, não tem servidor, não tem sessão. Guardem essa
> imagem, porque nas próximas horas a gente vai só acrescentar coisa em cima
> dela, e no fim vocês vão saber exatamente o que cada peça resolve e o que cada
> peça custa.

Com `ENABLE_OTEL=true`, abra o Application Insights e mostre o span `chat` com
modelo, tokens e latência.

> **Fala.** Esse número de tokens é o custo do turno. Um atendimento inteiro tem
> dez, quinze desses. Multipliquem por 400 mil assinantes e vocês entendem por
> que a escolha de modelo é decisão de arquitetura, não de gosto.

**Se o trace não aparecer:** o Application Insights demora alguns minutos para
ingerir. Não trave a aula esperando; volte a ele no fechamento do encontro.

---

## Parte 2 — O esquecimento (10 min)

A terceira pergunta do roteiro é "qual era mesmo o meu CPF?", e ele não sabe.

```
Cliente: meu CPF é 111.222.333-44, qual o status da minha conexão?
ARI:     ...não tenho acesso a sistemas da Aurora nesta versão...

Cliente: qual era mesmo o meu CPF?
ARI:     Eu não tenho acesso aos seus dados pessoais, então não consigo
         ver ou informar o seu CPF.
```

> **Fala.** Ele acabou de receber o CPF, no turno anterior, e não sabe. Não é bug
> e não é limitação do modelo: é que ninguém criou uma sessão. No ADK o runner te
> dava isso de graça e você nem percebia. Aqui, estado de conversa é opt-in. Quem
> vem do ADK descobre isso em produção; vocês estão descobrindo agora, que é bem
> mais barato.

**Deixe o silêncio.** Esta é a primeira vez que o curso mostra o agente falhando
de propósito, e a turma precisa de um segundo para entender que foi intencional.

---

## Parte 3 — Instruction é código (15 min)

> **Edição ao vivo.** `lab01_agente_puro/agent.py`, perto da linha 60:
>
> ```python
> INSTRUCTION_ATIVA = INSTRUCTION_VAGA     # era INSTRUCTION_PROTOCOLO
> ```

Rode de novo e faça a mesma pergunta sobre status da conexão. Com a versão vaga
ele inventa previsão de reparo para um cliente que não existe.

> **Fala.** Mesma pergunta, mesmo modelo, mesma temperatura. A única coisa que
> mudou foi um bloco de texto, e agora ele inventa previsão de reparo. A diferença
> entre as duas versões não é "capricho de prompt": é a seção LIMITES dizendo com
> todas as letras o que ele não tem. Instruction é código. Entra em revisão, entra
> em versionamento, quebra em produção.

Vale abrir as duas constantes lado a lado e ler a seção LIMITES em voz alta.

> **Desfazer.** Volte `INSTRUCTION_ATIVA` para `INSTRUCTION_PROTOCOLO`. Se
> esquecer, o lab 02a vira uma bagunça: o agente passa a inventar dado de fatura
> no meio da demo de memória, e você vai caçar o motivo no lugar errado.

**Gancho para o lab 08:** guarde essa discussão. No último lab a turma vai rodar
as duas instructions contra a mesma massa de testes e receber dois números em vez
de opinião.

---

## Parte 4 — Trocar de runtime sem tocar no agente (10 min)

No `.env`:

```
ARI_CLIENT=foundry
```

Rode de novo. O mesmo agente passa a rodar contra o Azure AI Foundry Agent Service.

> **Fala.** Nenhuma linha deste arquivo mudou. O que mudou foi uma variável de
> ambiente, e agora o agente e as threads vivem do lado do serviço, com as
> políticas do projeto aplicadas lá. Isto é o argumento de portabilidade do
> framework, e vale mais que qualquer diagrama: o agente não sabe onde roda.

**Se falhar:** `AZURE_AI_PROJECT_ENDPOINT` precisa terminar em
`/api/projects/<nome-do-projeto>`, e não na raiz do recurso. Volte para
`ARI_CLIENT=aoai` e siga — esta demo não vale travar a aula.

> **Desfazer.** `ARI_CLIENT=aoai`.

---

## Perguntas que a turma faz aqui

**"Por que não usar a API do OpenAI direto?"**
Porque o resto do sistema está no Azure. Identidade por Entra ID, cota gerenciada,
trace no Application Insights, e o dado corporativo que os próximos labs vão
consumir. Agente sem dado corporativo é demo.

**"Dá para usar chave em vez de `az login`?"**
Dá: preencha `AZURE_OPENAI_API_KEY`. É o plano B para sala com problema de
identidade. O caminho de produção é o Entra ID, e é o default aqui de propósito.

**"120 palavras não é pouco?"**
Instruction de tamanho de resposta é controle de custo e de experiência ao mesmo
tempo. Mostre o número de tokens do span e a conta fica evidente.

---

## Se der errado

| Sintoma | Causa | Saída |
|---|---|---|
| `ModuleNotFoundError: comum` | rodou o arquivo, ou fora da raiz | `python -m lab01_agente_puro.agent` |
| `ImportError: cannot import name 'Agent'` | Python do sistema | ative o venv |
| 404 do modelo | `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` é o nome do modelo, não do deployment | liste os deployments |
| `DefaultAzureCredential failed` | sem `az login` ou sem o papel | Cognitive Services OpenAI User no recurso |

---

## O gancho

O agente esquece o CPF do turno anterior. Não adianta caprichar mais na
instruction: falta uma peça, e ela tem nome.

→ [Lab 02a](lab02a.md)
