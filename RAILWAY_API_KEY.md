# 🚂 Como Renovar a API Key no Railway

## ❌ Problema: Erro 403 Forbidden

```
🚨 [CRÍTICO] Chave da API Riot inválida ou expirada!
Status: 403
```

## ⏰ Por que isso acontece?

As **chaves de desenvolvimento da Riot** expiram a cada **24 horas**. Você precisa gerar uma nova chave diariamente.

---

## 🔧 Solução Rápida (Railway)

### 1️⃣ Gere uma Nova Chave

1. Acesse: https://developer.riotgames.com/
2. Faça login com sua conta Riot Games
3. Role até a seção **"Development API Key"**
4. Clique em **"REGENERATE API KEY"** (ou copie a chave existente se foi gerada hoje)
5. Copie a chave completa (começa com `RGAPI-` e tem ~80 caracteres)

### 2️⃣ Atualize no Railway

1. Abra seu projeto no Railway
2. Vá em **"Variables"** (lado esquerdo)
3. Encontre a variável `RIOT_API_KEY`
4. Clique para editar
5. **Cole a nova chave**
6. Clique em **"Update"** ou pressione Enter

### 3️⃣ Reinicie o Bot

**IMPORTANTE:** O Railway **NÃO reinicia automaticamente** quando você muda variáveis de ambiente!

Duas opções:

**Opção A - Restart Manual:**

1. Vá na aba **"Deployments"**
2. Clique nos **três pontinhos** (...) do deployment atual
3. Clique em **"Restart"**

**Opção B - Redeploy:**

1. Vá na aba **"Settings"**
2. Role até **"Danger Zone"**
3. Clique em **"Redeploy"**

---

## ✅ Como Verificar se Funcionou

Após reiniciar, nos logs do Railway você deve ver:

```
🔧 Verificando variáveis de ambiente...
✅ DISCORD_TOKEN: Configurado
✅ RIOT_API_KEY: Configurado (RGAPI-78149d74-a863...)
✅ DEFAULT_REGION: br1
================================================================================
🔍 Testando chave da API Riot...
✅ Chave da API Riot funcionando corretamente!
```

Se ainda aparecer erro 403:

- ✅ Verifique se copiou a chave completa (sem espaços)
- ✅ Certifique-se que a chave começa com `RGAPI-`
- ✅ Gere uma nova chave (pode ter expirado durante o processo)
- ✅ **Sempre reinicie o bot após mudar a variável**

---

## 🎯 Dica: Chave de Produção (Personal API Key)

Para **não precisar renovar todos os dias**, você pode solicitar uma **Personal API Key**:

1. Acesse: https://developer.riotgames.com/
2. Vá em **"Personal API Key"**
3. Preencha o formulário explicando seu projeto
4. Aguarde aprovação (pode levar alguns dias)
5. A chave de produção **não expira**!

**Requisitos:**

- Projeto deve ter uso legítimo
- Deve respeitar os Rate Limits da Riot
- Não pode comercializar dados

---

## 🐛 Troubleshooting

### Bot não reinicia no Railway

→ Force o restart manualmente (veja passo 3)

### Logs não mostram a verificação da API

→ O código pode estar desatualizado, faça um novo deploy

### Erro persiste após renovar

→ Espere 1-2 minutos após o restart (Railway pode ter cache)
→ Verifique se não há espaços antes/depois da chave

### Como ver os logs no Railway?

1. Abra seu projeto
2. Clique na aba **"Deployments"**
3. Clique no deployment ativo
4. Os logs aparecem em tempo real

---

## 📝 Checklist Diário

Para projetos com chave de desenvolvimento:

- [ ] Gerar nova chave em https://developer.riotgames.com/
- [ ] Atualizar `RIOT_API_KEY` no Railway
- [ ] Reiniciar o deployment
- [ ] Verificar logs para confirmar que está funcionando

**Melhor:** Solicite uma Personal API Key para evitar esse processo diário!
