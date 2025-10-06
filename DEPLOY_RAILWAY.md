# 🚂 Deploy no Railway - Guia Completo

Este guia mostra como fazer deploy do bot no **Railway** para ele ficar online 24/7!

## 🎯 Por que Railway?

- ✅ **Gratuito** (500 horas/mês no plano free)
- ✅ **Fácil de usar** (deploy automático via GitHub)
- ✅ **Reinicialização automática** se o bot cair
- ✅ **Logs em tempo real**
- ✅ **Variáveis de ambiente seguras**

## 📋 Pré-requisitos

1. Conta no [GitHub](https://github.com)
2. Conta no [Railway](https://railway.app)
3. Bot do Discord criado (token)
4. Riot API Key

## 🚀 Passo a Passo

### 1️⃣ Preparar o Repositório GitHub

1. **Criar repositório no GitHub:**
   - Acesse https://github.com/new
   - Nome: `lol-flex-tracker-bot` (ou outro nome)
   - Deixe como **Público** ou **Privado**
   - Clique em "Create repository"

2. **Subir o código para o GitHub:**

```bash
# No terminal, dentro da pasta do projeto:
git init
git add .
git commit -m "Initial commit - Bot LOL Flex Tracker"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```

⚠️ **Importante:** O arquivo `.env` NÃO será enviado (está no .gitignore). Vamos configurar as variáveis no Railway.

### 2️⃣ Criar Projeto no Railway

1. **Acessar Railway:**
   - Vá em https://railway.app
   - Clique em **"Login"** e use sua conta GitHub
   - Clique em **"New Project"**

2. **Deploy do GitHub:**
   - Selecione **"Deploy from GitHub repo"**
   - Escolha o repositório que você criou
   - Railway detectará automaticamente o Python

3. **Aguardar o build:**
   - Railway fará o build automático
   - Pode levar 1-2 minutos

### 3️⃣ Configurar Variáveis de Ambiente

1. **Acessar Variables:**
   - No dashboard do projeto, clique em **"Variables"**
   - Clique em **"+ New Variable"**

2. **Adicionar as variáveis:**

Adicione uma por uma:

```
DISCORD_TOKEN=cole_seu_token_discord_aqui
RIOT_API_KEY=cole_sua_riot_api_key_aqui
DEFAULT_REGION=br1
```

**Como obter os tokens:**
- **DISCORD_TOKEN:** https://discord.com/developers/applications
- **RIOT_API_KEY:** https://developer.riotgames.com/

3. **Salvar:**
   - Clique em **"Add"** para cada variável
   - Railway reiniciará o bot automaticamente

### 4️⃣ Verificar se Está Online

1. **Ver Logs:**
   - No dashboard, clique em **"Deployments"**
   - Clique no deployment ativo
   - Veja os logs em tempo real

2. **Logs esperados:**
```
Bot NomeDoBot está online!
ID: 123456789
------
X comandos sincronizados
```

3. **Testar no Discord:**
   - Use `/logar Nome#TAG br1`
   - Se funcionou, está tudo certo! ✅

## 🔄 Atualizações Automáticas

Sempre que você fizer push no GitHub, o Railway atualiza automaticamente:

```bash
# Faça suas alterações no código
git add .
git commit -m "Descrição da alteração"
git push
```

O Railway detectará e fará novo deploy automaticamente! 🚀

## 📊 Monitoramento

### Ver Logs em Tempo Real

1. Acesse seu projeto no Railway
2. Clique em **"Deployments"**
3. Clique no deployment ativo
4. Veja os logs rolando

### Métricas

- **CPU Usage:** Uso de processador
- **Memory Usage:** Uso de memória
- **Network:** Requisições à API

## ⚠️ Limitações do Plano Free

- **500 horas/mês** de execução
- Aproximadamente **20 dias** de uptime contínuo
- Renovação automática todo mês

**Dicas para economizar horas:**
- Pause o bot quando não estiver usando (Settings → Pause)
- Use apenas quando necessário

## 🐛 Solução de Problemas

### Bot não inicia

**Erro nos logs:** `DISCORD_TOKEN not found`
- ✅ Verifique se adicionou as variáveis de ambiente
- ✅ Reinicie o bot após adicionar variáveis

**Erro:** `Module not found`
- ✅ Verifique se o `requirements.txt` está correto
- ✅ Force um novo deploy

### Bot fica offline

**"Application failed to start"**
- ✅ Veja os logs para identificar o erro
- ✅ Verifique se os tokens estão corretos
- ✅ Certifique-se que a Riot API Key não expirou

## 🎁 Recursos Extras do Railway

### Adicionar Volumes (Persistência de Dados)

O Railway usa sistema de arquivos efêmero. Para manter o banco de dados entre deploys:

1. No projeto, clique em **"Settings"**
2. Role até **"Volumes"**
3. Clique em **"+ Add Volume"**
4. Configure:
   - **Mount Path:** `/data`
   - Confirme

5. Ajuste o código em `database.py`:

```python
import os

class Database:
    def __init__(self, db_name=None):
        if db_name is None:
            # Usa /data se estiver no Railway, senão usa local
            if os.path.exists('/data'):
                db_name = '/data/bot_lol.db'
            else:
                db_name = 'bot_lol.db'
        self.db_name = db_name
        self.init_database()
```

6. Faça commit e push:
```bash
git add .
git commit -m "Adiciona suporte a volume Railway"
git push
```

Agora o banco de dados será persistente! 💾

## 📈 Upgrade para Pro

Se precisar de mais recursos:

- **Plano Pro:** $5/mês
- **Horas ilimitadas**
- **Mais memória e CPU**
- **Priority support**

## 🎯 Checklist Final

- [ ] Código no GitHub
- [ ] Projeto criado no Railway
- [ ] Variáveis de ambiente configuradas (DISCORD_TOKEN, RIOT_API_KEY)
- [ ] Bot está online (veja logs)
- [ ] Testou comandos no Discord
- [ ] Configurou volume para persistência (opcional)

## 🔒 Segurança

✅ **Nunca commite o arquivo `.env`** (já está no .gitignore)
✅ **Use as variáveis de ambiente do Railway**
✅ **Não compartilhe seu DISCORD_TOKEN ou RIOT_API_KEY**
✅ **Regenere tokens se expor acidentalmente**

## 📞 Suporte

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **GitHub Issues:** Crie uma issue no seu repositório

---

## 🎉 Pronto!

Seu bot está online 24/7 no Railway! 🚂

Agora é só:
1. Vincular contas com `/logar Nome#TAG br1`
2. Jogar Ranked Flex
3. Usar `/media` para ver estatísticas

**O bot está monitorando automaticamente e calculando carry scores!** 🏆

---

## 📋 Arquivos de Configuração Incluídos

Este projeto já inclui todos os arquivos necessários:

- ✅ `railway.json` - Configuração do Railway
- ✅ `Procfile` - Comando de inicialização
- ✅ `runtime.txt` - Versão do Python (3.11)
- ✅ `requirements.txt` - Dependências
- ✅ `.gitignore` - Arquivos ignorados
- ✅ `.railwayignore` - Arquivos ignorados no deploy
- ✅ `.dockerignore` - Para builds Docker (futuro)

**Tudo pronto para deploy!** Basta seguir os passos acima. 🚀

