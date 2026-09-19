# Como executar cada lab

Guia operacional: o que precisa estar no ar, o comando, e como saber que deu certo.
Sem didática — a condução da aula, com as falas de cada momento, está em
[`CONDUCAO_LAB_A_LAB.md`](CONDUCAO_LAB_A_LAB.md).

---

## Preparo, uma vez só

```bash
cd azure-maf

python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # macOS / Linux

pip install -r requirements.txt

cp .env.example .env                # e preencha, ver abaixo
az login
az account set --subscription <id-da-subscription>
```

### O `.env` mínimo

Só três campos travam os labs. O resto tem default que funciona.

```
AZURE_OPENAI_ENDPOINT=https://<seu-recurso>.openai.azure.com/
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=<nome-do-deployment>
AZURE_OPENAI_API_KEY=                # vazio = Entra ID, o caminho recomendado
```

`AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` é o nome do **deployment**, não o nome do modelo.
Errar isso dá 404 com mensagem pouco útil. Para descobrir o que existe:

```bash
az cognitiveservices account deployment list \
  -n <recurso> -g <resource-group> --query "[].name" -o tsv
```

Com a chave vazia, a autenticação é por Entra ID e o seu usuário precisa do papel
**Cognitive Services OpenAI User** no recurso.

### Duas regras que quebram todo mundo

**Sempre `-m`, sempre da raiz do projeto.** `python lab01_agente_puro/agent.py` falha
com `ModuleNotFoundError: No module named 'comum'` — rodar o arquivo põe a pasta dele
no `sys.path` em vez da raiz.

**Sempre o Python do venv.** Se o `python` do sistema tiver uma versão antiga do
`agent-framework`, você passa do erro acima e quebra no `from agent_framework import`.
Confirme com o `(.venv)` no prompt, ou chame `.venv\Scripts\python.exe` direto.

---

## O que cada lab precisa no ar

| Lab | Modelo | API de rede | Toolbox | Redis |
|---|:--:|:--:|:--:|:--:|
| 01 | sim | — | — | — |
| 02a | sim | — | — | opcional |
| 02b | sim | — | — | — |
| 03 | sim | **sim** | — | — |
| 04 | sim | sim | **sim** | — |
| 05 | sim | sim | **sim** | — |
| 06 | sim | sim | **sim** | — |
| 07 | sim | — | — | — |
| 08 | sim | sim | **sim** | — |

Os labs 01, 02a, 02b e 07 rodam com a rede corporativa bloqueando tudo, desde que o
endpoint do Azure OpenAI passe. É por isso que eles abrem e fecham o curso.

O lab 07 não usa Toolbox nem API de rede, mas precisa de **dois terminais**: um roda
o agente do "outro time", o outro roda o seu.

---

## Subindo os serviços

Três caminhos. Escolha um e siga com ele.

### A. Banco no Azure, resto no notebook

```bash
docker compose -f docker-compose.azure-db.yml up -d
```

Sobe Toolbox, API de rede e Redis apontando o Toolbox para o Postgres do Azure.
Exige no `.env`:

```
POSTGRES_HOST=<servidor>.postgres.database.azure.com
POSTGRES_DB=aurora_fibra
POSTGRES_USER=<usuario>
POSTGRES_PASSWORD=<senha>
```

Se faltar alguma, o Compose falha na hora com a variável que faltou, em vez de subir
um Toolbox que só quebra na primeira pergunta.

O IP da máquina precisa estar liberado no firewall do servidor:

```bash
az postgres flexible-server firewall-rule list -n <servidor> -g <rg> -o table
```

### B. Tudo local (Plano B de rede)

```bash
docker compose -f docker-compose.local.yml up -d
```

Sobe também um Postgres local, já carregado com `data/seed_aurora.sql`. Este arquivo
**ignora de propósito** o bloco `POSTGRES_*` do `.env`: ele é a rota de fuga do Azure
e não pode passar a depender do Azure.

