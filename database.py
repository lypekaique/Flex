import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict

class Database:
    def __init__(self, db_name=None):
        # Suporte para Railway Volumes
        if db_name is None:
            # Usa /data se existir (Railway Volume), senão usa local
            if os.path.exists('/data'):
                db_name = '/data/bot_lol.db'
                print("✅ Usando Railway Volume para persistência: /data/bot_lol.db")
            else:
                db_name = 'bot_lol.db'
                print("📁 Usando banco de dados local: bot_lol.db")
        
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Inicializa as tabelas do banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de usuários Discord
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de contas LOL vinculadas (máximo 3 por usuário)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lol_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT NOT NULL,
                summoner_name TEXT NOT NULL,
                summoner_id TEXT NOT NULL,
                puuid TEXT NOT NULL,
                account_id TEXT NOT NULL,
                region TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (discord_id) REFERENCES users(discord_id),
                UNIQUE(discord_id, puuid)
            )
        ''')
        
        # Tabela de partidas e nível de carry
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lol_account_id INTEGER NOT NULL,
                match_id TEXT NOT NULL,
                game_mode TEXT,
                champion_name TEXT,
                role TEXT,
                kills INTEGER,
                deaths INTEGER,
                assists INTEGER,
                damage_dealt INTEGER,
                damage_taken INTEGER,
                gold_earned INTEGER,
                cs INTEGER,
                vision_score INTEGER,
                game_duration INTEGER,
                win BOOLEAN,
                carry_score REAL,
                kda REAL,
                kill_participation REAL,
                played_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lol_account_id) REFERENCES lol_accounts(id),
                UNIQUE(lol_account_id, match_id)
            )
        ''')
        
        # Tabela de configurações dos servidores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_configs (
                guild_id TEXT PRIMARY KEY,
                notification_channel_id TEXT,
                match_channel_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, discord_id: str) -> bool:
        """Adiciona um usuário Discord"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO users (discord_id) VALUES (?)', (discord_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao adicionar usuário: {e}")
            return False
    
    def get_user_accounts(self, discord_id: str) -> List[Dict]:
        """Retorna todas as contas LOL de um usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, summoner_name, summoner_id, puuid, account_id, region, created_at
            FROM lol_accounts
            WHERE discord_id = ?
        ''', (discord_id,))
        
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                'id': row[0],
                'summoner_name': row[1],
                'summoner_id': row[2],
                'puuid': row[3],
                'account_id': row[4],
                'region': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return accounts
    
    def add_lol_account(self, discord_id: str, summoner_name: str, summoner_id: str, 
                       puuid: str, account_id: str, region: str) -> tuple[bool, str]:
        """Adiciona uma conta LOL para um usuário (máximo 3)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verifica se já tem 3 contas
        cursor.execute('SELECT COUNT(*) FROM lol_accounts WHERE discord_id = ?', (discord_id,))
        count = cursor.fetchone()[0]
        
        if count >= 3:
            conn.close()
            return False, "Você já tem 3 contas vinculadas. Remova uma para adicionar outra."
        
        # Adiciona usuário se não existir
        self.add_user(discord_id)
        
        try:
            cursor.execute('''
                INSERT INTO lol_accounts (discord_id, summoner_name, summoner_id, puuid, account_id, region)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (discord_id, summoner_name, summoner_id, puuid, account_id, region))
            conn.commit()
            conn.close()
            return True, "Conta vinculada com sucesso!"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "Esta conta já está vinculada ao seu Discord."
        except Exception as e:
            conn.close()
            return False, f"Erro ao vincular conta: {e}"
    
    def add_match(self, lol_account_id: int, match_data: Dict) -> bool:
        """Adiciona uma partida ao histórico"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO matches (
                    lol_account_id, match_id, game_mode, champion_name, role,
                    kills, deaths, assists, damage_dealt, damage_taken,
                    gold_earned, cs, vision_score, game_duration, win, 
                    carry_score, kda, kill_participation, played_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lol_account_id,
                match_data['match_id'],
                match_data['game_mode'],
                match_data['champion_name'],
                match_data.get('role', 'Unknown'),
                match_data['kills'],
                match_data['deaths'],
                match_data['assists'],
                match_data['damage_dealt'],
                match_data['damage_taken'],
                match_data['gold_earned'],
                match_data['cs'],
                match_data['vision_score'],
                match_data['game_duration'],
                match_data['win'],
                match_data['carry_score'],
                match_data.get('kda', 0),
                match_data.get('kill_participation', 0),
                match_data['played_at']
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao adicionar partida: {e}")
            return False
    
    def get_monthly_matches(self, lol_account_id: int, year: int, month: int) -> List[Dict]:
        """Retorna todas as partidas de um mês específico"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT match_id, game_mode, champion_name, role, kills, deaths, assists,
                   damage_dealt, damage_taken, gold_earned, cs, vision_score,
                   game_duration, win, carry_score, kda, kill_participation, played_at
            FROM matches
            WHERE lol_account_id = ?
              AND strftime('%Y', played_at) = ?
              AND strftime('%m', played_at) = ?
            ORDER BY played_at DESC
        ''', (lol_account_id, str(year), f"{month:02d}"))
        
        matches = []
        for row in cursor.fetchall():
            matches.append({
                'match_id': row[0],
                'game_mode': row[1],
                'champion_name': row[2],
                'role': row[3],
                'kills': row[4],
                'deaths': row[5],
                'assists': row[6],
                'damage_dealt': row[7],
                'damage_taken': row[8],
                'gold_earned': row[9],
                'cs': row[10],
                'vision_score': row[11],
                'game_duration': row[12],
                'win': row[13],
                'carry_score': row[14],
                'kda': row[15],
                'kill_participation': row[16],
                'played_at': row[17]
            })
        
        conn.close()
        return matches
    
    def get_last_match_id(self, lol_account_id: int) -> Optional[str]:
        """Retorna o ID da última partida registrada"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT match_id FROM matches
            WHERE lol_account_id = ?
            ORDER BY played_at DESC
            LIMIT 1
        ''', (lol_account_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def set_notification_channel(self, guild_id: str, channel_id: str) -> bool:
        """Define o canal de notificações para um servidor"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO server_configs (guild_id, notification_channel_id, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (guild_id, channel_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao configurar canal: {e}")
            return False
    
    def get_notification_channel(self, guild_id: str) -> Optional[str]:
        """Retorna o canal de notificações configurado para um servidor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT notification_channel_id FROM server_configs
            WHERE guild_id = ?
        ''', (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def set_match_channel(self, guild_id: str, channel_id: str) -> bool:
        """Define o canal de partidas para um servidor"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Verifica se já existe configuração
            cursor.execute('SELECT guild_id FROM server_configs WHERE guild_id = ?', (guild_id,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute('''
                    UPDATE server_configs 
                    SET match_channel_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE guild_id = ?
                ''', (channel_id, guild_id))
            else:
                cursor.execute('''
                    INSERT INTO server_configs (guild_id, match_channel_id, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (guild_id, channel_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao configurar canal de partidas: {e}")
            return False
    
    def get_match_channel(self, guild_id: str) -> Optional[str]:
        """Retorna o canal de partidas configurado para um servidor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT match_channel_id FROM server_configs
            WHERE guild_id = ?
        ''', (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_server_config(self, guild_id: str) -> Optional[Dict]:
        """Retorna todas as configurações de um servidor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT notification_channel_id, match_channel_id FROM server_configs
            WHERE guild_id = ?
        ''', (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'notification_channel_id': result[0],
                'match_channel_id': result[1]
            }
        return None
    
    def get_last_n_matches_with_champion(self, lol_account_id: int, champion_name: str, n: int = 3) -> List[Dict]:
        """Retorna as últimas N partidas de um usuário com um campeão específico"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT match_id, champion_name, role, kills, deaths, assists,
                   carry_score, win, played_at
            FROM matches
            WHERE lol_account_id = ? AND champion_name = ?
            ORDER BY played_at DESC
            LIMIT ?
        ''', (lol_account_id, champion_name, n))
        
        matches = []
        for row in cursor.fetchall():
            matches.append({
                'match_id': row[0],
                'champion_name': row[1],
                'role': row[2],
                'kills': row[3],
                'deaths': row[4],
                'assists': row[5],
                'carry_score': row[6],
                'win': row[7],
                'played_at': row[8]
            })
        
        conn.close()
        return matches
    
    def get_top_players_by_carry(self, limit: int = 10, min_games: int = 5) -> List[Dict]:
        """Retorna o ranking dos melhores jogadores por carry score médio (mínimo de jogos)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Busca melhores médias (apenas jogadores com mínimo de partidas)
        cursor.execute('''
            SELECT 
                la.discord_id,
                la.summoner_name,
                la.region,
                COUNT(m.id) as total_games,
                AVG(m.carry_score) as avg_carry,
                SUM(CASE WHEN m.win = 1 THEN 1 ELSE 0 END) as wins,
                AVG(m.kda) as avg_kda,
                AVG(m.kill_participation) as avg_kp
            FROM matches m
            JOIN lol_accounts la ON m.lol_account_id = la.id
            WHERE strftime('%Y-%m', m.played_at) = strftime('%Y-%m', 'now')
            GROUP BY la.id
            HAVING COUNT(m.id) >= ?
            ORDER BY avg_carry DESC
            LIMIT ?
        ''', (min_games, limit))
        
        ranking = []
        for row in cursor.fetchall():
            total_games = row[3]
            wins = row[5]
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            ranking.append({
                'discord_id': row[0],
                'summoner_name': row[1],
                'region': row[2],
                'total_games': total_games,
                'avg_carry': round(row[4], 2),
                'wins': wins,
                'win_rate': round(win_rate, 1),
                'avg_kda': round(row[6], 2),
                'avg_kp': round(row[7], 1)
            })
        
        conn.close()
        return ranking

