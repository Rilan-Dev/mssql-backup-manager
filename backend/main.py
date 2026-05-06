from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os
import re

# Add parent directory to path to import database_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_service import DatabaseService
from backend.history_service import HistoryService

app = FastAPI(title="MSSQL Backup Manager API", version="2.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    HistoryService.init_db()


# ---------- Pydantic Models ----------

class SSHConfig(BaseModel):
    host: str
    port: int = 22
    user: str
    password: Optional[str] = None
    key_file: Optional[str] = None
    docker_container: Optional[str] = None

class ConnectionConfig(BaseModel):
    host: str
    port: str = "1433"
    user: str
    password: Optional[str] = None
    driver: str = "ODBC Driver 17 for SQL Server"
    ssh: Optional[SSHConfig] = None

    def to_dict(self):
        d = self.dict()
        if self.ssh:
            d['ssh'] = self.ssh.dict()
        return d

class ConnectionRequest(BaseModel):
    config: ConnectionConfig

class BackupRequest(BaseModel):
    db_name: str
    config: Optional[ConnectionConfig] = None

class BatchBackupRequest(BaseModel):
    db_names: List[str]
    config: Optional[ConnectionConfig] = None

class RestoreRequest(BaseModel):
    db_name: str
    backup_file: str
    force: bool = False
    config: Optional[ConnectionConfig] = None

class QueryRequest(BaseModel):
    database: str
    query: str
    config: Optional[ConnectionConfig] = None

class UpdateConnectionRequest(BaseModel):
    host: Optional[str] = None
    port: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    driver: Optional[str] = None
    nickname: Optional[str] = None
    ssh: Optional[Dict] = None


# ---------- Health & Info ----------

@app.get("/api/health")
async def health_check():
    """API health check."""
    return {"status": "ok", "version": "2.0.0"}


@app.post("/api/server/info")
async def server_info(request: ConnectionRequest):
    """Get SQL Server version and edition info."""
    try:
        config_dict = request.config.to_dict()
        conn_str = DatabaseService.get_master_connection_string(config_dict)
        import pyodbc
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=10)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                SERVERPROPERTY('ProductVersion') AS version,
                SERVERPROPERTY('ProductLevel') AS level,
                SERVERPROPERTY('Edition') AS edition,
                SERVERPROPERTY('ServerName') AS server_name,
                @@VERSION AS full_version
        """)
        row = cursor.fetchone()
        info = {
            "version": str(row[0]),
            "level": str(row[1]),
            "edition": str(row[2]),
            "server_name": str(row[3]),
            "full_version": str(row[4]).split("\n")[0],
        }
        cursor.close()
        conn.close()
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/defaults")
async def get_defaults():
    """Get environment-configured default connection settings for Quick Connect."""
    # First check if there's a saved default in the database
    default_conn = HistoryService.get_default_connection()
    if default_conn:
        return {
            "source": "saved",
            "config": default_conn,
        }

    # Fall back to environment variables
    host = os.getenv("DB_HOST", "")
    if host:
        return {
            "source": "env",
            "config": {
                "host": host,
                "port": os.getenv("DB_PORT", "1433"),
                "user": os.getenv("DB_USER", "sa"),
                "password": os.getenv("DB_PASSWORD", ""),
                "driver": os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
            },
        }

    return {"source": "none", "config": None}


# ---------- Connection History CRUD ----------

@app.get("/api/history")
async def get_history():
    """Get all connection history."""
    return HistoryService.get_history()


@app.post("/api/history")
async def save_history(request: ConnectionRequest):
    """Save connection to history."""
    config_dict = request.config.to_dict()
    connection_id = HistoryService.save_connection(config_dict)
    return {"status": "success", "id": connection_id}


@app.get("/api/history/{connection_id}")
async def get_history_item(connection_id: int):
    """Get a single connection from history."""
    item = HistoryService.get_connection_by_id(connection_id)
    if not item:
        raise HTTPException(status_code=404, detail="Connection not found")
    return item


@app.put("/api/history/{connection_id}")
async def update_history_item(connection_id: int, data: UpdateConnectionRequest):
    """Update a saved connection."""
    update_data = data.dict(exclude_none=True)
    success = HistoryService.update_connection(connection_id, update_data)
    if not success:
        raise HTTPException(status_code=400, detail="Update failed")
    return {"status": "success"}


@app.delete("/api/history/{connection_id}")
async def delete_history_by_id(connection_id: int):
    """Delete connection from history by ID."""
    HistoryService.delete_connection(connection_id=connection_id)
    return {"status": "success"}


@app.delete("/api/history")
async def delete_history(host: str, user: str):
    """Delete connection from history by host+user (legacy)."""
    HistoryService.delete_connection(host=host, user=user)
    return {"status": "success"}


@app.post("/api/history/{connection_id}/default")
async def set_default(connection_id: int):
    """Set a connection as the default."""
    success = HistoryService.set_default_connection(connection_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set default")
    return {"status": "success"}


@app.delete("/api/history/default/clear")
async def clear_default():
    """Clear the default connection."""
    HistoryService.clear_default_connection()
    return {"status": "success"}


# ---------- Connection ----------

@app.post("/api/connect")
async def test_connection(request: ConnectionRequest):
    """Test SQL Server connection."""
    try:
        config_dict = request.config.to_dict()
        try:
            conn_str = DatabaseService.get_master_connection_string(config_dict)
            import pyodbc
            conn = pyodbc.connect(conn_str, autocommit=True, timeout=5)
            conn.close()

            # Save to history on successful connection
            connection_id = HistoryService.save_connection(config_dict)

            return {"status": "connected", "message": "Connection successful", "id": connection_id}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Databases ----------

@app.post("/api/databases")
async def list_databases(request: Optional[ConnectionRequest] = None):
    """List all databases."""
    config_dict = request.config.to_dict() if request else None
    databases = DatabaseService.list_all_databases(include_system=False, config=config_dict)
    return databases


@app.post("/api/databases/{db_name}")
async def get_database_info(db_name: str, request: Optional[ConnectionRequest] = None):
    """Get database details."""
    config_dict = request.config.to_dict() if request else None
    info = DatabaseService.get_database_info(db_name, config=config_dict)
    if not info:
        raise HTTPException(status_code=404, detail="Database not found")
    return info


@app.post("/api/databases/{db_name}/tables")
async def list_tables(db_name: str, request: Optional[ConnectionRequest] = None):
    """List all tables in a database."""
    config_dict = request.config.to_dict() if request else None
    try:
        conn_str = DatabaseService.build_connection_string(database=db_name, config=config_dict)
        import pyodbc
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=10)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.TABLE_SCHEMA,
                t.TABLE_NAME,
                t.TABLE_TYPE,
                (SELECT SUM(p.rows) FROM sys.partitions p 
                 JOIN sys.tables st ON p.object_id = st.object_id 
                 WHERE st.name = t.TABLE_NAME AND p.index_id IN (0,1)) as row_count
            FROM INFORMATION_SCHEMA.TABLES t
            ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME
        """)
        tables = []
        for row in cursor.fetchall():
            tables.append({
                "schema": row[0],
                "name": row[1],
                "type": row[2],
                "row_count": row[3] or 0,
            })
        cursor.close()
        conn.close()
        return tables
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/databases/{db_name}/shrink")
async def shrink_database(db_name: str, request: Optional[ConnectionRequest] = None):
    """Shrink a database."""
    config_dict = request.config.to_dict() if request else None
    try:
        conn_str = DatabaseService.get_master_connection_string(config_dict)
        import pyodbc
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=300)
        cursor = conn.cursor()
        cursor.execute(f"DBCC SHRINKDATABASE ([{db_name}])")
        while cursor.nextset():
            pass
        cursor.close()
        conn.close()
        return {"status": "success", "message": f"Database {db_name} shrunk successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/databases/{db_name}/history")
