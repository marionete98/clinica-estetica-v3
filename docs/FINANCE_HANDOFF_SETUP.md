# Configuração de Encaminhamento para Financeiro

## Visão Geral

O sistema agora suporta encaminhamento automático de conversas para o setor Financeiro, que possui uma Inbox separada com número de WhatsApp diferente.

## Arquitetura

```
Cliente (Inbox Principal)
    ↓
IA detecta assunto financeiro
    ↓
Endpoint /handoff-to-finance
    ↓
1. Pausa IA na conversa atual
2. Adiciona label "financeiro"
3. Envia mensagem ao cliente
4. Cria nota privada
5. [Opcional] Cria conversa na Inbox Financeiro
6. Resolve conversa atual
```

## Configuração

### 1. Variáveis de Ambiente

Adicione ao arquivo `.env`:

```bash
# Configuração do Financeiro
CHATWOOT_FINANCE_INBOX_ID=123          # ID da Inbox do Financeiro no Chatwoot
CHATWOOT_FINANCE_TEAM_ID=456           # [Opcional] ID do Team Financeiro
CHATWOOT_FINANCE_PHONE="+55 94 99123-4567"  # Número do WhatsApp do Financeiro (para exibir ao cliente)
```

### 2. Como Obter os IDs no Chatwoot

#### Inbox ID:
1. Acesse Chatwoot → Settings → Inboxes
2. Clique na Inbox do Financeiro
3. O ID está na URL: `https://app.chatwoot.com/app/accounts/X/settings/inboxes/123`
   - `123` é o `CHATWOOT_FINANCE_INBOX_ID`

#### Team ID (opcional):
1. Acesse Chatwoot → Settings → Teams
2. Clique no Team Financeiro
3. O ID está na URL: `https://app.chatwoot.com/app/accounts/X/settings/teams/456`
   - `456` é o `CHATWOOT_FINANCE_TEAM_ID`

## Uso

### Opção 1: Macro no Chatwoot (Recomendado)

#### Criar Macro:

1. Acesse Chatwoot → Settings → Macros → New Macro
2. Configure:

```
Nome: 🏦 Encaminhar para Financeiro

Visibilidade: Privada (apenas agentes)

Ações:
1. Enviar evento de Webhook
   - URL: https://seu-backend.railway.app/api/handoff-to-finance/{{conversation.id}}
   
   IMPORTANTE: Use exatamente {{conversation.id}} - o Chatwoot substitui automaticamente

2. [Opcional] Add Label: financeiro
   (O endpoint já adiciona, mas pode adicionar aqui também para redundância)
```

**Observações importantes:**
- O Chatwoot macro não permite configurar método HTTP (sempre POST) ✅
- O Chatwoot macro não permite adicionar headers de autenticação ✅
- O endpoint foi configurado para aceitar requisições sem autenticação quando vem do Chatwoot
- Todas as ações são logadas para auditoria

#### Como Usar:
- Agente identifica assunto financeiro
- Clica no macro "🏦 Encaminhar para Financeiro"
- Sistema executa automaticamente todo o processo

### Opção 2: Chamada Direta via API

```bash
curl -X POST \
  -H "Authorization: Bearer <SEU_TOKEN>" \
  https://seu-backend.railway.app/api/handoff-to-finance/123456
```

### Opção 3: Automação no Chatwoot

Criar automação para palavras-chave:

```
Nome: Auto-detectar Financeiro

Trigger: Nova mensagem
Condições:
  - Mensagem contém: "boleto" OU "pagamento" OU "fatura" OU "PIX" OU "NF"
  - Conversa não tem label "financeiro"

Ações:
  1. Adicionar label: "financeiro-pendente"
  2. Enviar nota privada: "⚠️ Cliente mencionou assunto financeiro"
  3. [Opcional] Execute Webhook (mesmo do macro)
```

## Fluxo Detalhado

### O que acontece quando o endpoint é chamado:

1. **Pausa IA na conversa atual**
   - Define `automation_paused = True` no Redis e Supabase
   - Marca motivo como `finance_handoff`

2. **Adiciona label "financeiro"**
   - Para rastreabilidade e filtros

3. **Envia mensagem ao cliente**
   ```
   Obrigado pelo contato! 💙

   Vou encaminhar sua solicitação para nosso setor Financeiro,
   que possui expertise para melhor atendê-lo(a).

   Você receberá contato pelo número: +55 94 99123-4567

   Aguarde, em breve nossa equipe entrará em contato! ✨
   ```

4. **Cria nota privada**
   ```
   🏦 Encaminhado para Financeiro

   - Data/Hora: 21/10/2025 11:30:45
   - Motivo: Solicitação financeira
   - Automação: Pausada
   - Inbox Financeiro: ID 123
   ```

5. **[Se configurado] Cria conversa na Inbox Financeiro**
   - Busca dados do contato
   - Cria nova conversa na Inbox do Financeiro
   - Envia nota privada com contexto

6. **Marca conversa atual como resolvida**
   - Status = "resolved"

## Resposta do Endpoint

```json
{
  "success": true,
  "conversation_id": "123456",
  "finance_conversation_id": "789012",  // Se criou conversa no Financeiro
  "message": "Conversation handed off to Finance team",
  "automation_paused": true,
  "timestamp": "2025-10-21T11:30:45.123Z"
}
```

## Monitoramento

### Logs

O sistema gera logs detalhados:

```
INFO: Starting finance handoff for conversation 123456
INFO: Created finance conversation: 789012
INFO: Finance handoff completed for conversation 123456
```

### Métricas

Filtros úteis no Chatwoot:
- Label: "financeiro"
- Status: "resolved"
- Team: "Financeiro"

## Troubleshooting

### Problema: Endpoint retorna erro 500

**Causa**: Configuração incompleta ou erro no Chatwoot

**Solução**:
1. Verificar variáveis de ambiente
2. Verificar logs: `railway logs`
3. Testar Chatwoot API manualmente

### Problema: Conversa não é criada na Inbox Financeiro

**Causa**: `CHATWOOT_FINANCE_INBOX_ID` não configurado ou inválido

**Solução**:
1. Verificar se variável está definida
2. Confirmar ID correto no Chatwoot
3. Sistema funciona mesmo sem criar conversa (handoff básico)

### Problema: Cliente não recebe mensagem

**Causa**: Janela de 24h do WhatsApp expirada

**Solução**:
- Sistema envia mensagem na conversa atual (ainda dentro da janela)
- Financeiro deve iniciar nova conversa com template aprovado

## Segurança

### Autenticação

O endpoint requer autenticação via Bearer token:

```bash
Authorization: Bearer <SEU_API_TOKEN>
```

Configure o token no macro do Chatwoot.

### Rate Limiting

O Chatwoot client já implementa rate limiting (100 req/min).

## Próximos Passos

1. ✅ Configurar variáveis de ambiente
2. ✅ Criar macro no Chatwoot
3. ✅ Treinar equipe
4. ⏳ [Opcional] Configurar automação para detecção automática
5. ⏳ [Opcional] Criar dashboard de métricas

## Suporte

Para dúvidas ou problemas:
1. Verificar logs no Railway
2. Testar endpoint manualmente
3. Revisar configuração do Chatwoot
