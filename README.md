# 🎮 Bot Discord - League of Legends Flex Tracker

Bot do Discord que rastreia automaticamente suas partidas de **Ranked Flex** no League of Legends, calcula seu **nível de carry** usando sistema avançado com pesos por role, e gera estatísticas mensais!

## 🌟 Funcionalidades

- ✅ **Vincule até 3 contas** do LOL por usuário (sistema Riot ID: Nome#TAG)
- 📊 **Monitoramento automático** de partidas Ranked Flex (a cada 5 minutos)
- 🏆 **Cálculo Avançado de Carry Score** com:
  - **🥊 Combate:** KDA, Dano por minuto, Kill Participation
  - **💰 Recursos:** Gold/min, CS/min
  - **🎯 Objetivos:** Torres, Dragões, Barões, Arauto
  - **👀 Visão:** Vision Score, Wards colocadas/destruídas
  - **🛡️ Utility:** CC aplicado, Cura/Escudos (para Supports)
- ⚖️ **Pesos por Role:** Sistema inteligente que avalia diferente cada role
- 🆕 **Sistema Avançado de Estatísticas** (`/media`):
  - Filtro por campeão específico com auto-complete
  - Análise de métricas específicas (KDA, dano, CS, visão, gold, etc)
  - Visualizar estatísticas de outros jogadores
  - Modo "todas" com visão completa de todas métricas
- 📈 **Estatísticas mensais** com média de carry score e análise detalhada
- 📜 **Histórico detalhado** de partidas com KDA, KP%, Role e mais
- 🏅 **Ranking de Jogadores** (`/tops_flex`) - Veja quem são os melhores carries do servidor!
- ⚠️ **Sistema de Alertas** - Notifica quando jogadores têm 3 performances ruins seguidas no mesmo campeão
- 🌍 **Suporte a todas as regiões** da Riot Games

## 📋 Comandos

### Comandos de Usuário

### `/logar <riot_id> [regiao]`

Vincula sua conta do League of Legends ao bot usando o **Riot ID** (Nome#TAG).

**Formato obrigatório:** `Nome#TAG`

**Exemplos:**

```
/logar Faker#KR1 kr
/logar SeuNick#BR1 br1
/logar ProPlayer#EUW euw1
```

⚠️ **Importante:**

- Use o formato `Nome#TAG` completo!
- Para descobrir seu Riot ID, abra o LOL e veja seu nome no canto superior direito
- A TAG pode ter números e letras (ex: BR1, EUW, 1234)

**Regiões disponíveis:**

- `br1` - Brasil
- `na1` - América do Norte
- `euw1` - Europa Oeste
- `eun1` - Europa Nordeste
- `kr` - Coreia
- `jp1` - Japão
- `la1` - América Latina Norte
- `la2` - América Latina Sul
- `oc1` - Oceania
- `tr1` - Turquia
- `ru` - Rússia

### `/contas`

Mostra todas as suas contas vinculadas (máximo 3).

### `/media [campeao] [metrica] [usuario] [conta]`

🆕 **NOVO!** Sistema completo de análise de estatísticas com múltiplas opções!

**Parâmetros (todos opcionais):**

- `campeao` - Filtrar por campeão específico (com auto-complete!)
- `metrica` - Métrica específica: carry, kda, dano, cs, visao, kp, gold, todas
- `usuario` - Ver estatísticas de outro jogador
- `conta` - Número da conta (1, 2 ou 3)

**Exemplos básicos:**

```
/media                    # Suas estatísticas gerais
/media conta:1            # Estatísticas da conta 1
/media metrica:todas      # Todas as métricas detalhadas
```

**Exemplos com filtro de campeão:**

```
/media campeao:Ahri                      # Stats apenas com Ahri
/media campeao:Yasuo metrica:kda         # KDA apenas com Yasuo
/media campeao:Thresh metrica:visao      # Vision Score com Thresh
```

**Exemplos vendo outros jogadores:**

```
/media usuario:@Amigo                           # Stats do amigo
/media usuario:@Amigo campeao:Zed               # Stats do amigo com Zed
/media usuario:@Amigo metrica:dano              # Dano médio do amigo
/media usuario:@TopLaner campeao:Garen metrica:todas  # Tudo sobre o top laner com Garen
```

**Métricas disponíveis:**

- 🏆 `carry` - Carry Score e visão geral (padrão)
- ⚔️ `kda` - KDA detalhado e Kill Participation
- 🗡️ `dano` - Análise de dano aos campeões
- 🌾 `cs` - Farm, CS/min e economia
- 👁️ `visao` - Vision Score (ótimo para supports!)
- 🎯 `kp` - Kill Participation detalhado
- 💰 `gold` - Gold/min e análise econômica
- 📊 `todas` - TODAS as métricas em uma visão completa!

**Informações exibidas (varia por métrica):**

- 📈 Carry Score médio (0-100)
- 🎮 Total de partidas e Win Rate
- ⚔️ KDA médio completo
- 🎯 Kill Participation média
- 🗡️ Dano médio aos campeões
- 🌾 CS médio e CS/min
- 💰 Gold médio e GPM
- 👁️ Vision Score
- 🎭 Role mais jogada no mês

**Classificação do Carry Score:**

- 🏆 **75+ pontos** - S+ Carry (GOD!)
- ⭐ **65-74 pontos** - S Carry (Muito bom!)
- 💎 **50-64 pontos** - A Carry (Bom desempenho)
- 🥈 **35-49 pontos** - B Normal (Desempenho OK)
- 📉 **< 35 pontos** - C Weight (Precisa melhorar)

### `/historico [conta] [quantidade]`

Mostra o histórico detalhado das últimas partidas.

**Exemplos:**

```
/historico 1 5   # Últimas 5 partidas da conta 1
/historico 2 10  # Últimas 10 partidas da conta 2
```

**Informações por partida:**

- ✅/❌ Resultado (Vitória/Derrota)
- 🎭 Champion e Role jogada
- 📊 KDA completo (ratio e números)
- 🎯 Kill Participation %
- 🏆 Carry Score (0-10)
- 🗡️ Dano causado e CS
- 📅 Data da partida

### `/tops_flex [quantidade]`

Mostra o **ranking dos melhores jogadores** do servidor no mês atual.

**Exemplos:**

```
/tops_flex      # Top 10 jogadores
/tops_flex 20   # Top 20 jogadores
```

**Informações do ranking:**

- 🥇🥈🥉 Medalhas para top 3
- 📈 Carry Score médio
- 🎮 Total de partidas
- ✅ Win Rate
- ⚔️ KDA médio
- 🎯 Kill Participation média

**Critérios:**

- Mínimo de **5 partidas** de Flex no mês
- Ordenado por carry score médio
- Atualizado em tempo real

---

### Comandos Administrativos

### `/configurar <tipo> <canal>` [ADMIN]

**[Apenas Administradores]** Configura os canais do bot.

**Tipos de configuração:**

- `alertas` - Canal para notificações de performance baixa
- `partidas` - Canal para notificações de partidas terminadas

**Exemplos:**

```
/configurar alertas #avisos-lol
/configurar partidas #flex-partidas
```

**O que é enviado em cada canal:**

📢 **Canal de Alertas:**

- ⚠️ Quando jogador usa o **mesmo campeão 3x seguidas**
- 📉 E tiver **carry score abaixo de 60** nas 3 partidas
- 💡 Sugestões de melhoria automáticas

🎮 **Canal de Partidas:**

- 📊 **Cada partida** de Flex que terminar
- 🏆 Carry Score, KDA, Role, Champion
- ✅/❌ Resultado (Vitória/Derrota)
- 📈 Estatísticas detalhadas

**Objetivo:** Manter o time informado sobre performances e progresso!

### `/reset_media <modo> [usuario] [conta_numero]` [ADMIN]

**[Apenas Administradores]** Reseta estatísticas de partidas do banco de dados.

**Modos disponíveis:**

- `all` - Reseta **TODAS** as partidas do servidor (requer confirmação)
- `usuario` - Reseta partidas de um usuário específico

**Exemplos:**

```
/reset_media modo:all
# Mostra aviso e requer confirmação com /reset_media_confirmar

/reset_media modo:usuario usuario:@Jogador
# Reseta TODAS as partidas de todas as contas do jogador

/reset_media modo:usuario usuario:@Jogador conta_numero:1
# Reseta apenas as partidas da conta 1 do jogador

/reset_media modo:usuario usuario:@Jogador conta_numero:2
# Reseta apenas as partidas da conta 2 do jogador
```

**⚠️ Importante:**

- Esta ação **NÃO PODE SER DESFEITA**
- As **contas vinculadas NÃO são removidas**, apenas as partidas
- Para resetar tudo, você precisa confirmar com `/reset_media_confirmar`
- O bot continuará monitorando novas partidas normalmente após o reset

**Casos de uso:**

- Limpar estatísticas de teste
- Começar um novo "season" limpo
- Remover dados incorretos de um jogador específico
- Reset completo do servidor

## 🚀 Instalação e Configuração

> 💡 **Quer hospedar online 24/7 gratuitamente?** Veja o guia de [Deploy no Railway](DEPLOY_RAILWAY.md) ou o [Guia Rápido](DEPLOY_RAPIDO.md)!

### 1. Pré-requisitos

- Python 3.8 ou superior
- Conta no Discord Developer Portal
- Riot Games API Key

### 2. Criando o Bot no Discord

1. Acesse [Discord Developer Portal](https://discord.com/developers/applications)
2. Clique em **"New Application"**
3. Dê um nome ao seu bot
4. Vá em **"Bot"** no menu lateral
5. Clique em **"Add Bot"**
6. Copie o **TOKEN** (você vai precisar dele!)
7. Em **"Privileged Gateway Intents"**, ative:
   - Message Content Intent
8. Vá em **"OAuth2"** > **"URL Generator"**
9. Selecione os escopos:
   - `bot`
   - `applications.commands`
10. Selecione as permissões:
    - Send Messages
    - Use Slash Commands
    - Embed Links
11. Copie a URL gerada e use para adicionar o bot ao seu servidor

### 3. Obtendo a Riot API Key

1. Acesse [Riot Games Developer Portal](https://developer.riotgames.com/)
2. Faça login com sua conta Riot
3. Copie sua **API Key** (Development Key)

⚠️ **Importante:** A Development Key expira a cada 24 horas. Para uso prolongado, solicite uma **Production Key**.

### 4. Instalando Dependências

```bash
# Clone ou baixe o projeto
cd flex-dos-crias

# Instale as dependências
pip install -r requirements.txt
```

### 5. Configurando o Bot

1. Crie um arquivo `.env` na raiz do projeto:

```env
# Token do seu bot Discord
DISCORD_TOKEN=seu_token_aqui

# Chave da API da Riot Games
RIOT_API_KEY=sua_chave_riot_aqui

# Região padrão (opcional, padrão: br1)
DEFAULT_REGION=br1
```

2. Substitua os valores pelos seus tokens reais

### 6. Executando o Bot

```bash
python bot.py
```

Se tudo estiver configurado corretamente, você verá:

```
Bot NomeDoBot está online!
ID: 123456789
------
X comandos sincronizados
```

## 📊 Sistema de Cálculo de Carry Score

O Carry Score é calculado em uma escala de **0 a 100 pontos** (inteiros, sem decimais) usando um sistema avançado com **pesos diferentes por role**.

### 🥊 Métricas de Combate

- **KDA** → (kills + assists) / deaths
- **Dano por Minuto (DPM)** → damageToChampions / gameTime
- **Dano por Ouro** → damageToChampions / goldEarned (eficiência de recursos)
- **Kill Participation (KP)** → (kills + assists) / teamKills

### 💰 Métricas de Recursos

- **Gold por Minuto (GPM)** → goldEarned / gameTime
- **CS por Minuto (CSPM)** → totalMinionsKilled / gameTime

### 🎯 Métricas de Objetivos

- **Torres destruídas** → turretKills
- **Dano em objetivos** → damageDealtToObjectives
- **Dano em estruturas** → damageDealtToBuildings

### 👀 Métricas de Visão

- **Vision Score por minuto** → visionScore / gameTime
- **Wards colocadas e destruídas**

### 🛡️ Métricas de Utility (Supports)

- **Tempo de CC aplicado** → timeCCingOthers
- **Cura/Escudos aplicados** → totalHealsOnTeammates + totalDamageShieldedOnTeammates

## ⚖️ Pesos por Role

### Top/Jungle/Mid/ADC

- **KDA:** 20%
- **Kill Participation:** 20%
- **Dano por Minuto:** 15%
- **Gold/CS por Minuto:** 15% (7.5% cada)
- **Objetivos:** 20%
- **Visão:** 5%
- **Utility:** 5%

### Support

- **KDA:** 15%
- **Kill Participation:** 25%
- **Visão:** 25%
- **Objetivos:** 15%
- **CC/Utility:** 15%
- **Dano por Minuto:** 5%

### 🎁 Bônus

- **+5% no score** se a partida foi vencida

## 🗄️ Estrutura do Banco de Dados

O bot usa SQLite para armazenar:

- **users**: Usuários do Discord
- **lol_accounts**: Contas LOL vinculadas (máximo 3 por usuário)
  - Armazena Riot ID (Nome#TAG), PUUID, região
- **matches**: Histórico de partidas com:
  - Estatísticas completas (KDA, dano, CS, vision, etc.)
  - Carry Score calculado
  - Role jogada
  - Kill Participation %
  - Data e hora da partida

## 🔄 Monitoramento Automático

O bot verifica **a cada 5 minutos** se há novas partidas de Ranked Flex para todas as contas vinculadas. Quando detecta uma nova partida:

1. Busca os detalhes na API da Riot
2. Extrai suas estatísticas completas
3. Identifica sua role na partida
4. Calcula o carry score com pesos específicos da role
5. Salva no banco de dados com todas as métricas

## 🛠️ Estrutura do Projeto

```
flex-dos-crias/
│
├── bot.py              # Bot principal do Discord (comandos)
├── database.py         # Gerenciamento do banco de dados SQLite
├── riot_api.py         # Integração com Riot Games API + cálculo de carry
├── requirements.txt    # Dependências Python
├── env_example.txt     # Exemplo de configuração
├── .gitignore         # Arquivos ignorados pelo Git
├── README.md          # Este arquivo (documentação completa)
└── INICIO_RAPIDO.md   # Guia rápido de início
```

## ⚠️ Limitações

- Apenas partidas de **Ranked Flex 5v5** são rastreadas
- A API de desenvolvimento da Riot tem limite de requisições
- A Development Key expira a cada 24 horas (renove diariamente)
- O bot precisa estar online para monitorar partidas
- Estatísticas são do mês atual (histórico por mês)

## 🐛 Solução de Problemas

### Bot não inicia

- Verifique se o arquivo `.env` está configurado corretamente
- Confirme que o token do Discord está correto
- Verifique se a Riot API Key está válida (não expirou)

### Conta não é encontrada

- Use o formato correto: `Nome#TAG` (com a hashtag)
- Verifique se o Riot ID está exatamente como no jogo
- Confirme se a região está correta

### Partidas não são detectadas

- Certifique-se de jogar **Ranked Flex** (não Solo/Duo)
- O bot verifica a cada 5 minutos
- A partida pode levar alguns minutos para aparecer na API
- Verifique se o bot está online e rodando

### Carry Score parece errado

- O score leva em conta múltiplas métricas, não só KDA
- Cada role tem pesos diferentes
- Support com bom KP e Vision pode ter score alto mesmo com pouco dano
- ADC com alto dano e farm tem score diferente de Support

## 📝 Notas Importantes

- O cálculo do carry score é uma métrica personalizada e não oficial da Riot
- Os pesos foram calibrados para equilibrar todas as roles
- Support tem maior peso em Vision e KP, menor em Dano
- Carrys (ADC/Mid/Top) tem maior peso em Dano e Farm
- Para uso em produção contínuo, considere obter uma Production API Key
- O banco de dados é local (arquivo .db na pasta do projeto)

## 🤝 Contribuindo

Sinta-se à vontade para melhorar o bot! Algumas ideias:

- [x] Sistema de rankings no servidor Discord ✅
- [x] Notificações de performance ruins ✅
- [x] Sistema avançado de estatísticas por campeão e métrica ✅
- [x] Visualizar stats de outros jogadores ✅
- [ ] Suporte a outros modos de jogo (Solo/Duo, Normal)
- [ ] Gráficos de progressão ao longo do tempo
- [ ] Análise de champions mais jogados com gráficos
- [ ] Alertas positivos (sequências boas)
- [ ] Comparação direta head-to-head entre dois jogadores

## 📄 Licença

Este projeto é livre para uso pessoal e educacional.

---

**Desenvolvido com ❤️ para a comunidade de League of Legends**

🎮 Boas partidas e muito carry! 🏆

**Novidade:** Sistema completo de análise por role com métricas avançadas!
