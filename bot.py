import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from database import Database
from riot_api import RiotAPI
from datetime import datetime
from typing import Dict
import asyncio

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
TOKEN = os.getenv('DISCORD_TOKEN')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')
DEFAULT_REGION = os.getenv('DEFAULT_REGION', 'br1')

# Inicializa bot e banco de dados
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
db = Database()
riot_api = RiotAPI(RIOT_API_KEY)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online!')
    print(f'ID: {bot.user.id}')
    print('------')
    
    # Sincroniza comandos slash
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)} comandos sincronizados')
    except Exception as e:
        print(f'Erro ao sincronizar comandos: {e}')
    
    # Inicia verificação de partidas
    check_new_matches.start()

@bot.tree.command(name="logar", description="Vincule sua conta do League of Legends (use formato: Nome#TAG)")
@app_commands.describe(
    riot_id="Seu Riot ID no formato Nome#TAG (ex: Faker#KR1)",
    regiao="Região do servidor (ex: br1, na1, euw1)"
)
async def logar(interaction: discord.Interaction, riot_id: str, regiao: str = DEFAULT_REGION):
    """Comando para vincular conta do LOL usando Riot ID (nome#tag)"""
    await interaction.response.defer(ephemeral=True)
    
    # Valida formato do Riot ID
    if '#' not in riot_id:
        await interaction.followup.send(
            "❌ Formato inválido! Use o formato: **Nome#TAG**\n"
            "Exemplo: `Faker#KR1` ou `SeuNick#BR1`",
            ephemeral=True
        )
        return
    
    game_name, tag_line = riot_id.split('#', 1)
    
    # Normaliza região
    regiao = regiao.lower()
    if regiao not in RiotAPI.REGIONS:
        regioes_disponiveis = ', '.join(RiotAPI.REGIONS.keys())
        await interaction.followup.send(
            f"❌ Região inválida! Regiões disponíveis: {regioes_disponiveis}",
            ephemeral=True
        )
        return
    
    # Busca conta na API da Riot (Riot ID)
    account = await riot_api.get_account_by_riot_id(game_name, tag_line, regiao)
    
    if not account:
        await interaction.followup.send(
            f"❌ Conta '{riot_id}' não encontrada.\n"
            f"Verifique se o nome e tag estão corretos!",
            ephemeral=True
        )
        return
    
    # Busca dados do summoner pelo PUUID
    summoner = await riot_api.get_summoner_by_puuid(account['puuid'], regiao)
    
    if not summoner:
        await interaction.followup.send(
            f"❌ Erro ao buscar dados do invocador na região {regiao.upper()}.",
            ephemeral=True
        )
        return
    
    # Adiciona conta ao banco de dados
    discord_id = str(interaction.user.id)
    success, message = db.add_lol_account(
        discord_id=discord_id,
        summoner_name=f"{game_name}#{tag_line}",
        summoner_id=summoner['id'],
        puuid=account['puuid'],
        account_id=summoner['accountId'],
        region=regiao
    )
    
    if success:
        # Cria embed bonito
        embed = discord.Embed(
            title="✅ Conta Vinculada!",
            description=f"Conta **{game_name}#{tag_line}** vinculada com sucesso!",
            color=discord.Color.green()
        )
        embed.add_field(name="🌍 Região", value=regiao.upper(), inline=True)
        embed.add_field(name="⭐ Nível", value=summoner['summonerLevel'], inline=True)
        
        # Mostra quantas contas o usuário tem
        accounts = db.get_user_accounts(discord_id)
        embed.add_field(
            name="📊 Contas Vinculadas", 
            value=f"{len(accounts)}/3", 
            inline=True
        )
        
        embed.set_footer(text="O bot começará a monitorar suas partidas de Flex automaticamente!")
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(f"❌ {message}", ephemeral=True)