async def get_database_history(db_name: str, request: Optional[ConnectionRequest] = None):
    """Get backup history for a specific database."""
    config_dict = request.config.to_dict() if request else None
    history = DatabaseService.get_backup_history(db_name, config=config_dict)
    return history


# ---------- Backup & Restore ----------

@app.post("/api/backup")
async def backup_database(request: BackupRequest):
    """Trigger a database backup."""
    config_dict = request.config.to_dict() if request.config else None
    success = DatabaseService.backup_database(request.db_name, config=config_dict)
    if success:
        return {"status": "success", "message": f"Backup of {request.db_name} completed"}
    else:
        raise HTTPException(status_code=500, detail="Backup failed")


@app.post("/api/backup/batch")
async def batch_backup(request: BatchBackupRequest):
    """Backup multiple databases."""
    config_dict = request.config.to_dict() if request.config else None
    results = {}
    for db_name in request.db_names:
        results[db_name] = DatabaseService.backup_database(db_name, config=config_dict)
    
    success_count = sum(1 for v in results.values() if v)
    fail_count = len(results) - success_count
    return {
        "status": "completed",
        "results": results,
        "summary": f"{success_count} succeeded, {fail_count} failed",
    }


@app.post("/api/restore")
async def restore_database(request: RestoreRequest):
    """Trigger a database restore."""
    config_dict = request.config.to_dict() if request.config else None
    success = DatabaseService.restore_database(
        request.db_name,
        request.backup_file,
        force=request.force,
        config=config_dict
    )
    if success:
        return {"status": "success", "message": f"Restore of {request.db_name} completed"}
    else:
        raise HTTPException(status_code=500, detail="Restore failed")


@app.get("/api/backups")
async def list_local_backups():
    """List local backup files."""
    backups = DatabaseService.list_backups()
    return backups


# ---------- Query Tool ----------

@app.post("/api/query")
async def execute_query(request: QueryRequest):
    """Execute a read-only SQL query (SELECT statements only)."""
    # Security: only allow SELECT statements
    stripped = request.query.strip().upper()
    if not stripped.startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

    # Block dangerous keywords
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "EXEC", "EXECUTE", "TRUNCATE", "MERGE"]
    for keyword in dangerous:
        if re.search(rf'\b{keyword}\b', stripped):
            raise HTTPException(status_code=400, detail=f"Query contains forbidden keyword: {keyword}")

    config_dict = request.config.to_dict() if request.config else None
    try:
        conn_str = DatabaseService.build_connection_string(
            database=request.database, config=config_dict
        )
        import pyodbc
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=30)
        cursor = conn.cursor()
        cursor.execute(request.query)

        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = []
        for row in cursor.fetchall():
            rows.append({columns[i]: (str(val) if val is not None else None) for i, val in enumerate(row)})

        cursor.close()
        conn.close()
        return {"columns": columns, "rows": rows, "row_count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
