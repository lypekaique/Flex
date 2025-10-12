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
                "`/media` - Ver estatísticas (por campeão, métrica, outro jogador)\n"
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
    
    # Registra Views persistentes
    bot.add_view(FlexGuideView())
    print('✅ Views persistentes registradas')
    
    # Sincroniza comandos slash
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)} comandos sincronizados')
    except Exception as e:
        print(f'Erro ao sincronizar comandos: {e}')
    
    # Inicia verificação de partidas (verifica se já não está rodando)
    if not check_new_matches.is_running():
        check_new_matches.start()
        print('✅ Task de verificação de partidas iniciada')
    else:
        print('⚠️ Task de verificação de partidas já está rodando')
    
    # Inicia verificação de live games (verifica se já não está rodando)
    if not check_live_games.is_running():
        check_live_games.start()
        print('✅ Task de verificação de live games iniciada')
    else:
        print('⚠️ Task de verificação de live games já está rodando')
    
    # Inicia verificação rápida de partidas finalizadas (a cada 10s)
    if not check_live_games_finished.is_running():
        check_live_games_finished.start()
        print('✅ Task de verificação rápida de partidas finalizadas iniciada (10s)')
    else:
        print('⚠️ Task de verificação rápida já está rodando')

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
        # Busca o ID da conta recém-criada
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
                            # Verifica se é Ranked Flex (queueId 440)
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
        
        # Cria embed bonito
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

