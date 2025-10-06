# ✅ Checklist Railway - Bot LOL Flex Tracker

Use esta checklist para garantir que tudo está configurado corretamente no Railway!

## 📋 Antes do Deploy

- [ ] Código está funcionando localmente
- [ ] Testou os comandos `/logar`, `/media`, `/historico`
- [ ] Tem token do Discord Bot
- [ ] Tem Riot API Key (Development ou Production)
- [ ] Criou repositório no GitHub

## 🚀 Deploy no Railway

- [ ] Criou conta no Railway (railway.app)
- [ ] Conectou conta do GitHub ao Railway
- [ ] Criou novo projeto no Railway
- [ ] Selecionou "Deploy from GitHub repo"
- [ ] Escolheu o repositório correto
- [ ] Aguardou o build completar

## 🔧 Configuração

- [ ] Adicionou variável `DISCORD_TOKEN`
- [ ] Adicionou variável `RIOT_API_KEY`
- [ ] Adicionou variável `DEFAULT_REGION` (opcional, padrão: br1)
- [ ] Salvou todas as variáveis
- [ ] Bot reiniciou automaticamente

## ✅ Verificação

- [ ] Logs mostram "Bot está online!"
- [ ] Logs mostram "X comandos sincronizados"
- [ ] Bot aparece online no Discord
- [ ] Testou `/logar Nome#TAG br1`
- [ ] Conta foi vinculada com sucesso
- [ ] Testou `/contas` e viu a conta listada

## 💾 Persistência (Opcional)

- [ ] Criou Volume no Railway (mount path: `/data`)
- [ ] Código ajustado para usar `/data/bot_lol.db` (já está configurado!)
- [ ] Fez novo deploy após adicionar volume
- [ ] Banco de dados persiste entre deploys

## 📊 Monitoramento

- [ ] Verificou os logs em tempo real
- [ ] Configurou alertas (opcional)
- [ ] Verificou uso de CPU/Memória
- [ ] Anotou quantas horas já usou no mês (500h free)

## 🔄 Manutenção

- [ ] Configurou renovação automática da Riot API Key (se Development)
- [ ] Adicionou lembrete para renovar API Key (24h)
- [ ] Documentou onde estão os tokens
- [ ] Configurou backup do banco (se usando Volume)

## 🐛 Troubleshooting

### Se o bot não iniciar:

1. **Verifique os logs:**

   - Railway → Deployments → Clique no deploy → Logs

2. **Erros comuns:**

   - `DISCORD_TOKEN not found` → Adicione a variável
   - `Module not found` → Verifique requirements.txt
   - `401 Unauthorized` → Token do Discord inválido
   - `403 Forbidden` → Riot API Key inválida/expirada

3. **Reiniciar:**
   - Settings → Restart

### Se comandos não aparecerem:

1. Aguarde 1-2 minutos
2. Saia e entre no servidor Discord
3. Verifique se bot tem permissões corretas
4. Use `/` no Discord para ver comandos disponíveis

## 📝 Informações Úteis

### URLs Importantes

- Railway Dashboard: https://railway.app/dashboard
- Discord Dev Portal: https://discord.com/developers/applications
- Riot Dev Portal: https://developer.riotgames.com/

### Comandos Git para Atualizar

```bash
git add .
git commit -m "Descrição da mudança"
git push
```

### Limites do Plano Free

- **500 horas/mês** (~20 dias online)
- **512 MB RAM**
- **1 GB disco**
- **100 GB bandwidth**

### Para Upgrade

- Plano Pro: $5/mês
- Horas ilimitadas
- Mais recursos

## 🎯 Status Final

Marque quando tudo estiver funcionando:

- [ ] ✅ Bot online 24/7
- [ ] ✅ Comandos funcionando
- [ ] ✅ Monitoramento configurado
- [ ] ✅ Persistência ativada (opcional)
- [ ] ✅ Documentação salva

---

## 🎉 Parabéns!

Seu bot está rodando no Railway! 🚂

**Próximos passos:**

1. Jogue Ranked Flex
2. Use `/media` para ver suas estatísticas
3. Compartilhe com seus amigos!

**Lembre-se:**

- Development API Key expira em 24h
- Renovar diariamente ou solicitar Production Key
- Verificar uso de horas no Railway

---

**Bot desenvolvido com ❤️ para a comunidade de League of Legends**

Para mais ajuda, veja:

- [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md) - Guia completo
- [DEPLOY_RAPIDO.md](DEPLOY_RAPIDO.md) - Guia rápido
- [README.md](README.md) - Documentação geral