### C. Sem Docker

Quando o Docker Desktop não coopera, dá para subir as duas peças na mão:

```bash
# API de rede
python -m uvicorn mock_api.main:app --port 8000

# Toolbox, binário nativo, com as POSTGRES_* no ambiente
toolbox --tools-file lab04_mcp_toolbox/tools.yaml --address 127.0.0.1 --port 5000
```

O binário sai de `https://storage.googleapis.com/genai-toolbox/v1.1.0/<so>/<arch>/toolbox`.
Atenção ao exportar o `.env` pelo shell: senha com caractere especial pode ser comida
antes de chegar no processo, e o Toolbox sobe reclamando de `password: null`.

### Conferindo

```bash
curl http://localhost:5000/         # Toolbox
curl http://localhost:8000/health   # API de rede -> {"status":"ok",...}
```

O log do Toolbox, quando sobe certo, diz: `Initialized 5 tools` e `Server ready to serve!`.

---

## Lab 01 — Agente puro

**Precisa:** só o modelo.

```bash
python -m lab01_agente_puro.agent
```

**Esperado:** três perguntas e três respostas. Na terceira, "qual era mesmo o meu CPF?",
ele responde que não sabe. **Isso é o resultado correto**, não uma falha de execução.

**Variações:**

- Trocar `INSTRUCTION_ATIVA` para `INSTRUCTION_VAGA` no topo do arquivo e rodar de novo.
- `ARI_CLIENT=foundry` no `.env`, para rodar contra o Foundry Agent Service. Exige
  `AZURE_AI_PROJECT_ENDPOINT` terminando em `/api/projects/<nome-do-projeto>`.

---

## Lab 02a — Sessão

**Precisa:** modelo. Redis é opcional e muda o resultado.

```bash
python -m lab02_memoria.a_thread
python -m lab02_memoria.a_thread --continuar
```

**Sem `REDIS_URL`:** a segunda execução não lembra de nada. Correto.

**Com Redis:** deixe `REDIS_URL=redis://localhost:6379` no `.env` e suba o container.
A segunda execução lembra. Se o Redis estiver configurado mas fora do ar, o lab avisa
no começo e segue com memória de processo, em vez de estourar.

**Verificação no banco:**

```bash
docker exec -it aurora-redis redis-cli KEYS '*'
```

---

## Lab 02b — Prontuário

**Precisa:** só o modelo.

```bash
rm lab02_memoria/prontuarios.json     # comece limpo
python -m lab02_memoria.b_memoria_longa
```

**Esperado:** dois atendimentos. No segundo, com sessão nova, ele já oferece visita de
manhã e aviso por WhatsApp sem perguntar. O arquivo gerado:

```json
{ "11122233344": ["Se precisar de visita técnica, prefere atendimento pela manhã.", "..."] }
```

Apague o arquivo e rode de novo: ele volta a perguntar tudo.

---

## Lab 03 — Tool externa

**Precisa:** modelo e API de rede.

```bash
docker compose -f docker-compose.azure-db.yml up -d mock_api
python -m lab03_tool_externa.agent
```

**Esperado:** na primeira fala ele consulta o CEP 06010-100 e acha o incidente na OLT
Osasco Centro. Na terceira, o pedido de reinício é barrado pelo middleware.

Se a resposta disser que "não consegui consultar o status da rede", a API não está no ar
ou `AURORA_API_URL` está errado.

**Variações:**

- Trocar a `description` de `consultar_status_rede` em `comum/tools_rede.py` por
  `"Consulta coisas"`.
- Comentar o `raise MiddlewareTermination(...)` em `lab03_tool_externa/agent.py`.
- `docker compose -f docker-compose.azure-db.yml stop mock_api` e rodar de novo.

---

## Lab 04 — MCP Toolbox

**Precisa:** modelo, API de rede e Toolbox.

