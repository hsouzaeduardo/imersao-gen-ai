// ============================================================================
// Infra do cenário ARI / Aurora Fibra, parte declarativa.
//
//   az deployment group create -g rg-ari-aurora -f infra/main.bicep \
//      -p sufixo=demo pgPassword='<senha forte>'
//
// Container Apps e o build das imagens ficam no deploy.sh, porque dependem
// de uma imagem já publicada no registry. Este bicep cobre o resto:
// modelo, banco, memória e observabilidade.
// ============================================================================

@description('Sufixo para nomes únicos.')
param sufixo string

@description('Região dos recursos regionais.')
param location string = resourceGroup().location

@description('Região com cota do modelo.')
param locationModelo string = 'eastus2'

@description('Nome do deployment do modelo.')
param modelo string = 'gpt-4o-mini'

@description('Versão do modelo.')
param modeloVersao string = '2024-07-18'

@description('Usuário administrador do PostgreSQL.')
param pgUser string = 'aurora'

@secure()
@description('Senha do administrador do PostgreSQL.')
param pgPassword string

var aoaiName = 'aoai-ari-${sufixo}'
var pgName = 'pg-ari-${sufixo}'
var redisName = 'redis-ari-${sufixo}'
var lawName = 'law-ari-${sufixo}'
var appiName = 'appi-ari-${sufixo}'

// ---------------------------------------------------------------- modelo
resource aoai 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: aoaiName
  location: locationModelo
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: aoaiName
    publicNetworkAccess: 'Enabled'
    // Em produção, desabilite chave e use somente Entra ID.
    disableLocalAuth: false
  }
}

resource deploymentModelo 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: aoai
  name: modelo
  sku: {
    name: 'GlobalStandard'
    capacity: 50
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelo
      version: modeloVersao
    }
  }
}

// ---------------------------------------------------------------- banco
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: pgName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: pgUser
    administratorLoginPassword: pgPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
  }
}

resource pgDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-03-01-preview' = {
  parent: postgres
  name: 'aurora_fibra'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Libera serviços do Azure, incluindo os Container Apps. Em produção,
// troque por private endpoint e VNet integration.
resource pgFirewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = {
  parent: postgres
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ---------------------------------------------------------------- memória
resource redis 'Microsoft.Cache/redis@2023-08-01' = {
  name: redisName
  location: location
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
}

// ---------------------------------------------------------------- telemetria
resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: lawName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appiName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: law.id
  }
}

// ---------------------------------------------------------------- saídas
output azureOpenAiEndpoint string = aoai.properties.endpoint
output modeloDeployment string = deploymentModelo.name
output postgresFqdn string = postgres.properties.fullyQualifiedDomainName
output redisHost string = redis.properties.hostName
output appInsightsConnectionString string = appInsights.properties.ConnectionString
