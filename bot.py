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

# Função auxiliar para verificar permissões de canal
async def check_command_channel(interaction: discord.Interaction) -> bool:
    """
    Verifica se o comando pode ser executado no canal atual.
    Admins podem usar em qualquer lugar.
    Se não houver canal configurado, qualquer um pode usar em qualquer lugar.
    Se houver canal configurado, usuários comuns só podem usar lá.
    Retorna True se pode executar, False caso contrário.
    """
    # Admins podem usar comandos em qualquer lugar
    if interaction.user.guild_permissions.administrator:
        return True
    
    # Busca o canal configurado
    guild_id = str(interaction.guild_id)
    command_channel_id = db.get_command_channel(guild_id)
    
    # Se não tem canal configurado, permite usar em qualquer lugar
    if not command_channel_id:
        return True
    
    # Verifica se está no canal correto
    if str(interaction.channel_id) != command_channel_id:
        await interaction.response.send_message(
            f"❌ **Canal incorreto!**\n"
            f"Use comandos apenas em <#{command_channel_id}>",
            ephemeral=True
        )
        return False
    
    return True

# View com botões persistentes para o comando /flex
class FlexGuideView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Timeout None = persistente
    
    @discord.ui.button(label="🎮 Como Vincular Conta", style=discord.ButtonStyle.primary, custom_id="flex_guide:vincular")
    async def vincular_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎮 Como Vincular Sua Conta",
            description="Para começar a usar o bot, você precisa vincular sua conta do LoL:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="1️⃣ Use o comando /logar",
            value=(
                "```/logar riot_id:SeuNick#TAG regiao:br1```\n"
                "**Importante:** Use o formato Nome#TAG!\n"
                "Exemplo: `Faker#KR1` ou `SeuNick#BR1`"
            ),
            inline=False
        )
        embed.add_field(
            name="2️⃣ Selecione sua região",
            value=(
                "• 🇧🇷 Brasil: `br1`\n"
                "• 🇺🇸 NA: `na1`\n"
                "• 🇪🇺 EUW: `euw1`\n"
                "• E outras disponíveis no auto-complete!"
            ),
            inline=False
        )
        embed.add_field(
            name="3️⃣ Pronto!",
            value="O bot começará a monitorar suas partidas de **Ranked Flex** automaticamente! 🎉",
            inline=False
        )
        embed.set_footer(text="Você pode vincular até 3 contas!")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="📊 Comandos Disponíveis", style=discord.ButtonStyle.success, custom_id="flex_guide:comandos")
    async def comandos_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📊 Comandos Disponíveis",
            description="Veja todos os comandos que você pode usar:",
            color=discord.Color.green()
        )
        embed.add_field(
            name="🎮 Comandos Básicos",
            value=(
                "`/logar` - Vincular sua conta do LoL\n"
                "`/contas` - Ver suas contas vinculadas\n"
                "`/media` - Ver suas estatísticas do mês\n"
                "`/historico` - Ver histórico de partidas\n"
                "`/tops_flex` - Ver ranking dos melhores\n"
                "`/flex` - Ver este guia novamente"
            ),
            inline=False
        )
        embed.add_field(
            name="⚙️ Comandos Admin (Apenas Administradores)",
            value=(
                "`/configurar` - Ver configuração atual\n"
                "`/configurar comandos #canal` - Definir canal de comandos\n"
                "`/configurar alertas #canal` - Canal de alertas\n"
                "`/configurar partidas #canal` - Canal de partidas\n"
                "`/configurar live #canal` - Canal de live tracking\n"
                "• Admins podem usar comandos em **qualquer lugar**\n"
                "• Usuários comuns só no **canal configurado**"
            ),
            inline=False
        )
        embed.add_field(
            name="💡 Dicas",
            value=(
                "• Todos os comandos tem **auto-complete**\n"
                "• Use a barra `/` para ver todos comandos\n"
                "• Estatísticas são apenas de **Ranked Flex**\n"
                "• Configure o canal de comandos primeiro!"
            ),
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🏆 Sistema de Carry Score", style=discord.ButtonStyle.secondary, custom_id="flex_guide:score")
    async def score_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏆 Sistema de Carry Score",
            description="Entenda como funciona o sistema de pontuação:",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="📈 O que é Carry Score?",
            value=(
                "É uma pontuação de **0 a 100** que mede o quanto você carregou seu time.\n"
                "Sistema inspirado no **U.GG** - não é apenas KDA! Considera múltiplos fatores.\n"
                "✨ **Menos punitivo**: performances medianas recebem scores justos!"
            ),
            inline=False
        )
        embed.add_field(
            name="📊 Fatores Analisados",
            value=(
                "• **KDA** e **Kill Participation**\n"
                "• **Dano** causado aos campeões\n"
                "• **Farm** (CS/min e Gold/min)\n"
                "• **Objetivos** (Torres, Drag, Baron)\n"
                "• **Visão** (Vision Score, Wards)\n"
                "• **Utility** (CC, Heals, Shields)\n"
                "• **Bônus** de +5% por vitória"
            ),
            inline=False
        )
        embed.add_field(
            name="🎯 Rankings",
            value=(
                "🏆 **75-100**: S+ Carry (GOD)\n"
                "⭐ **65-74**: S Carry (Muito bom)\n"
                "💎 **50-64**: A (Bom)\n"
                "🥈 **35-49**: B (Normal)\n"
                "📉 **0-34**: C (Precisa melhorar)"
            ),
            inline=False
        )
        embed.add_field(
            name="💡 Pesos por Role",
            value=(
                "**Carry Roles** (Top/Jungle/Mid/ADC):\n"
                "Foco em dano, farm e objetivos\n\n"
                "**Support**:\n"
                "Foco em KP, visão e utility"
            ),
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🔔 Sistema de Alertas", style=discord.ButtonStyle.danger, custom_id="flex_guide:alertas")
    async def alertas_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔔 Sistema de Alertas",
            description="O bot monitora seu desempenho e envia notificações:",
            color=discord.Color.red()
        )
        embed.add_field(
            name="⚠️ Alerta de Performance Baixa",
            value=(
                "Se você jogar **3x seguidas** com o mesmo campeão\n"
                "E tiver **Carry Score < 50** nas 3 partidas,\n"
                "O bot enviará um alerta com sugestões!"
            ),
            inline=False
        )
        embed.add_field(
            name="🎮 Notificação de Partidas",
            value=(
                "Toda vez que você terminar uma partida de Flex,\n"
                "O bot enviará automaticamente:\n"
                "• Resultado (Vitória/Derrota)\n"
                "• Seu Carry Score\n"
                "• KDA, Role, Champion\n"
                "• Estatísticas detalhadas"
            ),
            inline=False
        )
        embed.add_field(
            name="⚙️ Configuração (Admin)",
            value=(
                "Admins podem configurar os canais:\n"
                "`/configurar alertas #canal-alertas`\n"
                "`/configurar partidas #canal-partidas`"
            ),
            inline=False
        )
        embed.set_footer(text="O bot verifica novas partidas a cada 5 minutos")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online!')
    print(f'ID: {bot.user.id}')
    print('------')
    
    # Registra Views persistentes
    bot.add_view(FlexGuideView())
    print('✅ Views persistentes registradas')
    
    # Sincroniza comandos slash
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)} comandos sincronizados')
    except Exception as e:
        print(f'Erro ao sincronizar comandos: {e}')
    
    # Inicia verificação de partidas
    check_new_matches.start()
    
    # Inicia verificação de live games
    check_live_games.start()

