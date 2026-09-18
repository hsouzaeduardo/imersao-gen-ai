# Lab 04 (Azure + MAF): a chave do banco de dados

```bash
# local
docker compose -f docker-compose.local.yml up -d
python -m lab04_mcp_toolbox.agent

# Azure
./infra/deploy.sh          # provisiona Postgres Flexible Server e o Toolbox em Container Apps
# TOOLBOX_MCP_URL=https://aurora-toolbox.<regiao>.azurecontainerapps.io/mcp
```

## O que muda em relação ao ADK

Quase nada, e essa é a mensagem do lab.

| | ADK | MAF |
|---|---|---|
| Servidor de tools | MCP Toolbox for Databases | o mesmo, sem alteração |
| `tools.yaml` | idêntico | idêntico |
| Cliente | `ToolboxToolset(server_url=...)` | `MCPStreamableHTTPTool(url=".../mcp")` |
| Ciclo de vida | gerenciado pelo toolset | `async with`, você abre e fecha |

O `tools.yaml` deste repositório é byte a byte o mesmo do laboratório em ADK.
Trocar de framework não custou nada na camada de dados,
e esse é exatamente o argumento para padronizar acesso a dados em MCP
antes de decidir framework de agente.

## O desenho em Azure

```
Agent (MAF)
   |  MCPStreamableHTTPTool, HTTPS
   v
Container App: MCP Toolbox  --->  Azure Database for PostgreSQL Flexible Server
   |                                   (private endpoint, Entra ID auth)
   +--> Managed Identity para acessar o banco, sem senha no tools.yaml
```

Três pontos que só existem na versão Azure e que valem slide próprio:

1. **Identidade gerenciada em vez de senha.** O Flexible Server aceita autenticação
   por Entra ID, e o Container App do Toolbox usa identidade gerenciada.
   O `tools.yaml` deixa de ter credencial.
2. **Rede privada.** O banco não precisa de IP público. Container Apps com
   VNet integration alcança o banco por private endpoint.
3. **O agente nunca fala com o banco.** Quem fala é o Toolbox. Do ponto de vista
   de segurança, o blast radius de um prompt injection é o cardápio de queries,
   não a base inteira.

## Roteiro

Idêntico ao da versão ADK, com dois acréscimos:

- Mostre o `tools.yaml` sem senha nenhuma, só identidade gerenciada,
  e pergunte à turma o que aconteceria se o agente fosse comprometido.
- Abra o Application Insights e mostre o span da chamada MCP dentro do turno.
  A rastreabilidade ponta a ponta é um argumento de plataforma, não de framework.

## Gotchas

- **A URL do MCP termina em `/mcp`.** Apontar para a raiz do Toolbox não conecta.
- **`async with` importa.** MCP tool é conexão viva. Criar fora do contexto e
  passar para o agente é um erro conhecido e o sintoma é tool que some em runtime.
- **Nome de tool duplicado quebra a chamada.** Se o mesmo servidor MCP for anexado
  duas vezes, ou se uma function tool tiver o mesmo nome de uma tool do MCP,
  o modelo recebe a lista duplicada e falha.
- **Tool de escrita continua precisando de aprovação.** `abrir_chamado` faz INSERT.
  Middleware do lab 03, ou fluxo de aprovação nativo.
