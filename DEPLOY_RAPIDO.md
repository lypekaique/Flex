# 🚀 Deploy Rápido no Railway

Guia super rápido para colocar o bot online em **5 minutos**!

## ⚡ Passo a Passo Rápido

### 1. Criar conta no Railway

- Acesse: https://railway.app
- Login com GitHub

### 2. Subir código para GitHub

```bash
git init
git add .
git commit -m "Bot LOL Flex Tracker"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/NOME_REPO.git
git push -u origin main
```

### 3. Deploy no Railway

1. Railway → **"New Project"**
2. **"Deploy from GitHub repo"**
3. Escolha seu repositório
4. Aguarde o build (1-2 min)

### 4. Configurar Variáveis

No Railway, vá em **"Variables"** e adicione:

```
DISCORD_TOKEN=seu_token_discord
RIOT_API_KEY=sua_riot_api_key
DEFAULT_REGION=br1
```

### 5. Verificar

- Vá em **"Deployments"** → Logs
- Se aparecer "Bot está online!" → ✅ Funcionou!
- Teste no Discord: `/logar Nome#TAG br1`

## 🎯 Onde Pegar os Tokens?

- **Discord Token:** https://discord.com/developers/applications
- **Riot API Key:** https://developer.riotgames.com/

## ⚠️ Importante

- ✅ Riot API Key expira em 24h (Development Key)
- ✅ Plano free: 500 horas/mês (~20 dias)
- ✅ Bot reinicia automaticamente se cair

## 🔄 Atualizar o Bot

```bash
git add .
git commit -m "Atualização"
git push
```

Railway atualiza automaticamente! 🚂

## 📖 Guia Completo

Veja `DEPLOY_RAILWAY.md` para informações detalhadas.

---

**Pronto! Seu bot está online 24/7!** 🎉
