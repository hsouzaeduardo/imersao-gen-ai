# Infra do cenário em Azure

Dois caminhos, escolha um.

## Caminho rápido: script único

```bash
az login
./infra/deploy.sh
```

Provisiona tudo e escreve o `.env` da raiz com os endpoints prontos.
Leva de 15 a 25 minutos, quase tudo no PostgreSQL Flexible Server.
Rode na véspera, nunca no começo da aula.

## Caminho declarativo: bicep mais script

```bash
az group create -n rg-ari-aurora -l brazilsouth
az deployment group create -g rg-ari-aurora -f infra/main.bicep \
  -p sufixo=demo pgPassword='<senha forte>'
```

O `main.bicep` cobre modelo, banco, Redis e Application Insights.
Container Apps e o build das imagens continuam no `deploy.sh`,
porque dependem de imagem publicada em registry.

## O que é provisionado e por quê

| Recurso | Papel no cenário | Lab |
|---|---|---|
| Azure OpenAI e deployment do modelo | o modelo por trás do `Agent` | todos |
| Azure AI Foundry, opcional | agentes e threads gerenciados no serviço | 01, 02 |
| PostgreSQL Flexible Server | base de clientes da Aurora | 04 em diante |
| Container App: MCP Toolbox | cardápio de queries aprovadas | 04 em diante |
| Container App: API de rede | painel de status da Aurora | 03 em diante |
| Azure Cache for Redis | thread persistente e memória longa | 02 |
| Application Insights e Log Analytics | traces OpenTelemetry do MAF | todos |

## Custo

Com os SKUs deste script, o cenário fica na casa de poucas dezenas de dólares
por mês se ficar ligado, e quase nada se você apagar o grupo depois da aula:

```bash
az group delete -n rg-ari-aurora --yes --no-wait
```

O que pesa é o modelo, e o que pesa no modelo é o lab 06:
três ramos concorrentes multiplicam o consumo por três no mesmo instante.

## O que este script simplifica e produção não deve

1. **Postgres com acesso público e senha.** Em produção: private endpoint,
   VNet integration nos Container Apps e autenticação por Entra ID,
   com identidade gerenciada no Toolbox, o que remove a senha do `tools.yaml`.
2. **Toolbox com ingress externo e sem autenticação.** Em produção,
   ingress interno ou Entra ID na frente, porque quem alcança o Toolbox
   alcança o cardápio inteiro de queries.
3. **Chave do ACR em variável.** Em produção, identidade gerenciada no pull.
4. **Sem Key Vault.** Em produção, segredos no Key Vault com referência
   nos Container Apps.

Esses quatro pontos rendem um bloco de 15 minutos sobre a diferença entre
demo que funciona e arquitetura que passa em revisão de segurança.