```bash
docker compose -f docker-compose.azure-db.yml up -d
python -m lab04_mcp_toolbox.agent
```

**Esperado:** ele responde com a fatura vencida da Marcela — competência 2026-08,
R$ 129,90, vencimento 10/08/2026 — vinda do banco, e informa que não há visita agendada
para o CPF dela.

**Variação que vale a aula:** edite `lab04_mcp_toolbox/tools.yaml`, reinicie **só** o
Toolbox, e faça a mesma pergunta.

```bash
docker compose -f docker-compose.azure-db.yml restart toolbox
```

---

## Lab 05 — Multiagente

**Precisa:** modelo, API de rede e Toolbox.

```bash
python -m lab05_handoff.agent           # handoff
python -m lab05_handoff.agent --tools   # agentes como ferramentas
```

**Esperado, handoff:** o coordenador encaminha para cobrança e o workflow para,
aguardando a próxima fala do cliente. Uma etapa só na tela é o comportamento correto.

**Esperado, `--tools`:** uma resposta única, ligando as três faturas de R$ 69,90 do
Wellington (CPF 444.555.666-77) à luz vermelha do roteador.

**Variação:** trocar `DESC_TECNICO` por `"Agente técnico."` em `lab05_handoff/especialistas.py`.

---

## Lab 06 — Orquestração

**Precisa:** modelo, API de rede e Toolbox.

```bash
python -m lab06_workflows.run sequencial
python -m lab06_workflows.run concorrente
python -m lab06_workflows.run loop
python -m lab06_workflows.run comparar
python -m lab06_workflows.run completo
```

**`comparar`** é o que roda em aula: imprime os dois tempos e o ganho. Em execução real
deu 12,8s sequencial contra 7,4s concorrente, 1,7×. Os números variam com a latência do
deployment; a ordem de grandeza, não.

**`loop`** costuma aprovar em 2 a 4 iterações. Se travar no teto, é sinal de que o
crítico está exigente demais — o teto existe justamente porque a condição de saída é opinião.

**Cota:** este é o lab que estoura TPM com a turma inteira rodando junto. Confira a
capacidade do deployment antes, ou distribua deployments por dupla.

---

## Lab 07 — A2A

**Precisa:** modelo, e **dois terminais**. Não usa Toolbox nem API de rede.

```bash
# terminal 1 — o "outro time"
python -m uvicorn lab07_a2a.servidor:app --port 9000

# terminal 2 — você
python -m lab07_a2a.agent --card
python -m lab07_a2a.agent --direto
python -m lab07_a2a.agent
```

Os dois terminais precisam do venv ativado e rodar da raiz do projeto.

**Conferindo o servidor:**

```bash
curl http://localhost:9000/.well-known/agent-card.json
```

**Esperado:**

- `--card` imprime nome, descrição, versão e skill do agente remoto. É a descoberta.
- `--direto` devolve o diagnóstico vindo do outro processo.
- sem argumento, o maestro consulta o remoto e entrega uma resposta única, sem
  mencionar a consulta.

Se der `Não consegui ler o cartão`, o terminal 1 não está de pé.

**Variações:**

- Pare o terminal 1 e rode de novo: o especialista virou dependência de rede.
- Troque a `description` do `CARTAO` em `lab07_a2a/servidor.py` por `"Agente técnico."`,
  reinicie **só o servidor**, e veja o maestro deixar de consultar.

**Servidor noutra máquina ou atrás de proxy:** ajuste `A2A_TECNICO_URL` no `.env`.
Ela é lida nos dois lados — no servidor, para publicar o endereço certo dentro do
cartão; no cliente, para saber onde procurar.

---

## Lab 08 — Avaliação

**Precisa:** modelo, API de rede e Toolbox. É o lab mais demorado, porque roda
a massa inteira contra o modelo.

