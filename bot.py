import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from database import Database
from riot_api import RiotAPI
from datetime import datetime
from typing import Dict, List
import asyncio
import json

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')
DEFAULT_REGION = os.getenv('DEFAULT_REGION', 'br1')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
db = Database()
riot_api = RiotAPI(RIOT_API_KEY)

async def check_command_channel(interaction: discord.Interaction) -> bool:
    """
    Verifica se o comando pode ser executado no canal atual.
    Admins podem usar em qualquer lugar.
    Se não houver canal configurado, qualquer um pode usar em qualquer lugar.
    Se houver canal configurado, usuários comuns só podem usar lá.
    Retorna True se pode executar, False caso contrário.
    """
    if interaction.user.guild_permissions.administrator:
        return True
    
    guild_id = str(interaction.guild_id)
    command_channel_id = db.get_command_channel(guild_id)

    if not command_channel_id:
        return True

    if str(interaction.channel_id) != command_channel_id:
        await interaction.response.send_message(
            f"❌ **Canal incorreto!**\n"
            f"Use comandos apenas em <#{command_channel_id}>",
            ephemeral=True
        )
        return False
    
    return True

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
                "`/perfil` - Ver perfil completo com pintados de ouro\n"
                "`/media` - Ver estatísticas (por campeão, métrica, outro jogador)\n"
                "`/historico` - Ver histórico de partidas\n"
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
                "`/configurar score #canal` - Canal de score (avaliações)\n"
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
    
    @discord.ui.button(label="🏆 Sistema de MVP Score", style=discord.ButtonStyle.secondary, custom_id="flex_guide:score")
    async def score_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏆 Sistema de MVP Score",
            description="Entenda como funciona o sistema de pontuação:",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="📈 O que é MVP Score?",
            value=(
                "É uma pontuação de **0 a 100** que compara sua performance com **TODOS os 10 jogadores** da partida.\n"
                "Sistema estilo **OP.GG/U.GG** - baseado na sua posição no ranking da partida!\n"
                "⚠️ **Justo e balanceado**: pesos ajustados por role (suporte foca em visão/KP, carry em dano/gold)"
            ),
            inline=False
        )
        embed.add_field(
            name="📊 Fatores Analisados por Role",
            value=(
                "**Top**: KDA + Dano + Tank (absorver dano)\n"
                "**Mid**: KDA + Dano + Farm\n"
                "**Jungle**: KDA + Objetivos + Utility (Tank/CC/Peel) + CS\n"
                "**ADC**: Dano + Farm + Gold\n"
                "**Support**: KDA + Visão + Utility (CC/Heal/Shield/Tank) + Dano\n"
                "• **Bônus** de +4% por vitória\n"
                "• **Penalidades** por muitas mortes ou baixa participação"
            ),
            inline=False
        )
        embed.add_field(
            name="🎯 Rankings (Sistema Punitivo)",
            value=(
                "🏆 **95-100**: S+\n"
                "⭐ **90-80**: S\n"
                "💎 **80-70**: A\n"
                "🥈 **70-60**: B\n"
                "📊 **60-50**: C\n"
                "📉 **50-20**: D\n"
                "💀 **20-0**: F"
            ),
            inline=False
        )
        embed.add_field(
            name="💡 Pesos por Role (Sistema Específico)",
            value=(
                "**Top**: 30% KDA + 18% Dano + 11% Gold + 10% CS + 8.25% Objetivos + 8.25% Tank + 7.5% KP + 7% Visão\n"
                "**Mid**: 35% KDA + 15% Gold + 15% Dano + 13% CS + 9% KP + 7% Visão + 6% Obj\n"
                "**Jungle**: 35% KDA + 15% Objetivos + 10% CS + 10% KP + 9% Dano + 9% Utility + 7% Visão + 5% Gold\n"
                "**ADC**: 35% KDA + 20% Dano + 15% Gold + 12% CS + 8% KP + 7% Visão + 3% Obj\n"
                "**Support**: 35% KDA + 25% Visão + 15% Utility + 15% KP + 10% Dano"
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
                "E tiver **MVP Score < 45** nas 3 partidas,\n"
                "O bot enviará um alerta com sugestões!"
            ),
            inline=False
        )
        embed.add_field(
            name="🎮 Notificação de Partidas (Live Tracking Unificado)",
            value=(
                "**Sistema em tempo real:**\n"
                "🔵 Quando você **entra em partida** → Notificação AZUL\n"
                "🟢 Quando você **ganha** → Atualiza para VERDE\n"
                "🔴 Quando você **perde** → Atualiza para VERMELHO\n\n"
                "A mesma mensagem é atualizada do início ao fim!\n"
                "Mostra MVP Score, KDA e links para trackers."
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
    
    bot.add_view(FlexGuideView())
    print('✅ Views persistentes registradas')

    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)} comandos sincronizados')
    except Exception as e:
        print(f'Erro ao sincronizar comandos: {e}')
    
    if not check_new_matches.is_running():
        check_new_matches.start()
        print('✅ Task de verificação de partidas iniciada')
    else:
        print('⚠️ Task de verificação de partidas já está rodando')
    
    # Inicia verificação de live games (verifica se já não está rodando)
    if not check_live_games.is_running():
        check_live_games.start()
        print('✅ Task de verificação de live games iniciada (a cada 3 minutos)')
    else:
        print('⚠️ Task de verificação de live games já está rodando')

    # Inicia verificação de partidas finalizadas
    if not check_live_games_finished.is_running():
        check_live_games_finished.start()
        print('✅ Task de verificação de partidas finalizadas iniciada (a cada 60s)')
    else:
        print('⚠️ Task de verificação de partidas finalizadas já está rodando')

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
    if not await check_command_channel(interaction):
        return
    
    await interaction.response.defer(ephemeral=True)
    
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
    
    account = await riot_api.get_account_by_riot_id(game_name, tag_line, regiao)
    
    if not account:
        await interaction.followup.send(
            f"❌ Conta '{riot_id}' não encontrada.\n"
            f"Verifique se o nome e tag estão corretos!",
            ephemeral=True
        )
        return
    
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
    
    if 'id' not in summoner or 'accountId' not in summoner:
        print(f"⚠️ API retornou summoner sem id/accountId. Usando PUUID como fallback.")
        print(f"Summoner data: {summoner}")
    
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
        accounts = db.get_user_accounts(discord_id)
        new_account = None
        for acc in accounts:
            if acc['puuid'] == account['puuid']:
                new_account = acc
                break
        
        # Marca partidas antigas como já vistas para não enviar notificações
        if new_account:
            try:
                # Busca última partida sem processar (só para marcar como vista)
                match_ids = await riot_api.get_match_history(account['puuid'], regiao, count=5)
                if match_ids and len(match_ids) > 0:
                    # Procura a primeira partida de Ranked Flex
                    for match_id in match_ids:
                        match_data = await riot_api.get_match_details(match_id, regiao)
                        if match_data:
                            queue_id = match_data.get('info', {}).get('queueId', 0)
                            if queue_id == 440:
                                # Extrai stats mas NÃO envia notificações
                                stats = riot_api.extract_player_stats(match_data, account['puuid'])
                                if stats:
                                    # Salva silenciosamente para marcar como última partida vista
                                    db.add_match(new_account['id'], stats)
                                    print(f"✅ Última partida marcada para {game_name}#{tag_line} (sem notificar histórico)")
                                    break
            except Exception as e:
                print(f"⚠️ Erro ao marcar última partida: {e}")
                # Não interrompe o fluxo se houver erro
        
        embed = discord.Embed(
            title="✅ Conta Vinculada!",
            description=f"Conta **{game_name}#{tag_line}** vinculada com sucesso!",
            color=discord.Color.green()
        )
        embed.add_field(name="🌍 Região", value=regiao.upper(), inline=True)
        embed.add_field(name="⭐ Nível", value=summoner_level, inline=True)
        
        # Mostra quantas contas o usuário tem
        embed.add_field(
            name="📊 Contas Vinculadas", 
            value=f"{len(accounts)}/3", 
            inline=True
        )
        
        embed.set_footer(text="O bot começará a monitorar apenas suas PRÓXIMAS partidas de Flex!")
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(f"❌ {message}", ephemeral=True)

@bot.tree.command(name="contas", description="📋 Veja todas as suas contas vinculadas")
async def contas(interaction: discord.Interaction):
    """Lista todas as contas vinculadas do usuário"""
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

