import aiohttp
import asyncio
from typing import Optional, Dict, List
from datetime import datetime

class RiotAPI:
    """Cliente para interagir com a API da Riot Games"""
    
    # Mapeamento de regiões para endpoints
    REGIONS = {
        'br1': 'br1.api.riotgames.com',
        'eun1': 'eun1.api.riotgames.com',
        'euw1': 'euw1.api.riotgames.com',
        'jp1': 'jp1.api.riotgames.com',
        'kr': 'kr.api.riotgames.com',
        'la1': 'la1.api.riotgames.com',
        'la2': 'la2.api.riotgames.com',
        'na1': 'na1.api.riotgames.com',
        'oc1': 'oc1.api.riotgames.com',
        'tr1': 'tr1.api.riotgames.com',
        'ru': 'ru.api.riotgames.com',
    }
    
    ROUTING = {
        'br1': 'americas',
        'la1': 'americas',
        'la2': 'americas',
        'na1': 'americas',
        'eun1': 'europe',
        'euw1': 'europe',
        'tr1': 'europe',
        'ru': 'europe',
        'jp1': 'asia',
        'kr': 'asia',
        'oc1': 'sea',
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-Riot-Token": api_key
        }
    
    async def get_account_by_riot_id(self, game_name: str, tag_line: str, region: str = 'br1') -> Optional[Dict]:
        """Busca informações da conta pelo Riot ID (nome#tag)"""
        routing = self.ROUTING.get(region, 'americas')
        url = f"https://{routing}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        print(f"Erro na API Riot: {response.status}")
                        return None
            except Exception as e:
                print(f"Erro ao buscar conta: {e}")
                return None
    
    async def get_summoner_by_puuid(self, puuid: str, region: str = 'br1') -> Optional[Dict]:
        """Busca informações do invocador pelo PUUID"""
        if region not in self.REGIONS:
            return None
        
        url = f"https://{self.REGIONS[region]}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        print(f"Erro na API Riot: {response.status}")
                        return None
            except Exception as e:
                print(f"Erro ao buscar invocador: {e}")
                return None
    
    async def get_match_history(self, puuid: str, region: str = 'br1', count: int = 20, 
                                queue: int = 440) -> Optional[List[str]]:
        """Busca histórico de partidas (queue 440 = Ranked Flex)"""
        routing = self.ROUTING.get(region, 'americas')
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        
        params = {
            'start': 0,
            'count': count,
            'queue': queue  # 440 = Ranked Flex 5v5
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Erro ao buscar histórico: {response.status}")
                        return None
            except Exception as e:
                print(f"Erro ao buscar histórico: {e}")
                return None
    
    async def get_match_details(self, match_id: str, region: str = 'br1') -> Optional[Dict]:
        """Busca detalhes de uma partida específica"""
        routing = self.ROUTING.get(region, 'americas')
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Erro ao buscar detalhes da partida: {response.status}")
                        return None
            except Exception as e:
                print(f"Erro ao buscar detalhes da partida: {e}")
                return None
    
    async def get_active_game(self, puuid: str, region: str = 'br1') -> Optional[Dict]:
        """Busca informações de partida em andamento (Spectator API)"""
        if region not in self.REGIONS:
            return None
        
        url = f"https://{self.REGIONS[region]}/lol/spectator/v5/active-games/by-summoner/{puuid}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        # Jogador não está em partida
                        return None
                    else:
                        print(f"Erro ao buscar partida ativa: {response.status}")
                        return None
            except Exception as e:
                print(f"Erro ao buscar partida ativa: {e}")
                return None
    
    def extract_live_game_info(self, game_data: Dict, puuid: str) -> Optional[Dict]:
        """Extrai informações relevantes de uma partida ao vivo"""
        try:
            # Encontra o participante
            participant = None
            for p in game_data.get('participants', []):
                if p.get('puuid') == puuid:
                    participant = p
                    break
        
            if not participant:
                return None
            
            # Mapeamento de game mode
            game_modes = {
                440: 'Ranked Flex',
                420: 'Ranked Solo/Duo',
                400: 'Normal Draft',
                430: 'Normal Blind',
                450: 'ARAM',
            }
            
            queue_id = game_data.get('gameQueueConfigId', 0)
            game_mode = game_modes.get(queue_id, f'Queue {queue_id}')
            
            # Mapeamento de roles
            role_names = {
                'TOP': 'Top',
                'JUNGLE': 'Jungle',
                'MIDDLE': 'Mid',
                'BOTTOM': 'ADC',
                'UTILITY': 'Support'
            }
            
            # Pega informações dos times
            team_100 = []
            team_200 = []
            
            for p in game_data.get('participants', []):
                player_info = {
                    'summonerName': p.get('riotId', p.get('summonerName', 'Unknown')),
                    'championId': p.get('championId', 0),
                    'champion': self.get_champion_name(p.get('championId', 0))
                }
                
                if p.get('teamId') == 100:
                    team_100.append(player_info)
                else:
                    team_200.append(player_info)
            
            live_info = {
                'gameId': game_data.get('gameId'),
                'gameMode': game_mode,
                'queueId': queue_id,
                'champion': self.get_champion_name(participant.get('championId', 0)),
                'championId': participant.get('championId', 0),
                'summonerName': participant.get('riotId', participant.get('summonerName', 'Unknown')),
                'teamId': participant.get('teamId', 100),
                'gameLength': game_data.get('gameLength', 0),  # Em segundos
                'gameStartTime': game_data.get('gameStartTime', 0),
                'team_100': team_100,
                'team_200': team_200,
                'bannedChampions': [self.get_champion_name(b.get('championId', 0)) for b in game_data.get('bannedChampions', [])],
            }
            
            return live_info
        except Exception as e:
            print(f"Erro ao extrair informações de live game: {e}")
            return None
    
    def get_champion_name(self, champion_id: int) -> str:
        """Retorna nome do campeão pelo ID (mapeamento básico)"""
        # Mapeamento de alguns campeões mais comuns - pode ser expandido
        champions = {
            1: 'Annie', 2: 'Olaf', 3: 'Galio', 4: 'TwistedFate', 5: 'XinZhao',
            6: 'Urgot', 7: 'LeBlanc', 8: 'Vladimir', 9: 'Fiddlesticks', 10: 'Kayle',
            11: 'MasterYi', 12: 'Alistar', 13: 'Ryze', 14: 'Sion', 15: 'Sivir',
            16: 'Soraka', 17: 'Teemo', 18: 'Tristana', 19: 'Warwick', 20: 'Nunu',
            21: 'MissFortune', 22: 'Ashe', 23: 'Tryndamere', 24: 'Jax', 25: 'Morgana',
            26: 'Zilean', 27: 'Singed', 28: 'Evelynn', 29: 'Twitch', 30: 'Karthus',
            31: 'Chogath', 32: 'Amumu', 33: 'Rammus', 34: 'Anivia', 35: 'Shaco',
            36: 'DrMundo', 37: 'Sona', 38: 'Kassadin', 39: 'Irelia', 40: 'Janna',
            41: 'Gangplank', 42: 'Corki', 43: 'Karma', 44: 'Taric', 45: 'Veigar',
            48: 'Trundle', 50: 'Swain', 51: 'Caitlyn', 53: 'Blitzcrank', 54: 'Malphite',
            55: 'Katarina', 56: 'Nocturne', 57: 'Maokai', 58: 'Renekton', 59: 'JarvanIV',
            60: 'Elise', 61: 'Orianna', 62: 'Wukong', 63: 'Brand', 64: 'LeeSin',
            67: 'Vayne', 68: 'Rumble', 69: 'Cassiopeia', 72: 'Skarner', 74: 'Heimerdinger',
            75: 'Nasus', 76: 'Nidalee', 77: 'Udyr', 78: 'Poppy', 79: 'Gragas',
            80: 'Pantheon', 81: 'Ezreal', 82: 'Mordekaiser', 83: 'Yorick', 84: 'Akali',
            85: 'Kennen', 86: 'Garen', 89: 'Leona', 90: 'Malzahar', 91: 'Talon',
            92: 'Riven', 96: 'KogMaw', 98: 'Shen', 99: 'Lux', 101: 'Xerath',
            102: 'Shyvana', 103: 'Ahri', 104: 'Graves', 105: 'Fizz', 106: 'Volibear',
            107: 'Rengar', 110: 'Varus', 111: 'Nautilus', 112: 'Viktor', 113: 'Sejuani',
            114: 'Fiora', 115: 'Ziggs', 117: 'Lulu', 119: 'Draven', 120: 'Hecarim',
            121: 'Khazix', 122: 'Darius', 126: 'Jayce', 127: 'Lissandra', 131: 'Diana',
            133: 'Quinn', 134: 'Syndra', 136: 'AurelionSol', 141: 'Kayn', 142: 'Zoe',
            143: 'Zyra', 145: 'Kaisa', 147: 'Seraphine', 150: 'Gnar', 154: 'Zac',
            157: 'Yasuo', 161: 'Velkoz', 163: 'Taliyah', 164: 'Camille', 166: 'Akshan',
            200: 'Belveth', 201: 'Braum', 202: 'Jhin', 203: 'Kindred', 221: 'Zeri',
            222: 'Jinx', 223: 'TahmKench', 234: 'Viego', 235: 'Senna', 236: 'Lucian',
            238: 'Zed', 240: 'Kled', 245: 'Ekko', 246: 'Qiyana', 254: 'Vi',
            266: 'Aatrox', 267: 'Nami', 268: 'Azir', 350: 'Yuumi', 360: 'Samira',
            412: 'Thresh', 420: 'Illaoi', 421: 'RekSai', 427: 'Ivern', 429: 'Kalista',
            432: 'Bard', 497: 'Rakan', 498: 'Xayah', 516: 'Ornn', 517: 'Sylas',
            518: 'Neeko', 523: 'Aphelios', 526: 'Rell', 555: 'Pyke', 875: 'Sett',
            876: 'Lillia', 887: 'Gwen', 888: 'Renata', 895: 'Nilah', 897: 'KSante',
            902: 'Milio', 910: 'Hwei', 950: 'Naafiri',
        }
        return champions.get(champion_id, f'Champion{champion_id}')
    
    def normalize(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normaliza um valor entre 0 e 1 de forma equilibrada.
        Valores medianos recebem scores medianos, ruins são penalizados, bons são recompensados.
        """
        if max_val == min_val:
            return 0.5
        
        # Normalização básica
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0, min(1, normalized))  # Garante entre 0 e 1
        
        # Aplica curva leve para valorizar performance acima da média
        # Curva mais suave (1.15) para não ser muito punitivo
        normalized = normalized ** 1.15
        
        return normalized
    
    def calculate_carry_score(self, stats: Dict, team_stats: Dict) -> float:
        """
        Calcula o nível de carry do jogador baseado em métricas avançadas.
        Sistema RIGOROSO - 100 é reservado APENAS para performances EXCEPCIONAIS.
        Performances medianas recebem scores medianos (50-70),
        performances boas ficam em 70-85, performances EXCEPCIONAIS alcançam 85-100.
        
        Sistema de pesos por role (PRIORIZANDO KDA E DANO/GOLD):
        - Top/Mid/ADC: MÁXIMO FOCO em KDA e DANO/GOLD - você precisa performar EXCEPCIONALMENTE
        - Jungle: Kill Participation + Objetivos - você precisa estar presente e pegar objetivos
        - Support: Visão + Kill Participation - você precisa wardear E estar presente nas lutas
        
        Retorna um score de 0 a 100
        """
        # Extrai role
        role = stats.get('teamPosition', 'MIDDLE')
        if role == '': 
            role = stats.get('individualPosition', 'MIDDLE')
        
        # Dados do jogador
        kills = stats.get('kills', 0)
        deaths = stats.get('deaths', 0)
        assists = stats.get('assists', 0)
        damage_dealt = stats.get('totalDamageDealtToChampions', 0)
        gold_earned = max(stats.get('goldEarned', 1), 1)
        cs = stats.get('totalMinionsKilled', 0) + stats.get('neutralMinionsKilled', 0)
        vision_score = stats.get('visionScore', 0)
        # Trata gameDuration que pode estar ausente ou em formatos diferentes
        game_duration_raw = stats.get('gameDuration', stats.get('game_duration', 1800))
        game_duration = max(game_duration_raw / 60, 1) if game_duration_raw else 30  # em minutos
        win = stats.get('win', False)
        
        # Objetivos
        turret_kills = stats.get('turretKills', 0)
        damage_to_objectives = stats.get('damageDealtToObjectives', 0)
        damage_to_buildings = stats.get('damageDealtToBuildings', 0)
        
        # Visão
        wards_placed = stats.get('wardsPlaced', 0)
        wards_killed = stats.get('wardsKilled', 0)
        
        # Utility/CC
        time_ccing = stats.get('timeCCingOthers', 0)
        total_heal = stats.get('totalHealsOnTeammates', 0)
        total_shields = stats.get('totalDamageShieldedOnTeammates', 0)
        damage_taken = stats.get('totalDamageTaken', 0)
        
        # Dados do time
        team_kills = max(team_stats.get('team_kills', kills + assists + 1), 1)
        
        # ⏱️ FATOR DE ESCALA BASEADO NO TEMPO
        # Sistema de multiplicador progressivo moderado:
        # - 15 minutos: 1.4x o score
        # - A cada 5 minutos: reduz 0.08x
        # 
        # Exemplos:
        # 15 min: 1.4x | 20 min: 1.32x | 25 min: 1.24x | 30 min: 1.16x
        # 35 min: 1.08x | 40+ min: 1.0x
        
        if game_duration <= 15:
            # Jogos de até 15 minutos (stomps/remakes)
            time_scale_factor = 1.4
        else:
            # Após 15 minutos, reduz 0.08x a cada 5 minutos
            minutes_after_15 = game_duration - 15
            intervals_of_5 = minutes_after_15 / 5.0
            time_scale_factor = 1.4 - (intervals_of_5 * 0.08)
            
            # Garante que o multiplicador não fique abaixo de 1.0x
            time_scale_factor = max(time_scale_factor, 1.0)  # Mínimo de 1.0x
        
        # 🥊 COMBATE - KDA
        if deaths == 0:
            kda = (kills + assists) + 3  # Bônus por não morrer
        else:
            kda = (kills + assists) / deaths
        
        # Kill Participation
        kill_participation = (kills + assists) / team_kills
        
        # Dano por minuto (já normalizado por tempo)
        dpm = damage_dealt / game_duration
        
        # 💰 RECURSOS (já normalizados por tempo)
        gpm = gold_earned / game_duration
        cspm = cs / game_duration
        
        # 🎯 OBJETIVOS - Sistema diferenciado por role
        # Jungle: APENAS objetivos épicos (Dragão/Barão/Arauto)
        # Top: APENAS estruturas/torres (split push)
        # Mid/ADC/Support: Torres + épicos + estruturas
        if role == 'JUNGLE':
            objectives_score = (
                damage_to_objectives / 500  # APENAS épicos (dragão/barão/arauto)
            )
        elif role == 'TOP':
            objectives_score = (
                turret_kills * 120 +  # Torres são importantes para top
                damage_to_buildings / 600  # FOCO em estruturas (split push)
                # damage_to_objectives épicos não conta muito para top
            )
        else:
            objectives_score = (
                turret_kills * 120 +  # Torres contam
                damage_to_objectives / 700 +  # Objetivos épicos também contam
                damage_to_buildings / 1000  # Estruturas contam menos
            )
        
        # 👀 VISÃO
        vision_per_min = vision_score / game_duration
        wards_per_min = (wards_placed + wards_killed) / game_duration
        
        # 🛡️ SUSTENTAÇÃO/TEAMPLAY
        utility_score = (
            time_ccing / 8 +  # Mais generoso
            (total_heal + total_shields) / 800  # Mais generoso
        )
        
        # NORMALIZAÇÃO RIGOROSA - ranges expandidos para tornar 100 MUITO DIFÍCIL
        # Performance mediana = score mediano (50%), bom = 70%, EXCEPCIONAL = 100%
        norm_kda = self.normalize(kda, 0, 12)  # KDA 6 = 50%, KDA 12 = 100% (MUITO DIFÍCIL)
        norm_kp = self.normalize(kill_participation, 0.15, 0.90)  # 52.5% KP = score mediano
        norm_dpm = self.normalize(dpm, 80, 1200)  # Range expandido - 640 DPM = 50%, 1200 = 100%
        norm_gpm = self.normalize(gpm, 180, 550)  # Range expandido - 365 GPM = 50%, 550 = 100%
        norm_cspm = self.normalize(cspm, 0.5, 10)  # 5.25 CS/min = mediano, 10 CS/min = 100%
        norm_objectives = self.normalize(objectives_score, 0, 500)  # Mais difícil
        norm_vision = self.normalize(vision_per_min, 0.1, 2.5)  # Range expandido
        norm_utility = self.normalize(utility_score, 0, 70)  # Mais difícil
        
        # PESOS POR ROLE - MÁXIMA PRIORIDADE EM KDA E DANO/GOLD PARA TOP/MID/ADC
        if role == 'UTILITY':  # Support: VISÃO + KILL PARTICIPATION
            weights = {
                'kda': 0.15,      # Menos peso no KDA
                'kp': 0.55,       # MÁXIMO PESO em Kill Participation
                'dpm': 0.05,
                'gpm': 0.0,
                'cspm': 0.0,
                'objectives': 0.10,
                'vision': 0.25,   
                'utility': 0.05
            }
        elif role == 'JUNGLE':  # Jungle: KILL PARTICIPATION + KDA + OBJETIVOS
            weights = {
                'kda': 0.30,      # KDA importante (30%)
                'kp': 0.35,       # MÁXIMO PESO em Kill Participation (35%)
                'dpm': 0.10,
                'gpm': 0.05,
                'cspm': 0.05,
                'objectives': 0.15,  # Objetivos balanceados (15%)
                'vision': 0.0,
                'utility': 0.0
            }
        elif role == 'BOTTOM':  # ADC: KDA + DANO/GOLD (MÁXIMA PRIORIDADE)
            weights = {
                'kda': 0.35,      # MÁXIMO PESO em KDA
                'kp': 0.08,
                'dpm': 0.30,      # MÁXIMO PESO em Dano
                'gpm': 0.15,      # MUITO PESO em Gold
                'cspm': 0.12,     # Farm também importante
                'objectives': 0.0,
                'vision': 0.0,
                'utility': 0.0
            }
        elif role == 'TOP':  # Top: KDA + DANO + Split Push balanceado
            weights = {
                'kda': 0.45,      # MÁXIMO PESO em KDA (45%!)
                'kp': 0.075,      # KP balanceado (7.5%)
                'dpm': 0.25,      # MUITO PESO em Dano (25%)
                'gpm': 0.08,      # Gold também importante
                'cspm': 0.07,
                'objectives': 0.075,  # Objetivos balanceado (7.5% - estruturas/torres)
                'vision': 0.0,
                'utility': 0.0
            }
        else:  # Mid: KDA + DANO (MÁXIMA PRIORIDADE)
            weights = {
                'kda': 0.45,      # MÁXIMO PESO em KDA (45%!)
                'kp': 0.15,
                'dpm': 0.25,      # MUITO PESO em Dano (25%)
                'gpm': 0.08,      # Gold também importante
                'cspm': 0.07,
                'objectives': 0.0,
                'vision': 0.0,
                'utility': 0.0
            }
        
        # CÁLCULO FINAL
        base_score = (
            norm_kda * weights['kda'] +
            norm_kp * weights['kp'] +
            norm_dpm * weights['dpm'] +
            norm_gpm * weights['gpm'] +
            norm_cspm * weights['cspm'] +
            norm_objectives * weights['objectives'] +
            norm_vision * weights['vision'] +
            norm_utility * weights['utility']
        )
        
        # Escala para 0-100 com sistema RIGOROSO
        # Performances medianas ficam em 50-65, boas em 65-80, EXCEPCIONAIS em 80-100
        score = (base_score * 75) + 15  # Base de 15 + até 75 pontos = máx 90 base
        
        # ⏱️ APLICA FATOR DE ESCALA TEMPORAL (REDUZIDO)
        # Compensa partidas curtas mas com menos impacto
        score *= time_scale_factor
        
        # Bônus de vitória MENOR
        if win:
            score *= 1.04  # Apenas 4% de bônus por vitória (reduzido de 8%)
            
            # 🚀 BÔNUS ADICIONAL para SNOWBALL/STOMP (REDUZIDO)
            if game_duration < 20 and kill_participation >= 0.6:  # Vitória rápida com alta participação
                score += 4  # +4 pontos (reduzido de 15)
            elif game_duration < 25 and kill_participation >= 0.75:  # Vitória rápida com MUITO alta participação
                score += 3  # +3 pontos (reduzido de 5)
        
        # PENALIDADES SEVERAS por performance ruim
        if deaths > 10:  # Morreu MUITO
            score *= 0.65  # -35% de penalidade
        elif deaths > 8:  # Morreu muito
            score *= 0.75  # -25% de penalidade
        elif deaths > 6:
            score *= 0.85  # -15% de penalidade
        
        if kill_participation < 0.25:  # Participou muito pouco
            score *= 0.70  # -30% de penalidade
        elif kill_participation < 0.35:  # Participou pouco
            score *= 0.80  # -20% de penalidade
        
        # Bônus para performances REALMENTE EXCEPCIONAIS (REDUZIDOS)
        if kda >= 12:  # KDA EXTREMAMENTE excepcional
            score += 8
        elif kda >= 10:  # KDA muito excepcional
            score += 5
        elif kda >= 8:  # KDA excepcional
            score += 3
        
        if kill_participation >= 0.85:  # Participou de quase tudo
            score += 4
        elif kill_participation >= 0.75:
            score += 2
        
        # Bônus por DANO EXCEPCIONAL (novo - importante para Top/Mid/ADC)
        if dpm >= 1000:  # Dano excepcional
            score += 5
        elif dpm >= 850:  # Dano muito alto
            score += 3
        elif dpm >= 700:  # Dano alto
            score += 1
        
        return int(min(max(score, 0), 100))  # Garante entre 0 e 100
    
    def extract_player_stats(self, match_data: Dict, puuid: str) -> Optional[Dict]:
        """Extrai as estatísticas do jogador específico de uma partida"""
        try:
            # Encontra o participante com o PUUID correspondente
            participant = None
            team_id = None
            for p in match_data['info']['participants']:
                if p['puuid'] == puuid:
                    participant = p
                    team_id = p['teamId']
                    break
            
            if not participant:
                return None
            
            # Calcula total de kills do time
            team_kills = sum(
                p['kills'] for p in match_data['info']['participants']
                if p['teamId'] == team_id
            )
            
            # Dados do time para cálculo
            team_stats = {
                'team_kills': team_kills
            }
            
            # Calcula o carry score com o novo sistema
            carry_score = self.calculate_carry_score(participant, team_stats)
            
            # Extrai role
            role = participant.get('teamPosition', '')
            if not role or role == '':
                role = participant.get('individualPosition', 'MIDDLE')
            
            # Mapeamento de roles para nomes amigáveis
            role_names = {
                'TOP': 'Top',
                'JUNGLE': 'Jungle',
                'MIDDLE': 'Mid',
                'BOTTOM': 'ADC',
                'UTILITY': 'Support'
            }
            role_display = role_names.get(role, role)
            
            # Extrai game duration com fallback para diferentes formatos
            game_duration = match_data['info'].get('gameDuration')
            if game_duration is None:
                game_duration = match_data['info'].get('game_duration', 1800)
            
            # Detecta se é remake (partida < 5 minutos = 300 segundos)
            is_remake = game_duration < 300
            
            # Extrai informações relevantes
            stats = {
                'match_id': match_data['metadata']['matchId'],
                'game_mode': match_data['info'].get('gameMode', 'CLASSIC'),
                'champion_name': participant.get('championName', 'Unknown'),
                'role': role_display,
                'kills': participant.get('kills', 0),
                'deaths': participant.get('deaths', 0),
                'assists': participant.get('assists', 0),
                'damage_dealt': participant.get('totalDamageDealtToChampions', 0),
                'damage_taken': participant.get('totalDamageTaken', 0),
                'gold_earned': participant.get('goldEarned', 0),
                'cs': participant.get('totalMinionsKilled', 0) + participant.get('neutralMinionsKilled', 0),
                'vision_score': participant.get('visionScore', 0),
                'game_duration': game_duration,
                'win': participant.get('win', False),
                'carry_score': carry_score,
                'kda': round((participant.get('kills', 0) + participant.get('assists', 0)) / max(participant.get('deaths', 1), 1), 2),
                'kill_participation': round((participant.get('kills', 0) + participant.get('assists', 0)) / max(team_kills, 1) * 100, 1),
                'played_at': datetime.fromtimestamp(match_data['info'].get('gameStartTimestamp', 0) / 1000).isoformat() if match_data['info'].get('gameStartTimestamp') else datetime.now().isoformat(),
                'is_remake': is_remake
            }
            
            return stats
        except Exception as e:
            print(f"Erro ao extrair estatísticas: {e}")
            return None

