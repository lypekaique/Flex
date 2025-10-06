# ⚠️ Sistema de Alertas de Performance

Entenda como funciona o sistema de notificações automáticas do bot!

## 🎯 O que é?

O bot monitora automaticamente a performance dos jogadores e envia **alertas** quando detecta padrões de baixo desempenho com campeões específicos.

## 📋 Como Funciona?

### 1️⃣ Monitoramento Contínuo

- O bot verifica novas partidas **a cada 5 minutos**
- Para cada partida registrada, analisa:
  - Qual campeão foi usado
  - Qual foi o carry score obtido
  - Histórico recente com aquele campeão

### 2️⃣ Critérios de Alerta

Um alerta é enviado quando **TODAS** estas condições são atendidas:

✅ Jogador usou o **mesmo campeão 3 vezes seguidas**
✅ **Todas as 3 partidas** tiveram carry score **abaixo de 6.0**
✅ Canal de notificações está **configurado** no servidor

### 3️⃣ Conteúdo do Alerta

Quando um alerta é enviado, ele inclui:

- 📢 **Menção ao jogador**
- 🎮 **Nome do campeão** problemático
- 📊 **Estatísticas das 3 partidas:**
  - Carry score de cada uma
  - KDA de cada partida
  - Role jogada
  - Resultado (vitória/derrota)
- 📉 **Carry score médio** das 3 partidas
- 💡 **Sugestões práticas** de melhoria

## 🔧 Como Configurar?

### Para Administradores:

1. **Crie um canal** para as notificações (ex: `#avisos-lol`)

2. **Configure o canal:**
   ```
   /configurar #avisos-lol
   ```

3. **Pronto!** O bot começará a enviar alertas automaticamente.

### Para Alterar o Canal:

Basta usar `/configurar` novamente com o novo canal:
```
/configurar #novo-canal
```

### Para Desativar:

Atualmente, não é possível desativar sem remover o canal ou deletar a configuração do banco.

## 📊 Exemplo de Alerta

```
⚠️ ALERTA DE PERFORMANCE BAIXA
@Jogador está com dificuldades em Yasuo!

📊 Estatísticas Recentes
🎮 3 últimas partidas com Yasuo
📉 Carry Score médio: 4.3/10
⚠️ Todas abaixo de 6.0!

🎯 Últimas 3 Partidas
❌ 4.5 - 3/8/4 (Mid)
❌ 4.2 - 2/9/5 (Mid)
✅ 4.1 - 5/7/3 (Mid)

💡 Sugestão
Considere:
• Trocar de campeão temporariamente
• Rever builds e runas
• Assistir replays das partidas
• Praticar em Normal antes de voltar ao Ranked

Conta: SeuNick#BR1
```

## 🎯 Objetivo do Sistema

O sistema de alertas foi criado para:

1. **Ajudar jogadores** a identificarem quando estão tendo dificuldades
2. **Prevenir tilting** ao mostrar padrões negativos
3. **Incentivar melhoria** com sugestões práticas
4. **Criar awareness** no time sobre performance individual

## ⚙️ Detalhes Técnicos

### Verificação por Campeão

- O sistema verifica **por campeão específico**
- Se você jogar 3x com Yasuo e depois 3x com Zed, são análises separadas
- Apenas partidas **Ranked Flex** são consideradas

### Threshold de Score

- **Score < 6.0** é considerado baixo
- Equivale a:
  - **Rank C** (Weight)
  - **Rank B** (Normal)
  - Performance abaixo do esperado

### Frequência de Alertas

- **1 alerta por sequência** de 3 jogos ruins
- Se continuar jogando mal, novo alerta só na próxima sequência
- Evita spam excessivo

### Múltiplos Servidores

- Se o bot está em **múltiplos servidores**
- E o jogador também está nesses servidores
- Alertas são enviados em **todos** que têm canal configurado

## 🛡️ Privacidade

- Alertas são **públicos** no canal configurado
- Todos no servidor podem ver
- Administradores escolhem onde enviar
- Jogadores são **mencionados** diretamente

## 💡 Dicas para Administradores

### Canal Ideal

Considere criar um canal específico como:
- `#avisos-lol`
- `#performance-flex`
- `#coach-bot`

### Tom do Canal

- O sistema é **construtivo**, não punitivo
- Use para ajudar, não para "shaming"
- Incentive melhoria, não humilhação

### Complementos

Combine com:
- `/tops_flex` para mostrar quem está indo bem
- `/media` para análises individuais
- Conversas diretas com jogadores

## ❓ Perguntas Frequentes

### "O alerta é muito severo?"

O threshold de 6.0 é equilibrado:
- 6.0+ = Performance boa (S/A ranks)
- < 6.0 = Performance precisa melhorar (B/C ranks)

### "Como desativar alertas?"

Atualmente só removendo o canal ou configuração do banco.
Futura feature: comando para desativar temporariamente.

### "Posso mudar o threshold?"

Atualmente fixo em 6.0.
Futuras versões podem ter threshold configurável.

### "Alertas funcionam em Solo/Duo?"

**Não.** Apenas partidas de **Ranked Flex** são monitoradas.

### "Posso ver meus alertas históricos?"

Atualmente não há histórico de alertas.
Apenas notificações em tempo real.

## 🔮 Futuras Melhorias

Planejadas:
- [ ] Threshold configurável por servidor
- [ ] Comando para desativar alertas temporariamente
- [ ] Alertas privados (DM) em vez de públicos
- [ ] Histórico de alertas
- [ ] Alertas personalizados (ex: KDA baixo, poucas wards)
- [ ] Alertas positivos (sequências boas)

## 📞 Comandos Relacionados

- `/configurar <canal>` - Configurar canal de alertas (admin)
- `/media` - Ver sua própria performance
- `/historico` - Ver detalhes de partidas
- `/tops_flex` - Ver quem está indo bem

---

**O sistema de alertas é uma ferramenta de melhoria!** 🎯

Use para ajudar seus amigos a identificarem padrões e melhorarem no jogo, não para criticar negativamente.

**Bom jogo e carry forte!** 💪🏆