@bot.tree.command(name="champban", description="🚫 Veja todos os campeões banidos do servidor")
async def champban(interaction: discord.Interaction):
    """Mostra todos os campeões banidos de todos os jogadores do servidor"""
    if not await check_command_channel(interaction):
        return
    
    await interaction.response.defer()
    
    guild_id = str(interaction.guild.id)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT discord_id FROM lol_accounts
    ''')
    all_discord_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    server_bans = []
    for discord_id in all_discord_ids:
        member = interaction.guild.get_member(int(discord_id))
        if not member:
            continue
        
        accounts = db.get_user_accounts(discord_id)
        for account in accounts:
            bans = db.get_active_champion_bans(account['id'])
            for ban in bans:
                ban['discord_user'] = member
                ban['account_name'] = account['summoner_name']
                server_bans.append(ban)
    
    if not server_bans:
        embed = discord.Embed(
            title="✅ Nenhum Campeão Banido",
            description="Nenhum jogador do servidor tem campeões banidos no momento!\n\nParabéns a todos! 🎮",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)
        return
    
    embed = discord.Embed(
        title="🚫 Campeões Banidos do Servidor",
        description=f"Total: **{len(server_bans)}** banimento(s) ativo(s)",
        color=discord.Color.red()
    )
    
    from datetime import datetime
    now = datetime.now()
    
    for ban in server_bans:
        expires_at = datetime.fromisoformat(ban['expires_at'])
        time_left = expires_at - now
        
        days_left = time_left.days
        hours_left = time_left.seconds // 3600
        minutes_left = (time_left.seconds % 3600) // 60
        
        if days_left > 0:
            time_str = f"{days_left}d {hours_left}h"
        elif hours_left > 0:
            time_str = f"{hours_left}h {minutes_left}m"
        else:
            time_str = f"{minutes_left}m"
        
        if ban['ban_level'] == 1:
            level_emoji = "⚠️"
            level_text = "Nível 1"
        elif ban['ban_level'] == 2:
            level_emoji = "🚨"
            level_text = "Nível 2"
        else:
            level_emoji = "🔴"
            level_text = "Nível 3"
        
        embed.add_field(
            name=f"{level_emoji} {ban['champion_name']} - {ban['discord_user'].display_name}",
            value=(
                f"**Conta:** {ban['account_name']}\n"
                f"**{level_text}** ({ban['ban_days']} dias) | ⏱️ {time_str}\n"
                f"📋 {ban['reason']}"
            ),
            inline=True
        )
    
    embed.set_footer(text=f"Sistema de Banimento Progressivo • {interaction.guild.name}")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="champban_remove", description="🔓 [ADMIN] Remove banimento de campeão de um jogador")
@app_commands.describe(
    usuario="Usuário Discord para remover o banimento",
    campeao="Nome do campeão para desbanir (deixe vazio para remover todos)"
)
@app_commands.checks.has_permissions(administrator=True)
async def champban_remove(interaction: discord.Interaction, usuario: discord.Member, campeao: str = None):
    """[ADMIN] Remove banimento de campeão de um jogador específico"""
    if not await check_command_channel(interaction):
        return
    
    await interaction.response.defer(ephemeral=True)
    
    discord_id = str(usuario.id)
    accounts = db.get_user_accounts(discord_id)
    
    if not accounts:
        await interaction.followup.send(
            f"❌ {usuario.mention} não tem nenhuma conta vinculada!",
            ephemeral=True
        )
        return
    
    # Se campeão não foi especificado, remove todos os banimentos
    if not campeao:
        total_removed = 0
        for account in accounts:
            removed = db.remove_all_champion_bans(account['id'])
            total_removed += removed
        
        if total_removed > 0:
            embed = discord.Embed(
                title="✅ Banimentos Removidos",
                description=f"Todos os banimentos de {usuario.mention} foram removidos!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="📊 Total",
                value=f"**{total_removed}** banimento(s) removido(s)",
                inline=False
            )
            embed.set_footer(text=f"Removido por {interaction.user.name}")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(
                f"ℹ️ {usuario.mention} não tinha nenhum banimento ativo.",
                ephemeral=True
            )
        return
    
    # Remove banimento de campeão específico
    removed = False
    for account in accounts:
        if db.remove_champion_ban(account['id'], campeao):
            removed = True
    
    if removed:
        embed = discord.Embed(
            title="✅ Banimento Removido",
            description=f"O banimento de **{campeao}** foi removido para {usuario.mention}!",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Removido por {interaction.user.name}")
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Log no console
        print(f"🔓 [ADMIN] {interaction.user.name} removeu banimento de {campeao} de {usuario.name}")
    else:
        await interaction.followup.send(
            f"ℹ️ {usuario.mention} não tinha banimento ativo de **{campeao}**.",
            ephemeral=True
        )

@champban_remove.error
async def champban_remove_error(interaction: discord.Interaction, error):
    """Tratamento de erro para comando champban_remove"""
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "❌ Você precisa ser **Administrador** para usar este comando!",
            ephemeral=True
        )


async def champion_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Auto-complete para campeões jogados pelo usuário"""
    discord_id = str(interaction.user.id)
    accounts = db.get_user_accounts(discord_id)
    
    if not accounts:
        return []
    
    # Busca todos os campeões jogados este mês
    now = datetime.now()
    all_champions = set()
    for account in accounts:
        champions = db.get_all_champions_played(account['id'], now.year, now.month)
        all_champions.update(champions)
    
    # Filtra por texto digitado
    filtered = [champ for champ in sorted(all_champions) if current.lower() in champ.lower()]
    
    return [
        app_commands.Choice(name=champ, value=champ)
        for champ in filtered[:25]  # Discord limita a 25
    ]

# Auto-complete para métricas
async def metric_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Auto-complete para métricas disponíveis"""
    metrics = [
        ('🏆 MVP Score', 'mvp'),
        ('⚔️ KDA', 'kda'),
        ('🗡️ Dano aos Campeões', 'dano'),
        ('🌾 CS (Farm)', 'cs'),
        ('👁️ Vision Score', 'visao'),
        ('🎯 Kill Participation', 'kp'),
        ('💰 Gold por Minuto', 'gold'),
        ('📊 Todas as Métricas', 'todas'),
    ]
    
    return [
        app_commands.Choice(name=name, value=value)
        for name, value in metrics
        if current.lower() in name.lower() or current.lower() in value.lower()
    ]

@bot.tree.command(name="media", description="📊 Veja estatísticas detalhadas de desempenho no Flex")
@app_commands.describe(
    campeao="Filtrar por campeão específico (deixe vazio para ver todos)",
    metrica="Métrica específica para analisar (mvp, kda, dano, cs, visao, kp, gold)",
    usuario="Ver estatísticas de outro jogador (mencione ou digite o nome)",
    conta="Número da conta (1, 2 ou 3). Deixe vazio para ver todas"
)
@app_commands.autocomplete(campeao=champion_autocomplete, metrica=metric_autocomplete)
async def media(interaction: discord.Interaction, campeao: str = None, metrica: str = None, 
                usuario: discord.User = None, conta: int = None):
    """Calcula estatísticas e média de desempenho do mês atual"""
    if not await check_command_channel(interaction):
        return
    
    await interaction.response.defer()
    
    # Define qual usuário buscar
    target_user = usuario if usuario else interaction.user
    discord_id = str(target_user.id)
    accounts = db.get_user_accounts(discord_id)
    
    if not accounts:
        if usuario:
            await interaction.followup.send(
                f"❌ {target_user.mention} não tem nenhuma conta vinculada ao bot."
            )
        else:
            await interaction.followup.send(
                "❌ Você não tem nenhuma conta vinculada. Use `/logar` para vincular uma conta!"
            )
        return
    
    # Se especificou uma conta, valida
    if conta is not None:
        if conta < 1 or conta > len(accounts):
            await interaction.followup.send(
                f"❌ Conta inválida! {'Esse usuário tem' if usuario else 'Você tem'} {len(accounts)} conta(s) vinculada(s)."
            )
            return
        accounts = [accounts[conta - 1]]
    
    # Pega mês e ano atual
    now = datetime.now()
    month = now.month
    year = now.year
    
    # Define título do embed baseado nos filtros
    title_parts = ["📊 Estatísticas"]
    if campeao:
        title_parts.append(f"- {campeao}")
    if metrica and metrica != 'todas':
        metric_names = {
            'mvp': 'MVP Score',
            'kda': 'KDA',
            'dano': 'Dano',
            'cs': 'CS',
            'visao': 'Visão',
            'kp': 'Kill Participation',
            'gold': 'Gold'
        }
        title_parts.append(f"- {metric_names.get(metrica, metrica.upper())}")
    title_parts.append(f"- {now.strftime('%B/%Y')}")
    
    embed = discord.Embed(
        title=" ".join(title_parts),
        color=discord.Color.gold()
    )
    
    if usuario:
        embed.set_author(name=f"Estatísticas de {target_user.display_name}", icon_url=target_user.display_avatar.url)
    
    for account in accounts:
        # Busca partidas (filtradas por campeão se especificado, excluindo remakes)
        if campeao:
            matches = db.get_monthly_matches_by_champion(account['id'], year, month, campeao)
        else:
            matches = db.get_monthly_matches(account['id'], year, month, include_remakes=False)
        
        if not matches:
            msg = f"Nenhuma partida de Flex"
            if campeao:
                msg += f" com **{campeao}**"
            msg += " registrada este mês."
            embed.add_field(
                name=f"⚠️ {account['summoner_name']}",
                value=msg,
                inline=False
            )
            continue
        
        # Calcula estatísticas
        total_matches = len(matches)
        avg_mvp = sum(m.get('mvp_score', 0) for m in matches) / total_matches
        wins = sum(1 for m in matches if m['win'])
        win_rate = (wins / total_matches) * 100
        
        avg_kills = sum(m['kills'] for m in matches) / total_matches
        avg_deaths = sum(m['deaths'] for m in matches) / total_matches
        avg_assists = sum(m['assists'] for m in matches) / total_matches
        avg_kda_calc = (avg_kills + avg_assists) / max(avg_deaths, 1)
        avg_kp = sum(m['kill_participation'] for m in matches) / total_matches
        avg_dano = sum(m['damage_dealt'] for m in matches) / total_matches
        avg_cs = sum(m['cs'] for m in matches) / total_matches
        avg_visao = sum(m['vision_score'] for m in matches) / total_matches
        avg_gold = sum(m['gold_earned'] for m in matches) / total_matches
        
        # Calcula gold per minute médio
        avg_game_duration_min = sum(m['game_duration'] for m in matches) / total_matches / 60
        avg_gpm = avg_gold / avg_game_duration_min if avg_game_duration_min > 0 else 0
        
        # Estatísticas por role
        role_count = {}
        for m in matches:
            role = m['role']
            role_count[role] = role_count.get(role, 0) + 1
        most_played_role = max(role_count, key=role_count.get) if role_count else "Unknown"
        
        # Determina emoji baseado no MVP score
        if avg_mvp >= 90:
            emoji = "🏆"
            rank = "S+"
        elif avg_mvp >= 75:
            emoji = "⭐"
            rank = "S"
        elif avg_mvp >= 60:
            emoji = "💎"
            rank = "A"
        elif avg_mvp >= 50:
            emoji = "🥈"
            rank = "B"
        elif avg_mvp >= 40:
            emoji = "📊"
            rank = "C"
        elif avg_mvp >= 25:
            emoji = "📉"
            rank = "D"
        else:
            emoji = "💀"
            rank = "F"
        
        # Emoji por role
        role_emojis = {
            'Top': '⚔️',
            'Jungle': '🌳',
            'Mid': '✨',
            'ADC': '🏹',
            'Support': '🛡️'
        }
        role_emoji = role_emojis.get(most_played_role, '❓')
        
        # Constrói texto baseado na métrica selecionada
        if metrica in ['mvp'] or not metrica:
            stats_text = f"""
{emoji} **{rank}**
📈 MVP Score Médio: **{int(avg_mvp)}/100**
🎮 Partidas: **{total_matches}** • ✅ WR: **{win_rate:.1f}%**
⚔️ KDA: **{avg_kda_calc:.2f}** ({avg_kills:.1f}/{avg_deaths:.1f}/{avg_assists:.1f})
🎯 Kill Participation: **{avg_kp:.1f}%**
{role_emoji} Role Mais Jogada: **{most_played_role}** ({role_count[most_played_role]}x)
            """
        elif metrica == 'kda':
            stats_text = f"""
⚔️ **Análise de KDA**
📈 KDA Médio: **{avg_kda_calc:.2f}**
💀 K/D/A: **{avg_kills:.1f}** / **{avg_deaths:.1f}** / **{avg_assists:.1f}**
🎯 Kill Participation: **{avg_kp:.1f}%**
🎮 Partidas: **{total_matches}** • ✅ WR: **{win_rate:.1f}%**
{emoji} MVP Score: **{int(avg_mvp)}/100**
            """
        elif metrica == 'dano':
            stats_text = f"""
🗡️ **Análise de Dano**
💥 Dano Médio aos Campeões: **{int(avg_dano):,}**
📊 Dano por Partida: **{int(avg_dano):,}**
🎮 Partidas: **{total_matches}** • ✅ WR: **{win_rate:.1f}%**
⚔️ KDA: **{avg_kda_calc:.2f}**
{emoji} MVP Score: **{int(avg_mvp)}/100**
            """
        elif metrica == 'cs':
            avg_cspm = avg_cs / avg_game_duration_min if avg_game_duration_min > 0 else 0
            stats_text = f"""
🌾 **Análise de Farm (CS)**
📊 CS Médio por Partida: **{int(avg_cs)}**
⏱️ CS por Minuto: **{avg_cspm:.1f}**
💰 Gold Médio: **{int(avg_gold):,}**
🎮 Partidas: **{total_matches}** • ✅ WR: **{win_rate:.1f}%**
{emoji} MVP Score: **{int(avg_mvp)}/100**
            """
        elif metrica == 'visao':
            avg_vision_pm = avg_visao / avg_game_duration_min if avg_game_duration_min > 0 else 0
            stats_text = f"""
👁️ **Análise de Visão**
📊 Vision Score Médio: **{int(avg_visao)}**
⏱️ Vision Score por Minuto: **{avg_vision_pm:.2f}**
🎮 Partidas: **{total_matches}** • ✅ WR: **{win_rate:.1f}%**
⚔️ KDA: **{avg_kda_calc:.2f}**
{emoji} MVP Score: **{int(avg_mvp)}/100**
            """
        elif metrica == 'kp':
            stats_text = f"""
🎯 **Análise de Kill Participation**
📊 KP Médio: **{avg_kp:.1f}%**
💀 Kills: **{avg_kills:.1f}** • Assists: **{avg_assists:.1f}**
🎮 Partidas: **{total_matches}** • ✅ WR: **{win_rate:.1f}%**
⚔️ KDA: **{avg_kda_calc:.2f}**
{emoji} MVP Score: **{int(avg_mvp)}/100**
            """
        elif metrica == 'gold':
            stats_text = f"""
💰 **Análise de Gold**
📊 Gold Médio por Partida: **{int(avg_gold):,}**
⏱️ Gold por Minuto (GPM): **{int(avg_gpm)}**
🌾 CS Médio: **{int(avg_cs)}**
🎮 Partidas: **{total_matches}** • ✅ WR: **{win_rate:.1f}%**
{emoji} MVP Score: **{int(avg_mvp)}/100**
            """
        else:  # metrica == 'todas'
            avg_cspm = avg_cs / avg_game_duration_min if avg_game_duration_min > 0 else 0
            stats_text = f"""
{emoji} **{rank}** - MVP Score: **{int(avg_mvp)}/100**
🎮 **{total_matches}** partidas • ✅ **{win_rate:.1f}%** WR

**⚔️ Combate:**
• KDA: **{avg_kda_calc:.2f}** ({avg_kills:.1f}/{avg_deaths:.1f}/{avg_assists:.1f})
• KP: **{avg_kp:.1f}%** • Dano: **{int(avg_dano):,}**

**💰 Economia:**
• CS: **{int(avg_cs)}** ({avg_cspm:.1f}/min)
• Gold: **{int(avg_gold):,}** ({int(avg_gpm)} GPM)

**🎯 Utility:**
• Vision Score: **{int(avg_visao)}**
• {role_emoji} Role: **{most_played_role}** ({role_count[most_played_role]}x)
            """
        
        # Nome do campo
        field_name = f"🎯 {account['summoner_name']} ({account['region'].upper()})"
        if campeao:
            field_name += f" - {campeao}"
        
        embed.add_field(
            name=field_name,
            value=stats_text.strip(),
            inline=False
        )
    
    footer_text = "Apenas partidas de Ranked Flex são contabilizadas"
    if campeao:
        footer_text += f" • Filtrado por {campeao}"
    embed.set_footer(text=footer_text)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="historico", description="📜 Veja seu histórico detalhado de partidas por data")
@app_commands.describe(
    data="Data para ver partidas (formato: DD/MM/AAAA ou DD/MM). Padrão: hoje",
    conta="Número da conta (1, 2 ou 3). Se não informar, mostra todas as contas"
)
async def historico(interaction: discord.Interaction, data: str = None, conta: int = None):
    """Mostra histórico detalhado de partidas por data"""
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
    
    # Processa a data
    now = datetime.now()
    if data:
        try:
            # Tenta formato DD/MM/AAAA
            if len(data.split('/')) == 3:
                day, month, year = data.split('/')
                date_obj = datetime(int(year), int(month), int(day))
            # Tenta formato DD/MM (usa ano atual)
            elif len(data.split('/')) == 2:
                day, month = data.split('/')
                date_obj = datetime(now.year, int(month), int(day))
            else:
                await interaction.followup.send("❌ Formato de data inválido! Use DD/MM/AAAA ou DD/MM")
                return
        except ValueError:
            await interaction.followup.send("❌ Data inválida! Use DD/MM/AAAA ou DD/MM")
            return
    else:
        date_obj = now
    
    date_str = date_obj.strftime('%Y-%m-%d')
    date_display = date_obj.strftime('%d/%m/%Y')
    
    # Busca partidas
    if conta:
        if conta < 1 or conta > len(accounts):
            await interaction.followup.send(
                f"❌ Conta inválida! Você tem {len(accounts)} conta(s) vinculada(s)."
            )
            return
        account = accounts[conta - 1]
        matches = db.get_matches_by_date(account['id'], date_str)
        title_suffix = f" - {account['summoner_name']}"
    else:
        # Busca de todas as contas
        matches = db.get_all_matches_by_date(discord_id, date_str)
        title_suffix = ""
    
    if not matches:
        await interaction.followup.send(
            f"❌ Nenhuma partida encontrada em **{date_display}**{title_suffix}."
        )
        return
    
    # Título do embed
    if conta:
        embed_title = f"📜 Histórico - {account['summoner_name']}"
    else:
        embed_title = f"📜 Histórico - {interaction.user.display_name}"
    
    embed = discord.Embed(
        title=embed_title,
        description=f"**{len(matches)} partida(s) em {date_display}**\n_ _",
        color=discord.Color.purple()
    )
    
    for i, match in enumerate(matches, 1):
        is_remake = match.get('is_remake', False)
        summoner_info = f" ({match['summoner_name']})" if not conta and 'summoner_name' in match else ""
        
        if is_remake:
            # Layout especial para remakes
            role_emojis = {
                'Top': '⚔️',
                'Jungle': '🌳',
                'Mid': '✨',
                'ADC': '🏹',
                'Support': '🛡️'
            }
            role_emoji = role_emojis.get(match['role'], '❓')
            
            game_duration_min = match['game_duration'] // 60
            game_duration_sec = match['game_duration'] % 60
            
            match_info = f"""
**{match['champion_name']}** {role_emoji} {match['role']}{summoner_info}
━━━━━━━━━━━━━━━━━━━━━
⚠️ **REMAKE** - Partida cancelada
⏱️ Duração: **{game_duration_min}:{game_duration_sec:02d}**
📅 {match['played_at'][11:16]}

_Esta partida não conta para estatísticas_
            """
        else:
            # Layout normal para partidas completas
            result = "✅ Vitória" if match['win'] else "❌ Derrota"
            kda_ratio = f"{match['kills']}/{match['deaths']}/{match['assists']}"
            
            # Emoji do MVP score
            mvp_score = match.get('mvp_score', 0)
            if mvp_score >= 90:
                mvp_emoji = "🏆"
                rank_text = "S+"
            elif mvp_score >= 75:
                mvp_emoji = "⭐"
                rank_text = "S"
            elif mvp_score >= 60:
                mvp_emoji = "💎"
                rank_text = "A"
            elif mvp_score >= 50:
                mvp_emoji = "🥈"
                rank_text = "B"
            elif mvp_score >= 40:
                mvp_emoji = "📊"
                rank_text = "C"
            elif mvp_score >= 25:
                mvp_emoji = "📉"
                rank_text = "D"
            else:
                mvp_emoji = "💀"
                rank_text = "F"
            
         
            role_emojis = {
                'Top': '⚔️',
                'Jungle': '🌳',
                'Mid': '✨',
                'ADC': '🏹',
                'Support': '🛡️'
            }
            role_emoji = role_emojis.get(match['role'], '❓')
            
            match_info = f"""
**{match['champion_name']}** {role_emoji} {match['role']} • {result}{summoner_info}
━━━━━━━━━━━━━━━━━━━━━
{mvp_emoji} **MVP Score: {mvp_score}/100** ({rank_text})
⚔️ KDA: **{kda_ratio}** ({match['kda']:.2f})
🎯 Kill Participation: **{match['kill_participation']:.0f}%**
🗡️ Dano: **{match['damage_dealt']:,}**
🌾 CS: **{match['cs']}** • 👁️ Vision: **{match['vision_score']}**
📅 {match['played_at'][11:16]}
            """
        
        embed.add_field(
            name=f"━━━━━━━━━━━━━ Partida #{i} ━━━━━━━━━━━━━",
            value=match_info.strip(),
            inline=False
        )
    
    embed.set_footer(text=f"📊 Apenas Ranked Flex • {date_display}")
    await interaction.followup.send(embed=embed)

# Auto-complete para tipo de configuração
async def config_type_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Auto-complete para tipos de configuração"""
    types = [
        ('🔔 Alertas - Notificações de performance', 'alertas'),
        ('📊 Score - Avaliações individuais (MVP)', 'score'),
        ('💬 Comandos - Canal onde usuários podem usar comandos', 'comandos'),
        ('🔴 Live - Notificações de partidas ao vivo', 'live'),
        ('🗳️ Votação - Canal para votação de MVP após partida', 'votacao'),
    ]
    return [
        app_commands.Choice(name=name, value=value)
        for name, value in types
        if current.lower() in name.lower() or current.lower() in value.lower()
    ]

@bot.tree.command(name="configurar", description="⚙️ [ADMIN] Configure os canais do bot ou veja a configuração atual")
@app_commands.describe(
    tipo="Tipo de configuração: alertas, score, comandos ou live (deixe vazio para ver config atual)",
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
                    name="📊 Canal de Score",
                    value=f"<#{config['match_channel_id']}>\nNotificações individuais com MVP Score de cada jogador",
                    inline=False
                )
            else:
                embed.add_field(
                    name="📊 Canal de Score",
                    value="❌ Não configurado",
                    inline=False
                )
            
            if config['live_game_channel_id']:
                embed.add_field(
                    name="🔴 Canal de Live Games",
                    value=f"<#{config['live_game_channel_id']}>\n🔴 Notificação ao vivo → 🏁 Editada com resultado final (KDA + CS + Dano de todos)",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🔴 Canal de Live Games",
                    value="❌ Não configurado",
                    inline=False
                )
            
            if config.get('voting_channel_id'):
                embed.add_field(
                    name="🗳️ Canal de Votação",
                    value=f"<#{config['voting_channel_id']}>\nVotação de MVP após partida (Carry Score)",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🗳️ Canal de Votação",
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
    
    if tipo not in ['alertas', 'score', 'comandos', 'live', 'votacao']:
        await interaction.followup.send(
            "❌ Tipo inválido! Use: `alertas`, `score`, `comandos`, `live` ou `votacao`",
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
                    "• E tiver **MVP Score abaixo de 45** nas 3 partidas\n"
                    "• Será enviada uma notificação com sugestões"
                ),
                inline=False
            )
        else:
            await interaction.followup.send("❌ Erro ao configurar canal.", ephemeral=True)
            return
    
    elif tipo == 'score':
        success = db.set_match_channel(guild_id, channel_id)
        if success:
            embed = discord.Embed(
                title="✅ Canal de Score Configurado!",
                description=f"Notificações de score individuais serão enviadas em {canal.mention}",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="📊 O que será enviado?",
                value=(
                    "**Quando a partida termina:**\n"
                    "• ✅/❌ **Resultado** (Vitória/Derrota)\n"
                    "• 📊 **MVP Score** (comparado com os 10 jogadores)\n"
                    "• 👑 **MVP Score** (colocação entre 10 jogadores)\n"
                    "• ⚔️ **KDA**, 🗡️ **Dano**, 🌾 **CS**, 👁️ **Vision**\n"
                    "• 🏆 **Campeão** e **Role**\n\n"
                    "**CADA jogador** recebe sua notificação individual\n"
                    "com análise detalhada da performance!"
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
    
    elif tipo == 'live':
        success = db.set_live_game_channel(guild_id, channel_id)
        if success:
            embed = discord.Embed(
                title="✅ Canal de Live Games Configurado!",
                description=f"Notificações de live games serão enviadas em {canal.mention}",
                color=discord.Color.red()
            )
            embed.add_field(
                name="🔴 Como funciona?",
                value=(
                    "**Sistema de Live Games:**\n"
                    "• 🔴 **Partida começa**: Notificação mostrando quem entrou em partida\n"
                    "• 🏁 **Partida termina**: Mensagem EDITADA mostrando resultado:\n"
                    "   - Qual time venceu (Azul/Vermelho)\n"
                    "   - KDA de todos os 10 jogadores\n"
                    "   - CS e Dano de todos\n\n"
                    "**Notificações individuais** (com MVP Score) são enviadas\n"
                    "no **canal de score** configurado.\n\n"
                    "💡 **Recomendação:** Configure ambos os canais:\n"
                    "• `live` - Para acompanhar partidas em grupo\n"
                    "• `score` - Para avaliações individuais"
                ),
                inline=False
            )
        else:
            await interaction.followup.send("❌ Erro ao configurar canal.", ephemeral=True)
            return
    
    else:  # votacao
        success = db.set_voting_channel(guild_id, channel_id)
        if success:
            embed = discord.Embed(
                title="✅ Canal de Votação Configurado!",
                description=f"Votações de MVP serão enviadas em {canal.mention}",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="🗳️ Como funciona?",
                value=(
                    "**Sistema de Votação MVP:**\n"
                    "• Quando uma partida termina, os jogadores podem votar no MVP\n"
                    "• Cada jogador vota em quem carregou a partida (não pode votar em si)\n"
                    "• **Voto unânime (4 votos):** +5 Carry Score\n"
                    "• **1º lugar:** +3 Carry Score\n"
                    "• **2º lugar:** +2 Carry Score\n"
                    "• **Empate:** +2 cada\n\n"
                    "O Carry Score acumula durante o ano!"
                ),
                inline=False
            )
        else:
            await interaction.followup.send("❌ Erro ao configurar canal.", ephemeral=True)
            return
    
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

@bot.tree.command(name="perfil", description="👤 Veja seu perfil completo com estatísticas e pintados de ouro")
@app_commands.describe(
    usuario="Ver perfil de outro jogador (opcional)",
    ano="Ano/Season para ver estatísticas (padrão: ano atual)"
)
async def perfil(interaction: discord.Interaction, usuario: discord.User = None, ano: int = None):
    """Mostra o perfil completo do jogador com estatísticas e pintados de ouro"""
    if not await check_command_channel(interaction):
        return
    
    await interaction.response.defer()
    
    # Define o ano (padrão: ano atual)
    current_year = datetime.now().year
    year = ano if ano else current_year
    
    # Define o usuário alvo
    target_user = usuario or interaction.user
    discord_id = str(target_user.id)
    
    # Busca contas vinculadas
    accounts = db.get_user_accounts(discord_id)
    
    if not accounts:
        if usuario:
            await interaction.followup.send(
                f"❌ **{target_user.display_name}** não tem nenhuma conta vinculada.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "❌ Você não tem nenhuma conta vinculada.\n"
                "Use `/logar` para vincular sua conta do LoL!",
                ephemeral=True
            )
        return
    
    # Busca estatísticas do perfil (filtrado por ano)
    profile_stats = db.get_profile_stats(discord_id, year)
    
    if profile_stats['total_matches'] == 0:
        await interaction.followup.send(
            f"❌ {'**' + target_user.display_name + '**' if usuario else 'Você'} não tem partidas registradas em **{year}**.\n"
            "Jogue algumas partidas de Ranked Flex para ver suas estatísticas!",
            ephemeral=True
        )
        return
    
    # Busca top 3 campeões (filtrado por ano)
    top_champions = db.get_top_champions(discord_id, limit=3, year=year)
    
    # Busca estatísticas por role (filtrado por ano)
    role_stats = db.get_role_stats(discord_id, year)
    
    # Busca pintados de ouro (filtrado por ano)
    total_gold_medals = db.get_total_gold_medals_by_discord(discord_id, year)
    gold_by_champion = db.get_gold_medals_by_champion_all_accounts(discord_id, year)
    gold_by_role = db.get_gold_medals_by_role_all_accounts(discord_id, year)
    
    # Formata tempo de jogo
    total_seconds = profile_stats['total_time_seconds']
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    
    # Determina cor baseada no winrate
    winrate = profile_stats['winrate']
    if winrate >= 60:
        color = discord.Color.gold()
    elif winrate >= 50:
        color = discord.Color.green()
    elif winrate >= 45:
        color = discord.Color.orange()
    else:
        color = discord.Color.red()
    
    # Título com indicação de ano
    year_text = f" • Season {year}" if year != current_year else ""
    
    # Cria embed principal
    embed = discord.Embed(
        title=f"👤 Perfil de {target_user.display_name}{year_text}",
        description=f"**Contas vinculadas:** {len(accounts)}\n" + 
                    " • ".join([f"`{acc['summoner_name']}`" for acc in accounts]),
        color=color
    )
    
    # Avatar do usuário
    embed.set_thumbnail(url=target_user.display_avatar.url)
    
    # Estatísticas gerais
    embed.add_field(
        name="📊 Estatísticas Gerais",
        value=(
            f"🎮 **Partidas:** {profile_stats['total_matches']}\n"
            f"✅ **Vitórias:** {profile_stats['wins']} ({profile_stats['winrate']}%)\n"
            f"❌ **Derrotas:** {profile_stats['losses']}\n"
            f"⏱️ **Tempo de Jogo:** {hours}h {minutes}min\n"
            f"🎨 **Pintados de Ouro:** {total_gold_medals}"
        ),
        inline=True
    )
    
    # Médias gerais
    embed.add_field(
        name="📈 Médias por Partida",
        value=(
            f"⚔️ **KDA:** {profile_stats['avg_kda']:.2f}\n"
            f"🗡️ **Dano:** {int(profile_stats['avg_damage']):,}\n"
            f"💰 **Gold:** {int(profile_stats['avg_gold']):,}\n"
            f"🌾 **CS:** {profile_stats['avg_cs']:.1f}\n"
            f"👁️ **Visão:** {profile_stats['avg_vision']:.1f}\n"
            f"🎯 **MVP Score:** {profile_stats['avg_mvp_score']:.1f}"
        ),
        inline=True
    )
    
    # Top 3 campeões
    if top_champions:
        champ_text = ""
        medals = ["🥇", "🥈", "🥉"]
        for i, champ in enumerate(top_champions):
            medal = medals[i] if i < 3 else "•"
            champ_text += (
                f"{medal} **{champ['champion_name']}** ({champ['games']} jogos)\n"
                f"   WR: {champ['winrate']}% | KDA: {champ['avg_kda']:.2f} | Dano: {int(champ['avg_damage']):,}\n"
            )
        
        embed.add_field(
            name="🏆 Top 3 Campeões Mais Jogados",
            value=champ_text,
            inline=False
        )
    
    # Pintados de ouro por campeão (top 5)
    if gold_by_champion:
        gold_champ_text = ""
        for i, medal in enumerate(gold_by_champion[:5]):
            gold_champ_text += f"🎨 **{medal['champion_name']}:** {medal['count']}x\n"
        
        embed.add_field(
            name="🎨 Pintados de Ouro por Campeão",
            value=gold_champ_text if gold_champ_text else "Nenhum ainda",
            inline=True
        )
    
    # Pintados de ouro por role
    if gold_by_role:
        role_emojis = {
            'Top': '⚔️', 'Jungle': '🌳', 'Mid': '✨', 
            'ADC': '🏹', 'Support': '🛡️', 'Unknown': '❓'
        }
        gold_role_text = ""
        for medal in gold_by_role:
            role_emoji = role_emojis.get(medal['role'], '❓')
            gold_role_text += f"{role_emoji} **{medal['role']}:** {medal['count']}x\n"
        
        embed.add_field(
            name="🎨 Pintados de Ouro por Lane",
            value=gold_role_text if gold_role_text else "Nenhum ainda",
            inline=True
        )
    
    # Estatísticas por role
    if role_stats:
        role_emojis = {
            'Top': '⚔️', 'Jungle': '🌳', 'Mid': '✨', 
            'ADC': '🏹', 'Support': '🛡️', 'Unknown': '❓'
        }
        role_text = ""
        for role in role_stats[:5]:  # Top 5 roles
            role_emoji = role_emojis.get(role['role'], '❓')
            role_text += f"{role_emoji} **{role['role']}:** {role['games']} jogos ({role['winrate']}% WR)\n"
        
        embed.add_field(
            name="🎭 Partidas por Lane",
            value=role_text,
            inline=False
        )
    
    embed.set_footer(text=f"Ranked Flex • Season {year} • Use /media para estatísticas detalhadas")
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="flex", description="🎯 Guia completo do bot com botões interativos")
async def flex_guide(interaction: discord.Interaction):
    """Comando com guia interativo do bot"""
    if not await check_command_channel(interaction):
        return
    
    embed = discord.Embed(
        title="🎮 Flex dos Crias",
        description=(
            "**O bot definitivo de tracking para Ranked Flex!**\n\n"
            "Monitore suas partidas, acompanhe seu desempenho em tempo real,\n"
            "e descubra seu verdadeiro nível de performance com nosso sistema avançado.\n"
        ),
        color=discord.Color.from_rgb(200, 155, 255)
    )
    
    embed.add_field(
        name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        value="",
        inline=False
    )
    
    embed.add_field(
        name="🎯 **TRACKING EM TEMPO REAL**",
        value=(
            "🔴 **Live Tracking**\n"
            "• Notificação instantânea quando você entra em partida\n"
            "• Acompanhe composições de times ao vivo\n"
            "• Links para OP.GG, U.GG e Porofessor\n\n"
            "🎮 **Auto-Update ao Finalizar**\n"
            "• Mensagem atualiza automaticamente quando terminar\n"
            "• Resultado aparece em até 10 segundos após o fim\n"
            "• Histórico completo salvo automaticamente"
        ),
        inline=False
    )
    
    embed.add_field(
        name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        value="",
        inline=False
    )
    
    embed.add_field(
        name="🏆 **SISTEMA DE MVP SCORE**",
        value=(
            "**Pontuação de 0 a 100 - Sistema EXIGENTE:**\n"
            "⚔️ **Top/Mid**: Foco em KDA\n"
            "🌳 **Jungle**: Kill Participation + Objetivos\n"
            "🏹 **ADC**: Farm + Dano aos campeões\n"
            "🛡️ **Support**: Visão + Kill Participation\n\n"
            "**Penalidades por muitas mortes ou baixa participação!**\n"
            "**Apenas performances excepcionais recebem S/S+!**"
        ),
        inline=False
    )
    
    embed.add_field(
        name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        value="",
        inline=False
    )
    
    embed.add_field(
        name="📊 **COMANDOS PRINCIPAIS**",
        value=(
            "`/logar` • Vincule sua conta do LOL (até 3 contas)\n"
            "`/media` • Estatísticas detalhadas por campeão/métrica\n"
            "`/historico` • Veja suas últimas partidas\n"
            "`/tops_flex` • Ranking dos melhores jogadores\n"
            "`/contas` • Gerencie suas contas vinculadas"
        ),
        inline=False
    )
    
    embed.add_field(
        name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        value="",
        inline=False
    )
    
    embed.add_field(
        name="⚡ **DESTAQUES**",
        value=(
            "🔄 Verificação automática a cada **5 minutos**\n"
            "🚀 Detecção de partidas finalizadas em **10 segundos**\n"
            "📈 Análise por campeão, role e métrica específica\n"
            "⚠️ Alertas inteligentes de performance\n"
            "🌍 Suporte a **todas as regiões** da Riot"
        ),
        inline=False
    )
    
    embed.set_footer(text="💡 Clique nos botões abaixo para mais informações!")
    embed.set_thumbnail(url="https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/ranked-emblem-flex.png")
    
    view = FlexGuideView()
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="reset_media", description="🗑️ [ADMIN] Reseta estatísticas de partidas do banco de dados")
@app_commands.describe(
    modo="Escolha 'all' para resetar tudo ou 'usuario' para resetar de alguém específico",
    usuario="[Opcional] Usuário para resetar (apenas se modo='usuario')",
    conta_numero="[Opcional] Número da conta (1, 2 ou 3) para resetar apenas uma conta específica"
)
@app_commands.choices(modo=[
    app_commands.Choice(name="🗑️ Resetar TODAS as partidas do servidor", value="all"),
    app_commands.Choice(name="👤 Resetar partidas de um usuário específico", value="usuario")
])
@app_commands.checks.has_permissions(administrator=True)
async def reset_media(
    interaction: discord.Interaction, 
    modo: app_commands.Choice[str],
    usuario: discord.User = None,
    conta_numero: int = None
):
    """[ADMIN] Reseta estatísticas de partidas"""
    await interaction.response.defer(ephemeral=True)
    
    # Modo ALL - reseta tudo
    if modo.value == "all":
        # Confirmação extra para resetar tudo
        embed = discord.Embed(
            title="⚠️ CONFIRMAÇÃO NECESSÁRIA",
            description=(
                "Você está prestes a **DELETAR TODAS AS PARTIDAS** do banco de dados!\n\n"
                "**Isso inclui:**\n"
                "• Todas as partidas de todos os usuários\n"
                "• Todo o histórico de estatísticas\n"
                "• Todos os MVP scores registrados\n\n"
                "**As contas vinculadas NÃO serão removidas.**\n\n"
                "⚠️ **ESTA AÇÃO NÃO PODE SER DESFEITA!**"
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text="Use /reset_media_confirmar para confirmar a ação")
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    # Modo USUARIO - reseta de um usuário específico
    elif modo.value == "usuario":
        if not usuario:
            await interaction.followup.send(
                "❌ Você precisa mencionar um usuário quando usar o modo 'usuario'!\n"
                "Exemplo: `/reset_media modo:usuario usuario:@Jogador`",
                ephemeral=True
            )
            return
        
        discord_id = str(usuario.id)
        accounts = db.get_user_accounts(discord_id)
        
        if not accounts:
            await interaction.followup.send(
                f"❌ {usuario.mention} não tem nenhuma conta vinculada ao bot.",
                ephemeral=True
            )
            return
        
        # Se especificou número da conta
        if conta_numero:
            if conta_numero < 1 or conta_numero > len(accounts):
                await interaction.followup.send(
                    f"❌ Conta inválida! {usuario.mention} tem {len(accounts)} conta(s) vinculada(s).",
                    ephemeral=True
                )
                return
            
            # Reseta apenas uma conta específica
            account = accounts[conta_numero - 1]
            success, deleted_count = db.delete_matches_by_account(account['id'])
            
            if success:
                embed = discord.Embed(
                    title="✅ Partidas Resetadas!",
                    description=f"Partidas da conta **{account['summoner_name']}** foram deletadas.",
                    color=discord.Color.green()
                )
                embed.add_field(name="👤 Usuário", value=usuario.mention, inline=True)
                embed.add_field(name="🎮 Conta", value=account['summoner_name'], inline=True)
                embed.add_field(name="🗑️ Partidas Deletadas", value=str(deleted_count), inline=True)
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("❌ Erro ao deletar partidas.", ephemeral=True)
        
        else:
            # Reseta todas as contas do usuário
            total_deleted = 0
            accounts_info = []
            
            for account in accounts:
                success, deleted_count = db.delete_matches_by_account(account['id'])
                if success:
                    total_deleted += deleted_count
                    accounts_info.append(f"• **{account['summoner_name']}**: {deleted_count} partidas")
            
            embed = discord.Embed(
                title="✅ Partidas Resetadas!",
                description=f"Todas as partidas de {usuario.mention} foram deletadas.",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 Usuário", value=usuario.mention, inline=False)
            embed.add_field(
                name="🎮 Contas Afetadas",
                value="\n".join(accounts_info) if accounts_info else "Nenhuma",
                inline=False
            )
            embed.add_field(name="🗑️ Total Deletado", value=f"{total_deleted} partidas", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="reset_media_confirmar", description="🗑️ [ADMIN] Confirma o reset de TODAS as partidas")
@app_commands.checks.has_permissions(administrator=True)
async def reset_media_confirmar(interaction: discord.Interaction):
    """[ADMIN] Confirma o reset completo do banco de partidas"""
    await interaction.response.defer(ephemeral=True)
    
    # Deleta todas as partidas
    success, deleted_count = db.delete_all_matches()
    
    if success:
        embed = discord.Embed(
            title="✅ Banco de Dados Resetado!",
            description=(
                "**Todas as partidas foram deletadas com sucesso.**\n\n"
                "O bot continuará monitorando e registrando novas partidas normalmente."
            ),
            color=discord.Color.green()
        )
        embed.add_field(name="🗑️ Partidas Deletadas", value=str(deleted_count), inline=True)
        embed.add_field(name="📊 Status", value="Banco limpo", inline=True)
        embed.set_footer(text="As contas vinculadas não foram afetadas")
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"⚠️ [ADMIN] {interaction.user.name} resetou TODAS as partidas ({deleted_count} deletadas)")
    else:
        await interaction.followup.send(
            "❌ Erro ao resetar banco de dados. Verifique os logs.",
            ephemeral=True
        )

@bot.tree.command(name="resync_accounts", description="🔄 [ADMIN] Re-sincroniza todas as contas para corrigir PUUIDs corrompidos")
@app_commands.checks.has_permissions(administrator=True)
async def resync_accounts(interaction: discord.Interaction):
    """[ADMIN] Re-sincroniza todas as contas do banco de dados com a Riot API"""
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="🔄 Re-sincronizando Contas",
        description="Atualizando PUUIDs de todas as contas vinculadas...",
        color=discord.Color.blue()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    # Busca todas as contas
    all_accounts = db.get_all_accounts()
    
    if not all_accounts:
        embed = discord.Embed(
            title="❌ Nenhuma Conta Encontrada",
            description="Não há contas vinculadas no banco de dados.",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=embed)
        return
    
    success_count = 0
    fail_count = 0
    failed_accounts = []
    
    for account in all_accounts:
        try:
            # Parse o summoner name (formato: Nome#TAG)
            if '#' not in account['summoner_name']:
                print(f"⚠️ Conta sem formato Riot ID: {account['summoner_name']}")
                fail_count += 1
                failed_accounts.append(account['summoner_name'])
                continue
            
            game_name, tag_line = account['summoner_name'].split('#', 1)
            region = account['region']
            
            # Busca novos dados da Riot API
            riot_account = await riot_api.get_account_by_riot_id(game_name, tag_line, region)
            
            if not riot_account:
                print(f"❌ Não foi possível buscar: {account['summoner_name']}")
                fail_count += 1
                failed_accounts.append(account['summoner_name'])
                continue
            
            # Busca dados do summoner pelo novo PUUID
            summoner = await riot_api.get_summoner_by_puuid(riot_account['puuid'], region)
            
            if not summoner:
                print(f"❌ Não foi possível buscar summoner: {account['summoner_name']}")
                fail_count += 1
                failed_accounts.append(account['summoner_name'])
                continue
            
            # Atualiza no banco
            summoner_id = summoner.get('id', riot_account['puuid'])
            account_id = summoner.get('accountId', riot_account['puuid'])
            
            if db.update_account_puuid(account['id'], riot_account['puuid'], summoner_id, account_id):
                print(f"✅ Atualizado: {account['summoner_name']}")
                success_count += 1
            else:
                print(f"❌ Erro ao atualizar banco: {account['summoner_name']}")
                fail_count += 1
                failed_accounts.append(account['summoner_name'])
            
            # Delay para não sobrecarregar a API
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro ao processar {account.get('summoner_name', 'unknown')}: {e}")
            fail_count += 1
            failed_accounts.append(account.get('summoner_name', 'unknown'))
    
    # Resultado final
    result_embed = discord.Embed(
        title="✅ Re-sincronização Concluída",
        color=discord.Color.green() if fail_count == 0 else discord.Color.orange()
    )
    
    result_embed.add_field(
        name="📊 Resultado",
        value=(
            f"✅ **{success_count}** contas atualizadas\n"
            f"❌ **{fail_count}** contas falharam\n"
            f"📝 **{len(all_accounts)}** contas totais"
        ),
        inline=False
    )
    
    if failed_accounts:
        failed_text = "\n".join([f"• {acc}" for acc in failed_accounts[:10]])
        if len(failed_accounts) > 10:
            failed_text += f"\n... e mais {len(failed_accounts) - 10}"
        
        result_embed.add_field(
            name="❌ Contas que falharam",
            value=failed_text,
            inline=False
        )
        result_embed.add_field(
            name="💡 Solução",
            value="Peça para os usuários usarem `/logar` novamente para re-vincular suas contas.",
            inline=False
        )
    
    result_embed.set_footer(text="Os usuários podem continuar usando o bot normalmente")
    await interaction.edit_original_response(embed=result_embed)

@bot.tree.command(name="purge_media", description="🗑️ [ADMIN] Reseta TODAS as estatísticas e médias salvas no bot")
@app_commands.checks.has_permissions(administrator=True)
async def purge_media(interaction: discord.Interaction):
    """[ADMIN] Reseta todas as partidas e estatísticas do banco de dados (comando direto)"""
    await interaction.response.defer(ephemeral=True)
    
    # Confirmação inline
    embed = discord.Embed(
        title="⚠️ RESET COMPLETO DE MÉDIAS",
        description=(
            "Você está prestes a **DELETAR TODAS AS ESTATÍSTICAS E MÉDIAS**!\n\n"
            "**O que será resetado:**\n"
            "✅ Todas as partidas de todos os usuários\n"
            "✅ Todo o histórico de estatísticas e médias\n"
            "✅ Todos os MVP scores registrados\n"
            "✅ Todo o ranking\n\n"
            "**O que NÃO será afetado:**\n"
            "❌ Contas vinculadas (permanecem)\n"
            "❌ Configurações do servidor\n\n"
            "⚠️ **ESTA AÇÃO NÃO PODE SER DESFEITA!**\n"
            "Tem certeza? Use os botões abaixo:"
        ),
        color=discord.Color.red()
    )
    
    # Cria view com botões de confirmação
    class ConfirmPurgeView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.value = None
        
        @discord.ui.button(label="✅ CONFIRMAR RESET", style=discord.ButtonStyle.danger)
        async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            await button_interaction.response.defer()
            
            # Deleta todas as partidas
            success, deleted_count = db.delete_all_matches()
            
            if success:
                result_embed = discord.Embed(
                    title="✅ MÉDIAS RESETADAS COM SUCESSO!",
                    description=(
                        "**Todas as partidas e estatísticas foram deletadas.**\n\n"
                        "O bot continuará monitorando normalmente a partir de agora.\n"
                        "As próximas partidas começarão com médias zeradas."
                    ),
                    color=discord.Color.green()
                )
                result_embed.add_field(name="🗑️ Partidas Deletadas", value=f"**{deleted_count}** partidas", inline=True)
                result_embed.add_field(name="📊 Status", value="✅ Banco limpo", inline=True)
                result_embed.set_footer(text="Reset executado por " + button_interaction.user.name)
                await button_interaction.edit_original_response(embed=result_embed, view=None)
                print(f"⚠️ [ADMIN] {button_interaction.user.name} resetou TODAS as médias ({deleted_count} partidas deletadas)")
            else:
                error_embed = discord.Embed(
                    title="❌ Erro no Reset",
                    description="Ocorreu um erro ao resetar o banco. Verifique os logs.",
                    color=discord.Color.red()
                )
                await button_interaction.edit_original_response(embed=error_embed, view=None)
        
        @discord.ui.button(label="❌ CANCELAR", style=discord.ButtonStyle.secondary)
        async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            cancel_embed = discord.Embed(
                title="❌ Reset Cancelado",
                description="Nenhuma alteração foi feita no banco de dados.",
                color=discord.Color.blue()
            )
            await button_interaction.response.edit_message(embed=cancel_embed, view=None)
    
    view = ConfirmPurgeView()
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def send_match_notification(lol_account_id: int, stats: Dict):
    """
    Envia notificação INDIVIDUAL quando uma partida termina.
    SEMPRE envia uma notificação separada no canal de score.
    NÃO edita mais a mensagem de live game.
    """
    try:
        # 🔥 NOVA VALIDAÇÃO: Verifica se já foi enviada notificação para esta partida
        match_id = stats.get('match_id')
        if db.was_match_notification_sent(lol_account_id, match_id):
            print(f"⏭️ [Match Notification] Notificação já enviada para partida {match_id}, pulando...")
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
            
            # Busca canal de score configurado
            channel_id = db.get_match_channel(str(guild.id))
            if not channel_id:
                continue
            
            # Busca o canal
            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue
            
            # Verifica se é remake
            is_remake = stats.get('is_remake', False)
            
            # Determina cor baseada no resultado
            if is_remake:
                color = discord.Color.greyple()  # Cinza para remake
                result_emoji = "⚠️"
                result_text = "REMAKE"
            elif stats['win']:
                color = discord.Color.green()
                result_emoji = "✅"
                result_text = "VITÓRIA"
            else:
                color = discord.Color.red()
                result_emoji = "❌"
                result_text = "DERROTA"
            
            
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

            if is_remake:
                # Layout especial para remake
                embed = discord.Embed(
                    title=f"{result_emoji} {result_text}",
                    description=(
                        f"# {stats['champion_name']} {role_emoji}\n"
                        f"{member.mention} teve uma partida **cancelada** (remake)."
                    ),
                    color=color,
                    timestamp=datetime.fromisoformat(stats['played_at'])
                )
                
                embed.add_field(
                    name="⚠️ Partida Cancelada",
                    value=(
                        f"**Modo:** Ranked Flex\n"
                        f"**Invocador:** {summoner_name}\n"
                        f"**Campeão:** {stats['champion_name']}\n"
                        f"**Role:** {role_emoji} {stats['role']}\n"
                        f"⏱️ **Duração:** {game_duration_min}min {game_duration_sec}s\n"
                        f"\n"
                        f"_Esta partida não conta para estatísticas._"
                    ),
                    inline=False
                )
            else:
                # Layout normal para partidas completas
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
                
                # MVP Score (comparação com TODOS os 10 jogadores)
                mvp_score = stats.get('mvp_score', 0)
                mvp_placement = stats.get('mvp_placement', 0)
                
                # Emoji baseado na colocação
                if mvp_placement == 1:
                    mvp_emoji = "👑"
                elif mvp_placement == 2:
                    mvp_emoji = "🥇"
                elif mvp_placement == 3:
                    mvp_emoji = "🥈"
                elif mvp_placement <= 5:
                    mvp_emoji = "🥉"
                elif mvp_placement <= 7:
                    mvp_emoji = "📊"
                else:
                    mvp_emoji = "😴"
                
                # Formata o ordinal (1º, 2º, 3º...)
                placement_text = f"{mvp_placement}º"
                
                embed.add_field(
                    name="🎯 MVP Score",
                    value=(
                        f"**👑 MVP SCORE** _(vs 10 Jogadores)_\n"
                        f"{mvp_emoji} **{mvp_score}/100 ({placement_text})**\n"
                        f"```\n"
                        f"{'█' * int(mvp_score/5)}{'░' * (20 - int(mvp_score/5))}\n"
                        f"```"
                    ),
                    inline=False
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
            
            # Envia mensagem
            try:
                await channel.send(embed=embed)
                
                # 🔥 Marca que a notificação foi enviada para esta partida
                db.mark_match_notification_sent(lol_account_id, match_id)
                
                if is_remake:
                    print(f"⚠️ Partida enviada (REMAKE): {summoner_name} - {stats['champion_name']}")
                else:
                    print(f"🎮 Partida enviada: {summoner_name} - {stats['champion_name']} (MVP: {mvp_score}/{mvp_placement}º)")
            except Exception as e:
                print(f"Erro ao enviar partida: {e}")
    
    except Exception as e:
        print(f"Erro ao processar notificação de partida: {e}")

async def update_live_game_result(game_id: str, match_data: Dict):
    """
    Atualiza a mensagem de live game com o resultado final da partida.
    Mantém o formato original e adiciona informações de resultado, dano e CS.
    """
    try:
        print(f"🔍 [Live Update] Buscando mensagem de live game para game_id: {game_id}")
        print(f"   📍 Tipo do game_id: {type(game_id)}")
        
        # Converte game_id para string para garantir comparação correta
        game_id_str = str(game_id)
        
        # Busca se existe mensagem de live game para este match
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Debug: Lista todos os game_ids ativos
        cursor.execute('SELECT game_id, message_id, puuid FROM live_games_notified WHERE message_id IS NOT NULL')
        all_games = cursor.fetchall()
        print(f"🔍 [Live Update DEBUG] Games ativos no banco ({len(all_games)} encontrados):")
        for g in all_games:
            print(f"   - Game ID: {g[0]} (tipo: {type(g[0])}), Message ID: {g[1]}, PUUID: {g[2][:20]}...")
        
        # Busca PUUIDs dos participantes da partida
        match_puuids = [p['puuid'] for p in match_data['info']['participants']]
        print(f"🔍 [Live Update] PUUIDs da partida terminada ({len(match_puuids)} jogadores):")
        for i, p in enumerate(match_puuids[:3]):
            print(f"   {i+1}. {p[:30]}...")
        
        # Busca TODAS as mensagens relacionadas a esta partida (por PUUIDs dos participantes)
        print(f"🔍 [Live Update] Buscando mensagens por PUUIDs da partida...")
        placeholders = ','.join('?' * len(match_puuids))
        query = f'''
            SELECT DISTINCT message_id, channel_id, guild_id, lol_account_id, game_id
            FROM live_games_notified
            WHERE puuid IN ({placeholders})
              AND message_id IS NOT NULL
            ORDER BY notified_at DESC
        '''
        cursor.execute(query, match_puuids)
        results = cursor.fetchall()

        if results:
            # Processa TODAS as mensagens encontradas (não apenas a primeira)
            print(f"✅ [Live Update] Encontradas {len(results)} mensagem(ns) relacionada(s) à partida!")
            print(f"   📍 Processando todas as mensagens encontradas...")

            # Atualiza o game_id para usar na remoção posterior (usa o primeiro resultado)
            found_game_id = results[0][4]  # game_id
            game_id = found_game_id

            # Processa cada mensagem individualmente
            processed_count = 0
            for result in results:
                message_id, channel_id, guild_id, lol_account_id = result[:4]

                print(f"🔄 [Live Update] Processando mensagem {message_id} para conta {lol_account_id}...")

                # Busca informações da conta para pegar summoner_name e region
                cursor.execute('''
                    SELECT summoner_name, region FROM lol_accounts
                    WHERE id = ?
                ''', (lol_account_id,))
                account_info = cursor.fetchone()

                if not account_info:
                    print(f"⚠️ [Live Update] Informações da conta {lol_account_id} não encontradas")
                    continue

                summoner_name, region = account_info

                print(f"✅ [Live Update] Mensagem encontrada - ID: {message_id}, Canal: {channel_id}, Servidor: {guild_id}")

                # Busca o servidor e canal
                guild = bot.get_guild(int(guild_id))
                if not guild:
                    print(f"⚠️ [Live Update] Servidor {guild_id} não encontrado")
                    continue

                channel = guild.get_channel(int(channel_id))
                if not channel:
                    print(f"⚠️ [Live Update] Canal {channel_id} não encontrado")
                    continue

                try:
                    message = await channel.fetch_message(int(message_id))
                except:
                    print(f"⚠️ [Live Update] Mensagem {message_id} não encontrada")
                    continue

                # Pega o embed original
                if not message.embeds:
                    print(f"⚠️ [Live Update] Mensagem não possui embed")
                    continue

                original_embed = message.embeds[0]

                # Extrai informações da partida
                participants = match_data['info']['participants']
                game_info = match_data['info']

                # Encontra os dados do jogador principal
                player_data = None
                for p in participants:
                    # Compara pelo summonerName (removendo RiotID se tiver)
                    p_name = p['riotIdGameName'] if 'riotIdGameName' in p else p['summonerName']
                    summoner_clean = summoner_name.split('#')[0] if '#' in summoner_name else summoner_name

                    if p_name.lower() == summoner_clean.lower():
                        player_data = p
                        break

                if not player_data:
                    print(f"⚠️ [Live Update] Dados do jogador {summoner_name} não encontrados na partida")
                    continue

                # Verifica se o jogador venceu
                player_won = player_data['win']
                player_team = player_data['teamId']

                # Determina a nova cor (verde para vitória, vermelho para derrota)
                if player_won:
                    new_color = discord.Color.green()
                    result_emoji = "✅"
                    result_text = "VITÓRIA"
                else:
                    new_color = discord.Color.red()
                    result_emoji = "❌"
                    result_text = "DERROTA"

                # Calcula estatísticas do jogador principal
                kills = player_data['kills']
                deaths = player_data['deaths']
                assists = player_data['assists']
                kda_ratio = (kills + assists) / max(deaths, 1)
                cs = player_data.get('totalMinionsKilled', 0) + player_data.get('neutralMinionsKilled', 0)
                damage = player_data.get('totalDamageDealtToChampions', 0)

                # Duração da partida
                game_duration = game_info['gameDuration']
                game_duration_min = game_duration // 60
                game_duration_sec = game_duration % 60

                # Cria novo embed com resultado
                new_embed = discord.Embed(
                    title=f"{result_emoji} PARTIDA FINALIZADA - {result_text}!",
                    description=original_embed.description,
                    color=new_color,
                    timestamp=datetime.now()
                )

                # Adiciona modo de jogo e duração
                new_embed.add_field(
                    name="🎮 Modo de Jogo",
                    value=f"**{original_embed.fields[0].value if original_embed.fields else 'Ranked Flex'}**",
                    inline=True
                )

                new_embed.add_field(
                    name="⏱️ Duração",
                    value=f"**{game_duration_min}:{game_duration_sec:02d}**",
                    inline=True
                )

                new_embed.add_field(
                    name="\u200b",  # Campo vazio para quebra de linha
                    value="\u200b",
                    inline=True
                )

                # Calcula MVP score de todos os jogadores para determinar colocações únicas
                all_players_with_scores = []

                # Usa a instância global da RiotAPI que já foi inicializada com a chave
                # riot = RiotAPI()  # <- linha removida, estava causando erro
                # A variável global 'riot_api' já está disponível e inicializada com a chave

                # Prepara dados globais para cálculo
                all_kdas = [(pl['kills'] + pl['assists']) / max(pl['deaths'], 1) for pl in participants]
                all_damages = [pl.get('totalDamageDealtToChampions', 0) for pl in participants]
                all_golds = [pl.get('goldEarned', 0) for pl in participants]
                all_cs_list = [pl.get('totalMinionsKilled', 0) + pl.get('neutralMinionsKilled', 0) for pl in participants]
                all_visions = [pl.get('visionScore', 0) for pl in participants]

                team_1_kills = sum(pl['kills'] for pl in participants if pl['teamId'] == 100)
                team_2_kills = sum(pl['kills'] for pl in participants if pl['teamId'] == 200)
                all_kps = [
                    (pl['kills'] + pl['assists']) / max(team_1_kills if pl['teamId'] == 100 else team_2_kills, 1)
                    for pl in participants
                ]

                all_players_stats = {
                    'all_kdas': all_kdas,
                    'all_kps': all_kps,
                    'all_damages': all_damages,
                    'all_golds': all_golds,
                    'all_cs': all_cs_list,
                    'all_visions': all_visions
                }

                for p in participants:
                    p_team_id = p['teamId']
                    p_team_kills = sum(
                        pl['kills'] for pl in participants if pl['teamId'] == p_team_id
                    )
                    p_kda = (p['kills'] + p['assists']) / max(p['deaths'], 1)
                    p_kp = (p['kills'] + p['assists']) / max(p_team_kills, 1)
                    p_damage = p.get('totalDamageDealtToChampions', 0)
                    p_gold = p.get('goldEarned', 0)
                    p_cs = p.get('totalMinionsKilled', 0) + p.get('neutralMinionsKilled', 0)
                    p_vision = p.get('visionScore', 0)
                    p_role = p.get('teamPosition', '') or p.get('individualPosition', 'MIDDLE')

                    player_stats = {
                        'kda': p_kda,
                        'kill_participation': p_kp,
                        'total_damage_to_champions': p_damage,
                        'gold_earned': p_gold,
                        'total_minions_killed': p.get('totalMinionsKilled', 0),
                        'neutral_minions_killed': p.get('neutralMinionsKilled', 0),
                        'vision_score': p_vision,
                        'win': p.get('win', False)
                    }

                    mvp_score, _ = riot_api.calculate_mvp_score(player_stats, all_players_stats, p_role)

                    all_players_with_scores.append({
                        'player': p,
                        'mvp_score': mvp_score,
                        'kda': p_kda,
                        'kp': p_kp * 100,
                        'cs': p_cs,
                        'damage': p_damage,
                        'puuid': p['puuid']
                    })

                # Ordena por MVP score para determinar colocações únicas
                # Adiciona índice para garantir desempate total (colocações únicas de 1 a 10)
                for idx, player_info in enumerate(all_players_with_scores):
                    player_info['original_index'] = idx

                # Ordena: 1º por MVP score, 2º por dano, 3º por índice original (garante ordem única)
                all_players_with_scores.sort(key=lambda x: (-x['mvp_score'], -x['damage'], x['original_index']))

                # Atribui placement único baseado na ordem (sempre 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
                for i, player_info in enumerate(all_players_with_scores, 1):
                    player_info['placement'] = i

                # MVP da partida (1º lugar)
                mvp = all_players_with_scores[0]
                mvp_player = mvp['player']
                mvp_name = mvp_player.get('riotIdGameName', mvp_player.get('summonerName', 'Unknown'))
                mvp_champion = mvp_player.get('championName', 'Unknown')
                mvp_team = "🔵 Time Azul" if mvp_player['teamId'] == 100 else "🔴 Time Vermelho"

                # Adiciona estatísticas do MVP
                mvp_stats_text = (
                    f"👑 **{mvp_name}** - {mvp_champion} ({mvp_team})\n"
                    f"📊 **KDA:** {mvp_player['kills']}/{mvp_player['deaths']}/{mvp_player['assists']} ({mvp['kda']:.2f})\n"
                    f"🎯 **MVP Score:** {mvp['mvp_score']}/100 **(1º lugar)**\n"
                    f"🗡️ **Dano:** {mvp['damage']:,}\n"
                    f"🌾 **CS:** {mvp['cs']} | 👁️ **Visão:** {mvp_player.get('visionScore', 0)}"
                )

                new_embed.add_field(
                    name="🏆 MVP DA PARTIDA",
                    value=mvp_stats_text,
                    inline=False
                )

                # Separa jogadores por time
                team_100_players = [p for p in all_players_with_scores if p['player']['teamId'] == 100]
                team_200_players = [p for p in all_players_with_scores if p['player']['teamId'] == 200]

                # Ordena cada time por dano (como antes)
                team_100_players.sort(key=lambda p: p['damage'], reverse=True)
                team_200_players.sort(key=lambda p: p['damage'], reverse=True)

                # Time Azul (100)
                team_100_text = ""
                team_100_won = team_100_players[0]['player']['win'] if team_100_players else False
                for player_info in team_100_players:
                    p = player_info['player']
                    p_name = p.get('riotIdGameName', p.get('summonerName', 'Unknown'))
                    p_champion = p.get('championName', 'Unknown')
                    placement = player_info['placement']

                    # Emoji para colocação
                    if placement == 1:
                        placement_emoji = "👑"
                    elif placement == 2:
                        placement_emoji = "🥇"
                    elif placement == 3:
                        placement_emoji = "🥈"
                    elif placement <= 5:
                        placement_emoji = "🥉"
                    else:
                        placement_emoji = "📊"

                    # Destaca o jogador que estava sendo seguido
                    if p['puuid'] == player_data['puuid']:
                        p_name = f"**{p_name}**"

                    team_100_text += (
                        f"{placement_emoji} **{placement}º** {p_champion} - {p_name}\n"
                        f"   KDA: {p['kills']}/{p['deaths']}/{p['assists']} ({player_info['kda']:.1f}) | "
                        f"MVP: {player_info['mvp_score']} | Dano: {player_info['damage']:,}\n"
                    )

                new_embed.add_field(
                    name=f"🔵 Time Azul {'(Vitória)' if team_100_won else '(Derrota)'}",
                    value=team_100_text.strip() if team_100_text else "Nenhum dado disponível",
                    inline=False
                )

                # Time Vermelho (200)
                team_200_text = ""
                team_200_won = team_200_players[0]['player']['win'] if team_200_players else False
                for player_info in team_200_players:
                    p = player_info['player']
                    p_name = p.get('riotIdGameName', p.get('summonerName', 'Unknown'))
                    p_champion = p.get('championName', 'Unknown')
                    placement = player_info['placement']

                    # Emoji para colocação
                    if placement == 1:
                        placement_emoji = "👑"
                    elif placement == 2:
                        placement_emoji = "🥇"
                    elif placement == 3:
                        placement_emoji = "🥈"
                    elif placement <= 5:
                        placement_emoji = "🥉"
                    else:
                        placement_emoji = "📊"

                    # Destaca o jogador que estava sendo seguido
                    if p['puuid'] == player_data['puuid']:
                        p_name = f"**{p_name}**"

                    team_200_text += (
                        f"{placement_emoji} **{placement}º** {p_champion} - {p_name}\n"
                        f"   KDA: {p['kills']}/{p['deaths']}/{p['assists']} ({player_info['kda']:.1f}) | "
                        f"MVP: {player_info['mvp_score']} | Dano: {player_info['damage']:,}\n"
                    )

                new_embed.add_field(
                    name=f"🔴 Time Vermelho {'(Vitória)' if team_200_won else '(Derrota)'}",
                    value=team_200_text.strip() if team_200_text else "Nenhum dado disponível",
                    inline=False
                )

                # Mantém thumbnail e footer originais se existirem
                if original_embed.thumbnail:
                    new_embed.set_thumbnail(url=original_embed.thumbnail.url)

                if original_embed.footer:
                    new_embed.set_footer(
                        text=original_embed.footer.text,
                        icon_url=original_embed.footer.icon_url if original_embed.footer.icon_url else discord.Embed.Empty
                    )

                # Edita a mensagem de live game
                print(f"🔄 [Live Update] Editando mensagem {message_id} no canal {channel.name}...")
                print(f"🔄 [Live Update] Novo título: '{new_embed.title}'")
                print(f"🔄 [Live Update] Nova cor: {new_embed.color}")

                try:
                    await message.edit(embed=new_embed)
                    print(f"✅✅✅ [Live Update] MENSAGEM EDITADA COM SUCESSO! ✅✅✅")
                    print(f"🏁 [Live Update] Game ID: {game_id} - Resultado: {result_text}")
                    print(f"🏁 [Live Update] Mensagem ID: {message_id} no servidor: {guild.name}")
                    processed_count += 1
                    
                    # Envia votação de MVP se for a primeira mensagem processada
                    if processed_count == 1:
                        # Coleta jogadores que participaram da partida (apenas os que estão no bot)
                        voting_players = []
                        for puuid in match_puuids:
                            cursor.execute('''
                                SELECT la.id, u.discord_id, la.summoner_name
                                FROM lol_accounts la
                                JOIN users u ON la.discord_id = u.discord_id
                                WHERE la.puuid = ?
                            ''', (puuid,))
                            player_info = cursor.fetchone()
                            if player_info:
                                voting_players.append({
                                    'discord_id': player_info[1],
                                    'summoner_name': player_info[2]
                                })
                        
                        if len(voting_players) >= 2:
                            print(f"🗳️ [Votação] Enviando votação com {len(voting_players)} jogadores")
                            await send_mvp_voting(game_id, guild, voting_players)
                        else:
                            print(f"⚠️ [Votação] Apenas {len(voting_players)} jogador(es) no bot, pulando votação")
                            
                except discord.errors.Forbidden:
                    print(f"❌ [Live Update] Sem permissão para editar mensagem {message_id}")
                except discord.errors.NotFound:
                    print(f"❌ [Live Update] Mensagem {message_id} não encontrada (pode ter sido deletada)")
                except discord.errors.HTTPException as e:
                    print(f"❌ [Live Update] Erro HTTP ao editar mensagem: {e}")
                    print(f"   Status: {e.status}, Código: {e.code}")
                except Exception as e:
                    print(f"❌ [Live Update] Erro inesperado ao editar mensagem: {e}")
                    print(f"   Tipo do erro: {type(e)}")
                    import traceback
                    traceback.print_exc()

            # Fecha conexão com banco de dados fora do loop
            conn.close()

            # Log final para confirmar se a função foi executada completamente
            print(f"🏁 [Live Update] update_live_game_result FINALIZADA para game_id: {game_id}")
            print(f"✅ [Live Update] Processadas {processed_count} mensagens para a partida")

        else:
            print(f"⚠️ [Live Update] Nenhuma mensagem encontrada para esta partida!")
            print(f"⚠️ [Live Update] PUUIDs buscados: {len(match_puuids)}")
            conn.close()
            return

    except Exception as e:
        print(f"❌ [Live Update] Erro geral ao atualizar resultado: {e}")
        import traceback
        traceback.print_exc()

async def send_mvp_voting(game_id: str, guild: discord.Guild, players: List[Dict]):
    """Envia votação de MVP para o canal configurado após partida finalizada
    
    players: Lista de dicts com 'discord_id' e 'summoner_name' dos jogadores da partida
    """
    try:
        # Verifica se há canal de votação configurado
        voting_channel_id = db.get_voting_channel(str(guild.id))
        if not voting_channel_id:
            print(f"⚠️ [Votação] Canal de votação não configurado para {guild.name}")
            return
        
        channel = guild.get_channel(int(voting_channel_id))
        if not channel:
            print(f"❌ [Votação] Canal de votação não encontrado: {voting_channel_id}")
            return
        
        # Precisa de pelo menos 2 jogadores para votar
        if len(players) < 2:
            print(f"⚠️ [Votação] Menos de 2 jogadores na partida, pulando votação")
            return
        
        # Cria lista de jogadores para votação
        players_json = json.dumps([{'discord_id': p['discord_id'], 'summoner_name': p['summoner_name']} for p in players])
        
        # Cria votação pendente (expira em 5 minutos)
        db.create_pending_vote(game_id, str(guild.id), players_json, expires_minutes=5)
        
        # Cria embed de votação
        embed = discord.Embed(
            title="🗳️ VOTAÇÃO DE MVP",
            description=(
                f"**Partida finalizada!**\n"
                f"Vote em quem você acha que foi o MVP da partida.\n\n"
                f"**Jogadores:** {', '.join([f'<@{p['discord_id']}>' for p in players])}\n\n"
                f"⏱️ Votação expira em **5 minutos**\n"
                f"❌ Você **não pode votar em si mesmo**"
            ),
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🏆 Premiação",
            value=(
                "• **Voto unânime (todos votam na mesma pessoa):** +5 Carry Score\n"
                "• **1º lugar em votos:** +3 Carry Score\n"
                "• **2º lugar em votos:** +2 Carry Score\n"
                "• **Empate no 1º lugar:** +2 cada"
            ),
            inline=False
        )
        
        # Cria view com botões de votação
        view = MVPVotingView(game_id, players, str(guild.id))
        
        message = await channel.send(embed=embed, view=view)
        
        # Atualiza votação pendente com message_id
        db.create_pending_vote(game_id, str(guild.id), players_json, str(message.id), str(channel.id), expires_minutes=5)
        
        print(f"✅ [Votação] Votação enviada para partida {game_id} em {guild.name}")
        
    except Exception as e:
        print(f"❌ [Votação] Erro ao enviar votação: {e}")
        import traceback
        traceback.print_exc()

class MVPVotingView(discord.ui.View):
    """View com botões para votação de MVP"""
    
    def __init__(self, game_id: str, players: List[Dict], guild_id: str):
        super().__init__(timeout=300)  # 5 minutos
        self.game_id = game_id
        self.players = players
        self.guild_id = guild_id
        
        # Adiciona um botão para cada jogador
        for i, player in enumerate(players):
            button = discord.ui.Button(
                label=player['summoner_name'][:20],  # Limita nome a 20 chars
                style=discord.ButtonStyle.primary,
                custom_id=f"vote_{game_id}_{player['discord_id']}"
            )
            button.callback = self.create_vote_callback(player['discord_id'], player['summoner_name'])
            self.add_item(button)
    
    def create_vote_callback(self, voted_discord_id: str, summoner_name: str):
        async def callback(interaction: discord.Interaction):
            voter_id = str(interaction.user.id)
            
            # Verifica se o votante está na lista de jogadores
            player_ids = [p['discord_id'] for p in self.players]
            if voter_id not in player_ids:
                await interaction.response.send_message(
                    "❌ Apenas jogadores que participaram da partida podem votar!",
                    ephemeral=True
                )
                return
            
            # Verifica se está votando em si mesmo
            if voter_id == voted_discord_id:
                await interaction.response.send_message(
                    "❌ Você não pode votar em si mesmo!",
                    ephemeral=True
                )
                return
            
            # Registra o voto
            db.add_mvp_vote(self.game_id, voter_id, voted_discord_id)
            
            await interaction.response.send_message(
                f"✅ Você votou em **{summoner_name}** como MVP!",
                ephemeral=True
            )
            
            # Verifica se todos votaram
            votes = db.get_votes_for_game(self.game_id)
            total_players = len(self.players)
            
            if len(votes) >= total_players:
                await self.finalize_voting(interaction)
        
        return callback
    
    async def finalize_voting(self, interaction: discord.Interaction):
        """Finaliza a votação e distribui carry score"""
        try:
            vote_counts = db.get_vote_count_for_game(self.game_id)
            
            if not vote_counts:
                return
            
            # Ordena por quantidade de votos
            sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
            total_voters = len(self.players)
            
            results_text = "**Resultado da Votação:**\n\n"
            
            # Verifica se é voto unânime (todos votaram na mesma pessoa)
            if len(sorted_votes) == 1 and sorted_votes[0][1] == total_voters:
                # Voto unânime - +5 carry score
                winner_id = sorted_votes[0][0]
                db.add_carry_score(winner_id, self.game_id, 5, "Voto unânime de MVP")
                
                try:
                    winner = await bot.fetch_user(int(winner_id))
                    results_text += f"👑 **VOTO UNÂNIME!** <@{winner_id}> recebeu **+5 Carry Score**!"
                except:
                    results_text += f"👑 **VOTO UNÂNIME!** <@{winner_id}> recebeu **+5 Carry Score**!"
            else:
                # Distribui pontos normalmente
                first_place_votes = sorted_votes[0][1] if sorted_votes else 0
                
                # Encontra todos os empatados em primeiro
                first_place_winners = [v[0] for v in sorted_votes if v[1] == first_place_votes]
                
                if len(first_place_winners) > 1:
                    # Empate no primeiro lugar - +2 cada
                    for winner_id in first_place_winners:
                        db.add_carry_score(winner_id, self.game_id, 2, "Empate em 1º lugar MVP")
                        results_text += f"🥇 <@{winner_id}> - **{first_place_votes} votos** → **+2 Carry Score** (empate)\n"
                else:
                    # Primeiro lugar único - +3
                    winner_id = first_place_winners[0]
                    db.add_carry_score(winner_id, self.game_id, 3, "1º lugar MVP")
                    results_text += f"🥇 <@{winner_id}> - **{first_place_votes} votos** → **+3 Carry Score**\n"
                    
                    # Segundo lugar (se existir e não for empate)
                    if len(sorted_votes) > 1:
                        second_place_votes = sorted_votes[1][1]
                        second_place_winners = [v[0] for v in sorted_votes if v[1] == second_place_votes and v[0] not in first_place_winners]
                        
                        for second_id in second_place_winners:
                            db.add_carry_score(second_id, self.game_id, 2, "2º lugar MVP")
                            results_text += f"🥈 <@{second_id}> - **{second_place_votes} votos** → **+2 Carry Score**\n"
            
            # Fecha a votação
            db.close_pending_vote(self.game_id, self.guild_id)
            
            # Atualiza a mensagem original
            embed = discord.Embed(
                title="🏆 VOTAÇÃO ENCERRADA",
                description=results_text,
                color=discord.Color.green()
            )
            
            # Desabilita todos os botões
            for item in self.children:
                item.disabled = True
            
            await interaction.message.edit(embed=embed, view=self)
            
            print(f"✅ [Votação] Votação finalizada para partida {self.game_id}")
            
        except Exception as e:
            print(f"❌ [Votação] Erro ao finalizar votação: {e}")
            import traceback
            traceback.print_exc()
    
    async def on_timeout(self):
        """Chamado quando a votação expira"""
        try:
            vote_counts = db.get_vote_count_for_game(self.game_id)
            
            if vote_counts:
                # Processa votos mesmo com timeout
                sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
                
                results_text = "**Votação encerrada por tempo:**\n\n"
                
                if sorted_votes:
                    first_place_votes = sorted_votes[0][1]
                    first_place_winners = [v[0] for v in sorted_votes if v[1] == first_place_votes]
                    
                    if len(first_place_winners) > 1:
                        for winner_id in first_place_winners:
                            db.add_carry_score(winner_id, self.game_id, 2, "Empate em 1º lugar MVP (timeout)")
                            results_text += f"🥇 <@{winner_id}> - **{first_place_votes} votos** → **+2 Carry Score**\n"
                    else:
                        winner_id = first_place_winners[0]
                        db.add_carry_score(winner_id, self.game_id, 3, "1º lugar MVP (timeout)")
                        results_text += f"🥇 <@{winner_id}> - **{first_place_votes} votos** → **+3 Carry Score**\n"
                
                # Fecha a votação
                db.close_pending_vote(self.game_id, self.guild_id)
                
                print(f"⏱️ [Votação] Votação expirada para partida {self.game_id}, votos processados")
            else:
                results_text = "**Votação encerrada - Nenhum voto recebido**"
                db.close_pending_vote(self.game_id, self.guild_id)
                print(f"⏱️ [Votação] Votação expirada para partida {self.game_id}, sem votos")
            
        except Exception as e:
            print(f"❌ [Votação] Erro no timeout: {e}")

async def check_champion_performance(lol_account_id: int, champion_name: str):
    """Sistema de PROIBIÇÃO PROGRESSIVA - Verifica se o jogador teve performances ruins com o mesmo campeão
    Sistema de Stack: 2 dias → 4 dias → 1 semana
    Reseta após 3 dias do último banimento ou ao atingir o máximo

    Critérios de Proibição:
    1. 3 partidas ruins seguidas (< 45 pontos cada) - mostra todas as 3 partidas
    2. Partida ATUAL abaixo de 35 pontos (independente das anteriores) - mostra apenas a partida atual
    
    IMPORTANTE: Nível de ban é ESPECÍFICO POR CAMPEÃO. Se trocar de campeão, volta para nível 1."""
    try:
        # Busca as últimas 3 partidas com esse campeão
        matches = db.get_last_n_matches_with_champion(lol_account_id, champion_name, n=3)

        # Se não tem nenhuma partida, não faz nada
        if len(matches) == 0:
            return

        # CRITÉRIO 1: Sistema antigo - verifica se todas as 3 têm MVP Score abaixo de 45 (requer 3 partidas)
        all_bad_scores = len(matches) >= 3 and all(match.get('mvp_score', 0) < 45 for match in matches)

        # CRITÉRIO 2: Critério rigoroso - verifica se a PARTIDA ATUAL (primeira da lista) ficou abaixo de 35 pontos
        current_match_below_35 = matches[0].get('mvp_score', 0) < 35

        # Dispara alerta se qualquer um dos critérios for atendido
        should_alert = all_bad_scores or current_match_below_35

        if not should_alert:
            return
        
        # 🔥 NOVA VALIDAÇÃO: Verifica se já foi enviado alerta para esta partida atual com este campeão
        current_match_id = matches[0].get('match_id')
        if db.was_performance_alert_sent(lol_account_id, current_match_id, champion_name):
            print(f"⏭️ [Performance Alert] Alerta já enviado para partida {current_match_id} com {champion_name}, pulando...")
            return
        
        # Determina o nível de banimento (progressivo)
        current_level = db.get_champion_ban_level(lol_account_id, champion_name)
        
        # Sistema de stack: 1 (2 dias) → 2 (4 dias) → 3 (1 semana)
        if current_level == 0:
            new_level = 1
            ban_days = 2
        elif current_level == 1:
            new_level = 2
            ban_days = 4
        elif current_level == 2:
            new_level = 3
            ban_days = 7
        else:  # Já está no máximo (3), reseta para 1
            new_level = 1
            ban_days = 2
        
        # Determina a razão do banimento
        if current_match_below_35:
            reason = "Partida atual abaixo de 35 pontos"
        else:
            reason = "3 partidas ruins seguidas (< 45 pontos)"
        
        # Registra o banimento no banco
        db.add_champion_ban(lol_account_id, champion_name, ban_days, new_level, reason)
        
        # Registra pintado de ouro (+1) quando recebe banimento
        current_match = matches[0] if matches else None
        if current_match:
            match_id = current_match.get('match_id', f"ban_{champion_name}_{datetime.now().timestamp()}")
            mvp_score = current_match.get('mvp_score', 0)
            role = current_match.get('role', 'Unknown')
            db.add_gold_medal(lol_account_id, champion_name, role, match_id, mvp_score)
            print(f"🎨 [Pintado de Ouro] {champion_name} - Banimento aplicado!")
        
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
            
            # Calcula média dos MVP Scores
            avg_mvp_score = sum(m.get('mvp_score', 0) for m in matches) / len(matches)

            # Determina qual critério foi atendido para personalizar a mensagem
            alert_reason = ""
            if current_match_below_35:
                alert_reason = "• Teve uma partida abaixo de 35 pontos!"
            else:
                alert_reason = "• 3 partidas ruins seguidas (< 45 pontos cada)!"

            # Define emoji e cor baseado no nível
            if new_level == 1:
                level_emoji = "⚠️"
                level_color = discord.Color.orange()
                level_text = "NÍVEL 1"
            elif new_level == 2:
                level_emoji = "🚨"
                level_color = discord.Color.red()
                level_text = "NÍVEL 2"
            else:  # nível 3
                level_emoji = "🔴"
                level_color = discord.Color.dark_red()
                level_text = "NÍVEL 3 (MÁXIMO)"
            
            embed = discord.Embed(
                title=f"{level_emoji} BANIMENTO PROGRESSIVO - {level_text}",
                description=f"{member.mention} está **PROIBIDO** de jogar com **{champion_name}** por **{ban_days} dias**!",
                color=level_color
            )

            # Filtra partidas baseado no critério atendido
            if current_match_below_35:
                # Mostra apenas a partida atual (primeira da lista)
                relevant_matches = [matches[0]]
                field_title = "🎯 Partida Problemática"
                field_desc = f"Partida atual com MVP Score abaixo de 35 pontos com {champion_name}"
            else:
                # Mostra todas as 3 partidas ruins
                relevant_matches = matches
                field_title = "🎯 Últimas 3 Partidas"
                field_desc = f"As 3 partidas ruins seguidas com {champion_name}"

            embed.add_field(
                name="📊 Estatísticas Recentes",
                value=(
                    f"🎮 **{len(relevant_matches)}** partida(s) relevante(s) com {champion_name}\n"
                    f"👑 MVP Score médio: **{int(avg_mvp_score)}/100**\n"
                    f"⚠️ {alert_reason}"
                ),
                inline=False
            )

            # Adiciona detalhes das partidas relevantes
            matches_text = ""
            for i, match in enumerate(relevant_matches, 1):
                result_emoji = "✅" if match['win'] else "❌"
                mvp_placement = match.get('mvp_placement', 0)
                matches_text += (
                    f"{result_emoji} MVP: **{match.get('mvp_score', 0)} ({mvp_placement}º)** | "
                    f"{match['kills']}/{match['deaths']}/{match['assists']}\n"
                )

            embed.add_field(
                name=field_title,
                value=matches_text.strip(),
                inline=False
            )
            
            embed.add_field(
                name="🚫 SISTEMA DE BANIMENTO PROGRESSIVO",
                value=(
                    "**Critérios de Proibição:**\n"
                    "• **3 partidas ruins seguidas** (< 45 pontos cada)\n"
                    "• **Pelo menos 1 partida abaixo de 35 pontos**\n\n"
                    "**Sistema de Stack:**\n"
                    "• **Nível 1:** 2 dias de banimento\n"
                    "• **Nível 2:** 4 dias de banimento\n"
                    "• **Nível 3:** 1 semana de banimento\n\n"
                    "**Reset:** Após 3 dias do último banimento ou ao atingir nível máximo"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Conta: {summoner_name}")
            
            # Envia notificação
            try:
                await channel.send(embed=embed)
                
                # 🔥 Marca que o alerta foi enviado para esta partida e campeão
                alert_type = "below_35" if current_match_below_35 else "3_bad_matches"
                db.mark_performance_alert_sent(lol_account_id, current_match_id, champion_name, alert_type)
                
                if current_match_below_35:
                    print(f"⚠️ Alerta enviado: {summoner_name} com {champion_name} (partida abaixo de 35 pontos)")
                else:
                    print(f"⚠️ Alerta enviado: {summoner_name} com {champion_name} (3 partidas ruins seguidas)")
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
        
        # Busca APENAS o primeiro servidor válido onde está o bot (envia apenas UMA vez)
        for guild in bot.guilds:
            # Verifica se o usuário está nesse servidor
            member = guild.get_member(int(discord_id))
            if not member:
                continue
            
            # Busca canal configurado (prioriza live games, depois partidas como fallback)
            channel_id = db.get_live_game_channel(str(guild.id))
            if not channel_id:
                channel_id = db.get_match_channel(str(guild.id))
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
            
            # Formata tempo de jogo (se negativo ou 0, mostra 00:00)
            if game_length <= 0:
                game_time_display = "00:00"
            else:
                game_time_display = f"{game_time_min}:{game_time_sec:02d}"
            
            embed.add_field(
                name="⏱️ Tempo de Jogo",
                value=f"**{game_time_display}**",
                inline=True
            )
            
            # Campo vazio para quebra de linha (força os times a ficarem lado a lado)
            embed.add_field(
                name="\u200b",
                value="\u200b",
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
            
            # Envia notificação e salva message_id
            try:
                message = await channel.send(embed=embed)
                print(f"🔴 Live game: {summoner_name} - {live_info['champion']} ({live_info['gameMode']})")
                
                # Retorna informações da mensagem para salvar no banco
                return {
                    'message_id': str(message.id),
                    'channel_id': str(channel.id),
                    'guild_id': str(guild.id)
                }
            except Exception as e:
                print(f"Erro ao enviar notificação de live game: {e}")
                return None
    
    except Exception as e:
        print(f"Erro ao processar notificação de live game: {e}")

async def update_live_game_notification(game_id: str, guild_id: str, new_players: list):
    """Atualiza uma mensagem de live game existente com novos jogadores detectados"""
    try:
        print(f"🔍 [Update Live] Iniciando atualização para game {game_id}, guild {guild_id}")
        print(f"🔍 [Update Live] Novos jogadores recebidos: {len(new_players)}")
        
        # Busca a mensagem existente
        message_info = db.get_live_game_message_by_game_id(game_id, guild_id)
        if not message_info:
            print(f"⚠️ [Update Live] Mensagem não encontrada para game {game_id}")
            return False
        
        print(f"🔍 [Update Live] Mensagem encontrada: {message_info['message_id']}")
        
        # Busca o canal e a mensagem
        guild = bot.get_guild(int(message_info['guild_id']))
        if not guild:
            return False
        
        channel = guild.get_channel(int(message_info['channel_id']))
        if not channel:
            return False
        
        try:
            message = await channel.fetch_message(int(message_info['message_id']))
        except:
            print(f"⚠️ [Update Live] Erro ao buscar mensagem {message_info['message_id']}")
            return False
        
        # Busca todos os jogadores já notificados (incluindo os novos)
        print(f"🔍 [Update Live] Buscando todos os jogadores do banco para game {game_id}, guild {guild_id}")
        all_players_data = db.get_live_game_players(game_id, guild_id)
        print(f"🔍 [Update Live] Jogadores encontrados no banco: {len(all_players_data)}")
        for player_data in all_players_data:
            print(f"   📋 Player: {player_data['summoner_name']} (discord_id: {player_data['discord_id']}, champion: {player_data['champion_name']})")
        
        # Busca os members do Discord
        members = []
        for player_data in all_players_data:
            member = guild.get_member(int(player_data['discord_id']))
            if member:
                members.append({
                    'member': member,
                    'summoner_name': player_data['summoner_name'],
                    'champion_name': player_data['champion_name']
                })
                print(f"   ✅ Member encontrado: {member.display_name} ({player_data['summoner_name']})")
            else:
                print(f"   ⚠️ Member NÃO encontrado para discord_id {player_data['discord_id']} ({player_data['summoner_name']})")
        
        print(f"🔍 [Update Live] Total de members encontrados: {len(members)}")
        
        if not members:
            print(f"⚠️ [Update Live] Nenhum member encontrado, abortando atualização")
            return False
        
        # Pega o embed antigo e atualiza
        if not message.embeds:
            print(f"⚠️ [Update Live] Mensagem não tem embeds")
            return False
        
        old_embed = message.embeds[0]
        
        print(f"🔍 [Update Live] Criando novo embed com {len(members)} jogadores")
        print(f"🔍 [Update Live] Jogadores que serão mencionados:")
        for m in members:
            print(f"   👤 {m['member'].display_name} ({m['summoner_name']}) - {m['champion_name']}")
        
        # Cria novo embed mantendo as informações originais
        new_embed = discord.Embed(
            title="🔴 PARTIDA EM GRUPO AO VIVO!" if len(members) > 1 else "🔴 PARTIDA AO VIVO!",
            description=f"**{len(members)} jogador{'es' if len(members) > 1 else ''}** em partida!\n\n" + ", ".join([m['member'].mention for m in members]),
            color=old_embed.color,
            timestamp=old_embed.timestamp
        )
        
        # Mantém os campos originais (times, modo de jogo, etc.)
        print(f"🔍 [Update Live] Copiando {len(old_embed.fields)} campos do embed original")
        for field in old_embed.fields:
            new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
        
        # Mantém footer e thumbnail
        if old_embed.footer:
            new_embed.set_footer(text=old_embed.footer.text, icon_url=old_embed.footer.icon_url)
        if old_embed.thumbnail:
            new_embed.set_thumbnail(url=old_embed.thumbnail.url)
        
        # Edita a mensagem
        print(f"🔍 [Update Live] Editando mensagem {message.id}...")
        await message.edit(embed=new_embed)
        print(f"✅ [Update Live] Mensagem atualizada com {len(members)} jogadores na partida {game_id}")
        return True
        
    except Exception as e:
        print(f"❌ [Update Live] Erro ao atualizar mensagem: {e}")
        import traceback
        traceback.print_exc()
        return False

async def send_live_game_notification_grouped(game_id: str, players: list):
    """Envia UMA notificação para múltiplos jogadores na mesma partida"""
    try:
        # Usa as informações do primeiro jogador como base
        first_player = players[0]
        live_info = first_player['live_info']
        
        # Busca o servidor comum (assume que todos estão no mesmo servidor)
        # Pega o primeiro guild onde pelo menos um jogador está
        target_guild = None
        target_channel = None
        
        for guild in bot.guilds:
            # Verifica se todos os jogadores estão neste servidor
            members_in_guild = []
            for player in players:
                member = guild.get_member(int(player['discord_id']))
                if member:
                    members_in_guild.append(member)
            
            # Se tem pelo menos 2 jogadores nesse servidor, usa ele
            if len(members_in_guild) >= 2:
                target_guild = guild
                
                # Busca canal configurado (prioriza live games, depois partidas como fallback)
                channel_id = db.get_live_game_channel(str(guild.id))
                if not channel_id:
                    channel_id = db.get_match_channel(str(guild.id))
                if channel_id:
                    target_channel = guild.get_channel(int(channel_id))
                    if target_channel:
                        break
        
        if not target_guild or not target_channel:
            print(f"⚠️ Servidor ou canal não encontrado para partida agrupada {game_id}")
            return None
        
        # Busca os members
        members = []
        for player in players:
            member = target_guild.get_member(int(player['discord_id']))
            if member:
                members.append({'member': member, 'player': player})
        
        if not members:
            return None
        
        # Determina cor baseada no modo de jogo
        queue_id = live_info.get('queueId', 0)
        if queue_id == 440:  # Ranked Flex
            color = discord.Color.gold()
        elif queue_id == 420:  # Ranked Solo/Duo
            color = discord.Color.purple()
        else:
            color = discord.Color.blue()

        players_mentions = ", ".join([m['member'].mention for m in members])
        
        embed = discord.Embed(
            title="🔴 PARTIDA EM GRUPO AO VIVO!",
            description=f"**{len(members)} jogadores** entraram em partida juntos!\n\n{players_mentions}",
            color=color,
            timestamp=datetime.now()
        )
        
        # Informações principais
        embed.add_field(
            name="🎮 Modo de Jogo",
            value=f"**{live_info['gameMode']}**",
            inline=True
        )
        
        # Calcula tempo de jogo
        game_length = live_info.get('gameLength', 0)
        game_time_min = game_length // 60
        game_time_sec = game_length % 60
        
        if game_length <= 0:
            game_time_display = "00:00"
        else:
            game_time_display = f"{game_time_min}:{game_time_sec:02d}"
        
        embed.add_field(
            name="⏱️ Tempo de Jogo",
            value=f"**{game_time_display}**",
            inline=True
        )
        
        # Campo vazio para quebra de linha (força os times a ficarem lado a lado)
        embed.add_field(
            name="\u200b",
            value="\u200b",
            inline=True
        )
        
        # Lista os jogadores e seus campeões
        players_text = ""
        for m in members:
            info = m['player']['live_info']
            role_emoji = {
                'TOP': '⚔️', 'JUNGLE': '🌳', 'MIDDLE': '✨',
                'BOTTOM': '🏹', 'UTILITY': '🛡️'
            }.get(info.get('role', ''), '❓')
            
            players_text += f"{role_emoji} **{info['champion']}** - {m['member'].display_name}\n"
        
        
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
        
        embed.set_footer(
            text=f"Game ID: {game_id} • {first_player['region'].upper()}",
            icon_url="https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/ranked-emblem-flex.png"
        )
        
        # Envia notificação
        try:
            message = await target_channel.send(embed=embed)
            print(f"🔴 Live game agrupado: {len(members)} jogadores - {live_info['gameMode']}")
            
            return {
                'message_id': str(message.id),
                'channel_id': str(target_channel.id),
                'guild_id': str(target_guild.id)
            }
        except Exception as e:
            print(f"Erro ao enviar notificação agrupada: {e}")
            return None
    
    except Exception as e:
        print(f"Erro ao processar notificação agrupada: {e}")
        return None

@tasks.loop(seconds=180)
async def check_live_games():
    """Task que verifica se jogadores estão em partidas ao vivo a cada 3 minutos (180 segundos)"""
    try:
        print("🔄 [Live Games] Verificando partidas ao vivo...")
        
        # Limpa notificações antigas (mais de 6 horas)
        db.cleanup_old_live_game_notifications(hours=6)

        # Conta quantas notificações ativas existem
        active_count = len(db.get_active_live_games(hours=1))
        print(f"📊 [Live Games] {active_count} notificações ativas na última hora")
        
        # Busca todas as contas vinculadas
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, puuid, region, discord_id, summoner_name FROM lol_accounts')
        accounts = cursor.fetchall()
        conn.close()
        
        if not accounts:
            print("⚠️ [Live Games] Nenhuma conta vinculada para verificar")
            return
        
        print(f"📊 [Live Games] Verificando {len(accounts)} conta(s)...")
        
        # Agrupa jogadores por partida (game_id) e evita processamento duplicado
        games_map = {}  # game_id -> [(account_id, puuid, region, discord_id, summoner_name, live_info)]
        processed_game_ids = set()  # Para evitar processamento duplicado na mesma execução

        for account_id, puuid, region, discord_id, summoner_name in accounts:
            try:
                # Busca se está em partida ativa
                game_data = await riot_api.get_active_game(puuid, region)

                if game_data:
                    game_id = str(game_data.get('gameId'))
                    queue_id = game_data.get('gameQueueConfigId', 0)
                    
                    # Filtra apenas Ranked Flex (440) e Personalizadas (0)
                    if queue_id not in [440, 0]:
                        print(f"⚠️ [Live Games] Partida {game_id} ignorada (queueId: {queue_id} - não é Flex ou Personalizada)")
                        continue

                    # Verificação GLOBAL: se esta partida foi notificada recentemente (últimos 5 minutos), pula TUDO
                    last_notification = db.get_live_game_notification_time(game_id)
                    if last_notification:
                        from datetime import datetime, timedelta
                        try:
                            notification_time = datetime.fromisoformat(last_notification.replace('Z', '+00:00'))
                            now = datetime.now(notification_time.tzinfo) if notification_time.tzinfo else datetime.now()
                            if (now - notification_time) < timedelta(minutes=5):
                                print(f"⚠️ [Live Games] Partida {game_id} foi notificada há {(now - notification_time).seconds // 60} minutos, pulando...")
                                continue
                        except Exception as e:
                            print(f"⚠️ [Live Games] Erro ao processar timestamp: {e}")

                    # Verifica se já foi notificado
                    if not db.is_live_game_notified(account_id, game_id):
                        # Extrai informações
                        live_info = riot_api.extract_live_game_info(game_data, puuid)

                        if live_info:
                            # Agrupa por game_id
                            if game_id not in games_map:
                                games_map[game_id] = []

                            games_map[game_id].append({
                                'account_id': account_id,
                                'puuid': puuid,
                                'region': region,
                                'discord_id': discord_id,
                                'summoner_name': summoner_name,
                                'live_info': live_info
                            })
                            print(f"✅ [Live Games] Conta {account_id} ({summoner_name}) adicionada à partida {game_id}")
                    else:
                        print(f"⚠️ [Live Games] Conta {account_id} já notificada para partida {game_id}")

                # Delay entre verificações de contas
                await asyncio.sleep(1.5)
                
            except Exception as e:
                print(f"❌ [Live Games] Erro ao verificar conta {account_id}: {e}")
                continue
        
        # Log resumo de detecções
        if games_map:
            print(f"\n📋 [Live Games] Resumo de detecções:")
            for game_id, players in games_map.items():
                player_names = [p['summoner_name'] for p in players]
                print(f"   🎮 Partida {game_id}: {len(players)} jogador(es) - {', '.join(player_names)}")
        else:
            print(f"\n📋 [Live Games] Nenhuma nova partida detectada")
        
        # Envia notificações agrupadas (verifica se já existe mensagem)
        for game_id, players in games_map.items():
            try:
                print(f"\n🔍 [Live Games] Processando partida {game_id} com {len(players)} jogador(es)...")
                
                # Pula se já processamos esta partida nesta execução
                if game_id in processed_game_ids:
                    print(f"⚠️ [Live Games] Partida {game_id} já processada nesta execução, pulando...")
                    continue

                # Marca como processada antes de processar
                processed_game_ids.add(game_id)

                # Determina o guild_id a ser usado (pega do primeiro jogador)
                target_guild_id = None
                for guild in bot.guilds:
                    member = guild.get_member(int(players[0]['discord_id']))
                    if member:
                        channel_id = db.get_live_game_channel(str(guild.id))
                        if not channel_id:
                            channel_id = db.get_match_channel(str(guild.id))
                        if channel_id:
                            target_guild_id = str(guild.id)
                            break
                
                if not target_guild_id:
                    print(f"⚠️ [Live Games] Nenhum servidor válido encontrado para partida {game_id}")
                    continue

                # Verifica se JÁ EXISTE uma mensagem para esta partida
                existing_message = db.get_live_game_message_by_game_id(game_id, target_guild_id)
                
                if existing_message:
                    # JÁ EXISTE MENSAGEM - apenas marca novos jogadores e atualiza a mensagem
                    print(f"📝 [Live Games] Mensagem já existe para partida {game_id}, atualizando com novos jogadores...")
                    print(f"📝 [Live Games] Mensagem existente: {existing_message['message_id']} no canal {existing_message['channel_id']}")
                    print(f"📝 [Live Games] Novos jogadores a serem adicionados: {len(players)}")
                    
                    # Marca os novos jogadores como notificados
                    for player in players:
                        print(f"   📝 Marcando {player['summoner_name']} (conta {player['account_id']}) como notificado")
                        result = db.mark_live_game_notified(
                            player['account_id'],
                            game_id,
                            player['puuid'],
                            player['summoner_name'],
                            player['live_info']['championId'],
                            player['live_info']['champion'],
                            existing_message['message_id'],
                            existing_message['channel_id'],
                            existing_message['guild_id']
                        )
                        if result:
                            print(f"   ✅ {player['summoner_name']} marcado com sucesso")
                        else:
                            print(f"   ⚠️ Falha ao marcar {player['summoner_name']}")
                    
                    print(f"🔄 [Live Games] Chamando update_live_game_notification...")
                    # Atualiza a mensagem com todos os jogadores (incluindo os novos)
                    update_result = await update_live_game_notification(game_id, target_guild_id, players)
                    if update_result:
                        print(f"✅ [Live Games] Mensagem atualizada com sucesso para partida {game_id}")
                    else:
                        print(f"⚠️ [Live Games] Falha ao atualizar mensagem para partida {game_id}")
                    
                else:
                    # NÃO EXISTE MENSAGEM - cria uma nova
                    print(f"📤 [Live Games] Criando nova mensagem para partida {game_id}...")
                    
                    if len(players) > 1:
                        print(f"🎮 [Live Games] {len(players)} jogadores na mesma partida {game_id}")
                        # Múltiplos jogadores na mesma partida - envia UMA notificação
                        message_info = await send_live_game_notification_grouped(game_id, players)

                        # Marca TODOS como notificados com a mesma mensagem
                        if message_info:
                            for player in players:
                                db.mark_live_game_notified(
                                    player['account_id'],
                                    game_id,
                                    player['puuid'],
                                    player['summoner_name'],
                                    player['live_info']['championId'],
                                    player['live_info']['champion'],
                                    message_info.get('message_id'),
                                    message_info.get('channel_id'),
                                    message_info.get('guild_id')
                                )
                            print(f"✅ [Live Games] Nova mensagem criada para partida {game_id}")
                    else:
                        # Apenas 1 jogador - envia notificação individual normal
                        player = players[0]
                        message_info = await send_live_game_notification(player['account_id'], player['live_info'])

                        if message_info:
                            db.mark_live_game_notified(
                                player['account_id'],
                                game_id,
                                player['puuid'],
                                player['summoner_name'],
                                player['live_info']['championId'],
                                player['live_info']['champion'],
                                message_info.get('message_id'),
                                message_info.get('channel_id'),
                                message_info.get('guild_id')
                            )
                            print(f"✅ [Live Games] Nova mensagem criada para partida {game_id}")
                            
            except Exception as e:
                print(f"❌ [Live Games] Erro ao enviar notificação para game {game_id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("✅ [Live Games] Verificação concluída")
    
    except Exception as e:
        print(f"❌ [Live Games] Erro geral ao verificar live games: {e}")
        import traceback
        traceback.print_exc()

@check_live_games.before_loop
async def before_check_live_games():
    """Espera o bot estar pronto antes de iniciar o loop de live games"""
    print("⏳ [Live Games] Aguardando bot estar pronto...")
    await bot.wait_until_ready()
    print("✅ [Live Games] Bot pronto! Iniciando verificação de live games...")

@check_live_games.error
async def check_live_games_error(error):
    """Trata erros no loop de live games"""
    print(f"❌ [Live Games] Erro crítico no loop: {error}")
    import traceback
    traceback.print_exc()
    # Task loop automaticamente reinicia após erro

@tasks.loop(minutes=2)
async def check_new_matches():
    """Task que verifica novas partidas a cada 5 minutos (sistema automático completo)"""
    try:
        print("🔄 [Partidas] Verificando novas partidas...")

        # Busca todas as contas vinculadas
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, puuid, region FROM lol_accounts WHERE is_corrupted = 0 OR is_corrupted IS NULL')
        accounts = cursor.fetchall()
        conn.close()

        if not accounts:
            print("⚠️ [Partidas] Nenhuma conta vinculada para verificar")
            return

        print(f"📊 [Partidas] Verificando {len(accounts)} conta(s)...")
        new_matches_count = 0

        # Processa 8 contas simultaneamente para maior velocidade
        batch_size = 8
        for i in range(0, len(accounts), batch_size):
            batch_accounts = accounts[i:i + batch_size]

            # Processa batch em paralelo
            tasks = []
            for account_id, puuid, region in batch_accounts:
                tasks.append(process_account_batch(account_id, puuid, region, riot_api, db))

            # Aguarda todas as tarefas do batch terminarem
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Processa resultados
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"❌ [Partidas] Erro em processamento paralelo: {result}")
                else:
                    new_matches_count += result

        if new_matches_count > 0:
            print(f"🎮 [Partidas] {new_matches_count} nova(s) partida(s) encontrada(s) e salva(s) automaticamente")
        else:
            print("✅ [Partidas] Verificação concluída - Nenhuma partida nova nas últimas 2 horas")

    except Exception as e:
        print(f"❌ [Partidas] Erro geral ao verificar partidas: {e}")
        import traceback
        traceback.print_exc()

async def process_account_batch(account_id: int, puuid: str, region: str, riot_api, db) -> int:
    """Processa uma conta específica em paralelo"""
    try:
        print(f"🔍 Buscando partidas recentes para conta {account_id}...")

        # Busca apenas 1 partida (otimizado)
        flex_matches = await riot_api.get_flex_matches_batch(puuid, region, max_matches=1)

        if not flex_matches:
            print(f"⚠️ Nenhuma partida de flex encontrada para conta {account_id}")
            return 0

        print(f"📋 Encontrada {len(flex_matches)} partida de flex para conta {account_id}")
        matches_processed = 0

        # Verifica cada partida e salva apenas as novas E recentes
        for match_data in flex_matches:
            match_id = match_data['metadata']['matchId']

            # Verifica se já está registrada
            if db.get_last_match_id(account_id) == match_id:
                print(f"⏭️ Partida {match_id} já registrada, pulando")
                continue

            # Verifica se a partida acabou recentemente (última 1 hora)
            game_end_timestamp = match_data.get('info', {}).get('gameEndTimestamp')
            if game_end_timestamp:
                from datetime import datetime, timedelta
                game_end = datetime.fromtimestamp(game_end_timestamp / 1000)
                now = datetime.now()
                time_diff = (now - game_end).total_seconds()

                # Só processa partidas que acabaram há menos de 2 horas
                if time_diff > 7200:  # 2 horas
                    print(f"⏭️ Partida {match_id} antiga ({time_diff//60:.0f}min atrás, limite 2h), pulando")
                    continue

                print(f"🕐 Partida {match_id} terminou há {time_diff//60:.0f}min - processando...")

            try:
                # Extrai estatísticas
                stats = riot_api.extract_player_stats(match_data, puuid)

                if stats:
                    # Salva automaticamente no banco
                    success = db.add_match(account_id, stats)

                    if success:
                        matches_processed += 1

                        # Log diferente para remakes
                        if stats.get('is_remake', False):
                            print(f"⚠️ [Partidas] Remake registrado: {match_id} ({stats['game_duration']}s)")
                        else:
                            print(f"✅ [Partidas] Nova partida registrada: {match_id} (MVP: {stats.get('mvp_score', 0)})")

                        # Verifica performance apenas se não for remake
                        if not stats.get('is_remake', False):
                            await check_champion_performance(account_id, stats['champion_name'])

                        # Envia notificação automática da nova partida
                        await send_match_notification(account_id, stats)

                    else:
                        print(f"⚠️ Falha ao salvar partida {match_id} no banco")

            except Exception as e:
                print(f"❌ Erro ao processar partida {match_id}: {e}")
                continue

        return matches_processed

    except Exception as e:
        print(f"❌ [Partidas] Erro ao verificar conta {account_id}: {e}")
        return 0

@check_new_matches.before_loop
async def before_check_matches():
    """Espera o bot estar pronto antes de iniciar o loop"""
    print("⏳ [Partidas] Aguardando bot estar pronto...")
    await bot.wait_until_ready()
    print("✅ [Partidas] Bot pronto! Iniciando verificação de partidas...")

@check_new_matches.error
async def check_new_matches_error(error):
    """Trata erros no loop de verificação de partidas"""
    print(f"❌ [Partidas] Erro crítico no loop: {error}")
    import traceback
    traceback.print_exc()
    # Task loop automaticamente reinicia após erro

@tasks.loop(seconds=60)
async def check_live_games_finished():
    """Task que verifica a cada 60 segundos se jogos ao vivo já terminaram"""
    try:
        # Busca todas as live games notificadas recentemente (últimas 2 horas)
        live_games = db.get_active_live_games(hours=2)
        
        if not live_games:
            return
        
        print(f"🔄 [Live Check] Verificando {len(live_games)} partida(s) ao vivo...")

        # Debug: mostra informações das live games encontradas
        for lg in live_games:
            print(f"   📋 Live Game: {lg['game_id']} | Conta: {lg['lol_account_id']} | PUUID: {lg['puuid']}")

        # Agrupa por match_id para processar uma vez por partida
        processed_matches = set()
        
        for live_game in live_games:
            account_id = live_game['lol_account_id']
            game_id = live_game['game_id']
            
            try:
                # Busca informações da conta
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT puuid, region FROM lol_accounts WHERE id = ?', (account_id,))
                account_data = cursor.fetchone()
                conn.close()
                
                if not account_data:
                    continue
                
                puuid, region = account_data
                
                # Busca últimas 5 partidas (para ter mais opções de comparação)
                print(f"🔍 [Live Check] Buscando histórico para PUUID {puuid} na região {region}")
                match_ids = await riot_api.get_match_history(puuid, region, count=5)

                if not match_ids:
                    print(f"⚠️ [Live Check] Nenhum histórico encontrado para {puuid}")
                    continue

                print(f"🔍 [Live Check] Partidas encontradas: {match_ids}")

                # Busca a partida que pode ser a live game (verifica as últimas 5)
                match_id = None
                for mid in match_ids:
                    # Busca detalhes da partida para verificar se terminou recentemente
                    match_data = await riot_api.get_match_details(mid, region)
                    if match_data:
                        game_end_timestamp = match_data.get('info', {}).get('gameEndTimestamp')
                        if game_end_timestamp:
                            from datetime import datetime, timedelta
                            game_end = datetime.fromtimestamp(game_end_timestamp / 1000)
                            now = datetime.now()

                            # Se terminou há menos de 15 minutos, pode ser nossa partida
                            if (now - game_end) < timedelta(minutes=15):
                                match_id = mid
                                print(f"🔍 [Live Check] Candidato encontrado: {match_id} (terminou há {(now - game_end).seconds // 60} minutos)")
                                break

                if not match_id:
                    print(f"⚠️ [Live Check] Nenhuma partida recente encontrada para {puuid}")
                    continue

                print(f"🔍 [Live Check] Verificando partida {match_id} para live game {game_id}")

                # Busca informações da live game para comparar com a partida terminada
                live_game_info = db.get_live_game_message(account_id, match_id)
                if live_game_info:
                    print(f"🔍 [Live Check] Comparando live game {game_id} com partida terminada {match_id}")
                    print(f"   PUUID live: {live_game_info['puuid']} | PUUID partida: {puuid}")

                    # Se os PUUIDs batem, é a mesma partida
                    if live_game_info['puuid'] == puuid:
                        print(f"✅ [Live Check] PUUID corresponde - é a mesma partida!")
                    else:
                        print(f"⚠️ [Live Check] PUUID diferente - pode ser outra partida")
                        # Continua verificando mesmo assim, pois pode ser a mesma partida com PUUID diferente
                else:
                    print(f"⚠️ [Live Check] Nenhuma informação de live game encontrada para conta {account_id}")

                # Verifica se já está registrada no banco
                last_match_id = db.get_last_match_id(account_id)
                print(f"🔍 [Live Check] Última partida registrada: {last_match_id} | Nova partida: {match_id}")

                if last_match_id == match_id:
                    print(f"✅ [Live Check] Partida {match_id} já processada, removendo live game {game_id}")
                    # Já foi processada, pode remover da lista de live games
                    db.remove_live_game_notification(account_id, game_id)
                    continue

                print(f"🔍 [Live Check] Partida {match_id} ainda não processada, continuando verificação...")

                # Busca detalhes da partida
                print(f"🔍 [Live Check] Buscando detalhes da partida {match_id}...")
                match_data = await riot_api.get_match_details(match_id, region)

                if match_data:
                    # Verifica se é Ranked Flex (440) ou Personalizada (0)
                    queue_id = match_data.get('info', {}).get('queueId', 0)
                    print(f"🔍 [Live Check] Queue ID da partida: {queue_id}")
                    if queue_id not in [440, 0]:
                        # Não é Ranked Flex nem Personalizada, pula
                        print(f"⚠️ [Live Check] Partida {match_id} não é Flex ou Personalizada (queueId: {queue_id})")
                        continue
                    
                    # Verifica se é a partida do live game (o game_id da spectator API é diferente do match_id)
                    # Então verificamos se a partida terminou recentemente (menos de 10 minutos)
                    game_end_timestamp = match_data.get('info', {}).get('gameEndTimestamp')
                    if game_end_timestamp:
                        from datetime import datetime, timedelta
                        game_end = datetime.fromtimestamp(game_end_timestamp / 1000)
                        now = datetime.now()
                        minutes_ago = (now - game_end).seconds // 60

                        print(f"⏱️ [Live Check] Partida terminou em: {game_end} (há {minutes_ago} minutos)")

                        # Se terminou há menos de 10 minutos, processamos
                        if (now - game_end) < timedelta(minutes=10):
                            print(f"⏱️ [Live Check] Partida terminou recentemente (há {minutes_ago} minutos), iniciando processamento...")

                            # Verificação adicional: comparar campeão da live game com o da partida terminada
                            champion_match = True
                            if live_game_info and live_game_info['champion_name']:
                                participant_champion = None
                                for participant in match_data['info']['participants']:
                                    if participant['puuid'] == puuid:
                                        participant_champion = participant.get('championName', 'Unknown')
                                        break

                                if participant_champion:
                                    print(f"🏆 [Live Check] Campeão live: {live_game_info['champion_name']} | Campeão partida: {participant_champion}")
                                    if live_game_info['champion_name'] != participant_champion:
                                        print(f"⚠️ [Live Check] Campeões diferentes - pode não ser a mesma partida")
                                        champion_match = False
                                        # Continua mesmo assim, pois pode haver erro na comparação

                            if champion_match:
                                print(f"✅ [Live Check] Verificação de campeão passou ou foi ignorada")
                            print(f"🏁 [Live Check] Partida {match_id} terminou recentemente, iniciando processamento...")
                            # Extrai estatísticas do jogador
                            print(f"📊 [Live Check] Extraindo estatísticas para {puuid}...")
                            stats = riot_api.extract_player_stats(match_data, puuid)

                            if stats:
                                print(f"📊 [Live Check] Estatísticas extraídas para {puuid}: {stats['champion_name']} - MVP: {stats['mvp_score']}")

                                # Salva no banco de dados ANTES de tudo
                                print(f"💾 [Live Check] Salvando partida no banco de dados...")
                                save_result = db.add_match(account_id, stats)
                                if save_result:
                                    print(f"✅ [Live Check] Partida salva no banco com sucesso!")
                                else:
                                    print(f"⚠️ [Live Check] Falha ao salvar partida no banco (pode já existir)")

                                # Atualiza o resultado no live game (apenas uma vez por partida)
                                print(f"🔍 [Live Check] Verificando se deve chamar update_live_game_result...")
                                print(f"   📍 game_id atual: {game_id}")
                                print(f"   📍 processed_matches: {processed_matches}")
                                print(f"   📍 game_id not in processed_matches: {game_id not in processed_matches}")

                                if game_id not in processed_matches:
                                    print(f"🔄🔄🔄 [Live Check] CHAMANDO update_live_game_result 🔄🔄🔄")
                                    print(f"   📍 game_id: {game_id} (tipo: {type(game_id)})")
                                    print(f"   📍 match_id: {match_id}")
                                    print(f"   📍 account_id: {account_id}")
                                    print(f"   📍 puuid: {puuid}")
                                    await update_live_game_result(game_id, match_data)
                                    print(f"✅ [Live Check] update_live_game_result CONCLUÍDA")
                                    processed_matches.add(game_id)
                                    print(f"✅ [Live Check] Game ID {game_id} adicionado a processed_matches")
                                else:
                                    print(f"⏭️ [Live Check] Game ID {game_id} já foi processado, pulando update_live_game_result")

                                # Log diferente para remakes
                                if stats.get('is_remake', False):
                                    print(f"⚠️ [Live Check] Remake detectado: {match_id} ({stats['game_duration']}s)")
                                else:
                                    print(f"✅ [Live Check] Partida terminada detectada: {match_id} (MVP: {stats.get('mvp_score', 0)})")

                                # Envia notificação individual com estatísticas detalhadas
                                print(f"📨 [Live Check] Enviando notificação individual de estatísticas para {account_id}")
                                await send_match_notification(account_id, stats)

                                # Verifica performance apenas se não for remake
                                if not stats.get('is_remake', False):
                                    print(f"📊 [Live Check] Verificando performance do campeão...")
                                    await check_champion_performance(account_id, stats['champion_name'])

                                # Remove da lista de live games
                                print(f"🗑️ [Live Check] Removendo live game {game_id} da lista")
                                db.remove_live_game_notification(account_id, game_id)
                            else:
                                print(f"❌ [Live Check] Falha ao extrair estatísticas para {puuid}")
                
                # Pequeno delay entre contas
                await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"❌ [Live Check] Erro ao verificar partida {game_id}: {e}")
                continue
    
    except Exception as e:
        print(f"❌ [Live Check] Erro geral: {e}")

@check_live_games_finished.before_loop
async def before_check_live_games_finished():
    """Espera o bot estar pronto"""
    print("⏳ [Live Check] Aguardando bot estar pronto...")
    await bot.wait_until_ready()
    print("✅ [Live Check] Iniciando verificação rápida de partidas finalizadas (10s)...")

@check_live_games_finished.error
async def check_live_games_finished_error(error):
    """Trata erros no loop"""
    print(f"❌ [Live Check] Erro crítico: {error}")
    import traceback
    traceback.print_exc()

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

