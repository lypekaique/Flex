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
        kills = stats['kills']
        deaths = max(stats['deaths'], 1)  # Evita divisão por zero
        assists = stats['assists']
        damage_dealt = stats['totalDamageDealtToChampions']
        gold_earned = max(stats['goldEarned'], 1)
        cs = stats['totalMinionsKilled'] + stats.get('neutralMinionsKilled', 0)
        vision_score = stats['visionScore']
        game_duration = max(stats['gameDuration'] / 60, 1)  # em minutos
        win = stats['win']
        
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
            
            # Extrai informações relevantes
            stats = {
                'match_id': match_data['metadata']['matchId'],
                'game_mode': match_data['info']['gameMode'],
                'champion_name': participant['championName'],
                'role': role_display,
                'kills': participant['kills'],
                'deaths': participant['deaths'],
                'assists': participant['assists'],
                'damage_dealt': participant['totalDamageDealtToChampions'],
                'damage_taken': participant['totalDamageTaken'],
                'gold_earned': participant['goldEarned'],
                'cs': participant['totalMinionsKilled'] + participant.get('neutralMinionsKilled', 0),
                'vision_score': participant['visionScore'],
                'game_duration': match_data['info']['gameDuration'],
                'win': participant['win'],
                'carry_score': carry_score,
                'kda': round((participant['kills'] + participant['assists']) / max(participant['deaths'], 1), 2),
                'kill_participation': round((participant['kills'] + participant['assists']) / max(team_kills, 1) * 100, 1),
                'played_at': datetime.fromtimestamp(match_data['info']['gameStartTimestamp'] / 1000).isoformat()
            }
            
            return stats
        except Exception as e:
            print(f"Erro ao extrair estatísticas: {e}")
            return None

