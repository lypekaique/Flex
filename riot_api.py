import aiohttp
import asyncio
import time
from typing import Optional, Dict, List
from datetime import datetime
from urllib.parse import quote

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

        # Controle de rate limiting aprimorado
        self._last_request_time = 0
        self._request_interval = 1.2  # 1.2 segundos (50/min, abaixo do limite de 60/min)
        self._rate_limit_lock = asyncio.Lock()
        self._request_count_2min = 0  # Contador de requisições nos últimos 2 minutos
        self._rate_limit_window_start = time.time()
        self._max_requests_per_2min = 95  # Fica abaixo do limite de 100 para margem de segurança

        # Cache para evitar requisições desnecessárias
        self._cache = {}
        self._cache_ttl = 300  # 5 minutos de cache

        # Prioridades de requisição
        self._high_priority_endpoints = [
            '/lol/spectator/v5/active-games',
            '/lol/match/v5/matches/by-puuid'
        ]

        # Controle de chave da API
        self._api_key_invalid = False

        # Estatísticas de uso
        self._stats_requests_total = 0
        self._stats_cache_hits = 0
        self._stats_rate_limit_hits = 0

    def _is_high_priority_endpoint(self, url: str) -> bool:
        """Verifica se o endpoint é de alta prioridade"""
        for endpoint in self._high_priority_endpoints:
            if endpoint in url:
                return True
        return False

    def _get_cache_key(self, url: str, params: dict = None) -> str:
        """Gera chave de cache para a requisição"""
        params_str = str(sorted(params.items())) if params else ""
        return f"{url}:{params_str}"

    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Busca resposta no cache"""
        if cache_key in self._cache:
            timestamp, data = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                print(f"📋 [Cache] Usando resposta cacheada para {cache_key[:50]}...")
                return data
            else:
                del self._cache[cache_key]
        return None

    def _set_cached_response(self, cache_key: str, data: Dict):
        """Armazena resposta no cache"""
        self._cache[cache_key] = (time.time(), data)

    def clear_cache(self):
        """Limpa o cache de respostas"""
        cache_size = len(self._cache)
        self._cache.clear()
        print(f"🗑️ [Cache] Limpados {cache_size} itens do cache")

    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso da API"""
        return {
            'requests_total': self._stats_requests_total,
            'cache_hits': self._stats_cache_hits,
            'cache_hit_rate': (self._stats_cache_hits / max(self._stats_requests_total, 1)) * 100,
            'rate_limit_hits': self._stats_rate_limit_hits,
            'cache_size': len(self._cache)
        }

    async def _rate_limit_wait(self, url: str = "", priority_boost: bool = False):
        """Controla o rate limiting entre requisições com distribuição inteligente"""
        async with self._rate_limit_lock:
            current_time = time.time()

            # Reseta contador se passou 2 minutos
            if current_time - self._rate_limit_window_start > 120:
                self._request_count_2min = 0
                self._rate_limit_window_start = current_time
                print(f"🔄 [Rate Limit] Janela de 2 minutos resetada")

            # Verifica limite de 2 minutos
            if self._request_count_2min >= self._max_requests_per_2min:
                self._stats_rate_limit_hits += 1
                sleep_time = 120 - (current_time - self._rate_limit_window_start) + 1
                print(f"⏳ [Rate Limit] Aguardando {sleep_time:.1f}s para resetar janela de 2 minutos")
                await asyncio.sleep(sleep_time)
                self._request_count_2min = 0
                self._rate_limit_window_start = time.time()

            # Ajusta intervalo baseado na prioridade e distribuição
            is_high_priority = self._is_high_priority_endpoint(url) or priority_boost

            # Para endpoints de alta prioridade, usa intervalo menor
            if is_high_priority:
                dynamic_interval = max(0.8, self._request_interval - 0.2)  # 0.8-1.0s
            else:
                dynamic_interval = self._request_interval  # 1.2s normal

            # Controle de intervalo mínimo entre requisições
            time_since_last = current_time - self._last_request_time
            if time_since_last < dynamic_interval:
                sleep_time = dynamic_interval - time_since_last
                if sleep_time > 0.1:  # Só mostra se for significativo
                    print(f"⏱️ [Rate Limit] Aguardando {sleep_time:.2f}s (prioridade: {'alta' if is_high_priority else 'normal'})")
                await asyncio.sleep(sleep_time)

            self._last_request_time = time.time()
            self._request_count_2min += 1

    async def _make_request(self, url: str, params: dict = None) -> Optional[Dict]:
        """Método auxiliar para fazer requisições com tratamento de erro 429 e cache"""
        # Verifica cache primeiro (exceto para endpoints que mudam frequentemente)
        if not any(endpoint in url for endpoint in ['/lol/spectator/v5/active-games']):
            cache_key = self._get_cache_key(url, params)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                self._stats_cache_hits += 1
                return cached_response

        self._stats_requests_total += 1

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            await self._rate_limit_wait(url)

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=self.headers, params=params) as response:
                        if response.status == 429:
                            # Rate limit - aguardar mais tempo
                            retry_after = int(response.headers.get('Retry-After', 60))
                            print(f"🚫 [Rate Limit] API retornou 429, aguardando {retry_after}s")
                            await asyncio.sleep(retry_after)
                            continue

                        if response.status == 200:
                            data = await response.json()
                            # Armazena no cache para próximas requisições
                            if not any(endpoint in url for endpoint in ['/lol/spectator/v5/active-games']):
                                cache_key = self._get_cache_key(url, params)
                                self._set_cached_response(cache_key, data)
                            return data
                        elif response.status == 404:
                            # Para algumas APIs (como spectator), 404 significa "não encontrado" (normal)
                            # Para outras APIs, 404 significa "não encontrado" (erro)
                            # Vamos retornar None para ambos os casos
                            return None
                        elif response.status == 400:
                            # Bad Request - parâmetros inválidos, não adianta tentar novamente
                            text = await response.text()
                            print(f"❌ [BAD REQUEST] Erro 400 na API Riot")
                            print(f"🔗 URL: {url}")
                            print(f"📋 Params: {params}")
                            print(f"📄 Resposta: {text[:500]}")

                            # Detecta erro específico de PUUID corrompido
                            if "Exception decrypting" in text:
                                print(f"⚠️ PUUID CORROMPIDO detectado!")
                                print(f"💡 Solução: Use /logar novamente para revincular a conta")
                            elif "Bad Request" in text and "Exception" in text:
                                print(f"⚠️ Problema nos parâmetros da requisição")
                                print(f"💡 Verifique se PUUID e região estão corretos")
                            else:
                                print(f"⚠️ Não tentaremos novamente pois erro 400 indica problema nos parâmetros")
                            return None  # Não tenta novamente
                        elif response.status == 401:
                            # Chave da API não autorizada
                            print("🚨 [CRÍTICO] Chave da API Riot não autorizada!")
                            print("🚨 Verifique se a chave está correta no Railway (RIOT_API_KEY)")
                            print("🚨 Certifique-se de que copiou a chave completa (começa com 'RGAPI-')")
                            print(f"🚨 Status: {response.status}")
                            self._api_key_invalid = True
                            return None
                        elif response.status == 403:
                            # Chave da API inválida ou expirada
                            text = await response.text()
                            print("=" * 80)
                            print("🚨 [CRÍTICO] CHAVE DA API RIOT EXPIRADA OU INVÁLIDA!")
                            print("=" * 80)
                            print("⏰ Chaves de desenvolvimento expiram a cada 24 horas")
                            print()
                            print("🔍 Diagnóstico:")
                            print(f"   Chave atual: {self.api_key[:20]}...")
                            print(f"   URL testada: {url}")
                            print(f"   Status da resposta: {response.status}")
                            print(f"   Resposta da API: {text[:200]}")
                            print()
                            print("📝 Como resolver:")
                            print("   1. Acesse: https://developer.riotgames.com/")
                            print("   2. Faça login com sua conta Riot")
                            print("   3. Copie a nova 'Development API Key'")
                            print("   4. Atualize a variável RIOT_API_KEY no Railway")
                            print("   5. Reinicie o deployment no Railway")
                            print()
                            print("💡 A chave começa com 'RGAPI-' e tem ~80 caracteres")
                            print("=" * 80)
                            self._api_key_invalid = True
                            return None
                        else:
                            # Erros não tratados especificamente
                            text = await response.text()
                            print(f"❌ Erro não tratado na API Riot: {response.status}")
                            print(f"🔗 URL: {url}")
                            print(f"📋 Params: {params}")
                            print(f"📄 Resposta: {text[:300]}")

                            # Para erros 5xx (servidor), tenta novamente
                            if 500 <= response.status < 600:
                                print(f"⚠️ Erro do servidor ({response.status}), tentando novamente...")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(retry_delay)
                                    retry_delay *= 2  # Backoff exponencial
                                    continue
                            else:
                                # Para outros erros, não tenta novamente
                                print(f"⚠️ Erro {response.status} - não tentando novamente")
                                return None

            except Exception as e:
                print(f"Erro na requisição: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                return None

        return None

    async def get_account_by_riot_id(self, game_name: str, tag_line: str, region: str = 'br1') -> Optional[Dict]:
        """Busca informações da conta pelo Riot ID (nome#tag)"""
        routing = self.ROUTING.get(region, 'americas')
        # URL encode o game_name e tag_line para lidar com caracteres especiais
        encoded_game_name = quote(game_name, safe='')
        encoded_tag_line = quote(tag_line, safe='')
        url = f"https://{routing}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tag_line}"

        return await self._make_request(url)
    
    async def get_summoner_by_puuid(self, puuid: str, region: str = 'br1') -> Optional[Dict]:
        """Busca informações do invocador pelo PUUID"""
        if region not in self.REGIONS:
            print(f"⚠️ Região inválida: {region}")
            return None
        
        # Valida PUUID
        if not puuid or len(puuid) < 10:
            print(f"⚠️ PUUID inválido: {puuid}")
            return None

        # URL encode o PUUID para lidar com caracteres especiais
        encoded_puuid = quote(puuid, safe='')
        url = f"https://{self.REGIONS[region]}/lol/summoner/v4/summoners/by-puuid/{encoded_puuid}"

        return await self._make_request(url)
    
    async def get_match_history(self, puuid: str, region: str = 'br1', count: int = 20,
                                queue: int = 440) -> Optional[List[str]]:
        """Busca histórico de partidas (queue 440 = Ranked Flex)"""
        # Valida PUUID
        if not puuid or len(puuid) < 10:
            print(f"⚠️ PUUID inválido: {puuid}")
            return None
        
        routing = self.ROUTING.get(region, 'americas')
        # URL encode o PUUID para lidar com caracteres especiais
        encoded_puuid = quote(puuid, safe='')
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{encoded_puuid}/ids"

        # Nota: O parâmetro 'queue' foi removido pois causava erro 400
        # Agora filtramos as partidas pelo queueId após buscar os detalhes
        params = {
            'start': 0,
            'count': min(count, 20)  # Limita a 20 para não sobrecarregar
        }

        return await self._make_request(url, params)
    
    async def get_match_details(self, match_id: str, region: str = 'br1') -> Optional[Dict]:
        """Busca detalhes de uma partida específica"""
        routing = self.ROUTING.get(region, 'americas')
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"

        return await self._make_request(url)
    
    async def get_active_game(self, puuid: str, region: str = 'br1') -> Optional[Dict]:
        """Busca informações de partida em andamento (Spectator API)"""
        # Verifica se a chave da API está inválida
        if self._api_key_invalid:
            return None

        if region not in self.REGIONS:
            print(f"⚠️ Região inválida: {region}")
            return None

        # Valida PUUID
        if not puuid or len(puuid) < 10:
            print(f"⚠️ PUUID inválido para active game: {puuid}")
            return None

        # Spectator V5 usa PUUID diretamente
        # URL encode o PUUID para lidar com caracteres especiais
        encoded_puuid = quote(puuid, safe='')
        url = f"https://{self.REGIONS[region]}/lol/spectator/v5/active-games/by-summoner/{encoded_puuid}"

        # Prioridade alta para live games
        await self._rate_limit_wait(url, priority_boost=True)
        return await self._make_request(url)
    
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
    
    async def test_api_key(self) -> bool:
        """Testa se a chave da API está funcionando"""
        try:
            print("🔍 Testando chave da API Riot...")
            print(f"   Chave sendo usada: {self.api_key[:20]}...")

            # Usa uma região comum e uma requisição simples para testar
            test_url = "https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/FakeSummoner"

            await self._rate_limit_wait()

            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, headers=self.headers) as response:
                    print(f"   Status da resposta: {response.status}")

                    if response.status == 200:
                        print("✅ Chave da API Riot funcionando corretamente!")
                        return True
                    elif response.status == 404:
                        # 404 é esperado para um summoner fake, significa que a chave funciona
                        print("✅ Chave da API Riot funcionando corretamente!")
                        return True
                    elif response.status == 401:
                        text = await response.text()
                        print("=" * 80)
                        print("❌ Chave da API Riot não autorizada (erro 401)")
                        print(f"   Resposta da API: {text[:200]}")
                        print("💡 Verifique se a chave está correta no Railway (RIOT_API_KEY)")
                        print("=" * 80)
                        return False
                    elif response.status == 403:
                        text = await response.text()
                        print("=" * 80)
                        print("❌ Chave da API Riot inválida/expirada (erro 403)")
                        print(f"   Resposta da API: {text[:200]}")
                        print("⏰ Chaves de desenvolvimento expiram a cada 24 horas")
                        print()
                        print("💡 Gere uma nova chave em: https://developer.riotgames.com/")
                        print("=" * 80)
                        return False
                    else:
                        text = await response.text()
                        print(f"⚠️ Erro inesperado ao testar chave da API: {response.status}")
                        print(f"   Resposta da API: {text[:200]}")
                        return False
        except Exception as e:
            print(f"❌ Erro ao testar chave da API: {e}")
            print(f"   Tipo do erro: {type(e).__name__}")
            return False

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
        
        # Bônus para time vitorioso (+5 pontos no MVP score)
        # Isso dá uma leve vantagem para o time que venceu
        won = player_stats.get('win', False)
        if won:
            score = min(score + 5, 100)  # Adiciona 5 pontos, mas não passa de 100
        
        # Calcula colocação geral (média ponderada das posições)
        overall_placement = (
            rank_kda * weights['kda'] +
            rank_kp * weights['kp'] +
            rank_damage * weights['damage'] +
            rank_gold * weights['gold'] +
            rank_cs * weights['cs'] +
            rank_vision * weights['vision']
        )
        
        # Retorna score e placement (placement será corrigido depois com base em todos os scores)
        # Por enquanto retorna a média ponderada sem arredondar para manter precisão
        return (int(min(max(score, 0), 100)), overall_placement)
    
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
            
            # Calcula o MVP score inicial (retorna tupla: score, placement temporário)
            mvp_score, _ = self.calculate_mvp_score(player_mvp_stats, all_players_stats, role)
            
            # Calcula scores de TODOS os jogadores para determinar placement único
            all_player_scores = []
            for i, p in enumerate(match_data['info']['participants']):
                p_role = p.get('teamPosition', '') or p.get('individualPosition', 'MIDDLE')
                p_team_id = p['teamId']
                p_team_kills = sum(
                    pl['kills'] for pl in match_data['info']['participants']
                    if pl['teamId'] == p_team_id
                )
                
                p_stats = {
                    'kda': (p['kills'] + p['assists']) / max(p['deaths'], 1),
                    'kill_participation': (p['kills'] + p['assists']) / max(p_team_kills, 1),
                    'total_damage_to_champions': p.get('totalDamageDealtToChampions', 0),
                    'gold_earned': p.get('goldEarned', 0),
                    'total_minions_killed': p.get('totalMinionsKilled', 0),
                    'neutral_minions_killed': p.get('neutralMinionsKilled', 0),
                    'vision_score': p.get('visionScore', 0),
                    'win': p.get('win', False)
                }
                
                p_score, _ = self.calculate_mvp_score(p_stats, all_players_stats, p_role)
                all_player_scores.append((p_score, i, p['puuid']))
            
            # Ordena por score (descendente), depois por índice (para desempate consistente)
            all_player_scores.sort(key=lambda x: (-x[0], x[1]))
            
            # Encontra o placement do jogador atual
            mvp_placement = next(
                i + 1 for i, (score, idx, p_puuid) in enumerate(all_player_scores)
                if p_puuid == puuid
            )
            
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

