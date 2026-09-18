# Lab 01 (Azure + MAF): primeiro dia, sem crachá

```bash
az login
python -m lab01_agente_puro.agent
```

## O que muda em relação à versão ADK

| ADK | MAF |
|---|---|
| `LlmAgent(model="gemini-2.5-flash")` | `Agent(OpenAIChatClient(azure_endpoint=...))` |
| modelo declarado no agente | modelo injetado pelo chat client |
| `adk web` traz UI e trace prontos | DevUI, ou script próprio, ou hospedar como API |
| sessão implícita no runner | sem `AgentSession`, cada `run` é uma conversa nova |

O terceiro ponto dessa tabela é o que mais surpreende quem vem do ADK.
No MAF, estado de conversa é opt-in, e este lab mostra isso doendo:
o agente esquece o CPF no turno seguinte porque ninguém criou uma thread.

## Roteiro

1. **Anatomia do turno**: rode e mostre a resposta. Se `ENABLE_OTEL=true`,
   abra o Application Insights e mostre o span `chat` com modelo, tokens e latência.
   Vale mais do que qualquer slide sobre custo.
2. **Instruction é código**: troque `INSTRUCTION_ATIVA` para `INSTRUCTION_VAGA`
   e rode a mesma pergunta. Com a versão vaga ele inventa previsão de reparo.
3. **Trocar de provedor sem tocar no agente**: mude `ARI_CLIENT=foundry` no `.env`.
   O mesmo agente passa a rodar contra o Azure AI Foundry Agent Service.
   Nenhuma linha deste arquivo muda.

## Gotchas

- **Entra ID versus chave.** Com `AZURE_OPENAI_API_KEY` vazio, o código usa
  `AzureCliCredential` e você precisa de `az login` e do papel
  Cognitive Services OpenAI User no recurso. É o caminho de produção,
  e é o que trava aula corporativa quando ninguém conferiu antes.
- **`deployment_name` não é o nome do modelo.** É o nome do deployment que você criou.
  Errar isso dá 404 com mensagem pouco útil.
- **Aula com 30 pessoas no mesmo deployment estoura TPM.** Verifique a cota
  ou crie deployments separados por dupla.