```bash
python -m lab08_avaliacao.avaliar                 # ~3 a 5 min
python -m lab08_avaliacao.avaliar --repeticoes 3  # ~10 a 15 min
python -m lab08_avaliacao.avaliar --ab            # ~7 a 10 min
```

**Esperado:** 7 de 8 casos. O `incidente_na_regiao` falha de propósito — a regra
1 da instruction manda pedir CPF antes de qualquer consulta, e o caso só dá o
CEP. É achado, não defeito da suite.

No `--ab`, a variante vaga fica em 6/8 e a com protocolo em 7/8, e o caso que as
separa é o `reinicio_sem_autorizacao`.

No `--repeticoes`, espere ver pelo menos um caso oscilando. Se nenhum oscilar,
não significa determinismo: significa que a variação não apareceu em poucas voltas.

**Custo:** oito casos com rubrica são dezesseis chamadas de modelo por rodada, e
o `--ab` dobra. Não rode em loop sem olhar a cota.

---

## UI — os agentes no DevUI

**Precisa:** modelo. Toolbox e agente A2A são opcionais e mudam o que aparece.

```bash
python -m ui                 # http://localhost:8080
python -m ui --port 9090
```

**Esperado:** o launcher lista as entidades registradas e, se algo estiver fora
do ar, diz o que ficou de fora e o que isso custou. Com tudo no ar são **22
entidades**, dos oito labs; só com o modelo, 4.

Confira que a lista impressa no terminal bate com a da tela: se a porta 8080 já
estiver ocupada, o processo morre em silêncio e você fica olhando uma UI antiga.

Para ter todas:

```bash
docker compose -f docker-compose.azure-db.yml up -d
python -m uvicorn lab07_a2a.servidor:app --port 9000
```

**Portas em uso:** Toolbox 5000, API de rede 8000, DevUI 8080, A2A 9000.

---

## Visualização no Habbo (opcional)

Com `HABBO_URL` e `HABBO_API_KEY` no `.env`, cada agente publica o que está fazendo numa
sala de avatares. Sem `HABBO_URL`, tudo vira no-op e nenhum lab muda.

Esvaziar a sala entre demos:

```bash
python -c "import asyncio; from comum import limpar_sala; asyncio.run(limpar_sala())"
```

---

## Encerrando

```bash
docker compose -f docker-compose.azure-db.yml down
rm lab02_memoria/prontuarios.json
```

Se você liberou o seu IP no firewall do Postgres só para a aula, remova a regra:

```bash
az postgres flexible-server firewall-rule delete \
  -n <servidor> -g <rg> --rule-name <nome-da-regra> --yes
```

---

## Erros comuns

| Mensagem | Causa | Correção |
|---|---|---|
| `ModuleNotFoundError: No module named 'comum'` | rodou o arquivo, ou fora da raiz | `python -m pacote.modulo` a partir de `azure-maf/` |
| `ImportError: cannot import name 'Agent'` | Python do sistema, não o do venv | ative o venv, ou chame `.venv\Scripts\python.exe` |
| `404` no modelo | `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` é o nome do modelo, não do deployment | liste os deployments e use o nome exato |
| `API version not supported` | alguém fixou `api_version` no chat client | remova; o cliente negocia sozinho |
| `DefaultAzureCredential failed` | sem `az login`, ou sem o papel no recurso | `az login` e Cognitive Services OpenAI User |
| Tool "some" em runtime | MCP criado fora do `async with` | mantenha o agente dentro do bloco |
| Toolbox não sobe, `password: null` | `POSTGRES_PASSWORD` vazio ou comido pelo shell | confira o `.env`; não exporte pelo shell |
| Agente diz que não consultou a rede | `mock_api` fora do ar | `curl http://localhost:8000/health` |
| `--continuar` não lembra | Redis fora do ar | o lab avisa no começo; suba o container |
| `connection timed out` no Postgres | IP fora do firewall | adicione a regra para o seu IP |
