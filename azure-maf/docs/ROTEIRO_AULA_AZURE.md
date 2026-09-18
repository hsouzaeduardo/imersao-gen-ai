# Roteiro de condução, versão Azure

Mesma estrutura de dois encontros de 4 horas da versão ADK,
com os ajustes que a pilha Azure impõe.

Este arquivo é a grade: horários, demos e falas de abertura.
O nível abaixo — cada lab quebrado em partes, com comando, saída esperada
e a fala de cada momento — está em
[`CONDUCAO_LAB_A_LAB.md`](CONDUCAO_LAB_A_LAB.md).

## Encontro 1: do zero ao dado real

| Bloco | Tempo | Conteúdo | Momento chave |
|---|---|---|---|
| Abertura | 15 min | a Aurora Fibra e o contrato do curso | "o agente vai quebrar seis vezes, de propósito" |
| Lab 01 | 45 min | `Agent`, chat client, instruction | trocar `ARI_CLIENT` para foundry e o agente continuar igual |
| Lab 02a | 50 min | `AgentSession` e histórico em Redis | rodar sem Redis e com Redis, o mesmo código |
| Intervalo | 15 min | | |
| Lab 02b | 50 min | memória longa e context providers | apagar o prontuário e o agente voltar a perguntar tudo |
| Lab 03 | 60 min | `@tool` e function middleware | pedir reinício direto e o middleware bloquear |
| Fechamento | 25 min | trace no Application Insights | a árvore de um atendimento na tela |

## Encontro 2: do dado real ao processo

| Bloco | Tempo | Conteúdo | Momento chave |
|---|---|---|---|
| Retomada | 15 min | o quadro do MAPEAMENTO.md | onde estamos, nas duas pilhas |
| Lab 04 | 90 min | MCP Toolbox em Container Apps | editar o tools.yaml e reiniciar só o Toolbox |
| Intervalo | 15 min | | |
| Lab 05 | 70 min | handoff e `as_tool` | apagar a description e ver o roteamento desandar |
| Lab 06 | 80 min | sequential, concurrent, loop | `run comparar` com os dois tempos na tela |
| Fechamento | 30 min | ADK versus MAF, e o que sobrevive à troca | a seção 7 do MAPEAMENTO.md |

---

## As sete demos que não podem falhar

As seis da versão ADK, mais uma que só existe aqui.

1. **Lab 01**: instruction vaga contra instruction protocolo.
2. **Lab 01, extra Azure**: trocar `ARI_CLIENT=aoai` por `foundry`.
   O mesmo agente roda em outro runtime, sem mudar uma linha do lab.
   É o argumento de portabilidade, e vale mais do que qualquer diagrama.
3. **Lab 02a**: sem Redis esquece, com Redis lembra.
4. **Lab 03**: descrição da tool trocada por "Consulta coisas".
5. **Lab 04**: editar o `tools.yaml`, reiniciar o Toolbox, comportamento novo.
6. **Lab 06**: `run comparar`, os dois tempos na tela.
7. **Fechamento**: a árvore de trace no Application Insights,
   com o custo em tokens de um atendimento inteiro.

---

## Falas que funcionam nesta versão

**Na abertura do lab 02a:**
o ADK te dava sessão de graça e você nem percebia. Aqui você cria a thread
com a própria mão. Parece trabalho a mais, e é, e em troca você sabe
exatamente onde mora o estado do seu sistema. Em ambiente regulado,
saber onde o dado mora não é detalhe, é o requisito.

**No lab 04, apontando para o tools.yaml:**
este arquivo é idêntico ao do laboratório em Google. Byte a byte.
Trocamos o framework inteiro e a camada de dados não sentiu.
Quando vocês forem decidir stack de agente, decidam o acesso a dado primeiro:
é a decisão com maior meia-vida das três.

**No fechamento do lab 06:**
vocês viram o mesmo problema resolvido em dois frameworks.
O que mudou foram nomes de classe. O que não mudou foi o raciocínio:
o que é determinístico, o que é julgamento, onde mora a política,
quem paga a conta do paralelismo. Isso é o que vocês levam.

---

## Perguntas que a turma sempre faz nesta versão

**"ADK ou MAF?"**
A pergunta certa é qual nuvem já sustenta o resto do seu sistema.
Agente sem dado corporativo é demo, e o dado está onde o dado está.

**"Dá para misturar?"**
Dá, e o MCP é a costura. O Toolbox deste repositório serve os dois.
Agente em Azure consumindo tool MCP publicada pelo time de dados em outra nuvem
é arquitetura comum, não gambiarra.

**"E o Semantic Kernel e o AutoGen?"**
O MAF é a convergência dos dois. Código novo nasce em MAF.
Para código existente, existe guia de migração oficial para as duas origens.

**"Isso passa em revisão de segurança?"**
Este repositório não, e a seção final do `infra/README.md` lista os quatro
motivos exatos. Percorra os quatro em voz alta: é o melhor conteúdo
de arquitetura do curso inteiro e custa 15 minutos.

---

## Checklist do instrutor, véspera

- [ ] `./infra/deploy.sh` rodado e `.env` gerado
- [ ] `curl https://<toolbox>/mcp` respondendo e `curl https://<api>/health` ok
- [ ] cota do deployment conferida: turma de 30 no lab 06 concorrente estoura TPM
- [ ] `pip show agent-framework agent-framework-redis` e nomes de classe conferidos
- [ ] `az login` feito nas máquinas, ou chave distribuída como plano B
- [ ] `docker compose -f docker-compose.local.yml up -d` testado como plano B de rede
- [ ] Application Insights com dados, o trace demora alguns minutos para aparecer
- [ ] `prontuarios.json` apagado, para o lab 02b começar limpo