@bot.tree.command(name="contas", description="Veja suas contas vinculadas do League of Legends")
async def contas(interaction: discord.Interaction):
    """Lista todas as contas vinculadas do usuário"""
    await interaction.response.defer(ephemeral=True)
    
    discord_id = str(interaction.user.id)
    accounts = db.get_user_accounts(discord_id)
    
    if not accounts:
        await interaction.followup.send(
            "❌ Você não tem nenhuma conta vinculada. Use `/logar` para vincular uma conta!",
            ephemeral=True
        )
        return
    
    # Cria embed com as contas
    embed = discord.Embed(
        title="📋 Suas Contas Vinculadas",
        description=f"Total: {len(accounts)}/3 contas",
        color=discord.Color.blue()
    )
    
    for i, account in enumerate(accounts, 1):
        embed.add_field(
            name=f"{i}. {account['summoner_name']}",
            value=f"🌍 Região: {account['region'].upper()}\n📅 Vinculada em: {account['created_at'][:10]}",
            inline=False
        )
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="media", description="Veja a média do seu carry score no mês")
@app_commands.describe(
    conta="Número da conta (1, 2 ou 3). Deixe vazio para ver todas"
)
async def media(interaction: discord.Interaction, conta: int = None):
    """Calcula a média de carry score do mês atual"""
    await interaction.response.defer()
    
    discord_id = str(interaction.user.id)
    accounts = db.get_user_accounts(discord_id)
    
    if not accounts:
        await interaction.followup.send(
            "❌ Você não tem nenhuma conta vinculada. Use `/logar` para vincular uma conta!"
        )
        return
    
    # Se especificou uma conta, valida
    if conta is not None:
        if conta < 1 or conta > len(accounts):
            await interaction.followup.send(
                f"❌ Conta inválida! Você tem {len(accounts)} conta(s) vinculada(s)."
            )
            return
        accounts = [accounts[conta - 1]]
    
    # Pega mês e ano atual
    now = datetime.now()
    month = now.month
    year = now.year
    
    # Cria embed para resultados
    embed = discord.Embed(
        title=f"📊 Estatísticas de {now.strftime('%B/%Y')}",
        color=discord.Color.gold()
    )
    
    for account in accounts:
        matches = db.get_monthly_matches(account['id'], year, month)
        
        if not matches:
            embed.add_field(
                name=f"⚠️ {account['summoner_name']}",
                value="Nenhuma partida de Flex registrada este mês.",
                inline=False
            )
            continue
        
        # Calcula estatísticas
        total_matches = len(matches)
        avg_carry = sum(m['carry_score'] for m in matches) / total_matches
        wins = sum(1 for m in matches if m['win'])
        win_rate = (wins / total_matches) * 100
        
        avg_kills = sum(m['kills'] for m in matches) / total_matches
        avg_deaths = sum(m['deaths'] for m in matches) / total_matches
        avg_assists = sum(m['assists'] for m in matches) / total_matches
        avg_kda_calc = (avg_kills + avg_assists) / max(avg_deaths, 1)
        avg_kp = sum(m['kill_participation'] for m in matches) / total_matches
        
        # Estatísticas por role
        role_count = {}
        for m in matches:
            role = m['role']
            role_count[role] = role_count.get(role, 0) + 1
        most_played_role = max(role_count, key=role_count.get) if role_count else "Unknown"
        
        # Determina emoji baseado no carry score
        if avg_carry >= 70:
            emoji = "🏆"
            rank = "S+ Carry"
        elif avg_carry >= 60:
            emoji = "⭐"
            rank = "S Carry"
        elif avg_carry >= 50:
            emoji = "💎"
            rank = "A Carry"
        elif avg_carry >= 40:
            emoji = "🥈"
            rank = "B Normal"
        else:
            emoji = "📉"
            rank = "C Weight"
        
        # Emoji por role
        role_emojis = {
            'Top': '⚔️',
            'Jungle': '🌳',
            'Mid': '✨',
            'ADC': '🏹',
            'Support': '🛡️'
        }
        role_emoji = role_emojis.get(most_played_role, '❓')
        
        # Adiciona campo ao embed
        stats_text = f"""
{emoji} **{rank}**
📈 Carry Score Médio: **{int(avg_carry)}/100**
🎮 Partidas: **{total_matches}** • ✅ WR: **{win_rate:.1f}%**
⚔️ KDA: **{avg_kda_calc:.2f}** ({avg_kills:.1f}/{avg_deaths:.1f}/{avg_assists:.1f})
🎯 Kill Participation: **{avg_kp:.1f}%**
{role_emoji} Role Mais Jogada: **{most_played_role}** ({role_count[most_played_role]}x)
        """
        
        embed.add_field(
            name=f"🎯 {account['summoner_name']} ({account['region'].upper()})",
            value=stats_text.strip(),
            inline=False
        )
    
    embed.set_footer(text="Apenas partidas de Ranked Flex são contabilizadas")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="historico", description="Veja o histórico detalhado de partidas")
