# 🔧 Solução para Erro 400 - PUUIDs Corrompidos

## 🔍 Problema Identificado

O erro "Exception decrypting" indica que os **PUUIDs armazenados no banco de dados estão em um formato inválido ou corrompido**. Isso acontece quando a Riot API muda como os identificadores funcionam, tornando os PUUIDs antigos incompatíveis.

### Exemplo de Erro:

```json
{
  "status": {
    "message": "Bad Request - Exception decrypting 6HoLuJnPT8PcxTHL12uqVYK01DxmCwyH0529LvTJTwUp33PZytxcfW7HC7UBCDmlaF4aj11IMPPjDQ",
    "status_code": 400
  }
}
```

---

## ✅ Correções Aplicadas

### 1. **riot_api.py**

- ✅ Removido parâmetro `queue` da API de histórico (causava erro 400)
- ✅ Filtro de Ranked Flex (queue 440) agora é feito após buscar detalhes
- ✅ Melhorado log de erros com rate limiting (1x por minuto)
- ✅ Adicionado log detalhado da resposta da API para debug

### 2. **bot.py**

- ✅ Adicionado filtro `queueId == 440` ao processar partidas
- ✅ Melhorado processo de vincular conta (busca última partida Flex)
- ✅ Criado comando `/resync_accounts` para re-sincronizar todas as contas

### 3. **database.py**

- ✅ Adicionado método `update_account_puuid()` para atualizar PUUIDs
- ✅ Adicionado método `get_all_accounts()` para buscar todas as contas

---

## 🚀 Como Usar

### **Opção 1: Comando de Admin (Recomendado)**

Use o novo comando de admin para re-sincronizar **todas** as contas automaticamente:

```
/resync_accounts
```

**O que este comando faz:**

1. Busca todas as contas vinculadas no banco
2. Para cada conta, busca novos dados da Riot API usando o Riot ID
3. Atualiza os PUUIDs no banco de dados
4. Mostra um relatório com sucessos e falhas

**Exemplo de Resultado:**

```
✅ Re-sincronização Concluída
📊 Resultado
  ✅ 12 contas atualizadas
  ❌ 2 contas falharam
  📝 14 contas totais

❌ Contas que falharam
  • ContaInvalida#BR1
  • NomeAntigo#TAG

💡 Solução
  Peça para os usuários usarem /logar novamente
```

---

### **Opção 2: Re-vincular Manualmente**

Se preferir, os usuários podem **re-vincular** suas contas manualmente:

```
/logar riot_id:SeuNick#TAG regiao:br1
```

Isso irá:

- Buscar novos PUUIDs válidos da Riot API
- Substituir os dados antigos no banco
- Começar a funcionar normalmente

---

## 📊 Verificação

Após re-sincronizar, o bot deve:

- ✅ Parar de mostrar erros 400 com "Exception decrypting"
- ✅ Conseguir buscar histórico de partidas
- ✅ Detectar partidas ao vivo
- ✅ Processar partidas terminadas

---

## 🔄 Mudanças no Funcionamento

### **Antes:**

```python
# API com filtro de queue (causava erro 400)
params = {'queue': 440}  # ❌ Não funciona mais
```

### **Depois:**

```python
# Busca todas as partidas, depois filtra
match_data = await get_match_details(match_id)
if match_data['info']['queueId'] == 440:  # ✅ Funciona
    # Processa apenas Ranked Flex
```

---

## 💡 Dicas

1. **Execute `/resync_accounts` imediatamente** após reiniciar o bot
2. Se alguma conta falhar, peça ao usuário para usar `/logar` novamente
3. Os erros 400 devem parar completamente após a re-sincronização
4. As partidas antigas permanecem salvas no banco

---

## 🛠️ Para Desenvolvedores

### Método adicionado em `database.py`:

```python
def update_account_puuid(self, account_id: int, new_puuid: str,
                        new_summoner_id: str, new_account_id: str) -> bool:
    """Atualiza o PUUID e IDs de uma conta"""
```

### Novo comando em `bot.py`:

```python
@bot.tree.command(name="resync_accounts")
@app_commands.checks.has_permissions(administrator=True)
async def resync_accounts(interaction: discord.Interaction):
    """Re-sincroniza todas as contas do banco"""
```

---

## 📝 Checklist Final

- [ ] Reiniciar o bot
- [ ] Executar `/resync_accounts` como admin
- [ ] Verificar logs para erros
- [ ] Testar com `/media` ou `/historico`
- [ ] Confirmar que erros 400 pararam

---

## ❓ FAQ

**P: Vou perder as partidas antigas?**
R: Não! As partidas permanecem salvas no banco.

**P: Preciso fazer isso toda vez?**
R: Não, apenas uma vez após essa atualização.

**P: E se alguma conta falhar?**
R: O usuário deve usar `/logar` novamente para re-vincular.

**P: O bot vai funcionar durante a re-sincronização?**
R: Sim, o processo é rápido e não interrompe o bot.

---

**Criado em:** 09/10/2024
**Versão:** 2.0
