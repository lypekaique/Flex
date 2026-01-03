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
        
        # Tabela de partidas
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
                mvp_score REAL DEFAULT 0,
                mvp_placement INTEGER DEFAULT 0,
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
                puuid TEXT NOT NULL,
                summoner_name TEXT,
                champion_id INTEGER,
                champion_name TEXT,
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

        # Migração: Adiciona colunas puuid, summoner_name, champion_id, champion_name em live_games_notified
        try:
            cursor.execute("SELECT puuid FROM live_games_notified LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Migrando banco: adicionando colunas de identificação da partida...")
            cursor.execute('ALTER TABLE live_games_notified ADD COLUMN puuid TEXT')
            cursor.execute('ALTER TABLE live_games_notified ADD COLUMN summoner_name TEXT')
            cursor.execute('ALTER TABLE live_games_notified ADD COLUMN champion_id INTEGER')
            cursor.execute('ALTER TABLE live_games_notified ADD COLUMN champion_name TEXT')
            print("✅ Migração de identificação concluída!")
        
        # Migração: Adiciona coluna is_remake em matches
        try:
            cursor.execute("SELECT is_remake FROM matches LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Migrando banco: adicionando coluna is_remake...")
            cursor.execute('ALTER TABLE matches ADD COLUMN is_remake BOOLEAN DEFAULT 0')
            print("✅ Migração is_remake concluída!")
        
        # Migração: Adiciona coluna mvp_score em matches
        try:
            cursor.execute("SELECT mvp_score FROM matches LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Migrando banco: adicionando coluna mvp_score...")
            cursor.execute('ALTER TABLE matches ADD COLUMN mvp_score REAL DEFAULT 0')
            print("✅ Migração mvp_score concluída!")
        
        # Migração: Adiciona coluna mvp_placement em matches
        try:
            cursor.execute("SELECT mvp_placement FROM matches LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Migrando banco: adicionando coluna mvp_placement...")
            cursor.execute('ALTER TABLE matches ADD COLUMN mvp_placement INTEGER DEFAULT 0')
            print("✅ Migração mvp_placement concluída!")
        
        # Tabela de banimentos de campeões (sistema progressivo)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS champion_bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lol_account_id INTEGER NOT NULL,
                champion_name TEXT NOT NULL,
                ban_level INTEGER DEFAULT 1,
                ban_days INTEGER NOT NULL,
                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                reason TEXT,
                FOREIGN KEY (lol_account_id) REFERENCES lol_accounts(id),
                UNIQUE(lol_account_id, champion_name)
            )
        ''')
        
        # Tabela para rastrear alertas já enviados (evita duplicação)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_alerts_sent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lol_account_id INTEGER NOT NULL,
                match_id TEXT NOT NULL,
                champion_name TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lol_account_id) REFERENCES lol_accounts(id),
                UNIQUE(lol_account_id, match_id, champion_name)
            )
        ''')
        
        # Tabela para rastrear notificações de score já enviadas (evita duplicação)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_notifications_sent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lol_account_id INTEGER NOT NULL,
                match_id TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lol_account_id) REFERENCES lol_accounts(id),
                UNIQUE(lol_account_id, match_id)
            )
        ''')
        
        # Tabela de estatísticas de pintado de ouro (notas baixas - abaixo da média)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gold_medals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lol_account_id INTEGER NOT NULL,
                champion_name TEXT NOT NULL,
                role TEXT NOT NULL,
                match_id TEXT NOT NULL,
                mvp_score REAL DEFAULT 0,
                year INTEGER NOT NULL,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lol_account_id) REFERENCES lol_accounts(id),
                UNIQUE(lol_account_id, match_id)
            )
        ''')
        
        # Tabela de votação de MVP após partida
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mvp_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                voter_discord_id TEXT NOT NULL,
                voted_discord_id TEXT NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_id, voter_discord_id)
            )
        ''')
        
        # Tabela de carry score acumulado
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carry_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                reason TEXT,
                year INTEGER NOT NULL,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(discord_id, game_id)
            )
        ''')
        
        # Tabela de piorzin score acumulado (para derrotas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS piorzin_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                reason TEXT,
                year INTEGER NOT NULL,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(discord_id, game_id)
            )
        ''')
        
        # Tabela para rastrear votações pendentes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                message_id TEXT,
                channel_id TEXT,
                guild_id TEXT,
                players TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                closed INTEGER DEFAULT 0,
                UNIQUE(game_id, guild_id)
            )
        ''')
        
        # Migração: Adiciona coluna voting_channel_id em server_configs
        try:
            cursor.execute("SELECT voting_channel_id FROM server_configs LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Migrando banco: adicionando coluna voting_channel_id...")
            cursor.execute('ALTER TABLE server_configs ADD COLUMN voting_channel_id TEXT')
            print("✅ Migração voting_channel_id concluída!")
        
        # Migração: Adiciona coluna top_flex_role_id em server_configs
        try:
            cursor.execute("SELECT top_flex_role_id FROM server_configs LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Migrando banco: adicionando coluna top_flex_role_id...")
            cursor.execute('ALTER TABLE server_configs ADD COLUMN top_flex_role_id TEXT')
            print("✅ Migração top_flex_role_id concluída!")
        
        # Migração: Adiciona coluna pintado_de_ouro em lol_accounts
        try:
            cursor.execute("SELECT pintado_de_ouro FROM lol_accounts LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Migrando banco: adicionando coluna pintado_de_ouro...")
            cursor.execute('ALTER TABLE lol_accounts ADD COLUMN pintado_de_ouro INTEGER DEFAULT 0')
            print("✅ Migração pintado_de_ouro concluída!")
        
        # Migração: Adiciona coluna piorzin_role_id em server_configs
        try:
            cursor.execute("SELECT piorzin_role_id FROM server_configs LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Migrando banco: adicionando coluna piorzin_role_id...")
            cursor.execute('ALTER TABLE server_configs ADD COLUMN piorzin_role_id TEXT')
            print("✅ Migração piorzin_role_id concluída!")
        
        # Tabela para histórico de vencedores do top_flex semanal
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS top_flex_winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                week_start DATE NOT NULL,
                week_end DATE NOT NULL,
                total_score INTEGER NOT NULL,
                awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, week_start)
            )
        ''')
        
        # Tabela para histórico de vencedores do piorzin semanal
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS piorzin_winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                week_start DATE NOT NULL,
                week_end DATE NOT NULL,
                total_score INTEGER NOT NULL,
                awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, week_start)
            )
        ''')
        
        # Tabela para histórico de posições semanais de TODOS os participantes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT NOT NULL,
                week_start DATE NOT NULL,
                week_end DATE NOT NULL,
                position INTEGER NOT NULL,
                total_score INTEGER NOT NULL,
                total_participants INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(discord_id, week_start)
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
    
    def get_all_lol_accounts(self) -> List[Dict]:
        """Retorna todas as contas LOL cadastradas no sistema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, discord_id, summoner_name, summoner_id, puuid, account_id, region, created_at
            FROM lol_accounts
        ''')
        
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                'id': row[0],
                'discord_id': row[1],
                'summoner_name': row[2],
                'summoner_id': row[3],
                'puuid': row[4],
                'account_id': row[5],
                'region': row[6],
                'created_at': row[7]
            })
        
        conn.close()
        return accounts
    
    def add_lol_account(self, discord_id: str, summoner_name: str, summoner_id: str, 
                       puuid: str, account_id: str, region: str) -> tuple[bool, str]:
        """Adiciona uma conta LOL para um usuário (máximo 3)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM lol_accounts WHERE discord_id = ?', (discord_id,))
        count = cursor.fetchone()[0]
        
        if count >= 3:
            conn.close()
            return False, "Você já tem 3 contas vinculadas. Remova uma para adicionar outra."
        
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
    
    def unlink_lol_account(self, lol_account_id: int) -> bool:
        """Remove uma conta LOL do usuário (mantém as estatísticas nas tabelas matches)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Remove apenas da tabela lol_accounts
            # As estatísticas em matches são mantidas (lol_account_id ainda referencia)
            cursor.execute('DELETE FROM lol_accounts WHERE id = ?', (lol_account_id,))
            
            # Remove notificações de live games dessa conta
            cursor.execute('DELETE FROM live_games_notified WHERE lol_account_id = ?', (lol_account_id,))
            
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            
            return deleted > 0
        except Exception as e:
            print(f"❌ [DATABASE] Erro ao desvincular conta: {e}")
            return False
    
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
                    mvp_score, mvp_placement, kda, kill_participation, played_at, is_remake
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                match_data.get('mvp_score', 0),
                match_data.get('mvp_placement', 0),
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
                   game_duration, win, kda, kill_participation, played_at, is_remake
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
                'kda': row[14],
                'kill_participation': row[15],
                'played_at': row[16],
                'is_remake': row[17] if len(row) > 17 else False
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
    
    def get_matches_by_date(self, lol_account_id: int, date_str: str) -> List[Dict]:
        """Retorna todas as partidas de uma data específica (formato: YYYY-MM-DD)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT match_id, game_mode, champion_name, role, kills, deaths, assists,
                   damage_dealt, damage_taken, gold_earned, cs, vision_score,
                   game_duration, win, kda, kill_participation, played_at, is_remake,
                   mvp_score, mvp_placement
            FROM matches
            WHERE lol_account_id = ?
              AND date(played_at) = ?
            ORDER BY played_at DESC
        ''', (lol_account_id, date_str))
        
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
                'kda': row[14],
                'kill_participation': row[15],
                'played_at': row[16],
                'is_remake': row[17] if row[17] else False,
                'mvp_score': row[18] if row[18] else 0,
                'mvp_placement': row[19] if row[19] else 0
            })
        
        conn.close()
        return matches
    
    def get_all_matches_by_date(self, discord_id: str, date_str: str) -> List[Dict]:
        """Retorna todas as partidas de todas as contas de um usuário em uma data específica"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.match_id, m.game_mode, m.champion_name, m.role, m.kills, m.deaths, m.assists,
                   m.damage_dealt, m.damage_taken, m.gold_earned, m.cs, m.vision_score,
                   m.game_duration, m.win, m.kda, m.kill_participation, m.played_at, m.is_remake,
                   m.mvp_score, m.mvp_placement, la.summoner_name, la.id as account_id
            FROM matches m
            JOIN lol_accounts la ON m.lol_account_id = la.id
            WHERE la.discord_id = ?
              AND date(m.played_at) = ?
            ORDER BY m.played_at DESC
        ''', (discord_id, date_str))
        
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
                'kda': row[14],
                'kill_participation': row[15],
                'played_at': row[16],
                'is_remake': row[17] if row[17] else False,
                'mvp_score': row[18] if row[18] else 0,
                'mvp_placement': row[19] if row[19] else 0,
                'summoner_name': row[20],
                'account_id': row[21]
            })
        
        conn.close()
        return matches
    
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

    def get_live_game_notification_time(self, game_id: str) -> Optional[str]:
        """Retorna o horário da última notificação para um game_id específico"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT notified_at FROM live_games_notified
            WHERE game_id = ?
            ORDER BY notified_at DESC
            LIMIT 1
        ''', (game_id,))

        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def mark_live_game_notified(self, lol_account_id: int, game_id: str,
                                puuid: str, summoner_name: str, champion_id: int, champion_name: str,
                                message_id: str = None, channel_id: str = None,
                                guild_id: str = None) -> bool:
        """Marca uma live game como notificada e salva IDs da mensagem"""
        try:
            print(f"💾 [DB] Salvando live game: account={lol_account_id}, game={game_id}, summoner={summoner_name}, msg={message_id}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Usa INSERT OR REPLACE para atualizar se já existir
            cursor.execute('''
                INSERT OR REPLACE INTO live_games_notified
                (lol_account_id, game_id, puuid, summoner_name, champion_id, champion_name, message_id, channel_id, guild_id, notified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (lol_account_id, game_id, puuid, summoner_name, champion_id, champion_name, message_id, channel_id, guild_id))
            rows_affected = cursor.rowcount
            conn.commit()
            
            # Verifica se foi salvo
            cursor.execute('SELECT COUNT(*) FROM live_games_notified WHERE game_id = ?', (game_id,))
            count = cursor.fetchone()[0]
            conn.close()
            
            print(f"✅ [DB] Live game salva: {rows_affected} linha(s) afetada(s), total para game_id={game_id}: {count}")
            return True
        except Exception as e:
            print(f"❌ [DB] Erro ao marcar live game como notificada: {e}")
            import traceback
            traceback.print_exc()
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
            SELECT message_id, channel_id, guild_id, game_id, puuid, summoner_name, champion_name
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
                'game_id': result[3],
                'puuid': result[4],
                'summoner_name': result[5],
                'champion_name': result[6]
            }
        return None
    
    def get_live_game_message_by_game_id(self, game_id: str, guild_id: str = None) -> Optional[Dict]:
        """Busca a mensagem de uma partida ao vivo pelo game_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if guild_id:
            cursor.execute('''
                SELECT message_id, channel_id, guild_id
                FROM live_games_notified
                WHERE game_id = ? AND guild_id = ? AND message_id IS NOT NULL
                LIMIT 1
            ''', (game_id, guild_id))
        else:
            cursor.execute('''
                SELECT message_id, channel_id, guild_id
                FROM live_games_notified
                WHERE game_id = ? AND message_id IS NOT NULL
                LIMIT 1
            ''', (game_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'message_id': result[0],
                'channel_id': result[1],
                'guild_id': result[2]
            }
        return None
    
    def get_live_game_players(self, game_id: str, guild_id: str = None) -> List[Dict]:
        """Retorna todos os jogadores já notificados de uma partida ao vivo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if guild_id:
            cursor.execute('''
                SELECT la.discord_id, lg.summoner_name, lg.champion_name, lg.puuid, lg.lol_account_id
                FROM live_games_notified lg
                JOIN lol_accounts la ON lg.lol_account_id = la.id
                WHERE lg.game_id = ? AND lg.guild_id = ?
            ''', (game_id, guild_id))
        else:
            cursor.execute('''
                SELECT la.discord_id, lg.summoner_name, lg.champion_name, lg.puuid, lg.lol_account_id
                FROM live_games_notified lg
                JOIN lol_accounts la ON lg.lol_account_id = la.id
                WHERE lg.game_id = ?
            ''', (game_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        players = []
        for row in results:
            players.append({
                'discord_id': row[0],
                'summoner_name': row[1],
                'champion_name': row[2],
                'puuid': row[3],
                'lol_account_id': row[4]
            })
        return players
    
    def get_server_config(self, guild_id: str) -> Optional[Dict]:
        """Retorna todas as configurações de um servidor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT notification_channel_id, match_channel_id, command_channel_id, live_game_channel_id, voting_channel_id, top_flex_role_id FROM server_configs
            WHERE guild_id = ?
        ''', (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'notification_channel_id': result[0],
                'match_channel_id': result[1],
                'command_channel_id': result[2],
                'live_game_channel_id': result[3],
                'voting_channel_id': result[4] if len(result) > 4 else None,
                'top_flex_role_id': result[5] if len(result) > 5 else None
            }
        return None
    
    def get_last_n_matches_with_champion(self, lol_account_id: int, champion_name: str, n: int = 3) -> List[Dict]:
        """Retorna as últimas N partidas de um usuário com um campeão específico (exclui remakes)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT match_id, champion_name, role, kills, deaths, assists,
                   mvp_score, mvp_placement, win, played_at
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
                'mvp_score': row[6],
                'mvp_placement': row[7],
                'win': row[8],
                'played_at': row[9]
            })
        
        conn.close()
        return matches
    
    def get_top_players_by_mvp(self, limit: int = 10, min_games: int = 5) -> List[Dict]:
        """Retorna o ranking dos melhores jogadores por MVP score médio (mínimo de jogos, exclui remakes)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Busca melhores médias (apenas jogadores com mínimo de partidas, excluindo remakes)
        # Ordenado por MVP Score médio
        cursor.execute('''
            SELECT
                la.discord_id,
                la.summoner_name,
                la.region,
                COUNT(m.id) as total_games,
                AVG(COALESCE(m.mvp_score, 0)) as avg_mvp,
                SUM(CASE WHEN m.win = 1 THEN 1 ELSE 0 END) as wins,
                AVG(m.kda) as avg_kda,
                AVG(m.kill_participation) as avg_kp
            FROM matches m
            JOIN lol_accounts la ON m.lol_account_id = la.id
            WHERE strftime('%Y-%m', m.played_at) = strftime('%Y-%m', 'now')
              AND (m.is_remake = 0 OR m.is_remake IS NULL)
            GROUP BY la.id
            HAVING COUNT(m.id) >= ?
            ORDER BY avg_mvp DESC
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
                'avg_mvp': round(row[4], 2),
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
                   game_duration, win, kda, kill_participation, played_at
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
                'kda': row[14],
                'kill_participation': row[15],
                'played_at': row[16]
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
            
            cursor.execute('SELECT COUNT(*) FROM matches')
            count = cursor.fetchone()[0]
            
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
            
            cursor.execute('SELECT COUNT(*) FROM matches WHERE lol_account_id = ?', (lol_account_id,))
            count = cursor.fetchone()[0]
            
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
            
            cursor.execute('SELECT id FROM lol_accounts WHERE discord_id = ?', (discord_id,))
            account_ids = [row[0] for row in cursor.fetchall()]
            
            if not account_ids:
                conn.close()
                return True, 0
            
            placeholders = ','.join('?' * len(account_ids))
            cursor.execute(f'SELECT COUNT(*) FROM matches WHERE lol_account_id IN ({placeholders})', account_ids)
            count = cursor.fetchone()[0]
            
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
            SELECT lol_account_id, game_id, message_id, channel_id, guild_id, notified_at, puuid, summoner_name, champion_name
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
                'notified_at': row[5],
                'puuid': row[6],
                'summoner_name': row[7],
                'champion_name': row[8]
            })
        
        conn.close()
        print(f"📋 [DB] Encontradas {len(live_games)} live games ativas nas últimas {hours}h")
        for lg in live_games:
            print(f"   📋 {lg['game_id']} | {lg['summoner_name']} | {lg['champion_name']}")
        return live_games
    
    def clear_live_game_notifications(self, game_id: str) -> bool:
        """Remove TODAS as notificações de uma partida ao vivo (quando a mensagem foi excluída)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM live_games_notified
                WHERE game_id = ?
            ''', (game_id,))
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            
            print(f"🗑️ [DATABASE] {deleted} registro(s) de live game {game_id} removidos")
            return True
        except Exception as e:
            print(f"❌ [DATABASE] Erro ao limpar notificações: {e}")
            return False
    
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
    
    def update_account_puuid(self, account_id: int, new_puuid: str, new_summoner_id: str, new_account_id: str) -> bool:
        """Atualiza o PUUID e IDs de uma conta"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE lol_accounts
                SET puuid = ?, summoner_id = ?, account_id = ?
                WHERE id = ?
            ''', (new_puuid, new_summoner_id, new_account_id, account_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ [DATABASE] Erro ao atualizar PUUID: {e}")
            return False
    
    def get_all_accounts(self) -> List[Dict]:
        """Retorna todas as contas LOL do banco"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, discord_id, summoner_name, summoner_id, puuid, account_id, region
            FROM lol_accounts
        ''')
        
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                'id': row[0],
                'discord_id': row[1],
                'summoner_name': row[2],
                'summoner_id': row[3],
                'puuid': row[4],
                'account_id': row[5],
                'region': row[6]
            })
        
        conn.close()
        return accounts
    
    def add_champion_ban(self, lol_account_id: int, champion_name: str, ban_days: int, ban_level: int, reason: str = None) -> bool:
        """Adiciona ou atualiza um banimento de campeão com sistema progressivo"""
        try:
            from datetime import datetime, timedelta
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Formata a data de expiração como string ISO para consistência com SQLite
            expires_at = (datetime.now() + timedelta(days=ban_days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Verifica se já existe um banimento (ativo ou não) para este campeão
            cursor.execute('''
                SELECT id, ban_level FROM champion_bans
                WHERE lol_account_id = ? AND champion_name = ?
            ''', (lol_account_id, champion_name))
            
            existing = cursor.fetchone()
            
            if existing:
                # Atualiza banimento existente
                cursor.execute('''
                    UPDATE champion_bans
                    SET ban_level = ?, ban_days = ?, banned_at = CURRENT_TIMESTAMP, 
                        expires_at = ?, reason = ?
                    WHERE lol_account_id = ? AND champion_name = ?
                ''', (ban_level, ban_days, expires_at, reason, lol_account_id, champion_name))
                print(f"🔄 [ChampBan] Atualizado banimento: {champion_name} -> Nível {ban_level}, expira em {expires_at}")
            else:
                # Cria novo banimento
                cursor.execute('''
                    INSERT INTO champion_bans (lol_account_id, champion_name, ban_level, ban_days, expires_at, reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (lol_account_id, champion_name, ban_level, ban_days, expires_at, reason))
                print(f"✅ [ChampBan] Novo banimento: {champion_name} -> Nível {ban_level}, expira em {expires_at}")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Erro ao adicionar banimento: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_active_champion_bans(self, lol_account_id: int) -> List[Dict]:
        """Retorna todos os banimentos ativos de um jogador"""
        from datetime import datetime
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT champion_name, ban_level, ban_days, banned_at, expires_at, reason
            FROM champion_bans
            WHERE lol_account_id = ? AND expires_at > datetime('now')
            ORDER BY expires_at DESC
        ''', (lol_account_id,))
        
        bans = []
        for row in cursor.fetchall():
            bans.append({
                'champion_name': row[0],
                'ban_level': row[1],
                'ban_days': row[2],
                'banned_at': row[3],
                'expires_at': row[4],
                'reason': row[5]
            })
        
        conn.close()
        return bans
    
    def is_champion_banned(self, lol_account_id: int, champion_name: str) -> bool:
        """Verifica se um campeão está banido para o jogador"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM champion_bans
            WHERE lol_account_id = ? AND champion_name = ? AND expires_at > datetime('now')
        ''', (lol_account_id, champion_name))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def get_champion_ban_level(self, lol_account_id: int, champion_name: str) -> int:
        """
        Retorna o nível de banimento atual do campeão.
        
        Sistema progressivo:
        - Se ban ativo: retorna nível atual
        - Se expirou há menos de 2 dias: mantém nível (próximo ban será nível+1)
        - Se expirou há mais de 2 dias: reseta para 0 (próximo ban será nível 1)
        """
        from datetime import datetime, timedelta
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Busca o último banimento (ativo ou expirado recentemente)
        cursor.execute('''
            SELECT ban_level, expires_at FROM champion_bans
            WHERE lol_account_id = ? AND champion_name = ?
            ORDER BY banned_at DESC
            LIMIT 1
        ''', (lol_account_id, champion_name))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return 0
        
        ban_level, expires_at_str = result
        expires_at = datetime.fromisoformat(expires_at_str)
        now = datetime.now()
        
        # Se ainda está ativo, retorna o nível atual
        if expires_at > now:
            return ban_level
        
        # Se expirou há menos de 2 dias, mantém o nível para próximo banimento
        if (now - expires_at) < timedelta(days=2):
            return ban_level
        
        # Se expirou há mais de 2 dias, reseta para 0 (volta pro nível 1 no próximo ban)
        return 0
    
    def cleanup_expired_bans(self) -> int:
        """Remove banimentos expirados há mais de 30 dias (limpeza de histórico)"""
        try:
            from datetime import datetime, timedelta
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=30)
            
            cursor.execute('''
                DELETE FROM champion_bans
                WHERE expires_at < ?
            ''', (cutoff_date,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            print(f"❌ Erro ao limpar banimentos expirados: {e}")
            return 0
    
    def remove_champion_ban(self, lol_account_id: int, champion_name: str) -> bool:
        """Remove um banimento específico de campeão"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM champion_bans
                WHERE lol_account_id = ? AND champion_name = ?
            ''', (lol_account_id, champion_name))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            print(f"❌ Erro ao remover banimento: {e}")
            return False
    
    def remove_all_champion_bans(self, lol_account_id: int) -> int:
        """Remove todos os banimentos de uma conta. Retorna quantidade removida."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM champion_bans
                WHERE lol_account_id = ?
            ''', (lol_account_id,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            print(f"❌ Erro ao remover todos os banimentos: {e}")
            return 0
    
    def get_all_active_champion_bans(self) -> List[Dict]:
        """Retorna todos os banimentos ativos de todos os jogadores"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cb.champion_name, cb.ban_level, cb.ban_days, cb.banned_at, cb.expires_at, cb.reason,
                   la.summoner_name, la.discord_id
            FROM champion_bans cb
            JOIN lol_accounts la ON cb.lol_account_id = la.id
            WHERE cb.expires_at > datetime('now')
            ORDER BY cb.expires_at ASC
        ''')
        
        bans = []
        for row in cursor.fetchall():
            bans.append({
                'champion_name': row[0],
                'ban_level': row[1],
                'ban_days': row[2],
                'banned_at': row[3],
                'expires_at': row[4],
                'reason': row[5],
                'summoner_name': row[6],
                'discord_id': row[7]
            })
        
        conn.close()
        return bans
    
    def was_performance_alert_sent(self, lol_account_id: int, match_id: str, champion_name: str) -> bool:
        """Verifica se já foi enviado alerta de performance para esta partida e campeão"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM performance_alerts_sent
                WHERE lol_account_id = ? AND match_id = ? AND champion_name = ?
            ''', (lol_account_id, match_id, champion_name))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            print(f"❌ Erro ao verificar alerta: {e}")
            return False
    
    def mark_performance_alert_sent(self, lol_account_id: int, match_id: str, champion_name: str, alert_type: str) -> bool:
        """Marca que um alerta de performance foi enviado para esta partida e campeão"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO performance_alerts_sent
                (lol_account_id, match_id, champion_name, alert_type)
                VALUES (?, ?, ?, ?)
            ''', (lol_account_id, match_id, champion_name, alert_type))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Erro ao marcar alerta: {e}")
            return False
    
    def was_match_notification_sent(self, lol_account_id: int, match_id: str) -> bool:
        """Verifica se já foi enviada notificação de score para esta partida"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM match_notifications_sent
                WHERE lol_account_id = ? AND match_id = ?
            ''', (lol_account_id, match_id))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            print(f"❌ Erro ao verificar notificação: {e}")
            return False
    
    def mark_match_notification_sent(self, lol_account_id: int, match_id: str) -> bool:
        """Marca que uma notificação de score foi enviada para esta partida"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO match_notifications_sent
                (lol_account_id, match_id)
                VALUES (?, ?)
            ''', (lol_account_id, match_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Erro ao marcar notificação: {e}")
            return False
    
    # ==================== SISTEMA DE PINTADO DE OURO (NOTAS BAIXAS) ====================
    
    def add_gold_medal(self, lol_account_id: int, champion_name: str, role: str, match_id: str, mvp_score: float, year: int = None) -> bool:
        """Adiciona um pintado de ouro (nota baixa - abaixo da média) para uma conta"""
        try:
            from datetime import datetime
            if year is None:
                year = datetime.now().year
            
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO gold_medals
                (lol_account_id, champion_name, role, match_id, mvp_score, year)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (lol_account_id, champion_name, role, match_id, mvp_score, year))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Erro ao adicionar pintado de ouro: {e}")
            return False
    
    def get_gold_medals_by_champion(self, lol_account_id: int, year: int = None) -> List[Dict]:
        """Retorna contagem de pintados de ouro por campeão (filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT champion_name, COUNT(*) as count
            FROM gold_medals
            WHERE lol_account_id = ? AND year = ?
            GROUP BY champion_name
            ORDER BY count DESC
        ''', (lol_account_id, year))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'champion_name': row[0],
                'count': row[1]
            })
        
        conn.close()
        return results
    
    def get_gold_medals_by_role(self, lol_account_id: int, year: int = None) -> List[Dict]:
        """Retorna contagem de pintados de ouro por role/lane (filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT role, COUNT(*) as count
            FROM gold_medals
            WHERE lol_account_id = ? AND year = ?
            GROUP BY role
            ORDER BY count DESC
        ''', (lol_account_id, year))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'role': row[0],
                'count': row[1]
            })
        
        conn.close()
        return results
    
    def get_total_gold_medals(self, lol_account_id: int, year: int = None) -> int:
        """Retorna total de pintados de ouro de uma conta (filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM gold_medals
            WHERE lol_account_id = ? AND year = ?
        ''', (lol_account_id, year))
        
        result = cursor.fetchone()[0]
        conn.close()
        return result
    
    def get_total_gold_medals_by_discord(self, discord_id: str, year: int = None) -> int:
        """Retorna total de pintados de ouro de todas as contas de um usuário Discord (filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM gold_medals gm
            JOIN lol_accounts la ON gm.lol_account_id = la.id
            WHERE la.discord_id = ? AND gm.year = ?
        ''', (discord_id, year))
        
        result = cursor.fetchone()[0]
        conn.close()
        return result
    
    def get_gold_medals_by_champion_all_accounts(self, discord_id: str, year: int = None) -> List[Dict]:
        """Retorna contagem de pintados de ouro por campeão de todas as contas (filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT gm.champion_name, COUNT(*) as count
            FROM gold_medals gm
            JOIN lol_accounts la ON gm.lol_account_id = la.id
            WHERE la.discord_id = ? AND gm.year = ?
            GROUP BY gm.champion_name
            ORDER BY count DESC
        ''', (discord_id, year))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'champion_name': row[0],
                'count': row[1]
            })
        
        conn.close()
        return results
    
    def get_gold_medals_by_role_all_accounts(self, discord_id: str, year: int = None) -> List[Dict]:
        """Retorna contagem de pintados de ouro por role de todas as contas (filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT gm.role, COUNT(*) as count
            FROM gold_medals gm
            JOIN lol_accounts la ON gm.lol_account_id = la.id
            WHERE la.discord_id = ? AND gm.year = ?
            GROUP BY gm.role
            ORDER BY count DESC
        ''', (discord_id, year))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'role': row[0],
                'count': row[1]
            })
        
        conn.close()
        return results
    
    # ==================== ESTATÍSTICAS DO PERFIL ====================
    
    def get_profile_stats(self, discord_id: str, year: int = None) -> Dict:
        """Retorna estatísticas completas do perfil de um usuário (todas as contas, filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total de partidas, tempo de jogo, vitórias (filtrado por ano)
        cursor.execute('''
            SELECT 
                COUNT(*) as total_matches,
                SUM(m.game_duration) as total_time,
                SUM(CASE WHEN m.win = 1 THEN 1 ELSE 0 END) as wins,
                AVG(m.kills) as avg_kills,
                AVG(m.deaths) as avg_deaths,
                AVG(m.assists) as avg_assists,
                AVG(m.kda) as avg_kda,
                AVG(m.damage_dealt) as avg_damage,
                AVG(m.gold_earned) as avg_gold,
                AVG(m.cs) as avg_cs,
                AVG(m.vision_score) as avg_vision,
                AVG(m.mvp_score) as avg_mvp_score
            FROM matches m
            JOIN lol_accounts la ON m.lol_account_id = la.id
            WHERE la.discord_id = ?
              AND (m.is_remake = 0 OR m.is_remake IS NULL)
              AND strftime('%Y', m.played_at) = ?
        ''', (discord_id, str(year)))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row or row[0] == 0:
            return {
                'total_matches': 0,
                'total_time_seconds': 0,
                'wins': 0,
                'losses': 0,
                'winrate': 0,
                'avg_kills': 0,
                'avg_deaths': 0,
                'avg_assists': 0,
                'avg_kda': 0,
                'avg_damage': 0,
                'avg_gold': 0,
                'avg_cs': 0,
                'avg_vision': 0,
                'avg_mvp_score': 0
            }
        
        total_matches = row[0] or 0
        wins = row[2] or 0
        losses = total_matches - wins
        winrate = (wins / total_matches * 100) if total_matches > 0 else 0
        
        return {
            'total_matches': total_matches,
            'total_time_seconds': row[1] or 0,
            'wins': wins,
            'losses': losses,
            'winrate': round(winrate, 1),
            'avg_kills': round(row[3] or 0, 1),
            'avg_deaths': round(row[4] or 0, 1),
            'avg_assists': round(row[5] or 0, 1),
            'avg_kda': round(row[6] or 0, 2),
            'avg_damage': round(row[7] or 0, 0),
            'avg_gold': round(row[8] or 0, 0),
            'avg_cs': round(row[9] or 0, 1),
            'avg_vision': round(row[10] or 0, 1),
            'avg_mvp_score': round(row[11] or 0, 1)
        }
    
    def get_top_champions(self, discord_id: str, limit: int = 3, year: int = None) -> List[Dict]:
        """Retorna os campeões mais jogados com estatísticas detalhadas (filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                m.champion_name,
                COUNT(*) as games,
                SUM(CASE WHEN m.win = 1 THEN 1 ELSE 0 END) as wins,
                AVG(m.kills) as avg_kills,
                AVG(m.deaths) as avg_deaths,
                AVG(m.assists) as avg_assists,
                AVG(m.kda) as avg_kda,
                AVG(m.damage_dealt) as avg_damage,
                AVG(m.gold_earned) as avg_gold,
                AVG(m.cs) as avg_cs,
                AVG(m.vision_score) as avg_vision,
                AVG(m.mvp_score) as avg_mvp_score,
                AVG(m.kill_participation) as avg_kp
            FROM matches m
            JOIN lol_accounts la ON m.lol_account_id = la.id
            WHERE la.discord_id = ?
              AND (m.is_remake = 0 OR m.is_remake IS NULL)
              AND strftime('%Y', m.played_at) = ?
            GROUP BY m.champion_name
            ORDER BY games DESC
            LIMIT ?
        ''', (discord_id, str(year), limit))
        
        champions = []
        for row in cursor.fetchall():
            games = row[1]
            wins = row[2]
            winrate = (wins / games * 100) if games > 0 else 0
            
            champions.append({
                'champion_name': row[0],
                'games': games,
                'wins': wins,
                'losses': games - wins,
                'winrate': round(winrate, 1),
                'avg_kills': round(row[3] or 0, 1),
                'avg_deaths': round(row[4] or 0, 1),
                'avg_assists': round(row[5] or 0, 1),
                'avg_kda': round(row[6] or 0, 2),
                'avg_damage': round(row[7] or 0, 0),
                'avg_gold': round(row[8] or 0, 0),
                'avg_cs': round(row[9] or 0, 1),
                'avg_vision': round(row[10] or 0, 1),
                'avg_mvp_score': round(row[11] or 0, 1),
                'avg_kp': round(row[12] or 0, 1)
            })
        
        conn.close()
        return champions
    
    def get_role_stats(self, discord_id: str, year: int = None) -> List[Dict]:
        """Retorna estatísticas por role/lane (filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                m.role,
                COUNT(*) as games,
                SUM(CASE WHEN m.win = 1 THEN 1 ELSE 0 END) as wins,
                AVG(m.kda) as avg_kda,
                AVG(m.mvp_score) as avg_mvp_score
            FROM matches m
            JOIN lol_accounts la ON m.lol_account_id = la.id
            WHERE la.discord_id = ?
              AND (m.is_remake = 0 OR m.is_remake IS NULL)
              AND m.role IS NOT NULL
              AND m.role != 'Unknown'
              AND strftime('%Y', m.played_at) = ?
            GROUP BY m.role
            ORDER BY games DESC
        ''', (discord_id, str(year)))
        
        roles = []
        for row in cursor.fetchall():
            games = row[1]
            wins = row[2]
            winrate = (wins / games * 100) if games > 0 else 0
            
            roles.append({
                'role': row[0],
                'games': games,
                'wins': wins,
                'winrate': round(winrate, 1),
                'avg_kda': round(row[3] or 0, 2),
                'avg_mvp_score': round(row[4] or 0, 1)
            })
        
        conn.close()
        return roles
    
    # ==================== SISTEMA DE VOTAÇÃO MVP ====================
    
    def set_voting_channel(self, guild_id: str, channel_id: str) -> bool:
        """Define o canal de votação para um servidor"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO server_configs (guild_id, voting_channel_id, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(guild_id) DO UPDATE SET voting_channel_id = ?, updated_at = CURRENT_TIMESTAMP
            ''', (guild_id, channel_id, channel_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao configurar canal de votação: {e}")
            return False
    
    def get_voting_channel(self, guild_id: str) -> Optional[str]:
        """Retorna o canal de votação configurado"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT voting_channel_id FROM server_configs WHERE guild_id = ?', (guild_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def create_pending_vote(self, game_id: str, guild_id: str, players: str, message_id: str = None, channel_id: str = None, expires_minutes: int = 5) -> bool:
        """Cria uma votação pendente para uma partida"""
        try:
            from datetime import datetime, timedelta
            conn = self.get_connection()
            cursor = conn.cursor()
            expires_at = (datetime.now() + timedelta(minutes=expires_minutes)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT OR REPLACE INTO pending_votes (game_id, message_id, channel_id, guild_id, players, expires_at, closed)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            ''', (game_id, message_id, channel_id, guild_id, players, expires_at))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao criar votação pendente: {e}")
            return False
    
    def get_pending_vote(self, game_id: str, guild_id: str) -> Optional[Dict]:
        """Retorna uma votação pendente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, game_id, message_id, channel_id, guild_id, players, created_at, expires_at, closed
            FROM pending_votes
            WHERE game_id = ? AND guild_id = ? AND closed = 0
        ''', (game_id, guild_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'game_id': result[1],
                'message_id': result[2],
                'channel_id': result[3],
                'guild_id': result[4],
                'players': result[5],
                'created_at': result[6],
                'expires_at': result[7],
                'closed': result[8]
            }
        return None
    
    def close_pending_vote(self, game_id: str, guild_id: str) -> bool:
        """Fecha uma votação pendente"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pending_votes SET closed = 1 WHERE game_id = ? AND guild_id = ?
            ''', (game_id, guild_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao fechar votação: {e}")
            return False
    
    def add_mvp_vote(self, game_id: str, voter_discord_id: str, voted_discord_id: str) -> bool:
        """Adiciona um voto de MVP"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO mvp_votes (game_id, voter_discord_id, voted_discord_id)
                VALUES (?, ?, ?)
            ''', (game_id, voter_discord_id, voted_discord_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao adicionar voto: {e}")
            return False
    
    def get_votes_for_game(self, game_id: str) -> List[Dict]:
        """Retorna todos os votos de uma partida"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT voter_discord_id, voted_discord_id FROM mvp_votes WHERE game_id = ?
        ''', (game_id,))
        
        votes = []
        for row in cursor.fetchall():
            votes.append({
                'voter': row[0],
                'voted': row[1]
            })
        conn.close()
        return votes
    
    def get_vote_count_for_game(self, game_id: str) -> Dict[str, int]:
        """Retorna contagem de votos por jogador"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT voted_discord_id, COUNT(*) as votes
            FROM mvp_votes
            WHERE game_id = ?
            GROUP BY voted_discord_id
            ORDER BY votes DESC
        ''', (game_id,))
        
        counts = {}
        for row in cursor.fetchall():
            counts[row[0]] = row[1]
        conn.close()
        return counts
    
    def add_carry_score(self, discord_id: str, game_id: str, score: int, reason: str = None) -> bool:
        """Adiciona carry score para um jogador"""
        try:
            from datetime import datetime
            conn = self.get_connection()
            cursor = conn.cursor()
            year = datetime.now().year
            
            cursor.execute('''
                INSERT OR REPLACE INTO carry_scores (discord_id, game_id, score, reason, year)
                VALUES (?, ?, ?, ?, ?)
            ''', (discord_id, game_id, score, reason, year))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao adicionar carry score: {e}")
            return False
    
    def get_total_carry_score(self, discord_id: str, year: int = None) -> int:
        """Retorna o carry score total de um jogador (filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(score), 0) FROM carry_scores
            WHERE discord_id = ? AND year = ?
        ''', (discord_id, year))
        
        result = cursor.fetchone()[0]
        conn.close()
        return result
    
    def get_carry_score_ranking(self, guild_id: str = None, limit: int = 10, year: int = None) -> List[Dict]:
        """Retorna ranking de carry score"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Busca todos os carry scores do ano
        cursor.execute('''
            SELECT discord_id, SUM(score) as total_score, COUNT(*) as games
            FROM carry_scores
            WHERE year = ?
            GROUP BY discord_id
            ORDER BY total_score DESC
            LIMIT ?
        ''', (year, limit))
        
        ranking = []
        for row in cursor.fetchall():
            ranking.append({
                'discord_id': row[0],
                'total_score': row[1],
                'games': row[2]
            })
        conn.close()
        return ranking
    
    def get_weekly_carry_score_ranking(self, week_start: str, week_end: str, limit: int = 10) -> List[Dict]:
        """Retorna ranking de carry score da semana específica"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT discord_id, SUM(score) as total_score, COUNT(*) as games
            FROM carry_scores
            WHERE date(earned_at) >= ? AND date(earned_at) <= ?
            GROUP BY discord_id
            ORDER BY total_score DESC
            LIMIT ?
        ''', (week_start, week_end, limit))
        
        ranking = []
        for row in cursor.fetchall():
            ranking.append({
                'discord_id': row[0],
                'total_score': row[1],
                'games': row[2]
            })
        conn.close()
        return ranking
    
    def get_player_current_week_position(self, discord_id: str, week_start: str, week_end: str) -> Dict:
        """Retorna a posição atual do jogador no ranking da semana"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Busca ranking completo da semana
        cursor.execute('''
            SELECT discord_id, SUM(score) as total_score
            FROM carry_scores
            WHERE date(earned_at) >= ? AND date(earned_at) <= ?
            GROUP BY discord_id
            ORDER BY total_score DESC
        ''', (week_start, week_end))
        
        ranking = cursor.fetchall()
        conn.close()
        
        total_participants = len(ranking)
        
        # Encontra a posição do jogador
        for position, (player_id, score) in enumerate(ranking, 1):
            if player_id == discord_id:
                return {
                    'position': position,
                    'total_score': score,
                    'total_participants': total_participants
                }
        
        # Jogador não está no ranking
        return {
            'position': 0,
            'total_score': 0,
            'total_participants': total_participants
        }
    
    # ==================== SISTEMA DE PIORZIN SCORE (DERROTAS) ====================
    
    def add_piorzin_score(self, discord_id: str, game_id: str, score: int, reason: str = None) -> bool:
        """Adiciona piorzin score para um jogador (derrotas)"""
        try:
            from datetime import datetime
            conn = self.get_connection()
            cursor = conn.cursor()
            year = datetime.now().year
            
            cursor.execute('''
                INSERT OR REPLACE INTO piorzin_scores (discord_id, game_id, score, reason, year)
                VALUES (?, ?, ?, ?, ?)
            ''', (discord_id, game_id, score, reason, year))
            conn.commit()
            conn.close()
            print(f"✅ [Piorzin] Adicionado {score} pontos para {discord_id}")
            return True
        except Exception as e:
            print(f"❌ Erro ao adicionar piorzin score: {e}")
            return False
    
    def get_total_piorzin_score(self, discord_id: str, year: int = None) -> int:
        """Retorna o piorzin score total de um jogador (filtrado por ano)"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(score), 0) FROM piorzin_scores
            WHERE discord_id = ? AND year = ?
        ''', (discord_id, year))
        
        result = cursor.fetchone()[0]
        conn.close()
        return result
    
    def get_piorzin_score_ranking(self, guild_id: str = None, limit: int = 10, year: int = None) -> List[Dict]:
        """Retorna ranking de piorzin score"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT discord_id, SUM(score) as total_score, COUNT(*) as games
            FROM piorzin_scores
            WHERE year = ?
            GROUP BY discord_id
            ORDER BY total_score DESC
            LIMIT ?
        ''', (year, limit))
        
        ranking = []
        for row in cursor.fetchall():
            ranking.append({
                'discord_id': row[0],
                'total_score': row[1],
                'games': row[2]
            })
        conn.close()
        return ranking
    
    def get_weekly_piorzin_score_ranking(self, week_start: str, week_end: str, limit: int = 10) -> List[Dict]:
        """Retorna ranking de piorzin score da semana específica"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT discord_id, SUM(score) as total_score, COUNT(*) as games
            FROM piorzin_scores
            WHERE date(earned_at) >= ? AND date(earned_at) <= ?
            GROUP BY discord_id
            ORDER BY total_score DESC
            LIMIT ?
        ''', (week_start, week_end, limit))
        
        ranking = []
        for row in cursor.fetchall():
            ranking.append({
                'discord_id': row[0],
                'total_score': row[1],
                'games': row[2]
            })
        conn.close()
        return ranking
    
    def get_player_current_week_piorzin_position(self, discord_id: str, week_start: str, week_end: str) -> Dict:
        """Retorna a posição atual do jogador no ranking de piorzin da semana"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT discord_id, SUM(score) as total_score
            FROM piorzin_scores
            WHERE date(earned_at) >= ? AND date(earned_at) <= ?
            GROUP BY discord_id
            ORDER BY total_score DESC
        ''', (week_start, week_end))
        
        ranking = cursor.fetchall()
        conn.close()
        
        total_participants = len(ranking)
        
        for position, (player_id, score) in enumerate(ranking, 1):
            if player_id == discord_id:
                return {
                    'position': position,
                    'total_score': score,
                    'total_participants': total_participants
                }
        
        return {
            'position': 0,
            'total_score': 0,
            'total_participants': total_participants
        }
    
    def set_top_flex_role(self, guild_id: str, role_id: str) -> bool:
        """Define o cargo de premiação do top_flex para um servidor"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO server_configs (guild_id, top_flex_role_id, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(guild_id) DO UPDATE SET top_flex_role_id = ?, updated_at = CURRENT_TIMESTAMP
            ''', (guild_id, role_id, role_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao configurar cargo top_flex: {e}")
            return False
    
    def get_top_flex_role(self, guild_id: str) -> Optional[str]:
        """Retorna o cargo de premiação do top_flex configurado"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT top_flex_role_id FROM server_configs WHERE guild_id = ?', (guild_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None
    
    def add_top_flex_winner(self, discord_id: str, guild_id: str, week_start: str, week_end: str, total_score: int) -> bool:
        """Registra o vencedor do top_flex da semana"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO top_flex_winners (discord_id, guild_id, week_start, week_end, total_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (discord_id, guild_id, week_start, week_end, total_score))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao registrar vencedor top_flex: {e}")
            return False
    
    def get_last_top_flex_winner(self, guild_id: str) -> Optional[Dict]:
        """Retorna o último vencedor do top_flex"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT discord_id, week_start, week_end, total_score, awarded_at
            FROM top_flex_winners
            WHERE guild_id = ?
            ORDER BY awarded_at DESC
            LIMIT 1
        ''', (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'discord_id': result[0],
                'week_start': result[1],
                'week_end': result[2],
                'total_score': result[3],
                'awarded_at': result[4]
            }
        return None
    
    # ==================== SISTEMA DE CARGO PIORZIN ====================
    
    def set_piorzin_role(self, guild_id: str, role_id: str) -> bool:
        """Define o cargo de premiação do piorzin para um servidor"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO server_configs (guild_id, piorzin_role_id, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(guild_id) DO UPDATE SET piorzin_role_id = ?, updated_at = CURRENT_TIMESTAMP
            ''', (guild_id, role_id, role_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao configurar cargo piorzin: {e}")
            return False
    
    def get_piorzin_role(self, guild_id: str) -> Optional[str]:
        """Retorna o cargo de premiação do piorzin configurado"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT piorzin_role_id FROM server_configs WHERE guild_id = ?', (guild_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None
    
    def add_piorzin_winner(self, discord_id: str, guild_id: str, week_start: str, week_end: str, total_score: int) -> bool:
        """Registra o vencedor do piorzin da semana"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO piorzin_winners (discord_id, guild_id, week_start, week_end, total_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (discord_id, guild_id, week_start, week_end, total_score))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao registrar vencedor piorzin: {e}")
            return False
    
    def get_last_piorzin_winner(self, guild_id: str) -> Optional[Dict]:
        """Retorna o último vencedor do piorzin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT discord_id, week_start, week_end, total_score, awarded_at
            FROM piorzin_winners
            WHERE guild_id = ?
            ORDER BY awarded_at DESC
            LIMIT 1
        ''', (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'discord_id': result[0],
                'week_start': result[1],
                'week_end': result[2],
                'total_score': result[3],
                'awarded_at': result[4]
            }
        return None
    
    def save_weekly_ranking(self, week_start: str, week_end: str, ranking: List[Dict]) -> bool:
        """Salva o ranking semanal de todos os participantes"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            total_participants = len(ranking)
            
            for position, player in enumerate(ranking, 1):
                cursor.execute('''
                    INSERT OR REPLACE INTO weekly_rankings 
                    (discord_id, week_start, week_end, position, total_score, total_participants)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (player['discord_id'], week_start, week_end, position, player['total_score'], total_participants))
            
            conn.commit()
            conn.close()
            print(f"✅ [Weekly Ranking] Salvo ranking de {total_participants} participantes")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar ranking semanal: {e}")
            return False
    
    def get_player_weekly_history(self, discord_id: str, limit: int = 10) -> List[Dict]:
        """Retorna histórico de posições semanais de um jogador"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT week_start, week_end, position, total_score, total_participants
            FROM weekly_rankings
            WHERE discord_id = ?
            ORDER BY week_start DESC
            LIMIT ?
        ''', (discord_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'week_start': row[0],
                'week_end': row[1],
                'position': row[2],
                'total_score': row[3],
                'total_participants': row[4]
            })
        conn.close()
        return history
    
    def get_player_average_position(self, discord_id: str) -> Dict:
        """Retorna a média de posição e estatísticas de um jogador"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as weeks_played,
                AVG(position) as avg_position,
                MIN(position) as best_position,
                MAX(position) as worst_position,
                SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as first_places,
                SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END) as top3_count,
                AVG(total_score) as avg_score
            FROM weekly_rankings
            WHERE discord_id = ?
        ''', (discord_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] > 0:
            return {
                'weeks_played': result[0],
                'avg_position': round(result[1], 1),
                'best_position': result[2],
                'worst_position': result[3],
                'first_places': result[4],
                'top3_count': result[5],
                'avg_score': round(result[6], 1) if result[6] else 0
            }
        return {
            'weeks_played': 0,
            'avg_position': 0,
            'best_position': 0,
            'worst_position': 0,
            'first_places': 0,
            'top3_count': 0,
            'avg_score': 0
        }

    def get_champion_stats(self, discord_id: str, champion_name: str, year: int = None) -> Optional[Dict]:
        """Retorna estatísticas detalhadas de um campeão específico para um jogador"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as games,
                SUM(CASE WHEN m.win = 1 THEN 1 ELSE 0 END) as wins,
                AVG(m.kills) as avg_kills,
                AVG(m.deaths) as avg_deaths,
                AVG(m.assists) as avg_assists,
                AVG(m.kda) as avg_kda,
                AVG(m.damage_dealt) as avg_damage,
                AVG(m.gold_earned) as avg_gold,
                AVG(m.cs) as avg_cs,
                AVG(m.vision_score) as avg_vision,
                AVG(m.mvp_score) as avg_mvp_score,
                AVG(m.kill_participation) as avg_kp,
                SUM(m.game_duration) as total_time
            FROM matches m
            JOIN lol_accounts la ON m.lol_account_id = la.id
            WHERE la.discord_id = ?
              AND LOWER(m.champion_name) = LOWER(?)
              AND (m.is_remake = 0 OR m.is_remake IS NULL)
              AND strftime('%Y', m.played_at) = ?
        ''', (discord_id, champion_name, str(year)))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row or row[0] == 0:
            return None
        
        games = row[0]
        wins = row[1] or 0
        winrate = (wins / games * 100) if games > 0 else 0
        
        return {
            'champion_name': champion_name,
            'games': games,
            'wins': wins,
            'losses': games - wins,
            'winrate': round(winrate, 1),
            'avg_kills': round(row[2] or 0, 1),
            'avg_deaths': round(row[3] or 0, 1),
            'avg_assists': round(row[4] or 0, 1),
            'avg_kda': round(row[5] or 0, 2),
            'avg_damage': round(row[6] or 0, 0),
            'avg_gold': round(row[7] or 0, 0),
            'avg_cs': round(row[8] or 0, 1),
            'avg_vision': round(row[9] or 0, 1),
            'avg_mvp_score': round(row[10] or 0, 1),
            'avg_kp': round(row[11] or 0, 1),
            'total_time_seconds': row[12] or 0
        }
    
    def increment_pintado_de_ouro(self, lol_account_id: int) -> bool:
        """Incrementa o contador de 'Pintado de Ouro' de uma conta"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE lol_accounts 
                SET pintado_de_ouro = pintado_de_ouro + 1
                WHERE id = ?
            ''', (lol_account_id,))
            conn.commit()
            
            # Busca o novo valor
            cursor.execute('SELECT pintado_de_ouro FROM lol_accounts WHERE id = ?', (lol_account_id,))
            new_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"✅ [Pintado de Ouro] Contador incrementado para account_id={lol_account_id}, novo valor: {new_count}")
            return True
        except Exception as e:
            print(f"❌ [Pintado de Ouro] Erro ao incrementar: {e}")
            return False
    
    def add_pintado_de_ouro_manual(self, lol_account_id: int, amount: int = 1) -> bool:
        """Adiciona manualmente 'Pintado de Ouro' a uma conta"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE lol_accounts 
                SET pintado_de_ouro = pintado_de_ouro + ?
                WHERE id = ?
            ''', (amount, lol_account_id))
            conn.commit()
            
            # Busca o novo valor
            cursor.execute('SELECT pintado_de_ouro FROM lol_accounts WHERE id = ?', (lol_account_id,))
            new_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"✅ [Pintado de Ouro] Adicionado {amount} manualmente para account_id={lol_account_id}, novo valor: {new_count}")
            return True
        except Exception as e:
            print(f"❌ [Pintado de Ouro] Erro ao adicionar manualmente: {e}")
            return False
    
    def get_pintado_de_ouro_count(self, lol_account_id: int) -> int:
        """Retorna a quantidade de 'Pintado de Ouro' de uma conta"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT pintado_de_ouro FROM lol_accounts WHERE id = ?', (lol_account_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 0
        except Exception as e:
            print(f"❌ [Pintado de Ouro] Erro ao buscar contador: {e}")
            return 0
    
    def set_pintado_de_ouro(self, lol_account_id: int, amount: int) -> bool:
        """Define o valor de 'Pintado de Ouro' de uma conta (SET, não ADD)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE lol_accounts 
                SET pintado_de_ouro = ?
                WHERE id = ?
            ''', (amount, lol_account_id))
            conn.commit()
            conn.close()
            
            print(f"✅ [Pintado de Ouro] Valor definido para {amount} na account_id={lol_account_id}")
            return True
        except Exception as e:
            print(f"❌ [Pintado de Ouro] Erro ao definir valor: {e}")
            return False

    def get_gold_medals_by_champion(self, discord_id: str, champion_name: str, year: int = None) -> int:
        """Retorna quantidade de pintados de ouro de um campeão específico"""
        from datetime import datetime
        if year is None:
            year = datetime.now().year
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) 
            FROM gold_medals gm
            JOIN lol_accounts la ON gm.lol_account_id = la.id
            WHERE la.discord_id = ? 
              AND LOWER(gm.champion_name) = LOWER(?)
              AND gm.year = ?
        ''', (discord_id, champion_name, year))
        
        result = cursor.fetchone()[0]
        conn.close()
        return result
