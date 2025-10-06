# 🚀 Início Rápido - Bot LOL Flex Tracker

## 📝 Checklist de Configuração

### 1️⃣ Instalar Python
- Baixe Python 3.8+ em [python.org](https://www.python.org/)
- Marque "Add Python to PATH" durante instalação

### 2️⃣ Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3️⃣ Criar Bot no Discord
1. Vá em https://discord.com/developers/applications
2. Clique em "New Application"
3. Vá em "Bot" → "Add Bot"
4. Copie o **Token**
5. Ative "Message Content Intent"
6. Em "OAuth2" → "URL Generator":
   - Marque: `bot` e `applications.commands`
   - Marque: "Send Messages", "Use Slash Commands", "Embed Links"
7. Use a URL gerada para adicionar ao servidor

### 4️⃣ Obter Riot API Key
1. Vá em https://developer.riotgames.com/
2. Faça login
3. Copie a **Development Key**

⚠️ A Development Key expira em 24h (renove diariamente)

### 5️⃣ Configurar o Bot
Crie um arquivo `.env` na pasta do projeto:

```env
DISCORD_TOKEN=cole_seu_token_discord_aqui
RIOT_API_KEY=cole_sua_chave_riot_aqui
DEFAULT_REGION=br1
```

### 6️⃣ Executar o Bot
```bash
python bot.py
```

Se aparecer "Bot está online!", está tudo certo! ✅

## 🎮 Como Usar

### No Discord:

1. **Vincular conta (use Nome#TAG):**
   ```
   /logar SeuNick#BR1 br1
   /logar Faker#KR1 kr
   ```
   
   ⚠️ **Importante:** Use o formato `Nome#TAG` completo!
   
   Para descobrir seu Riot ID:
   - Abra o League of Legends
   - Veja seu nome no canto superior direito
   - Exemplo: "Faker#KR1" ou "SeuNick#1234"

2. **Ver suas contas:**
   ```
   /contas
   ```

3. **Ver estatísticas do mês:**
   ```
   /media
   /media 1    # Apenas conta 1
   ```
   
   Mostra:
   - 📈 Carry Score médio (0-10)
   - 🎮 Total de partidas e Win Rate
   - ⚔️ KDA médio
   - 🎯 Kill Participation %
   - 🎭 Role mais jogada

4. **Ver histórico de partidas:**
   ```
   /historico 1 5    # Últimas 5 partidas
   /historico 2 10   # Últimas 10 partidas
   ```

5. **Ver ranking do servidor:**
   ```
   /tops_flex        # Top 10
   /tops_flex 20     # Top 20
   ```

6. **Configurar alertas (Admin):**
   ```
   /configurar #avisos-lol
   ```
   
   Envia alertas quando jogadores usam o mesmo campeão 3x com score < 6.0!

## 🏆 Sistema de Carry Score

O bot calcula um score de **0 a 10** baseado em:

### 🥊 Combate
- KDA (Kills/Deaths/Assists)
- Dano por minuto
- Kill Participation %

### 💰 Recursos
- Gold por minuto
- CS por minuto (para roles que farmam)

### 🎯 Objetivos
- Torres destruídas
- Dano em objetivos (Dragão, Barão, Arauto)

### 👀 Visão
- Vision Score
- Wards colocadas/destruídas

### 🛡️ Utility (Supports)
- Tempo de CC aplicado
- Cura/Escudos aplicados

## ⚖️ Pesos por Role

**Top/Jungle/Mid/ADC:**
- Foco em KDA, Dano, Farm e Objetivos

**Support:**
- Foco em Kill Participation, Visão e Utility
- Menor peso em Dano (5%)

**Bônus:** +5% no score se ganhou a partida! 🎁

## 📊 Classificação

- 🏆 **7.0+** → S+ Carry (Você carregou!)
- ⭐ **6.0-6.9** → S Carry (Muito bem!)
- 💎 **5.0-5.9** → A Carry (Bom)
- 🥈 **4.0-4.9** → B Normal (OK)
- 📉 **< 4.0** → C Weight (Melhorar)

## ⚠️ Importante

- Jogue **Ranked Flex** (não Solo/Duo)
- O bot verifica novas partidas a cada **5 minutos**
- Use o formato `Nome#TAG` para logar
- Máximo de **3 contas** por usuário
- A Development Key **expira em 24h** (renove diariamente)

## 🆘 Problemas Comuns

**"Module not found"**
→ Execute: `pip install -r requirements.txt`

**"Bot não conecta"**
→ Verifique se o DISCORD_TOKEN está correto no .env

**"Conta não encontrada"**
→ Use o formato `Nome#TAG` completo (ex: Faker#KR1)
→ Verifique se o Riot ID está correto (veja no jogo)

**"Partidas não aparecem"**
→ Certifique-se de jogar **Ranked Flex**, não Solo/Duo
→ Aguarde até 5 minutos (bot verifica a cada 5 min)
→ Verifique se o bot está online

**"Carry Score parece errado"**
→ O score não é só KDA, considera múltiplas métricas
→ Support tem pesos diferentes (mais Vision/KP, menos Dano)
→ ADC/Mid/Top tem mais peso em Dano e Farm

## 📞 Estrutura dos Arquivos

```
├── bot.py           → Bot principal (comandos Discord)
├── riot_api.py      → API da Riot + cálculo de carry
├── database.py      → Banco de dados SQLite
├── requirements.txt → Bibliotecas necessárias
└── .env            → Suas configurações (criar)
```

## 🎯 Pronto!

Agora é só:
1. Usar `/logar Nome#TAG br1`
2. Jogar Ranked Flex
3. Usar `/media` para ver suas stats! 🏆

O bot calculará automaticamente seu carry score com pesos específicos para sua role! 🎮
