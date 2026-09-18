#!/usr/bin/env bash
# ============================================================================
# Provisiona o cenário ARI / Aurora Fibra em Azure.
#
#   ./infra/deploy.sh
#
# Leva de 15 a 25 minutos, quase tudo é o Postgres Flexible Server.
# Rode com antecedência, nunca no começo da aula.
# ============================================================================
set -euo pipefail

# ------------------------- parâmetros -------------------------
SUFIXO="${SUFIXO:-$RANDOM}"
RG="${RG:-rg-ari-aurora}"
LOC="${LOC:-brazilsouth}"
LOC_MODELO="${LOC_MODELO:-eastus2}"     # região com cota de modelo

AOAI="aoai-ari-$SUFIXO"
DEPLOY_MODELO="${DEPLOY_MODELO:-gpt-4o-mini}"
VERSAO_MODELO="${VERSAO_MODELO:-2024-07-18}"

PG="pg-ari-$SUFIXO"
PG_USER="aurora"
PG_PASS="${PG_PASS:-Aurora#$RANDOM$RANDOM}"
PG_DB="aurora_fibra"

ACR="acrari$SUFIXO"
CAE="cae-ari-$SUFIXO"
REDIS="redis-ari-$SUFIXO"
LAW="law-ari-$SUFIXO"
APPI="appi-ari-$SUFIXO"

echo ">> Grupo de recursos"
az group create -n "$RG" -l "$LOC" -o none

# ------------------------- modelo -------------------------
echo ">> Azure OpenAI e deployment do modelo"
az cognitiveservices account create \
  -n "$AOAI" -g "$RG" -l "$LOC_MODELO" \
  --kind OpenAI --sku S0 --custom-domain "$AOAI" -o none

az cognitiveservices account deployment create \
  -n "$AOAI" -g "$RG" \
  --deployment-name "$DEPLOY_MODELO" \
  --model-name "$DEPLOY_MODELO" \
  --model-version "$VERSAO_MODELO" \
  --model-format OpenAI \
  --sku-capacity 50 --sku-name GlobalStandard -o none

AOAI_ENDPOINT=$(az cognitiveservices account show -n "$AOAI" -g "$RG" --query properties.endpoint -o tsv)

# Papel de acesso por Entra ID, sem chave no .env
ASSINATURA=$(az account show --query id -o tsv)
EU=$(az ad signed-in-user show --query id -o tsv)
az role assignment create \
  --assignee "$EU" \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/$ASSINATURA/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$AOAI" -o none || true

# ------------------------- banco -------------------------
echo ">> PostgreSQL Flexible Server (demora)"
az postgres flexible-server create \
  -n "$PG" -g "$RG" -l "$LOC" \
  --admin-user "$PG_USER" --admin-password "$PG_PASS" \
  --database-name "$PG_DB" \
  --tier Burstable --sku-name Standard_B1ms --storage-size 32 \
  --version 16 --public-access 0.0.0.0 -o none

echo ">> Carregando a base da Aurora"
az postgres flexible-server execute \
  -n "$PG" -u "$PG_USER" -p "$PG_PASS" -d "$PG_DB" \
  -f ./data/seed_aurora.sql -o none

# ------------------------- imagens -------------------------
echo ">> Container Registry e build das imagens"
az acr create -n "$ACR" -g "$RG" --sku Basic --admin-enabled true -o none

cp lab04_mcp_toolbox/tools.yaml infra/tools.yaml
az acr build -r "$ACR" -t toolbox:v1 -f infra/Dockerfile.toolbox infra/ -o none
rm -f infra/tools.yaml

cp mock_api/main.py infra/main.py
az acr build -r "$ACR" -t mockapi:v1 -f infra/Dockerfile.mockapi infra/ -o none
rm -f infra/main.py

ACR_SERVER=$(az acr show -n "$ACR" --query loginServer -o tsv)
ACR_USER=$(az acr credential show -n "$ACR" --query username -o tsv)
ACR_PASS=$(az acr credential show -n "$ACR" --query "passwords[0].value" -o tsv)

# ------------------------- container apps -------------------------
echo ">> Container Apps"
az extension add --name containerapp --upgrade -y -o none
az containerapp env create -n "$CAE" -g "$RG" -l "$LOC" -o none

az containerapp create \
  -n aurora-toolbox -g "$RG" --environment "$CAE" \
  --image "$ACR_SERVER/toolbox:v1" \
  --registry-server "$ACR_SERVER" --registry-username "$ACR_USER" --registry-password "$ACR_PASS" \
  --target-port 5000 --ingress external \
  --min-replicas 1 --max-replicas 2 \
  --env-vars \
    POSTGRES_HOST="$PG.postgres.database.azure.com" \
    POSTGRES_PORT=5432 \
    POSTGRES_DB="$PG_DB" \
    POSTGRES_USER="$PG_USER" \
    POSTGRES_PASSWORD="$PG_PASS" -o none

az containerapp create \
  -n aurora-mockapi -g "$RG" --environment "$CAE" \
  --image "$ACR_SERVER/mockapi:v1" \
  --registry-server "$ACR_SERVER" --registry-username "$ACR_USER" --registry-password "$ACR_PASS" \
  --target-port 8000 --ingress external \
  --min-replicas 1 --max-replicas 2 -o none

TOOLBOX_FQDN=$(az containerapp show -n aurora-toolbox -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)
API_FQDN=$(az containerapp show -n aurora-mockapi -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)

# ------------------------- memória e observabilidade -------------------------
echo ">> Redis e Application Insights"
az redis create -n "$REDIS" -g "$RG" -l "$LOC" --sku Basic --vm-size c0 -o none
REDIS_HOST=$(az redis show -n "$REDIS" -g "$RG" --query hostName -o tsv)
REDIS_KEY=$(az redis list-keys -n "$REDIS" -g "$RG" --query primaryKey -o tsv)

az monitor log-analytics workspace create -n "$LAW" -g "$RG" -l "$LOC" -o none
az extension add --name application-insights --upgrade -y -o none
LAW_ID=$(az monitor log-analytics workspace show -n "$LAW" -g "$RG" --query id -o tsv)
az monitor app-insights component create --app "$APPI" -g "$RG" -l "$LOC" --workspace "$LAW_ID" -o none
APPI_CONN=$(az monitor app-insights component show --app "$APPI" -g "$RG" --query connectionString -o tsv)

# ------------------------- saída -------------------------
cat > .env <<ENV
AZURE_OPENAI_ENDPOINT=$AOAI_ENDPOINT
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=$DEPLOY_MODELO
AZURE_OPENAI_API_KEY=
ARI_CLIENT=aoai

AURORA_API_URL=https://$API_FQDN
TOOLBOX_MCP_URL=https://$TOOLBOX_FQDN/mcp

REDIS_URL=rediss://$REDIS_HOST:6380
REDIS_PASSWORD=$REDIS_KEY

APPLICATIONINSIGHTS_CONNECTION_STRING=$APPI_CONN
ENABLE_OTEL=true
ENV

echo
echo "============================================================"
echo "Pronto. O .env foi gerado com os endpoints."
echo "Postgres:  $PG.postgres.database.azure.com  (senha no .env do script)"
echo "Toolbox:   https://$TOOLBOX_FQDN/mcp"
echo "API rede:  https://$API_FQDN/health"
echo
echo "Para apagar tudo depois da aula:"
echo "  az group delete -n $RG --yes --no-wait"
echo "============================================================"