@app_commands.describe(
    conta="Número da conta (1, 2 ou 3)",
    quantidade="Quantidade de partidas para mostrar (padrão: 5)"
)
async def historico(interaction: discord.Interaction, conta: int = 1, quantidade: int = 5):
    """Mostra histórico detalhado de partidas"""
    await interaction.response.defer()
    
    discord_id = str(interaction.user.id)
    accounts = db.get_user_accounts(discord_id)
    
    if not accounts:
        await interaction.followup.send(
            "❌ Você não tem nenhuma conta vinculada. Use `/logar` para vincular uma conta!"
        )
        return
    
    if conta < 1 or conta > len(accounts):
        await interaction.followup.send(
            f"❌ Conta inválida! Você tem {len(accounts)} conta(s) vinculada(s)."
        )
        return
    
    account = accounts[conta - 1]
    now = datetime.now()
    matches = db.get_monthly_matches(account['id'], now.year, now.month)
    
    if not matches:
        await interaction.followup.send(
            f"❌ Nenhuma partida encontrada para **{account['summoner_name']}** este mês."
        )
        return
    
    # Limita quantidade
    matches = matches[:min(quantidade, 10)]
    
    embed = discord.Embed(
        title=f"📜 Histórico - {account['summoner_name']}",
        description=f"Últimas {len(matches)} partidas de Ranked Flex",
        color=discord.Color.purple()
    )
    
    for i, match in enumerate(matches, 1):
        result = "✅ Vitória" if match['win'] else "❌ Derrota"
        kda_ratio = f"{match['kills']}/{match['deaths']}/{match['assists']}"
        
        # Emoji do carry score
        if match['carry_score'] >= 70:
            carry_emoji = "🏆"
        elif match['carry_score'] >= 50:
            carry_emoji = "⭐"
        elif match['carry_score'] >= 40:
            carry_emoji = "💎"
        else:
            carry_emoji = "📊"
        
        # Emoji por role
        role_emojis = {
            'Top': '⚔️',
            'Jungle': '🌳',
            'Mid': '✨',
            'ADC': '🏹',
            'Support': '🛡️'
        }
        role_emoji = role_emojis.get(match['role'], '❓')
        
        match_info = f"""
{result} • **{match['champion_name']}** {role_emoji} {match['role']}
📊 KDA: {kda_ratio} ({match['kda']:.2f}) • KP: {match['kill_participation']:.0f}%
{carry_emoji} Carry Score: **{match['carry_score']}/100**
🗡️ Dano: {match['damage_dealt']:,} • 🌾 CS: {match['cs']}
📅 {match['played_at'][:10]}
        """
        
        embed.add_field(
            name=f"#{i}",
            value=match_info.strip(),
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="configurar", description="[ADMIN] Configure os canais do bot")
@app_commands.describe(
    tipo="Tipo de configuração: alertas (performance ruim) ou partidas (quando termina partida)",
    canal="Canal onde serão enviadas as mensagens"
)
@app_commands.checks.has_permissions(administrator=True)
async def configurar(interaction: discord.Interaction, tipo: str, canal: discord.TextChannel):
    """Configura os canais do bot (apenas administradores)"""
    await interaction.response.defer(ephemeral=True)
    
    guild_id = str(interaction.guild_id)
    channel_id = str(canal.id)
    tipo = tipo.lower()
    
    if tipo not in ['alertas', 'partidas']:
        await interaction.followup.send(
            "❌ Tipo inválido! Use: `alertas` ou `partidas`",
            ephemeral=True
        )
        return
    
    if tipo == 'alertas':
        success = db.set_notification_channel(guild_id, channel_id)
        if success:
            embed = discord.Embed(
                title="✅ Canal de Alertas Configurado!",
                description=f"Alertas de performance serão enviados em {canal.mention}",
                color=discord.Color.green()
            )
            embed.add_field(
                name="📢 O que será notificado?",
                value=(
                    "• Quando um jogador usar o **mesmo campeão 3x seguidas**\n"
                    "• E tiver **carry score abaixo de 60** nas 3 partidas\n"
                    "• Será enviada uma notificação com sugestões"
                ),
                inline=False
            )
        else:
            await interaction.followup.send("❌ Erro ao configurar canal.", ephemeral=True)
            return
    
    else:  # partidas
        success = db.set_match_channel(guild_id, channel_id)
        if success:
            embed = discord.Embed(
                title="✅ Canal de Partidas Configurado!",
                description=f"Partidas terminadas serão enviadas em {canal.mention}",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🎮 O que será enviado?",
                value=(
                    "• **Cada partida** de Flex que terminar\n"
                    "• **Carry Score** da partida\n"
                    "• **KDA, Role, Champion** e estatísticas\n"
                    "• **Resultado** (Vitória/Derrota)\n"
                    "• Enviado automaticamente quando detectada"
                ),
                inline=False
            )
        else:
            await interaction.followup.send("❌ Erro ao configurar canal.", ephemeral=True)
            return
    
    # Mostra configuração atual
    config = db.get_server_config(guild_id)
    config_text = "**Configuração Atual:**\n"
    
    if config:
        if config['notification_channel_id']:
            config_text += f"🔔 Alertas: <#{config['notification_channel_id']}>\n"
        else:
            config_text += "🔔 Alertas: Não configurado\n"
        
        if config['match_channel_id']:
            config_text += f"🎮 Partidas: <#{config['match_channel_id']}>\n"
        else:
            config_text += "🎮 Partidas: Não configurado\n"
    
    embed.add_field(name="⚙️ Status", value=config_text, inline=False)
    embed.set_footer(text="Use /configurar alertas #canal ou /configurar partidas #canal")
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="tops_flex", description="Veja o ranking dos melhores jogadores do mês")
@app_commands.describe(
    quantidade="Quantidade de jogadores no ranking (padrão: 10)"
)
async def tops_flex(interaction: discord.Interaction, quantidade: int = 10):
    """Mostra o ranking dos melhores jogadores por carry score"""
    await interaction.response.defer()
    
    # Limita quantidade
    quantidade = max(5, min(quantidade, 25))
    
    # Busca ranking
    ranking = db.get_top_players_by_carry(limit=quantidade, min_games=5)
    
    if not ranking:
        await interaction.followup.send(
            "❌ Ainda não há jogadores suficientes no ranking.\n"
            "**Mínimo:** 5 partidas de Flex no mês."
        )
        return
    
    # Cria embed
    now = datetime.now()
    embed = discord.Embed(
        title="🏆 TOP FLEX PLAYERS - RANKING",
        description=f"**{now.strftime('%B/%Y')}** • Mínimo: 5 partidas",
        color=discord.Color.gold()
    )
    
    # Emojis de medalha
    medals = ["🥇", "🥈", "🥉"]
    
    for i, player in enumerate(ranking, 1):
        # Emoji da posição
        if i <= 3:
            position_emoji = medals[i-1]
        else:
            position_emoji = f"**#{i}**"
        
        # Determina rank baseado no carry score
        avg_carry = player['avg_carry']
        if avg_carry >= 70:
            rank_emoji = "🏆 S+"
        elif avg_carry >= 60:
            rank_emoji = "⭐ S"
        elif avg_carry >= 50:
            rank_emoji = "💎 A"
        elif avg_carry >= 40:
            rank_emoji = "🥈 B"
        else:
            rank_emoji = "📊 C"
        
        # Busca usuário do Discord
        try:
            user = await bot.fetch_user(int(player['discord_id']))
            player_name = f"{user.mention}"
        except:
            player_name = player['summoner_name']
        
        player_info = f"""
{position_emoji} {player_name} • {rank_emoji}
📈 Carry: **{int(avg_carry)}/100** | 🎮 Jogos: **{player['total_games']}**
✅ WR: **{player['win_rate']:.1f}%** | ⚔️ KDA: **{player['avg_kda']:.2f}**
🎯 KP: **{player['avg_kp']:.1f}%**
        """
        
        embed.add_field(
            name=f"{player['summoner_name']} ({player['region'].upper()})",
            value=player_info.strip(),
            inline=False
        )
    
    embed.set_footer(text="Apenas Ranked Flex • Atualizado em tempo real")
    await interaction.followup.send(embed=embed)

