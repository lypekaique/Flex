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
                is_remake BOOLEAN DEFAULT 0,
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
                command_channel_id TEXT,
                live_game_channel_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela para rastrear partidas ao vivo já notificadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_games_notified (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lol_account_id INTEGER NOT NULL,
                game_id TEXT NOT NULL,
                message_id TEXT,
                channel_id TEXT,
                guild_id TEXT,
                notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lol_account_id) REFERENCES lol_accounts(id),
                UNIQUE(lol_account_id, game_id)
            )
        ''')
        
        # Migração: Adiciona coluna command_channel_id se não existir
        try:
            cursor.execute("SELECT command_channel_id FROM server_configs LIMIT 1")
        except sqlite3.OperationalError:
            # Coluna não existe, precisa adicionar
            print("🔄 Migrando banco: adicionando coluna command_channel_id...")
            cursor.execute('''
                ALTER TABLE server_configs 
                ADD COLUMN command_channel_id TEXT
            ''')
            print("✅ Migração command_channel_id concluída!")
        
        # Migração: Adiciona coluna live_game_channel_id se não existir
        try:
            cursor.execute("SELECT live_game_channel_id FROM server_configs LIMIT 1")
        except sqlite3.OperationalError:
            # Coluna não existe, precisa adicionar
            print("🔄 Migrando banco: adicionando coluna live_game_channel_id...")
            cursor.execute('''
                ALTER TABLE server_configs 
                ADD COLUMN live_game_channel_id TEXT
            ''')
            print("✅ Migração live_game_channel_id concluída!")
        
        # Migração: Adiciona colunas message_id, channel_id e guild_id em live_games_notified
        try:
            cursor.execute("SELECT message_id FROM live_games_notified LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Migrando banco: adicionando colunas para tracking de mensagens...")
            cursor.execute('ALTER TABLE live_games_notified ADD COLUMN message_id TEXT')
            cursor.execute('ALTER TABLE live_games_notified ADD COLUMN channel_id TEXT')
            cursor.execute('ALTER TABLE live_games_notified ADD COLUMN guild_id TEXT')
            print("✅ Migração de tracking concluída!")
        
        # Migração: Adiciona coluna is_remake em matches
        try:
            cursor.execute("SELECT is_remake FROM matches LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Migrando banco: adicionando coluna is_remake...")
            cursor.execute('ALTER TABLE matches ADD COLUMN is_remake BOOLEAN DEFAULT 0')
            print("✅ Migração is_remake concluída!")
        
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
                    carry_score, kda, kill_participation, played_at, is_remake
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                match_data['played_at'],
                match_data.get('is_remake', False)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao adicionar partida: {e}")
            return False
    
    def get_monthly_matches(self, lol_account_id: int, year: int, month: int, include_remakes: bool = True) -> List[Dict]:
        """Retorna todas as partidas de um mês específico (por padrão inclui remakes apenas para histórico)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Query base
        query = '''
            SELECT match_id, game_mode, champion_name, role, kills, deaths, assists,
                   damage_dealt, damage_taken, gold_earned, cs, vision_score,
                   game_duration, win, carry_score, kda, kill_participation, played_at, is_remake
            FROM matches
            WHERE lol_account_id = ?
              AND strftime('%Y', played_at) = ?
              AND strftime('%m', played_at) = ?
        '''
        
        # Se não quer incluir remakes, adiciona filtro
        if not include_remakes:
            query += ' AND (is_remake = 0 OR is_remake IS NULL)'
        
        query += ' ORDER BY played_at DESC'
        
        cursor.execute(query, (lol_account_id, str(year), f"{month:02d}"))
        
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
                'played_at': row[17],
                'is_remake': row[18] if len(row) > 18 else False
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
    
    def set_command_channel(self, guild_id: str, channel_id: str) -> bool:
        """Define o canal de comandos para um servidor"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Verifica se já existe configuração
            cursor.execute('SELECT guild_id FROM server_configs WHERE guild_id = ?', (guild_id,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute('''
                    UPDATE server_configs 
                    SET command_channel_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE guild_id = ?
                ''', (channel_id, guild_id))
            else:
                cursor.execute('''
                    INSERT INTO server_configs (guild_id, command_channel_id, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (guild_id, channel_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao configurar canal de comandos: {e}")
            return False
    
    def get_command_channel(self, guild_id: str) -> Optional[str]:
        """Retorna o canal de comandos configurado para um servidor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT command_channel_id FROM server_configs
            WHERE guild_id = ?
        ''', (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def set_live_game_channel(self, guild_id: str, channel_id: str) -> bool:
        """Define o canal de live games para um servidor"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Verifica se já existe configuração
            cursor.execute('SELECT guild_id FROM server_configs WHERE guild_id = ?', (guild_id,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute('''
                    UPDATE server_configs 
                    SET live_game_channel_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE guild_id = ?
                ''', (channel_id, guild_id))
            else:
                cursor.execute('''
                    INSERT INTO server_configs (guild_id, live_game_channel_id, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (guild_id, channel_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao configurar canal de live games: {e}")
            return False
    
    def get_live_game_channel(self, guild_id: str) -> Optional[str]:
        """Retorna o canal de live games configurado para um servidor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT live_game_channel_id FROM server_configs
            WHERE guild_id = ?
        ''', (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def is_live_game_notified(self, lol_account_id: int, game_id: str) -> bool:
        """Verifica se uma live game já foi notificada"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM live_games_notified
            WHERE lol_account_id = ? AND game_id = ?
        ''', (lol_account_id, game_id))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def mark_live_game_notified(self, lol_account_id: int, game_id: str, 
                                message_id: str = None, channel_id: str = None, 
                                guild_id: str = None) -> bool:
        """Marca uma live game como notificada e salva IDs da mensagem"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO live_games_notified 
                (lol_account_id, game_id, message_id, channel_id, guild_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (lol_account_id, game_id, message_id, channel_id, guild_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao marcar live game como notificada: {e}")
            return False
    
    def cleanup_old_live_game_notifications(self, hours: int = 24) -> bool:
        """Remove notificações de live games antigas (padrão: 24h)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM live_games_notified
                WHERE notified_at < datetime('now', '-' || ? || ' hours')
            ''', (hours,))
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            if deleted > 0:
                print(f"🧹 Limpeza: {deleted} notificações antigas removidas")
            return True
        except Exception as e:
            print(f"Erro ao limpar notificações antigas: {e}")
            return False
    
    def get_live_game_message(self, lol_account_id: int, match_id: str) -> Optional[Dict]:
        """Busca informações da mensagem de uma live game pelo match_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # O game_id da spectator API é diferente do match_id final
        # Precisamos buscar por lol_account_id e pelo game_id que contém parte do match_id
        # Ou simplesmente pegar a mais recente do jogador
        cursor.execute('''
            SELECT message_id, channel_id, guild_id, game_id 
            FROM live_games_notified
            WHERE lol_account_id = ?
            ORDER BY notified_at DESC
            LIMIT 1
        ''', (lol_account_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'message_id': result[0],
                'channel_id': result[1],
                'guild_id': result[2],
                'game_id': result[3]
            }
        return None
    
    def get_server_config(self, guild_id: str) -> Optional[Dict]:
        """Retorna todas as configurações de um servidor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT notification_channel_id, match_channel_id, command_channel_id, live_game_channel_id FROM server_configs
            WHERE guild_id = ?
        ''', (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'notification_channel_id': result[0],
                'match_channel_id': result[1],
                'command_channel_id': result[2],
                'live_game_channel_id': result[3]
            }
        return None
    
    def get_last_n_matches_with_champion(self, lol_account_id: int, champion_name: str, n: int = 3) -> List[Dict]:
        """Retorna as últimas N partidas de um usuário com um campeão específico (exclui remakes)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT match_id, champion_name, role, kills, deaths, assists,
                   carry_score, win, played_at
            FROM matches
            WHERE lol_account_id = ? AND champion_name = ?
              AND (is_remake = 0 OR is_remake IS NULL)
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
        """Retorna o ranking dos melhores jogadores por carry score médio (mínimo de jogos, exclui remakes)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Busca melhores médias (apenas jogadores com mínimo de partidas, excluindo remakes)
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
              AND (m.is_remake = 0 OR m.is_remake IS NULL)
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
    
    def get_monthly_matches_by_champion(self, lol_account_id: int, year: int, month: int, champion_name: str) -> List[Dict]:
        """Retorna todas as partidas de um mês específico filtradas por campeão (exclui remakes)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT match_id, game_mode, champion_name, role, kills, deaths, assists,
                   damage_dealt, damage_taken, gold_earned, cs, vision_score,
                   game_duration, win, carry_score, kda, kill_participation, played_at
            FROM matches
            WHERE lol_account_id = ?
              AND champion_name = ?
              AND strftime('%Y', played_at) = ?
              AND strftime('%m', played_at) = ?
              AND (is_remake = 0 OR is_remake IS NULL)
            ORDER BY played_at DESC
        ''', (lol_account_id, champion_name, str(year), f"{month:02d}"))
        
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
    
    def get_all_champions_played(self, lol_account_id: int, year: int, month: int) -> List[str]:
        """Retorna lista de todos os campeões jogados por uma conta em um mês"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT champion_name
            FROM matches
            WHERE lol_account_id = ?
              AND strftime('%Y', played_at) = ?
              AND strftime('%m', played_at) = ?
            ORDER BY champion_name
        ''', (lol_account_id, str(year), f"{month:02d}"))
        
        champions = [row[0] for row in cursor.fetchall()]
        conn.close()
        return champions
    
    def get_user_by_summoner_name(self, summoner_name: str) -> Optional[str]:
        """Busca discord_id pelo summoner name (ignora case e #TAG)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Remove #TAG se presente e busca com LIKE case insensitive
        search_name = summoner_name.split('#')[0]
        cursor.execute('''
            SELECT discord_id FROM lol_accounts
            WHERE LOWER(summoner_name) LIKE LOWER(?)
            LIMIT 1
        ''', (f"{search_name}%",))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def delete_all_matches(self) -> tuple[bool, int]:
        """Deleta TODAS as partidas do banco de dados. Retorna (sucesso, quantidade deletada)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Conta quantas partidas tem antes de deletar
            cursor.execute('SELECT COUNT(*) FROM matches')
            count = cursor.fetchone()[0]
            
            # Deleta todas as partidas
            cursor.execute('DELETE FROM matches')
            
            # Também limpa as notificações de live games antigas
            cursor.execute('DELETE FROM live_games_notified')
            
            conn.commit()
            conn.close()
            
            print(f"🗑️ [DATABASE] {count} partidas deletadas do banco")
            return True, count
        except Exception as e:
            print(f"❌ [DATABASE] Erro ao deletar todas as partidas: {e}")
            return False, 0
    
    def delete_matches_by_account(self, lol_account_id: int) -> tuple[bool, int]:
        """Deleta todas as partidas de uma conta específica. Retorna (sucesso, quantidade deletada)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Conta quantas partidas tem antes de deletar
            cursor.execute('SELECT COUNT(*) FROM matches WHERE lol_account_id = ?', (lol_account_id,))
            count = cursor.fetchone()[0]
            
            # Deleta as partidas
            cursor.execute('DELETE FROM matches WHERE lol_account_id = ?', (lol_account_id,))
            
            # Limpa notificações de live games dessa conta
            cursor.execute('DELETE FROM live_games_notified WHERE lol_account_id = ?', (lol_account_id,))
            
            conn.commit()
            conn.close()
            
            print(f"🗑️ [DATABASE] {count} partidas deletadas da conta ID {lol_account_id}")
            return True, count
        except Exception as e:
            print(f"❌ [DATABASE] Erro ao deletar partidas da conta {lol_account_id}: {e}")
            return False, 0
    
    def delete_matches_by_discord_user(self, discord_id: str) -> tuple[bool, int]:
        """Deleta todas as partidas de todas as contas de um usuário Discord. Retorna (sucesso, quantidade deletada)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Busca IDs de todas as contas do usuário
            cursor.execute('SELECT id FROM lol_accounts WHERE discord_id = ?', (discord_id,))
            account_ids = [row[0] for row in cursor.fetchall()]
            
            if not account_ids:
                conn.close()
                return True, 0
            
            # Conta quantas partidas tem antes de deletar
            placeholders = ','.join('?' * len(account_ids))
            cursor.execute(f'SELECT COUNT(*) FROM matches WHERE lol_account_id IN ({placeholders})', account_ids)
            count = cursor.fetchone()[0]
            
            # Deleta as partidas
            cursor.execute(f'DELETE FROM matches WHERE lol_account_id IN ({placeholders})', account_ids)
            
            # Limpa notificações de live games dessas contas
            cursor.execute(f'DELETE FROM live_games_notified WHERE lol_account_id IN ({placeholders})', account_ids)
            
            conn.commit()
            conn.close()
            
            print(f"🗑️ [DATABASE] {count} partidas deletadas do usuário Discord {discord_id}")
            return True, count
        except Exception as e:
            print(f"❌ [DATABASE] Erro ao deletar partidas do usuário {discord_id}: {e}")
            return False, 0
    
    def get_active_live_games(self, hours: int = 2) -> List[Dict]:
        """Retorna lista de live games notificadas recentemente (últimas X horas) que ainda não foram processadas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT lol_account_id, game_id, message_id, channel_id, guild_id, notified_at
            FROM live_games_notified
            WHERE notified_at > datetime('now', '-' || ? || ' hours')
            ORDER BY notified_at DESC
        ''', (hours,))
        
        live_games = []
        for row in cursor.fetchall():
            live_games.append({
                'lol_account_id': row[0],
                'game_id': row[1],
                'message_id': row[2],
                'channel_id': row[3],
                'guild_id': row[4],
                'notified_at': row[5]
            })
        
        conn.close()
        return live_games
    
    def remove_live_game_notification(self, lol_account_id: int, game_id: str) -> bool:
        """Remove uma notificação de live game específica"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM live_games_notified
                WHERE lol_account_id = ? AND game_id = ?
            ''', (lol_account_id, game_id))
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            
            if deleted > 0:
                print(f"✅ [DATABASE] Live game {game_id} removida da lista de notificações")
            return True
        except Exception as e:
            print(f"❌ [DATABASE] Erro ao remover live game notification: {e}")
            return False