# Auto-complete para campeões
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
    metrica="Métrica específica para analisar (carry, kda, dano, cs, visao, kp, gold)",
    usuario="Ver estatísticas de outro jogador (mencione ou digite o nome)",
    conta="Número da conta (1, 2 ou 3). Deixe vazio para ver todas"
)
@app_commands.autocomplete(campeao=champion_autocomplete, metrica=metric_autocomplete)
async def media(interaction: discord.Interaction, campeao: str = None, metrica: str = None, 
                usuario: discord.User = None, conta: int = None):
    """Calcula estatísticas e média de desempenho do mês atual"""
    # Verifica permissão de canal
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
    
    # Cria embed para resultados
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
        if metrica in ['carry', 'mvp'] or not metrica:
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
        description=f"**{len(matches)} partidas mais recentes de Ranked Flex**\n_ _",
        color=discord.Color.purple()
    )
    
    for i, match in enumerate(matches, 1):
        # Verifica se é remake
        is_remake = match.get('is_remake', False)
        
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
**{match['champion_name']}** {role_emoji} {match['role']}
━━━━━━━━━━━━━━━━━━━━━
⚠️ **REMAKE** - Partida cancelada
⏱️ Duração: **{game_duration_min}:{game_duration_sec:02d}**
📅 {match['played_at'][:10]} às {match['played_at'][11:16]}

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
**{match['champion_name']}** {role_emoji} {match['role']} • {result}
━━━━━━━━━━━━━━━━━━━━━
{mvp_emoji} **MVP Score: {mvp_score}/100** ({rank_text})
⚔️ KDA: **{kda_ratio}** ({match['kda']:.2f})
🎯 Kill Participation: **{match['kill_participation']:.0f}%**
🗡️ Dano: **{match['damage_dealt']:,}**
🌾 CS: **{match['cs']}** • 👁️ Vision: **{match['vision_score']}**
📅 {match['played_at'][:10]} às {match['played_at'][11:16]}
            """
        
        embed.add_field(
            name=f"━━━━━━━━━━━━━ Partida #{i} ━━━━━━━━━━━━━",
            value=match_info.strip(),
            inline=False
        )
    
    embed.set_footer(text=f"📊 Apenas Ranked Flex • Região: {account['region'].upper()}")
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
    
    if tipo not in ['alertas', 'score', 'comandos', 'live']:
        await interaction.followup.send(
            "❌ Tipo inválido! Use: `alertas`, `score`, `comandos` ou `live`",
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
    
    else:  # live
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
    """Mostra o ranking dos melhores jogadores por MVP score"""
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
        description=f"**{now.strftime('%B/%Y')}** • Mínimo: 5 partidas\n_Ordenado por MVP Score_",
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
        
        # Determina rank baseado no MVP score
        avg_mvp = player['avg_mvp']
        
        if avg_mvp >= 90:
            rank_emoji = "👑"
        elif avg_mvp >= 80:
            rank_emoji = "⭐"
        elif avg_mvp >= 70:
            rank_emoji = "💎"
        elif avg_mvp >= 60:
            rank_emoji = "🥈"
        elif avg_mvp >= 50:
            rank_emoji = "📊"
        else:
            rank_emoji = "📉"
        
        # Busca usuário do Discord
        try:
            user = await bot.fetch_user(int(player['discord_id']))
            player_name = f"{user.mention}"
        except:
            player_name = player['summoner_name']
        
        player_info = f"""
{position_emoji} {player_name} • {rank_emoji}
👑 **MVP Score:** {int(avg_mvp)}/100
🎮 Jogos: **{player['total_games']}** | ✅ WR: **{player['win_rate']:.1f}%**
⚔️ KDA: **{player['avg_kda']:.2f}** | 🎯 KP: **{player['avg_kp']:.1f}%**
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
        title="🎮 Flex dos Crias",
        description=(
            "**O bot definitivo de tracking para Ranked Flex!**\n\n"
            "Monitore suas partidas, acompanhe seu desempenho em tempo real,\n"
            "e descubra seu verdadeiro nível de carry com nosso sistema avançado.\n"
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
            
            # Cria embed com informações detalhadas
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
            
            # Envia nova mensagem (sempre)
            try:
                await channel.send(embed=embed)
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
        # Busca se existe mensagem de live game para este match
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Debug: Lista todos os game_ids ativos
        cursor.execute('SELECT game_id, message_id FROM live_games_notified WHERE message_id IS NOT NULL')
        all_games = cursor.fetchall()
        print(f"🔍 [Live Update DEBUG] Games ativos no banco: {[(g[0], g[1]) for g in all_games]}")
        
        cursor.execute('''
            SELECT DISTINCT message_id, channel_id, guild_id, lol_account_id
            FROM live_games_notified
            WHERE game_id = ?
              AND message_id IS NOT NULL
            LIMIT 1
        ''', (game_id,))
        live_msg = cursor.fetchone()
        
        if not live_msg:
            print(f"⚠️ [Live Update] Nenhuma mensagem de live game encontrada para game_id: {game_id}")
            print(f"⚠️ [Live Update] Tipo do game_id buscado: {type(game_id)}")
            conn.close()
            return
        
        message_id, channel_id, guild_id, lol_account_id = live_msg
        
        # Busca informações da conta para pegar summoner_name e region
        cursor.execute('''
            SELECT summoner_name, region FROM lol_accounts
            WHERE id = ?
        ''', (lol_account_id,))
        account_info = cursor.fetchone()
        conn.close()
        
        if not account_info:
            print(f"⚠️ [Live Update] Informações da conta {lol_account_id} não encontradas")
            return
        
        summoner_name, region = account_info
        print(f"✅ [Live Update] Mensagem encontrada - ID: {message_id}, Canal: {channel_id}, Servidor: {guild_id}")

        # Busca o servidor e canal
        guild = bot.get_guild(int(guild_id))
        if not guild:
            print(f"⚠️ [Live Update] Servidor {guild_id} não encontrado")
            return

        channel = guild.get_channel(int(channel_id))
        if not channel:
            print(f"⚠️ [Live Update] Canal {channel_id} não encontrado")
            return
        
        try:
            message = await channel.fetch_message(int(message_id))
        except:
            print(f"⚠️ [Live Update] Mensagem {message_id} não encontrada")
            return
        
        # Pega o embed original
        if not message.embeds:
            print(f"⚠️ [Live Update] Mensagem não possui embed")
            return
        
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
            return
        
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
        
        from riot_api import RiotAPI
        riot = RiotAPI()
        
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
                'vision_score': p_vision
            }
            
            mvp_score, _ = riot.calculate_mvp_score(player_stats, all_players_stats, p_role)
            
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
        await message.edit(embed=new_embed)
        print(f"🏁 [Live Update] Mensagem de live game atualizada com sucesso para game_id: {game_id} - {result_text}")
        
    except Exception as e:
        print(f"Erro ao atualizar resultado do live game: {e}")
        import traceback
        traceback.print_exc()

