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
        """Normaliza um valor entre 0 e 1"""
        if max_val == min_val:
            return 0.5
        normalized = (value - min_val) / (max_val - min_val)
        return max(0, min(1, normalized))  # Garante entre 0 e 1
    
    def calculate_carry_score(self, stats: Dict, team_stats: Dict) -> float:
        """
        Calcula o nível de carry do jogador baseado em métricas avançadas
        
        Sistema de pesos por role:
        - Top/Jungle/Mid/ADC: foco em KDA, KP, dano, farm e objetivos
        - Support: foco em KP, vision, objetivos, CC/utility
        
        Retorna um score de 0 a 10
        """
        # Extrai role
        role = stats.get('teamPosition', 'MIDDLE')
        if role == '': 
            role = stats.get('individualPosition', 'MIDDLE')
        
        # Dados do jogador
        kills = stats.get('kills', 0)
        deaths = max(stats.get('deaths', 1), 1)  # Evita divisão por zero
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
        
        # 🥊 COMBATE
        kda = (kills + assists) / deaths
        dpm = damage_dealt / game_duration
        damage_per_gold = damage_dealt / gold_earned
        kill_participation = (kills + assists) / team_kills
        
        # 💰 RECURSOS
        gpm = gold_earned / game_duration
        cspm = cs / game_duration
        
        # 🎯 OBJETIVOS
        objectives_score = (
            turret_kills * 100 + 
            damage_to_objectives / 1000 + 
            damage_to_buildings / 1000
        )
        
        # 👀 VISÃO
        vision_per_min = vision_score / game_duration
        wards_per_min = (wards_placed + wards_killed) / game_duration
        
        # 🛡️ SUSTENTAÇÃO/TEAMPLAY
        utility_score = (
            time_ccing / 10 + 
            (total_heal + total_shields) / 1000
        )
        damage_taken_per_min = damage_taken / game_duration
        
        # NORMALIZAÇÃO (benchmarks baseados em dados reais de partidas)
        norm_kda = self.normalize(kda, 0, 8)
        norm_kp = self.normalize(kill_participation, 0.3, 0.8)
        norm_dpm = self.normalize(dpm, 200, 1200)
        norm_gpm = self.normalize(gpm, 250, 500)
        norm_cspm = self.normalize(cspm, 2, 10)
        norm_objectives = self.normalize(objectives_score, 0, 500)
        norm_vision = self.normalize(vision_per_min, 0.5, 2.5)
        norm_utility = self.normalize(utility_score, 0, 50)
        
        # PESOS POR ROLE
        if role == 'UTILITY':  # Support
            weights = {
                'kda': 0.15,
                'kp': 0.25,
                'dpm': 0.05,
                'gpm': 0.0,
                'cspm': 0.0,
                'objectives': 0.15,
                'vision': 0.25,
                'utility': 0.15
            }
        else:  # Top/Jungle/Mid/ADC
            weights = {
                'kda': 0.20,
                'kp': 0.20,
                'dpm': 0.15,
                'gpm': 0.075,
                'cspm': 0.075,
                'objectives': 0.20,
                'vision': 0.05,
                'utility': 0.05
            }
        
        # CÁLCULO FINAL
        score = (
            norm_kda * weights['kda'] +
            norm_kp * weights['kp'] +
            norm_dpm * weights['dpm'] +
            norm_gpm * weights['gpm'] +
            norm_cspm * weights['cspm'] +
            norm_objectives * weights['objectives'] +
            norm_vision * weights['vision'] +
            norm_utility * weights['utility']
        ) * 100  # Escala para 0-100
        
        # Bônus de 5% por vitória
        if win:
            score *= 1.05
        
        return int(min(score, 100))  # Garante máximo de 100 e converte para inteiro
    
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
                'played_at': datetime.fromtimestamp(match_data['info'].get('gameStartTimestamp', 0) / 1000).isoformat() if match_data['info'].get('gameStartTimestamp') else datetime.now().isoformat()
            }
            
            return stats
        except Exception as e:
            print(f"Erro ao extrair estatísticas: {e}")
            return None

