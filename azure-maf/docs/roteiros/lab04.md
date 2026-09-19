# Lab 04 — A chave do banco de dados

**80 min** · precisa do modelo, da API de rede e do Toolbox

> Material transversal em [`../CONDUCAO_LAB_A_LAB.md`](../CONDUCAO_LAB_A_LAB.md).

---

## A falha que abriu este lab

"E a minha fatura de agosto?" O painel de rede não sabe. Fatura, contrato,
chamado e agenda estão no Postgres, e o agente não tem a chave.

---

## Preparação

```bash
docker compose -f docker-compose.azure-db.yml up -d
curl http://localhost:5000/                  # Toolbox
curl http://localhost:8000/health            # API de rede
python -m lab04_mcp_toolbox.agent
```

O log do Toolbox, quando sobe certo, diz `Initialized 5 tools` e
`Server ready to serve!`.

**Dados deste lab:** Marcela, CPF `111.222.333-44` — contrato ativo, uma fatura
vencida de R$ 129,90 (competência 2026-08, vencimento 10/08), dois chamados de
lentidão e **nenhuma visita agendada**.

---

## Parte 1 — O atendimento com dado real (15 min)

```
Cliente: meu CPF é 111.222.333-44, tenho alguma fatura em aberto?
ARI:     Competência 2026-08, R$ 129,90, vencimento 10/08/2026.
```

> **Fala.** Esse valor saiu do Postgres, no Azure, agora. E o agente nunca falou
> com o banco.

Deixe a frase no ar por um segundo antes de explicar. A turma vai assumir que o
agente tem string de conexão.

Na terceira fala, ele responde que não há visita agendada para a Marcela. **Isso
está correto** — é a Ana Beatriz que tem visita. Se alguém achar que a tool
falhou, é o momento de mostrar a tabela do elenco.

---

## Parte 2 — O tools.yaml (20 min)

Abra o arquivo e percorra uma tool inteira, de cima a baixo.

```yaml
listar_faturas_em_aberto:
  kind: postgres-sql
  parameters:
    - name: cpf
  statement: |
    SELECT f.competencia, f.valor, f.vencimento, f.status
    FROM faturas f ... WHERE c.cpf = $1
```

> **Fala.** O time de Dados não entrega a senha do banco para o agente. Entrega
> este arquivo: cada tool é uma query parametrizada, revisada, com escopo fechado.
> O agente escolhe **qual** chamar, nunca **o que** executar.

E o argumento que fecha:

> **Fala.** Se alguém injetar prompt no seu agente, o estrago máximo é chamar uma
> das cinco queries que já estavam aprovadas. O blast radius é o cardápio, não a base.

Mostre também os `toolsets` no fim do arquivo, e que `abrir_chamado` **não** está
no `atendimento_n1`. É o gancho do isolamento do lab 05.

---

## Parte 3 — Mudar o agente sem deploy de agente (25 min)

> **Edição ao vivo.** `lab04_mcp_toolbox/tools.yaml`: mude a descrição de uma tool,
> ou acrescente uma coluna ao `SELECT` de `buscar_cliente_por_cpf`.

```bash
docker compose -f docker-compose.azure-db.yml restart toolbox
```

Faça a mesma pergunta.

> **Fala.** O comportamento do agente mudou e o processo do agente não foi
> reiniciado. Nem recompilado, nem redeployado. O cardápio de dados tem ciclo de
> vida próprio, e é o time de Dados que manda nele. Isso é organograma virando
> arquitetura, e é o melhor argumento para MCP que eu conheço.

> **Desfazer.** Volte o `tools.yaml` e reinicie o Toolbox de novo. O lab 08 usa
> os nomes e os retornos dessas queries na massa de testes.

---

## Parte 4 — A linha que não muda (15 min)

> **Fala.** Este `tools.yaml` é byte a byte o mesmo do laboratório em Google ADK.
> Trocamos o framework inteiro e a camada de dados não sentiu. Quando vocês forem
> decidir stack de agente, decidam o acesso a dado primeiro: é a decisão com maior
> meia-vida das três.

É a única linha do `MAPEAMENTO.md` que não muda entre as duas pilhas. Vale abrir
a tabela e apontar.

---

## Parte 5 — O desenho em Azure (15 min)

```
Agente  --MCP/HTTPS-->  Container App: Toolbox  -->  PostgreSQL Flexible Server
  sem credencial          5 queries aprovadas         private endpoint
                          identidade gerenciada       sem IP público
```

Percorra os três pontos:

1. **Identidade gerenciada em vez de senha.** O Flexible Server aceita Entra ID, e
   o Container App do Toolbox usa identidade gerenciada. O `tools.yaml` deixa de
   ter credencial.
2. **Rede privada.** O banco não precisa de IP público.
3. **O agente nunca fala com o banco.**

> **Fala.** Perguntem para o time de segurança de vocês qual desses três é
> inegociável na casa de vocês. A resposta muda o desenho, e é melhor descobrir
> agora do que na revisão de arquitetura.

---

## Perguntas que a turma faz aqui

**"MCP não é só para IDE?"**
Não. MCP é um protocolo para expor tools a um cliente LLM, e IDE é um cliente
entre outros. Aqui o cliente é o agente.

**"Por que não deixar o modelo escrever SQL?"**
Porque aí o blast radius é a base inteira, e a revisão de segurança some. Text-to-SQL
tem lugar — em ferramenta de analista, com credencial de leitura e sandbox — e não
é este.

**"Quem escreve o tools.yaml?"**
Quem conhece o dado. É a resposta que muda a conversa: o cardápio é entregável do
time de Dados, com revisão e versão, e não um detalhe do time de agente.

---

## Se der errado

| Sintoma | Causa | Saída |
|---|---|---|
| Toolbox não sobe, `password: null` | `POSTGRES_PASSWORD` vazio | confira o `.env`; não exporte pelo shell |
| `connection timed out` | IP fora do firewall do Postgres | `az postgres flexible-server firewall-rule list ...` |
| Tool "some" em runtime | MCP criado fora do `async with` | mantenha o agente dentro do bloco |
| A URL não conecta | falta o `/mcp` no fim | `TOOLBOX_MCP_URL=http://localhost:5000/mcp` |

---

## O gancho

Um agente, o cardápio inteiro na mão, três assuntos no mesmo prompt. Ele mistura
cobrança com técnico e trata na ordem errada.

→ [Lab 05](lab05.md)