# Auto-complete para regiões
async def region_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Auto-complete para seleção de região"""
    regions = [
        ('🇧🇷 Brasil (br1)', 'br1'),
        ('🇺🇸 América do Norte (na1)', 'na1'),
        ('🇪🇺 Europa Ocidental (euw1)', 'euw1'),
        ('🇪🇺 Europa Nórdica (eun1)', 'eun1'),
        ('🇰🇷 Coreia (kr)', 'kr'),
        ('🇯🇵 Japão (jp1)', 'jp1'),
        ('🇲🇽 América Latina Norte (la1)', 'la1'),
        ('🇦🇷 América Latina Sul (la2)', 'la2'),
        ('🇦🇺 Oceania (oc1)', 'oc1'),
        ('🇹🇷 Turquia (tr1)', 'tr1'),
        ('🇷🇺 Rússia (ru)', 'ru'),
    ]
    return [
        app_commands.Choice(name=name, value=value)
        for name, value in regions
        if current.lower() in name.lower() or current.lower() in value.lower()
    ][:25]  # Discord limita a 25 opções

@bot.tree.command(name="logar", description="🎮 Vincule sua conta do League of Legends ao bot")
@app_commands.describe(
    riot_id="Seu Riot ID no formato Nome#TAG (ex: Faker#KR1 ou SeuNick#BR1)",
    regiao="Selecione a região do seu servidor"
)
@app_commands.autocomplete(regiao=region_autocomplete)
async def logar(interaction: discord.Interaction, riot_id: str, regiao: str = DEFAULT_REGION):
    """Comando para vincular conta do LOL usando Riot ID (nome#tag)"""
    # Verifica permissão de canal
    if not await check_command_channel(interaction):
        return
    
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
    
    # A API da Riot às vezes não retorna 'id' e 'accountId' mais
    # Nesses casos, usamos o PUUID que é o identificador universal moderno
    summoner_id = summoner.get('id', account['puuid'])
    account_id = summoner.get('accountId', account['puuid'])
    summoner_level = summoner.get('summonerLevel', 0)
    
    # Log para debug se os campos estiverem faltando
    if 'id' not in summoner or 'accountId' not in summoner:
        print(f"⚠️ API retornou summoner sem id/accountId. Usando PUUID como fallback.")
        print(f"Summoner data: {summoner}")
    
    # Adiciona conta ao banco de dados
    discord_id = str(interaction.user.id)
    success, message = db.add_lol_account(
        discord_id=discord_id,
        summoner_name=f"{game_name}#{tag_line}",
        summoner_id=summoner_id,
        puuid=account['puuid'],
        account_id=account_id,
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
        embed.add_field(name="⭐ Nível", value=summoner_level, inline=True)
        
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

@bot.tree.command(name="contas", description="📋 Veja todas as suas contas vinculadas")
async def contas(interaction: discord.Interaction):
    """Lista todas as contas vinculadas do usuário"""
    # Verifica permissão de canal
    if not await check_command_channel(interaction):
        return
    
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

@bot.tree.command(name="media", description="📊 Veja suas estatísticas e média de carry score do mês")
@app_commands.describe(
    conta="Número da conta (1, 2 ou 3). Deixe vazio para ver todas"
)
async def media(interaction: discord.Interaction, conta: int = None):
    """Calcula a média de carry score do mês atual"""
    # Verifica permissão de canal
    if not await check_command_channel(interaction):
        return
    
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
        if avg_carry >= 75:
            emoji = "🏆"
            rank = "S+ Carry"
        elif avg_carry >= 65:
            emoji = "⭐"
            rank = "S Carry"
        elif avg_carry >= 50:
            emoji = "💎"
            rank = "A Carry"
        elif avg_carry >= 35:
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

@bot.tree.command(name="historico", description="📜 Veja seu histórico detalhado de partidas recentes")
@app_commands.describe(
    conta="Número da conta (1, 2 ou 3)",
    quantidade="Quantidade de partidas para mostrar (padrão: 5)"
)
async def historico(interaction: discord.Interaction, conta: int = 1, quantidade: int = 5):
    """Mostra histórico detalhado de partidas"""
    # Verifica permissão de canal
    if not await check_command_channel(interaction):
        return
    
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
        if match['carry_score'] >= 75:
            carry_emoji = "🏆"
        elif match['carry_score'] >= 65:
            carry_emoji = "⭐"
        elif match['carry_score'] >= 50:
            carry_emoji = "💎"
        elif match['carry_score'] >= 35:
            carry_emoji = "🥈"
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

# Auto-complete para tipo de configuração
async def config_type_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Auto-complete para tipos de configuração"""
    types = [
        ('🔔 Alertas - Notificações de performance', 'alertas'),
        ('🎮 Partidas - Notificações de jogos', 'partidas'),
        ('💬 Comandos - Canal onde usuários podem usar comandos', 'comandos'),
        ('🔴 Live - Notificações de partidas ao vivo', 'live'),
    ]
    return [
        app_commands.Choice(name=name, value=value)
        for name, value in types
        if current.lower() in name.lower() or current.lower() in value.lower()
    ]

@bot.tree.command(name="configurar", description="⚙️ [ADMIN] Configure os canais do bot ou veja a configuração atual")
@app_commands.describe(
    tipo="Tipo de configuração: alertas, partidas, comandos ou live (deixe vazio para ver config atual)",
    canal="Canal onde serão enviadas as mensagens (obrigatório se tipo for especificado)"
)
@app_commands.autocomplete(tipo=config_type_autocomplete)
@app_commands.checks.has_permissions(administrator=True)
async def configurar(interaction: discord.Interaction, tipo: str = None, canal: discord.TextChannel = None):
    """Configura os canais do bot (apenas administradores)"""
    await interaction.response.defer(ephemeral=True)
    
    guild_id = str(interaction.guild_id)
    
    # Se não especificou tipo, apenas mostra configuração atual
    if tipo is None:
        config = db.get_server_config(guild_id)
        
        embed = discord.Embed(
            title="⚙️ Configuração Atual do Servidor",
            description="Veja como o bot está configurado neste servidor:",
            color=discord.Color.blue()
        )
        
        if config:
            if config['command_channel_id']:
                embed.add_field(
                    name="💬 Canal de Comandos",
                    value=f"<#{config['command_channel_id']}>\nUsuários podem usar comandos apenas neste canal.",
                    inline=False
                )
            else:
                embed.add_field(
                    name="💬 Canal de Comandos",
                    value="❌ Não configurado\nUsuários não podem usar comandos.",
                    inline=False
                )
            
            if config['notification_channel_id']:
                embed.add_field(
                    name="🔔 Canal de Alertas",
                    value=f"<#{config['notification_channel_id']}>\nAlertas de performance baixa serão enviados aqui.",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🔔 Canal de Alertas",
                    value="❌ Não configurado",
                    inline=False
                )
            
            if config['match_channel_id']:
                embed.add_field(
                    name="🎮 Canal de Partidas",
                    value=f"<#{config['match_channel_id']}>\nNotificações de partidas terminadas serão enviadas aqui.",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🎮 Canal de Partidas",
                    value="❌ Não configurado",
                    inline=False
                )
            
            if config['live_game_channel_id']:
                embed.add_field(
                    name="🔴 Canal de Partidas Ao Vivo",
                    value=f"<#{config['live_game_channel_id']}>\nNotificações quando jogadores entrarem em partida serão enviadas aqui.",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🔴 Canal de Partidas Ao Vivo",
                    value="❌ Não configurado",
                    inline=False
                )
        else:
            embed.description = "❌ Nenhuma configuração encontrada para este servidor."
        
        embed.set_footer(text="Use /configurar <tipo> #canal para configurar")
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    # Se especificou tipo mas não especificou canal
    if canal is None:
        await interaction.followup.send(
            "❌ Você precisa especificar um canal quando escolhe um tipo de configuração!\n"
            "Use: `/configurar tipo:alertas canal:#seu-canal`",
            ephemeral=True
        )
        return
    
    channel_id = str(canal.id)
    tipo = tipo.lower()
    
    if tipo not in ['alertas', 'partidas', 'comandos', 'live']:
        await interaction.followup.send(
            "❌ Tipo inválido! Use: `alertas`, `partidas`, `comandos` ou `live`",
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
    
    elif tipo == 'partidas':
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
    
    elif tipo == 'comandos':
        success = db.set_command_channel(guild_id, channel_id)
        if success:
            embed = discord.Embed(
                title="✅ Canal de Comandos Configurado!",
                description=f"Comandos do bot poderão ser usados em {canal.mention}",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="💬 Quem pode usar?",
                value=(
                    "• **Usuários comuns** podem usar comandos apenas neste canal\n"
                    "• **Administradores** podem usar comandos em qualquer lugar\n"
                    "• Isso organiza melhor o uso do bot no servidor!"
                ),
                inline=False
            )
        else:
            await interaction.followup.send("❌ Erro ao configurar canal.", ephemeral=True)
            return
    
    else:  # live
        success = db.set_live_game_channel(guild_id, channel_id)
        if success:
            embed = discord.Embed(
                title="✅ Canal de Partidas Ao Vivo Configurado!",
                description=f"Notificações de live games serão enviadas em {canal.mention}",
                color=discord.Color.red()
            )
            embed.add_field(
                name="🔴 O que será notificado?",
                value=(
                    "• Quando um jogador **entrar em partida**\n"
                    "• **Champion e Role** do jogador\n"
                    "• **Modo de jogo** (Ranked Flex, Solo/Duo, etc)\n"
                    "• **Composição dos times**\n"
                    "• Link para **op.gg** e trackers\n"
                    "• Verificado a cada 2 minutos"
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
        if config['command_channel_id']:
            config_text += f"💬 Comandos: <#{config['command_channel_id']}>\n"
        else:
            config_text += "💬 Comandos: Não configurado\n"
        
        if config['notification_channel_id']:
            config_text += f"🔔 Alertas: <#{config['notification_channel_id']}>\n"
        else:
            config_text += "🔔 Alertas: Não configurado\n"
        
        if config['match_channel_id']:
            config_text += f"🎮 Partidas: <#{config['match_channel_id']}>\n"
        else:
            config_text += "🎮 Partidas: Não configurado\n"
        
        if config['live_game_channel_id']:
            config_text += f"🔴 Live: <#{config['live_game_channel_id']}>\n"
        else:
            config_text += "🔴 Live: Não configurado\n"
    
    embed.add_field(name="⚙️ Status do Servidor", value=config_text, inline=False)
    embed.set_footer(text="Use /configurar para ver todas as configurações")
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="tops_flex", description="🏆 Veja o ranking dos melhores jogadores de Flex do mês")
@app_commands.describe(
    quantidade="Quantidade de jogadores no ranking (padrão: 10)"
)
async def tops_flex(interaction: discord.Interaction, quantidade: int = 10):
    """Mostra o ranking dos melhores jogadores por carry score"""
    # Verifica permissão de canal
    if not await check_command_channel(interaction):
        return
    
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
        if avg_carry >= 75:
            rank_emoji = "🏆 S+"
        elif avg_carry >= 65:
            rank_emoji = "⭐ S"
        elif avg_carry >= 50:
            rank_emoji = "💎 A"
        elif avg_carry >= 35:
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

@bot.tree.command(name="flex", description="🎯 Guia completo do bot com botões interativos")
async def flex_guide(interaction: discord.Interaction):
    """Comando com guia interativo do bot"""
    # Verifica permissão de canal
    if not await check_command_channel(interaction):
        return
    
    embed = discord.Embed(
        title="🎯 Flex dos Crias - Guia do Bot",
        description=(
            "**Bem-vindo ao melhor bot de tracking de Ranked Flex!**\n\n"
            "Este bot monitora suas partidas automaticamente e calcula\n"
            "um **Carry Score** baseado em múltiplos fatores.\n\n"
            "Use os botões abaixo para aprender mais! 👇"
        ),
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="🚀 Início Rápido",
        value=(
            "1️⃣ Use `/logar` para vincular sua conta\n"
            "2️⃣ Jogue Ranked Flex normalmente\n"
            "3️⃣ Veja suas stats com `/media`\n"
            "4️⃣ Compete no ranking com `/tops_flex`"
        ),
        inline=False
    )
    
    embed.add_field(
        name="✨ Funcionalidades",
        value=(
            "📊 Tracking automático de partidas\n"
            "🏆 Sistema de Carry Score (0-100)\n"
            "📈 Estatísticas mensais detalhadas\n"
            "🎯 Ranking de melhores jogadores\n"
            "⚠️ Alertas de performance\n"
            "🔔 Notificações de partidas"
        ),
        inline=False
    )
    
    embed.set_footer(text="Clique nos botões abaixo para mais informações!")
    embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
    
    view = FlexGuideView()
    await interaction.response.send_message(embed=embed, view=view)

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
            if carry_score >= 75:
                rank_emoji = "🏆"
                rank_text = "S+ CARRY"
            elif carry_score >= 65:
                rank_emoji = "⭐"
                rank_text = "S CARRY"
            elif carry_score >= 50:
                rank_emoji = "💎"
                rank_text = "A"
            elif carry_score >= 35:
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
            
            # Duração da partida
            game_duration_min = stats['game_duration'] // 60
            game_duration_sec = stats['game_duration'] % 60
            
            # URL da imagem do campeão (Data Dragon Riot)
            champion_image_url = f"https://ddragon.leagueoflegends.com/cdn/14.1.1/img/champion/{stats['champion_name']}.png"
            
            # Cria embed com informações detalhadas
            embed = discord.Embed(
                title=f"{result_emoji} {result_text}",
                description=(
                    f"# {stats['champion_name']} {role_emoji}\n"
                    f"{member.mention} terminou uma partida de **Ranked Flex**!"
                ),
                color=color,
                timestamp=datetime.fromisoformat(stats['played_at'])
            )
            
            # Campo principal - Estatísticas da partida
            embed.add_field(
                name="📊 Estatísticas da Partida",
                value=(
                    f"⚔️ **KDA:** {stats['kills']}/{stats['deaths']}/{stats['assists']} ({stats['kda']:.2f})\n"
                    f"🎯 **Kill Participation:** {stats['kill_participation']:.0f}%\n"
                    f"🗡️ **Dano:** {stats['damage_dealt']:,}\n"
                    f"🌾 **CS:** {stats['cs']}\n"
                    f"👁️ **Vision Score:** {stats['vision_score']}\n"
                    f"⏱️ **Duração:** {game_duration_min}min {game_duration_sec}s"
                ),
                inline=True
            )
            
            # Carry Score em destaque
            embed.add_field(
                name="🏆 Carry Score",
                value=(
                    f"# {rank_emoji} {carry_score}/100\n"
                    f"**Rank:** {rank_text}\n"
                    f"\n"
                    f"```\n"
                    f"{'█' * int(carry_score/5)}{'░' * (20 - int(carry_score/5))}\n"
                    f"```"
                ),
                inline=True
            )
            
            # Informações adicionais
            embed.add_field(
                name="ℹ️ Detalhes",
                value=(
                    f"**Invocador:** {summoner_name}\n"
                    f"**Role:** {role_emoji} {stats['role']}\n"
                    f"**Campeão:** {stats['champion_name']}"
                ),
                inline=False
            )
            
            # Imagem do campeão (grande no lado direito)
            embed.set_image(url=champion_image_url)
            
            # Avatar do jogador como thumbnail
            embed.set_thumbnail(url=member.display_avatar.url)
            
            embed.set_footer(
                text=f"Ranked Flex • {summoner_name}",
                icon_url="https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/ranked-emblem-flex.png"
            )
            
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
        
        # Verifica se todas as 3 têm score abaixo de 50
        all_bad_scores = all(match['carry_score'] < 50 for match in matches)
        
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
                    f"⚠️ Todas abaixo de 50!"
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

async def send_live_game_notification(lol_account_id: int, live_info: Dict):
    """Envia notificação quando um jogador entra em partida ao vivo"""
    try:
        # Busca informações da conta
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT discord_id, summoner_name, region FROM lol_accounts
            WHERE id = ?
        ''', (lol_account_id,))
        account_info = cursor.fetchone()
        conn.close()
        
        if not account_info:
            return
        
        discord_id, summoner_name, region = account_info
        
        # Busca todos os servidores onde está o bot
        for guild in bot.guilds:
            # Verifica se o usuário está nesse servidor
            member = guild.get_member(int(discord_id))
            if not member:
                continue
            
            # Busca canal de live games configurado
            channel_id = db.get_live_game_channel(str(guild.id))
            if not channel_id:
                continue
            
            # Busca o canal
            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue
            
            # Determina cor baseada no modo de jogo
            queue_id = live_info.get('queueId', 0)
            if queue_id == 440:  # Ranked Flex
                color = discord.Color.gold()
            elif queue_id == 420:  # Ranked Solo/Duo
                color = discord.Color.purple()
            else:
                color = discord.Color.blue()
            
            # Cria embed
            embed = discord.Embed(
                title="🔴 PARTIDA AO VIVO!",
                description=f"{member.mention} **entrou em partida!**",
                color=color,
                timestamp=datetime.now()
            )
            
            # Informações principais
            embed.add_field(
                name="🎮 Modo de Jogo",
                value=f"**{live_info['gameMode']}**",
                inline=True
            )
            
            embed.add_field(
                name="🏆 Campeão",
                value=f"**{live_info['champion']}**",
                inline=True
            )
            
            # Calcula tempo de jogo
            game_length = live_info.get('gameLength', 0)
            game_time_min = game_length // 60
            game_time_sec = game_length % 60
            
            embed.add_field(
                name="⏱️ Tempo de Jogo",
                value=f"**{game_time_min}:{game_time_sec:02d}**",
                inline=True
            )
            
            # Composições de time
            team_100 = live_info.get('team_100', [])
            team_200 = live_info.get('team_200', [])
            
            if team_100:
                team_100_text = "\n".join([f"• **{p['champion']}** - {p['summonerName']}" for p in team_100[:5]])
                embed.add_field(
                    name="🔵 Time Azul",
                    value=team_100_text,
                    inline=True
                )
            
            if team_200:
                team_200_text = "\n".join([f"• **{p['champion']}** - {p['summonerName']}" for p in team_200[:5]])
                embed.add_field(
                    name="🔴 Time Vermelho",
                    value=team_200_text,
                    inline=True
                )
            
            # Links úteis
            region_map = {
                'br1': 'br', 'na1': 'na', 'euw1': 'euw', 'eun1': 'eune',
                'kr': 'kr', 'jp1': 'jp', 'la1': 'lan', 'la2': 'las',
                'oc1': 'oce', 'tr1': 'tr', 'ru': 'ru'
            }
            region_short = region_map.get(region.lower(), region.lower())
            
            # Remove #TAG do summoner name para os links
            summoner_clean = summoner_name.split('#')[0] if '#' in summoner_name else summoner_name
            
            links = f"""
[OP.GG](https://www.op.gg/summoners/{region_short}/{summoner_clean}) • 
[U.GG](https://u.gg/lol/profile/{region_short}/{summoner_clean}/overview) • 
[Porofessor](https://porofessor.gg/live/{region_short}/{summoner_clean})
            """
            
            embed.add_field(
                name="📊 Live Trackers",
                value=links.strip(),
                inline=False
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(
                text=f"{summoner_name} • {region.upper()}",
                icon_url="https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/ranked-emblem-flex.png"
            )
            
            # Envia notificação
            try:
                await channel.send(embed=embed)
                print(f"🔴 Live game: {summoner_name} - {live_info['champion']} ({live_info['gameMode']})")
            except Exception as e:
                print(f"Erro ao enviar notificação de live game: {e}")
    
    except Exception as e:
        print(f"Erro ao processar notificação de live game: {e}")

@tasks.loop(minutes=2)
async def check_live_games():
    """Task que verifica se jogadores estão em partidas ao vivo a cada 2 minutos"""
    try:
        # Limpa notificações antigas (mais de 6 horas)
        db.cleanup_old_live_game_notifications(hours=6)
        
        # Busca todas as contas vinculadas
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, puuid, region FROM lol_accounts')
        accounts = cursor.fetchall()
        conn.close()
        
        for account_id, puuid, region in accounts:
            try:
                # Busca se está em partida ativa
                game_data = await riot_api.get_active_game(puuid, region)
                
                if game_data:
                    game_id = str(game_data.get('gameId'))
                    
                    # Verifica se já foi notificado
                    if not db.is_live_game_notified(account_id, game_id):
                        # Extrai informações
                        live_info = riot_api.extract_live_game_info(game_data, puuid)
                        
                        if live_info:
                            # Envia notificação
                            await send_live_game_notification(account_id, live_info)
                            
                            # Marca como notificado
                            db.mark_live_game_notified(account_id, game_id)
                
                # Delay para não sobrecarregar a API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Erro ao verificar live game para conta {account_id}: {e}")
                continue
    
    except Exception as e:
        print(f"Erro ao verificar live games: {e}")

@check_live_games.before_loop
async def before_check_live_games():
    """Espera o bot estar pronto antes de iniciar o loop de live games"""
    await bot.wait_until_ready()

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
    try:
        error_message = ""
        
        if isinstance(error, app_commands.CommandOnCooldown):
            error_message = f"⏰ Aguarde {error.retry_after:.1f} segundos antes de usar este comando novamente."
        elif isinstance(error, app_commands.MissingPermissions):
            error_message = "❌ Você não tem permissão para usar este comando."
        elif isinstance(error, app_commands.CommandInvokeError):
            error_message = "❌ Ocorreu um erro ao executar o comando. Tente novamente."
            print(f"Erro no comando: {error.original}")
        else:
            error_message = f"❌ Ocorreu um erro: {str(error)}"
            print(f"Erro no comando: {error}")
        
        # Verifica se a interação já foi respondida
        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)
    except Exception as e:
        print(f"Erro no error handler: {e}")

if __name__ == "__main__":
    if not TOKEN or not RIOT_API_KEY:
        print("❌ ERRO: Configure as variáveis DISCORD_TOKEN e RIOT_API_KEY no arquivo .env")
        print("Veja o arquivo .env.example para mais informações")
    else:
        bot.run(TOKEN)

