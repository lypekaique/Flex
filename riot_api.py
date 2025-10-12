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
        
        # Nota: O parâmetro 'queue' foi removido pois causava erro 400
        # Agora filtramos as partidas pelo queueId após buscar os detalhes
        params = {
            'start': 0,
            'count': count
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Erro ao buscar histórico: {response.status}")
                        text = await response.text()
                        print(f"Resposta da API: {text}")
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
        
        # Spectator V5 usa PUUID diretamente
        url = f"https://{self.REGIONS[region]}/lol/spectator/v5/active-games/by-summoner/{puuid}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        # Jogador não está em partida (normal, não é erro)
                        return None
                    else:
                        # Apenas mostra erro uma vez por minuto para não spammar logs
                        if not hasattr(self, '_last_spectator_error') or \
                           (datetime.now() - self._last_spectator_error).seconds > 60:
                            print(f"Erro ao buscar partida ativa: {response.status}")
                            text = await response.text()
                            print(f"Resposta da API: {text[:200]}")
                            self._last_spectator_error = datetime.now()
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
    
    def calculate_mvp_score(self, player_stats: Dict, all_players_stats: Dict, role: str = '') -> tuple:
        """
        Calcula o MVP Score (estilo OP.GG/U.GG)
        Compara o jogador com TODOS os 10 jogadores da partida
        Ajusta pesos baseado na role do jogador
        Retorna: (score, placement) - ex: (65, 7) = 65 pontos, 7º lugar
        """
        # Normaliza baseado no rank entre 10 jogadores
        def rank_normalize(value: float, all_values: list, player_index: int) -> tuple:
            """Normaliza baseado na posição no ranking dos 10 jogadores"""
            if len(all_values) <= 1:
                return 1.0, 1
            
            # Cria lista de tuplas (valor, índice_original) para manter ordem única
            indexed_values = [(v, i) for i, v in enumerate(all_values)]
            # Ordena por valor (descendente), depois por índice (ascendente) para quebrar empates
            sorted_indexed = sorted(indexed_values, key=lambda x: (-x[0], x[1]))
            
            # Encontra a posição do jogador (1º ao 10º) usando o índice correto
            try:
                # Encontra a posição única baseada na tupla (valor, índice)
                rank = next(i + 1 for i, (v, idx) in enumerate(sorted_indexed) if idx == player_index)
            except (StopIteration, ValueError):
                return 0.5, 5
            
            # 1º = 100%, 2º = 90%, 3º = 80%, ..., 10º = 10%
            # Escala linear: (11 - rank) / 10
            normalized = max(0.0, (11 - rank) / 10)
            return normalized, rank
        
        # Extrai métricas do jogador
        kda = player_stats['kda']
        kill_participation = player_stats['kill_participation']
        damage = player_stats['total_damage_to_champions']
        gold = player_stats['gold_earned']
        cs = player_stats['total_minions_killed'] + player_stats['neutral_minions_killed']
        vision = player_stats['vision_score']
        
        # Compara com TODOS os 10 jogadores
        all_kdas = all_players_stats.get('all_kdas', [kda])
        all_kps = all_players_stats.get('all_kps', [kill_participation])
        all_damages = all_players_stats.get('all_damages', [damage])
        all_golds = all_players_stats.get('all_golds', [gold])
        all_cs = all_players_stats.get('all_cs', [cs])
        all_visions = all_players_stats.get('all_visions', [vision])
        
        # Pega o índice do jogador na lista (encontra pela correspondência exata de todas as métricas)
        player_index = -1
        for i, (k, kp, d, g, c, v) in enumerate(zip(all_kdas, all_kps, all_damages, all_golds, all_cs, all_visions)):
            if k == kda and kp == kill_participation and d == damage and g == gold and c == cs and v == vision:
                player_index = i
                break
        
        # Se não encontrou, usa o primeiro
        if player_index == -1:
            player_index = 0
        
        # Calcula scores normalizados E posições
        norm_kda, rank_kda = rank_normalize(kda, all_kdas, player_index)
        norm_kp, rank_kp = rank_normalize(kill_participation, all_kps, player_index)
        norm_damage, rank_damage = rank_normalize(damage, all_damages, player_index)
        norm_gold, rank_gold = rank_normalize(gold, all_golds, player_index)
        norm_cs, rank_cs = rank_normalize(cs, all_cs, player_index)
        norm_vision, rank_vision = rank_normalize(vision, all_visions, player_index)
        
        # PESOS por ROLE (estilo OP.GG)
        # Suporte: mais peso em visão e KP, menos em CS e dano
        if role.upper() in ['UTILITY', 'SUPPORT']:
            weights = {
                'kda': 0.30,       # KDA importante
                'kp': 0.25,        # KP muito importante para suporte
                'damage': 0.10,    # Dano menos importante
                'gold': 0.10,      # Gold menos importante
                'vision': 0.20,    # Visão MUITO importante para suporte
                'cs': 0.05         # CS quase irrelevante para suporte
            }
        else:
            # Carries (Top, Mid, ADC, Jungle) - focado em KDA/Dano/Gold
            weights = {
                'kda': 0.35,       # KDA é rei
                'damage': 0.30,    # Dano muito importante
                'gold': 0.15,      # Gold importante
                'kp': 0.10,        # KP importante
                'cs': 0.05,        # CS menos importante
                'vision': 0.05     # Vision quase ignorada (realista com sites)
            }
        
        # Calcula score final (0-100)
        score = (
            norm_kda * weights['kda'] +
            norm_kp * weights['kp'] +
            norm_damage * weights['damage'] +
            norm_gold * weights['gold'] +
            norm_cs * weights['cs'] +
            norm_vision * weights['vision']
        ) * 100
        
        # Calcula colocação geral (média ponderada das posições)
        overall_placement = (
            rank_kda * weights['kda'] +
            rank_kp * weights['kp'] +
            rank_damage * weights['damage'] +
            rank_gold * weights['gold'] +
            rank_cs * weights['cs'] +
            rank_vision * weights['vision']
        )
        
        return (int(min(max(score, 0), 100)), int(round(overall_placement)))
    
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
            
            # Calcula total de kills do time (para Carry Score)
            team_kills = sum(
                p['kills'] for p in match_data['info']['participants']
                if p['teamId'] == team_id
            )
            
            # Coleta stats de TODOS os 10 jogadores (para MVP Score)
            all_kdas = []
            all_damages = []
            all_golds = []
            all_cs = []
            all_visions = []
            
            for p in match_data['info']['participants']:
                # Calcula KDA do jogador
                deaths = p['deaths'] if p['deaths'] > 0 else 1
                player_kda = (p['kills'] + p['assists']) / deaths
                all_kdas.append(player_kda)
                
                all_damages.append(p.get('totalDamageDealtToChampions', 0))
                all_golds.append(p.get('goldEarned', 0))
                all_cs.append(p.get('totalMinionsKilled', 0) + p.get('neutralMinionsKilled', 0))
                all_visions.append(p.get('visionScore', 0))
            
            # Calcula KPs de todos (precisa dos kills de cada time)
            team_1_kills = sum(p['kills'] for p in match_data['info']['participants'] if p['teamId'] == 100)
            team_2_kills = sum(p['kills'] for p in match_data['info']['participants'] if p['teamId'] == 200)
            
            all_kps = []
            for p in match_data['info']['participants']:
                team_total_kills = team_1_kills if p['teamId'] == 100 else team_2_kills
                player_kp = (p['kills'] + p['assists']) / max(team_total_kills, 1)
                all_kps.append(player_kp)
            
            # Dados de TODOS os jogadores para cálculo do MVP Score
            all_players_stats = {
                'all_kdas': all_kdas,
                'all_kps': all_kps,
                'all_damages': all_damages,
                'all_golds': all_golds,
                'all_cs': all_cs,
                'all_visions': all_visions
            }
            
            # Extrai role PRIMEIRO (necessária para cálculo do MVP Score)
            role = participant.get('teamPosition', '')
            if not role or role == '':
                role = participant.get('individualPosition', 'MIDDLE')
            
            # Prepara stats do jogador para MVP Score
            player_mvp_stats = {
                'kda': (participant['kills'] + participant['assists']) / max(participant['deaths'], 1),
                'kill_participation': (participant['kills'] + participant['assists']) / max(team_kills, 1),
                'total_damage_to_champions': participant.get('totalDamageDealtToChampions', 0),
                'gold_earned': participant.get('goldEarned', 0),
                'total_minions_killed': participant.get('totalMinionsKilled', 0),
                'neutral_minions_killed': participant.get('neutralMinionsKilled', 0),
                'vision_score': participant.get('visionScore', 0)
            }
            
            # Calcula o MVP score (retorna tupla: score, placement) passando a role
            mvp_score, mvp_placement = self.calculate_mvp_score(player_mvp_stats, all_players_stats, role)
            
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
                'mvp_score': mvp_score,
                'mvp_placement': mvp_placement,
                'kda': round((participant.get('kills', 0) + participant.get('assists', 0)) / max(participant.get('deaths', 1), 1), 2),
                'kill_participation': round((participant.get('kills', 0) + participant.get('assists', 0)) / max(team_kills, 1) * 100, 1),
                'played_at': datetime.fromtimestamp(match_data['info'].get('gameStartTimestamp', 0) / 1000).isoformat() if match_data['info'].get('gameStartTimestamp') else datetime.now().isoformat(),
                'is_remake': is_remake
            }
            
            return stats
        except Exception as e:
            print(f"Erro ao extrair estatísticas: {e}")
            return None