async def send_match_notification(lol_account_id: int, stats: Dict):
    """Envia notificação quando uma partida termina"""
    try:
        # Busca informações da conta
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT discord_id, summoner_name FROM lol_accounts
            WHERE id = ?
        ''', (lol_account_id,))
        account_info = cursor.fetchone()
        conn.close()
        
        if not account_info:
            return
        
        discord_id, summoner_name = account_info
        
        # Busca todos os servidores onde está o bot
        for guild in bot.guilds:
            # Verifica se o usuário está nesse servidor
            member = guild.get_member(int(discord_id))
            if not member:
                continue
            
            # Busca canal de partidas configurado
            channel_id = db.get_match_channel(str(guild.id))
            if not channel_id:
                continue
            
            # Busca o canal
            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue
            
            # Determina cor baseada no resultado
            if stats['win']:
                color = discord.Color.green()
                result_emoji = "✅"
                result_text = "VITÓRIA"
            else:
                color = discord.Color.red()
                result_emoji = "❌"
                result_text = "DERROTA"
            
            # Determina emoji e rank do carry score
            carry_score = stats['carry_score']
            if carry_score >= 70:
                rank_emoji = "🏆"
                rank_text = "S+ CARRY"
            elif carry_score >= 60:
                rank_emoji = "⭐"
                rank_text = "S CARRY"
            elif carry_score >= 50:
                rank_emoji = "💎"
                rank_text = "A"
            elif carry_score >= 40:
                rank_emoji = "🥈"
                rank_text = "B"
            else:
                rank_emoji = "📉"
                rank_text = "C"
            
            # Emoji por role
            role_emojis = {
                'Top': '⚔️',
                'Jungle': '🌳',
                'Mid': '✨',
                'ADC': '🏹',
                'Support': '🛡️'
            }
            role_emoji = role_emojis.get(stats['role'], '❓')
            
            # Cria embed
            embed = discord.Embed(
                title=f"{result_emoji} {result_text} - {stats['champion_name']}",
                description=f"{member.mention} terminou uma partida de Ranked Flex!",
                color=color
            )
            
            # Informações principais
            embed.add_field(
                name="🎮 Partida",
                value=(
                    f"{role_emoji} **{stats['role']}** - {stats['champion_name']}\n"
                    f"⚔️ KDA: **{stats['kills']}/{stats['deaths']}/{stats['assists']}** ({stats['kda']:.2f})\n"
                    f"🎯 Kill Part: **{stats['kill_participation']:.0f}%**"
                ),
                inline=True
            )
            
            # Carry Score (destaque)
            embed.add_field(
                name="🏆 Performance",
                value=(
                    f"{rank_emoji} **{rank_text}**\n"
                    f"📊 Carry Score\n"
                    f"# **{carry_score}**/100"
                ),
                inline=True
            )
            
            # Estatísticas adicionais
            game_duration_min = stats['game_duration'] // 60
            embed.add_field(
                name="📊 Estatísticas",
                value=(
                    f"🗡️ Dano: **{stats['damage_dealt']:,}**\n"
                    f"🌾 CS: **{stats['cs']}**\n"
                    f"👁️ Vision: **{stats['vision_score']}**\n"
                    f"⏱️ Duração: **{game_duration_min}min**"
                ),
                inline=True
            )
            
            embed.set_footer(text=f"{summoner_name} • {stats['played_at'][:10]}")
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Envia notificação
            try:
                await channel.send(embed=embed)
                print(f"🎮 Partida enviada: {summoner_name} - {stats['champion_name']} (Score: {carry_score})")
            except Exception as e:
                print(f"Erro ao enviar partida: {e}")
    
    except Exception as e:
        print(f"Erro ao processar notificação de partida: {e}")

async def check_champion_performance(lol_account_id: int, champion_name: str):
    """Verifica se o jogador teve 3 performances ruins seguidas com o mesmo campeão"""
    try:
        # Busca as últimas 3 partidas com esse campeão
        matches = db.get_last_n_matches_with_champion(lol_account_id, champion_name, n=3)
        
        # Se não tem 3 partidas ainda, não faz nada
        if len(matches) < 3:
            return
        
        # Verifica se todas as 3 têm score abaixo de 60
        all_bad_scores = all(match['carry_score'] < 60 for match in matches)
        
        if not all_bad_scores:
            return
        
        # Busca informações da conta
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT discord_id, summoner_name FROM lol_accounts
            WHERE id = ?
        ''', (lol_account_id,))
        account_info = cursor.fetchone()
        conn.close()
        
        if not account_info:
            return
        
        discord_id, summoner_name = account_info
        
        # Busca todos os servidores onde está o bot
        for guild in bot.guilds:
            # Verifica se o usuário está nesse servidor
            member = guild.get_member(int(discord_id))
            if not member:
                continue
            
            # Busca canal de notificações configurado para esse servidor
            channel_id = db.get_notification_channel(str(guild.id))
            if not channel_id:
                continue
            
            # Busca o canal
            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue
            
            # Calcula média dos scores
            avg_score = sum(m['carry_score'] for m in matches) / 3
            
            # Cria embed de "vergonha"
            embed = discord.Embed(
                title="⚠️ ALERTA DE PERFORMANCE BAIXA",
                description=f"{member.mention} está com dificuldades em **{champion_name}**!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="📊 Estatísticas Recentes",
                value=(
                    f"🎮 **3 últimas partidas** com {champion_name}\n"
                    f"📉 Carry Score médio: **{int(avg_score)}/100**\n"
                    f"⚠️ Todas abaixo de 60!"
                ),
                inline=False
            )
            
            # Adiciona detalhes das 3 partidas
            matches_text = ""
            for i, match in enumerate(matches, 1):
                result_emoji = "✅" if match['win'] else "❌"
                matches_text += (
                    f"{result_emoji} **{match['carry_score']}** - "
                    f"{match['kills']}/{match['deaths']}/{match['assists']} "
                    f"({match['role']})\n"
                )
            
            embed.add_field(
                name="🎯 Últimas 3 Partidas",
                value=matches_text.strip(),
                inline=False
            )
            
            embed.add_field(
                name="💡 Sugestão",
                value=(
                    "Considere:\n"
                    "• Trocar de campeão temporariamente\n"
                    "• Rever builds e runas\n"
                    "• Assistir replays das partidas\n"
                    "• Praticar em Normal antes de voltar ao Ranked"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Conta: {summoner_name}")
            
            # Envia notificação
            try:
                await channel.send(embed=embed)
                print(f"⚠️ Notificação enviada: {summoner_name} com {champion_name} ({avg_score:.2f})")
            except Exception as e:
                print(f"Erro ao enviar notificação: {e}")
    
    except Exception as e:
        print(f"Erro ao verificar performance: {e}")

@tasks.loop(minutes=5)
async def check_new_matches():
    """Task que verifica novas partidas a cada 5 minutos"""
    try:
        # Busca todas as contas vinculadas
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, puuid, region FROM lol_accounts')
        accounts = cursor.fetchall()
        conn.close()
        
        for account_id, puuid, region in accounts:
            # Busca últimas partidas
            match_ids = await riot_api.get_match_history(puuid, region, count=5)
            
            if not match_ids:
                continue
            
            # Verifica se são partidas novas
            last_match = db.get_last_match_id(account_id)
            
            for match_id in match_ids:
                # Se já foi registrada, para
                if match_id == last_match:
                    break
                
                # Busca detalhes da partida
                match_data = await riot_api.get_match_details(match_id, region)
                
                if match_data:
                    # Extrai estatísticas do jogador
                    stats = riot_api.extract_player_stats(match_data, puuid)
                    
                    if stats:
                        # Salva no banco de dados
                        db.add_match(account_id, stats)
                        print(f"Nova partida registrada: {match_id} (Score: {stats['carry_score']})")
                        
                        # Envia notificação de partida terminada
                        await send_match_notification(account_id, stats)
                        
                        # Verifica se jogou 3x o mesmo campeão com score baixo
                        await check_champion_performance(account_id, stats['champion_name'])
                
                # Delay para não sobrecarregar a API
                await asyncio.sleep(1)
            
            await asyncio.sleep(2)
    
    except Exception as e:
        print(f"Erro ao verificar partidas: {e}")

@check_new_matches.before_loop
async def before_check_matches():
    """Espera o bot estar pronto antes de iniciar o loop"""
    await bot.wait_until_ready()

# Tratamento de erros
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏰ Aguarde {error.retry_after:.1f} segundos antes de usar este comando novamente.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌ Ocorreu um erro: {str(error)}",
            ephemeral=True
        )
        print(f"Erro no comando: {error}")

if __name__ == "__main__":
    if not TOKEN or not RIOT_API_KEY:
        print("❌ ERRO: Configure as variáveis DISCORD_TOKEN e RIOT_API_KEY no arquivo .env")
        print("Veja o arquivo .env.example para mais informações")
    else:
        bot.run(TOKEN)