async def check_champion_performance(lol_account_id: int, champion_name: str):
    """Verifica se o jogador teve 3 performances ruins seguidas com o mesmo campeão"""
    try:
        # Busca as últimas 3 partidas com esse campeão
        matches = db.get_last_n_matches_with_champion(lol_account_id, champion_name, n=3)
        
        # Se não tem 3 partidas ainda, não faz nada
        if len(matches) < 3:
            return
        
        # Verifica se todas as 3 têm MVP Score abaixo de 45
        all_bad_scores = all(match.get('mvp_score', 0) < 45 for match in matches)
        
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
            
            # Calcula média dos MVP Scores
            avg_mvp_score = sum(m.get('mvp_score', 0) for m in matches) / 3
            
            # Cria embed de "vergonha"
            embed = discord.Embed(
                title="⚠️ ALERTA DE PERFORMANCE BAIXA",
                description=f"{member.mention} está Proibido de jogar **{champion_name}**!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="📊 Estatísticas Recentes",
                value=(
                    f"🎮 **3 últimas partidas** com {champion_name}\n"
                    f"👑 MVP Score médio: **{int(avg_mvp_score)}/100**\n"
                    f"⚠️ MVP Score abaixo de 45 nas 3 partidas!"
                ),
                inline=False
            )
            
            # Adiciona detalhes das 3 partidas
            matches_text = ""
            for i, match in enumerate(matches, 1):
                result_emoji = "✅" if match['win'] else "❌"
                mvp_placement = match.get('mvp_placement', 0)
                matches_text += (
                    f"{result_emoji} MVP: **{match.get('mvp_score', 0)} ({mvp_placement}º)** | "
                    f"{match['kills']}/{match['deaths']}/{match['assists']}\n"
                )
            
            embed.add_field(
                name="🎯 Últimas 3 Partidas",
                value=matches_text.strip(),
                inline=False
            )
            
            embed.add_field(
                name="😄 Regra",
                value=(
                    "• Está proibido de jogar por 2 dias com esse boneco"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Conta: {summoner_name}")
            
            # Envia notificação
            try:
                await channel.send(embed=embed)
                print(f"⚠️ Notificação enviada: {summoner_name} com {champion_name} (MVP médio: {avg_mvp_score:.2f})")
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
        
        # Cria embed agrupado
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

@tasks.loop(seconds=30)
async def check_live_games():
    """Task que verifica se jogadores estão em partidas ao vivo a cada 30 segundos"""
    try:
        print("🔄 [Live Games] Verificando partidas ao vivo...")
        
        # Limpa notificações antigas (mais de 6 horas)
        db.cleanup_old_live_game_notifications(hours=6)
        
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
        
        # Agrupa jogadores por partida (game_id)
        games_map = {}  # game_id -> [(account_id, puuid, region, discord_id, summoner_name, live_info)]
        
        for account_id, puuid, region, discord_id, summoner_name in accounts:
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
                
                # Delay para não sobrecarregar a API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ [Live Games] Erro ao verificar conta {account_id}: {e}")
                continue
        
        # Envia notificações agrupadas (verifica se já foi notificado globalmente)
        for game_id, players in games_map.items():
            try:
                # Verificação adicional: verifica se QUALQUER jogador desta partida já foi notificado
                already_notified = False
                for player in players:
                    if db.is_live_game_notified(player['account_id'], game_id):
                        already_notified = True
                        break

                if already_notified:
                    print(f"⚠️ [Live Games] Partida {game_id} já foi notificada, pulando...")
                    continue

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
            except Exception as e:
                print(f"❌ [Live Games] Erro ao enviar notificação para game {game_id}: {e}")
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

@tasks.loop(minutes=5)
async def check_new_matches():
    """Task que verifica novas partidas a cada 5 minutos"""
    try:
        print("🔄 [Partidas] Verificando novas partidas...")
        
        # Busca todas as contas vinculadas
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, puuid, region FROM lol_accounts')
        accounts = cursor.fetchall()
        conn.close()
        
        if not accounts:
            print("⚠️ [Partidas] Nenhuma conta vinculada para verificar")
            return
        
        print(f"📊 [Partidas] Verificando {len(accounts)} conta(s)...")
        new_matches_count = 0
        
        for account_id, puuid, region in accounts:
            try:
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
                        # Verifica se é Ranked Flex (queueId 440)
                        queue_id = match_data.get('info', {}).get('queueId', 0)
                        if queue_id != 440:
                            # Não é Ranked Flex, pula essa partida
                            continue
                        
                        # Extrai estatísticas do jogador
                        stats = riot_api.extract_player_stats(match_data, puuid)
                        
                        if stats:
                            # Salva no banco de dados
                            db.add_match(account_id, stats)
                            new_matches_count += 1
                            
                            # Log diferente para remakes
                            if stats.get('is_remake', False):
                                print(f"⚠️ [Partidas] Remake registrado: {match_id} ({stats['game_duration']}s)")
                            else:
                                print(f"✅ [Partidas] Nova partida registrada: {match_id} (MVP: {stats.get('mvp_score', 0)})")
                            
                            # NÃO envia notificação aqui - o check_live_games_finished já cuida disso
                            # await send_match_notification(account_id, stats)
                            
                            # Verifica performance apenas se não for remake
                            if not stats.get('is_remake', False):
                                await check_champion_performance(account_id, stats['champion_name'])
                    
                    # Delay para não sobrecarregar a API
                    await asyncio.sleep(1)
                
                await asyncio.sleep(2)
            
            except Exception as e:
                print(f"❌ [Partidas] Erro ao verificar conta {account_id}: {e}")
                continue
        
        if new_matches_count > 0:
            print(f"🎮 [Partidas] {new_matches_count} nova(s) partida(s) encontrada(s)")
        else:
            print("✅ [Partidas] Verificação concluída - Nenhuma partida nova")
    
    except Exception as e:
        print(f"❌ [Partidas] Erro geral ao verificar partidas: {e}")
        import traceback
        traceback.print_exc()

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

@tasks.loop(seconds=10)
async def check_live_games_finished():
    """Task rápida que verifica a cada 10s se jogos ao vivo já terminaram"""
    try:
        # Busca todas as live games notificadas recentemente (últimas 2 horas)
        live_games = db.get_active_live_games(hours=2)
        
        if not live_games:
            return
        
        print(f"🔄 [Live Check] Verificando {len(live_games)} partida(s) ao vivo...")
        
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
                
                # Busca últimas partidas (apenas 1, a mais recente)
                match_ids = await riot_api.get_match_history(puuid, region, count=1)

                if not match_ids:
                    print(f"⚠️ [Live Check] Nenhum histórico encontrado para {puuid}")
                    continue

                match_id = match_ids[0]
                print(f"🔍 [Live Check] Verificando partida {match_id} para live game {game_id}")

                # Verifica se já está registrada no banco
                last_match_id = db.get_last_match_id(account_id)
                if last_match_id == match_id:
                    print(f"✅ [Live Check] Partida {match_id} já processada, removendo live game {game_id}")
                    # Já foi processada, pode remover da lista de live games
                    db.remove_live_game_notification(account_id, game_id)
                    continue

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
                
                # Busca detalhes da partida
                match_data = await riot_api.get_match_details(match_id, region)
                
                if match_data:
                    # Verifica se é Ranked Flex (queueId 440)
                    queue_id = match_data.get('info', {}).get('queueId', 0)
                    if queue_id != 440:
                        # Não é Ranked Flex, pula
                        continue
                    
                    # Verifica se é a partida do live game (o game_id da spectator API é diferente do match_id)
                    # Então verificamos se a partida terminou recentemente (menos de 10 minutos)
                    game_end_timestamp = match_data.get('info', {}).get('gameEndTimestamp')
                    if game_end_timestamp:
                        from datetime import datetime, timedelta
                        game_end = datetime.fromtimestamp(game_end_timestamp / 1000)
                        now = datetime.now()

                        # Se terminou há menos de 10 minutos, processamos
                        if (now - game_end) < timedelta(minutes=10):
                            print(f"⏱️ [Live Check] Partida terminou há {(now - game_end).seconds // 60} minutos")

                            # Verificação adicional: comparar campeão da live game com o da partida terminada
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
                                        # Continua mesmo assim, pois pode haver erro na comparação
                            print(f"🏁 [Live Check] Partida {match_id} terminou recentemente, iniciando processamento...")
                            # Extrai estatísticas do jogador
                            stats = riot_api.extract_player_stats(match_data, puuid)

                            if stats:
                                print(f"📊 [Live Check] Estatísticas extraídas para {puuid}: {stats['champion_name']} - MVP: {stats['mvp_score']}")
                                
                                # Salva no banco de dados ANTES de tudo
                                db.add_match(account_id, stats)
                                
                                # Atualiza o resultado no live game (apenas uma vez por partida)
                                if match_id not in processed_matches:
                                    print(f"🔄 [Live Check] Atualizando mensagem de live game para {match_id}")
                                    await update_live_game_result(game_id, match_data)
                                    processed_matches.add(match_id)
                                
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
                                    await check_champion_performance(account_id, stats['champion_name'])
                                
                                # Remove da lista de live games
                                db.remove_live_game_notification(account_id, game_id)
                
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

