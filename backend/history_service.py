
import sqlite3
import os
import json
from typing import List, Dict, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "connections.db")

class HistoryService:
    @staticmethod
    def _get_connection():
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Initialize the database table and run migrations."""
        try:
            conn = cls._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT NOT NULL,
                    port TEXT NOT NULL,
                    user TEXT NOT NULL,
                    password TEXT,
                    driver TEXT,
                    ssh_config TEXT,
                    nickname TEXT,
                    auto_connect INTEGER DEFAULT 0,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(host, user)
                )
            """)
            conn.commit()

            # Migration: add columns if missing (for existing DBs)
            cursor.execute("PRAGMA table_info(connections)")
            columns = [col["name"] for col in cursor.fetchall()]

            if "nickname" not in columns:
                cursor.execute("ALTER TABLE connections ADD COLUMN nickname TEXT")
                # Auto-generate nicknames for existing rows
                cursor.execute("UPDATE connections SET nickname = host || ':' || port WHERE nickname IS NULL")
                conn.commit()

            if "auto_connect" not in columns:
                cursor.execute("ALTER TABLE connections ADD COLUMN auto_connect INTEGER DEFAULT 0")
                conn.commit()

            conn.close()
        except Exception as e:
            print(f"Failed to init history DB: {e}")

    @classmethod
    def _row_to_dict(cls, row) -> Dict:
        """Convert a database row to a connection dict."""
        item = {
            "id": row["id"],
            "host": row["host"],
            "port": row["port"],
            "user": row["user"],
            "password": row["password"],
            "driver": row["driver"],
            "nickname": row["nickname"] or f"{row['host']}:{row['port']}",
            "auto_connect": bool(row["auto_connect"]) if row["auto_connect"] is not None else False,
            "last_used": row["last_used"],
        }
        if row["ssh_config"]:
            item["ssh"] = json.loads(row["ssh_config"])
        return item

    @classmethod
    def get_history(cls) -> List[Dict]:
        """Retrieve all connection history."""
        try:
            conn = cls._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connections ORDER BY last_used DESC")
            rows = cursor.fetchall()
            history = [cls._row_to_dict(row) for row in rows]
            conn.close()
            return history
        except Exception as e:
            print(f"Error getting history: {e}")
            return []

    @classmethod
    def get_connection_by_id(cls, connection_id: int) -> Optional[Dict]:
        """Get a single connection by its ID."""
        try:
            conn = cls._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connections WHERE id = ?", (connection_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return cls._row_to_dict(row)
            return None
        except Exception as e:
            print(f"Error getting connection: {e}")
            return None

    @classmethod
    def get_default_connection(cls) -> Optional[Dict]:
        """Get the connection marked as auto_connect (default)."""
        try:
            conn = cls._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connections WHERE auto_connect = 1 LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                return cls._row_to_dict(row)
            return None
        except Exception as e:
            print(f"Error getting default connection: {e}")
            return None

    @classmethod
    def save_connection(cls, config: Dict) -> int:
        """Save or update a connection configuration. Returns the connection ID."""
        try:
            conn = cls._get_connection()
            cursor = conn.cursor()

            ssh_config = json.dumps(config.get("ssh")) if config.get("ssh") else None
            nickname = config.get("nickname") or f"{config['host']}:{config.get('port', '1433')}"

            cursor.execute("""
                INSERT INTO connections (host, port, user, password, driver, ssh_config, nickname, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(host, user) DO UPDATE SET
                    port=excluded.port,
                    password=excluded.password,
                    driver=excluded.driver,
                    ssh_config=excluded.ssh_config,
                    nickname=COALESCE(excluded.nickname, connections.nickname),
                    last_used=CURRENT_TIMESTAMP
            """, (
                config["host"],
                config.get("port", "1433"),
                config["user"],
                config.get("password"),
                config.get("driver", "ODBC Driver 17 for SQL Server"),
                ssh_config,
                nickname,
            ))

            conn.commit()
            connection_id = cursor.lastrowid or cursor.execute(
                "SELECT id FROM connections WHERE host = ? AND user = ?",
                (config["host"], config["user"])
            ).fetchone()["id"]
            conn.close()
            return connection_id
        except Exception as e:
            print(f"Error saving connection: {e}")
            return -1

    @classmethod
    def update_connection(cls, connection_id: int, data: Dict) -> bool:
        """Update a connection's editable fields."""
        try:
            conn = cls._get_connection()
            cursor = conn.cursor()

            updates = []
            values = []

            for field in ["host", "port", "user", "password", "driver", "nickname"]:
                if field in data:
                    updates.append(f"{field} = ?")
                    values.append(data[field])

            if "ssh" in data:
                updates.append("ssh_config = ?")
                values.append(json.dumps(data["ssh"]) if data["ssh"] else None)

            if not updates:
                return False

            values.append(connection_id)
            cursor.execute(
                f"UPDATE connections SET {', '.join(updates)} WHERE id = ?",
                values
            )
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating connection: {e}")
            return False

    @classmethod
    def set_default_connection(cls, connection_id: int) -> bool:
        """Set a connection as the default (auto_connect). Clears others."""
        try:
            conn = cls._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE connections SET auto_connect = 0")
            cursor.execute("UPDATE connections SET auto_connect = 1 WHERE id = ?", (connection_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error setting default: {e}")
            return False

    @classmethod
    def clear_default_connection(cls) -> bool:
        """Clear any default connection."""
        try:
            conn = cls._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE connections SET auto_connect = 0")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error clearing default: {e}")
            return False

    @classmethod
    def delete_connection(cls, host: str = None, user: str = None, connection_id: int = None):
        """Delete a connection from history by host+user or by ID."""
        try:
            conn = cls._get_connection()
            cursor = conn.cursor()
            if connection_id:
                cursor.execute("DELETE FROM connections WHERE id = ?", (connection_id,))
            elif host and user:
                cursor.execute("DELETE FROM connections WHERE host = ? AND user = ?", (host, user))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting connection: {e}")
            return False
