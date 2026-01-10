"""
MSSQL Database Service
======================
Core service class for SQL Server database operations.
"""

import os
import datetime
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseService:
    """Service class for SQL Server database operations."""
    
    @classmethod
    def build_connection_string(
        cls,
        host: str = None,
        port: str = None,
        user: str = None,
        password: str = None,
        driver: str = None,
        database: str = 'master'
    ) -> str:
        """
        Build a connection string with custom parameters.
        
        Args:
            host: Server hostname/IP (defaults to DB_HOST)
            port: Server port (defaults to DB_PORT)
            user: Username (defaults to DB_USER)
            password: Password (defaults to DB_PASSWORD)
            driver: ODBC driver (defaults to DB_DRIVER)
            database: Database name (defaults to 'master')
        """
        host = host or os.getenv('DB_HOST', 'localhost')
        port = port or os.getenv('DB_PORT', '1433')
        user = user or os.getenv('DB_USER', 'sa')
        password = password or os.getenv('DB_PASSWORD', '')
        driver = driver or os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
        
        server = f"{host},{port}" if port else host
        
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
        )
    
    @classmethod
    def get_master_connection_string(cls) -> str:
        """Build connection string to master database."""
        return cls.build_connection_string(database='master')
    
    @classmethod
    def list_all_databases(cls, include_system: bool = False) -> list:
        """
        List all databases on the SQL Server.
        
        Args:
            include_system: Include system databases (master, model, msdb, tempdb)
            
        Returns:
            List of database info dictionaries
        """
        try:
            conn_str = cls.get_master_connection_string()
            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()
            
            if include_system:
                where_clause = ""
            else:
                where_clause = "WHERE d.name NOT IN ('master', 'model', 'msdb', 'tempdb')"
            
            cursor.execute(f"""
                SELECT 
                    d.name,
                    d.database_id,
                    d.create_date,
                    d.state_desc,
                    d.recovery_model_desc,
                    CAST(SUM(mf.size) * 8.0 / 1024 AS DECIMAL(18,2)) as size_mb
                FROM sys.databases d
                LEFT JOIN sys.master_files mf ON d.database_id = mf.database_id
                {where_clause}
                GROUP BY d.name, d.database_id, d.create_date, d.state_desc, d.recovery_model_desc
                ORDER BY d.name
            """)
            
            databases = []
            for row in cursor.fetchall():
                databases.append({
                    'name': row[0],
                    'id': row[1],
                    'created': row[2],
                    'state': row[3],
                    'recovery_model': row[4],
                    'size_mb': float(row[5]) if row[5] else 0
                })
            
            cursor.close()
            conn.close()
            return databases
            
        except Exception as e:
            print(f"  ❌ Error listing databases: {e}")
            return []
    
    @classmethod
    def get_database_info(cls, db_name: str) -> dict:
        """
        Get detailed information about a specific database.
        
        Args:
            db_name: Name of the database
            
        Returns:
            Dictionary with database details
        """
        try:
            conn_str = cls.get_master_connection_string()
            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    d.name,
                    d.state_desc,
                    d.recovery_model_desc,
                    d.create_date,
                    (SELECT SUM(size) * 8.0 / 1024 FROM sys.master_files WHERE database_id = d.database_id AND type = 0) as data_size_mb,
                    (SELECT SUM(size) * 8.0 / 1024 FROM sys.master_files WHERE database_id = d.database_id AND type = 1) as log_size_mb
                FROM sys.databases d
                WHERE d.name = ?
            """, (db_name,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            info = {
                'name': row[0],
                'state': row[1],
                'recovery_model': row[2],
                'created': row[3],
                'data_size_mb': float(row[4]) if row[4] else 0,
                'log_size_mb': float(row[5]) if row[5] else 0,
                'total_size_mb': (float(row[4]) if row[4] else 0) + (float(row[5]) if row[5] else 0),
            }
            
            # Get last backup info
            cursor.execute("""
                SELECT TOP 1 
                    backup_finish_date,
                    type,
                    CAST(backup_size / 1024.0 / 1024.0 AS DECIMAL(18,2)) as backup_size_mb,
                    CAST(compressed_backup_size / 1024.0 / 1024.0 AS DECIMAL(18,2)) as compressed_size_mb
                FROM msdb.dbo.backupset
                WHERE database_name = ?
                ORDER BY backup_finish_date DESC
            """, (db_name,))
            
            backup_row = cursor.fetchone()
            if backup_row:
                backup_types = {'D': 'Full', 'I': 'Differential', 'L': 'Log'}
                info['last_backup_date'] = backup_row[0]
                info['last_backup_type'] = backup_types.get(backup_row[1], backup_row[1])
                info['last_backup_size_mb'] = float(backup_row[2]) if backup_row[2] else 0
                info['last_backup_compressed_mb'] = float(backup_row[3]) if backup_row[3] else 0
            else:
                info['last_backup_date'] = None
                info['last_backup_type'] = None
                info['last_backup_size_mb'] = 0
                info['last_backup_compressed_mb'] = 0
            
            cursor.close()
            conn.close()
            return info
            
        except Exception as e:
            print(f"  ❌ Error getting database info: {e}")
            return None
    
    @classmethod
    def get_backup_history(cls, db_name: str = None, limit: int = 10) -> list:
        """
        Get backup history for a database or all databases.
        
        Args:
            db_name: Optional database name (None for all)
            limit: Maximum number of records to return
            
        Returns:
            List of backup history records
        """
        try:
            conn_str = cls.get_master_connection_string()
            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()
            
            where_clause = f"WHERE database_name = '{db_name}'" if db_name else ""
            
            cursor.execute(f"""
                SELECT TOP {limit}
                    database_name,
                    backup_start_date,
                    backup_finish_date,
                    type,
                    CAST(backup_size / 1024.0 / 1024.0 AS DECIMAL(18,2)) as backup_size_mb,
                    CAST(compressed_backup_size / 1024.0 / 1024.0 AS DECIMAL(18,2)) as compressed_size_mb,
                    physical_device_name
                FROM msdb.dbo.backupset bs
                JOIN msdb.dbo.backupmediafamily bmf ON bs.media_set_id = bmf.media_set_id
                {where_clause}
                ORDER BY backup_finish_date DESC
            """)
            
            backup_types = {'D': 'Full', 'I': 'Differential', 'L': 'Log'}
            history = []
            for row in cursor.fetchall():
                history.append({
                    'database': row[0],
                    'start_time': row[1],
                    'end_time': row[2],
                    'type': backup_types.get(row[3], row[3]),
                    'size_mb': float(row[4]) if row[4] else 0,
                    'compressed_mb': float(row[5]) if row[5] else 0,
                    'file': row[6],
                })
            
            cursor.close()
            conn.close()
            return history
            
        except Exception as e:
            print(f"  ❌ Error getting backup history: {e}")
            return []
    
    @classmethod
    def get_backup_path(cls) -> str:
        """Get local backup directory path."""
        return os.getenv('BACKUP_PATH', './backups')
    
    @classmethod
    def get_server_backup_path(cls) -> str:
        """Get backup path as seen by SQL Server (for Docker/remote).
        
        Default: /var/opt/mssql/backup for Docker-based SQL Server.
        Set DB_BACKUP_SERVER_PATH in .env to customize.
        """
        return os.getenv('DB_BACKUP_SERVER_PATH', '/var/opt/mssql/backup')
    
    @classmethod
    def _get_ssh_config(cls) -> dict:
        """Get SSH configuration from environment variables."""
        return {
            'host': os.getenv('SSH_HOST'),
            'port': int(os.getenv('SSH_PORT', '22')),
            'user': os.getenv('SSH_USER'),
            'password': os.getenv('SSH_PASSWORD'),
            'key_file': os.getenv('SSH_KEY_FILE'),
            'docker_container': os.getenv('DOCKER_CONTAINER'),
        }
    
    @classmethod
    def _download_remote_backup(cls, remote_file: str, backup_name: str) -> str:
        """Download backup file from remote server via SSH/SFTP."""
        config = cls._get_ssh_config()
        
        if not config['host'] or not config['user']:
            print(f"\n   ⚠️ SSH not configured. Set SSH_HOST, SSH_USER in .env for auto-download.")
            return None
        
        try:
            import paramiko
        except ImportError:
            print(f"\n   ⚠️ Install paramiko for auto-download: pip install paramiko")
            return None
        
        try:
            print(f"\n   🔄 Connecting to {config['host']} via SSH...")
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': config['host'],
                'port': config['port'],
                'username': config['user'],
            }
            if config['key_file']:
                connect_kwargs['key_filename'] = config['key_file']
            elif config['password']:
                connect_kwargs['password'] = config['password']
            
            ssh.connect(**connect_kwargs)
            
            docker_container = config['docker_container']
            if docker_container:
                print(f"   🐳 Copying from Docker container: {docker_container}")
                host_temp_file = f"/tmp/{backup_name}"
                
                _, stdout, stderr = ssh.exec_command(
                    f"docker cp {docker_container}:{remote_file} {host_temp_file}"
                )
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    error = stderr.read().decode()
                    print(f"   ❌ Docker copy failed: {error}")
                    ssh.close()
                    return None
                
                remote_file = host_temp_file
            
            local_backup_path = cls.get_backup_path()
            os.makedirs(local_backup_path, exist_ok=True)
            local_file = os.path.join(local_backup_path, backup_name)
            
            print(f"   📥 Downloading backup file...")
            sftp = ssh.open_sftp()
            sftp.get(remote_file, local_file)
            sftp.close()
            
            if docker_container:
                ssh.exec_command(f"rm -f {remote_file}")
            
            ssh.close()
            return local_file
            
        except Exception as e:
            print(f"   ❌ SSH download failed: {e}")
            return None
    
    @classmethod
    def backup_database(
        cls,
        db_name: str,
        backup_path: str = None,
        backup_name: str = None,
        use_server_path: bool = None
    ) -> bool:
        """
        Create a backup of a SQL Server database.
        
        Args:
            db_name: Name of the database to backup
            backup_path: Optional path for backup file
            backup_name: Optional name for backup file
            use_server_path: If True, use DB_BACKUP_SERVER_PATH for Docker/remote
            
        Returns:
            True if backup was successful, False otherwise
        """
        if use_server_path is None:
            # Auto-detect remote server: if host is not localhost, use server path
            db_host = os.getenv('DB_HOST', 'localhost').lower()
            is_remote = db_host not in ('localhost', '127.0.0.1', '.')
            use_server_path = is_remote or os.getenv('DB_BACKUP_SERVER_PATH') is not None
        
        if backup_path is None:
            if use_server_path:
                backup_path = cls.get_server_backup_path()
            else:
                backup_path = cls.get_backup_path()
                # Convert to absolute path - SQL Server interprets relative paths
                # from its own working directory, not the Python script's directory
                backup_path = os.path.abspath(backup_path)
                os.makedirs(backup_path, exist_ok=True)
        
        if backup_name is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{db_name}_{timestamp}.bak"
        elif not backup_name.endswith('.bak'):
            backup_name += '.bak'
        
        backup_file = f"{backup_path.rstrip('/\\')}/{backup_name}"
        
        print(f"\n📦 Backing up database: {db_name}")
        print(f"   Backup file: {backup_file}")
        if use_server_path:
            print(f"   (Using server-side path for Docker/remote SQL Server)")
        
        try:
            conn_str = cls.get_master_connection_string()
            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()
            
            try:
                backup_sql = f"""
                    BACKUP DATABASE [{db_name}]
                    TO DISK = N'{backup_file}'
                    WITH FORMAT, INIT,
                    NAME = N'{db_name} Full Backup',
                    COMPRESSION,
                    STATS = 10
                """
                cursor.execute(backup_sql)
            except Exception:
                print(f"   ⚠️ Retrying without compression...")
                backup_sql = f"""
                    BACKUP DATABASE [{db_name}]
                    TO DISK = N'{backup_file}'
                    WITH FORMAT, INIT,
                    NAME = N'{db_name} Full Backup',
                    STATS = 10
                """
                cursor.execute(backup_sql)
            
            while cursor.nextset():
                pass
            
            cursor.close()
            conn.close()
            
            print(f"   ✅ Backup completed: {backup_file}")
            
            if use_server_path:
                # Ensure local backup directory exists
                local_backup_path = cls.get_backup_path()
                os.makedirs(local_backup_path, exist_ok=True)
                local_file = os.path.join(local_backup_path, backup_name)
                
                local_backup = cls._download_remote_backup(backup_file, backup_name)
                if local_backup:
                    print(f"   📥 Downloaded to: {local_backup}")
                else:
                    docker_container = os.getenv('DOCKER_CONTAINER', '<container_name>')
                    print(f"\n   ⚠️ Backup is on SQL Server, not local machine!")
                    print(f"   📋 To copy backup from Docker container to local:")
                    print(f"      docker cp {docker_container}:{backup_file} {os.path.abspath(local_file)}")
                    print(f"\n   💡 To enable auto-download, configure SSH in .env:")
                    print(f"      SSH_HOST, SSH_USER, SSH_PASSWORD or SSH_KEY_FILE")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Backup failed: {e}")
            return False
    
    @classmethod
    def _upload_backup_for_restore(cls, local_file: str) -> str:
        """Upload backup file to remote server for restore.
        
        Returns the path accessible by SQL Server (inside Docker container).
        """
        config = cls._get_ssh_config()
        
        if not config['host'] or not config['user']:
            return None
        
        try:
            import paramiko
        except ImportError:
            print(f"   ⚠️ Install paramiko for remote restore: pip install paramiko")
            return None
        
        try:
            print(f"   🔄 Connecting to {config['host']} via SSH...")
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': config['host'],
                'port': config['port'],
                'username': config['user'],
            }
            if config['key_file']:
                connect_kwargs['key_filename'] = config['key_file']
            elif config['password']:
                connect_kwargs['password'] = config['password']
            
            ssh.connect(**connect_kwargs)
            
            backup_filename = os.path.basename(local_file)
            remote_temp_path = f"/tmp/{backup_filename}"
            
            print(f"   📤 Uploading backup file...")
            sftp = ssh.open_sftp()
            sftp.put(local_file, remote_temp_path)
            sftp.close()
            
            docker_container = config['docker_container']
            if docker_container:
                print(f"   🐳 Copying to Docker container: {docker_container}")
                server_backup_path = cls.get_server_backup_path()
                remote_backup_file = f"{server_backup_path.rstrip('/')}/{backup_filename}"
                
                _, stdout, stderr = ssh.exec_command(
                    f"docker cp {remote_temp_path} {docker_container}:{remote_backup_file}"
                )
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    error = stderr.read().decode()
                    print(f"   ❌ Docker copy failed: {error}")
                    ssh.close()
                    return None
                
                # Clean up temp file on host
                ssh.exec_command(f"rm -f {remote_temp_path}")
            else:
                remote_backup_file = remote_temp_path
            
            ssh.close()
            return remote_backup_file
            
        except Exception as e:
            print(f"   ❌ SSH upload failed: {e}")
            return None
    
    @classmethod
    def restore_database(
        cls,
        db_name: str,
        backup_file: str,
        force: bool = False
    ) -> bool:
        """
        Restore a SQL Server database from a backup file.
        
        Args:
            db_name: Name of the database to restore
            backup_file: Path to the backup file
            force: If True, drop existing database before restore
            
        Returns:
            True if restore was successful, False otherwise
        """
        if not os.path.exists(backup_file):
            print(f"   ❌ Backup file not found: {backup_file}")
            return False
        
        print(f"\n📥 Restoring database: {db_name}")
        print(f"   From backup: {backup_file}")
        
        # Check if SQL Server is remote/Docker
        db_host = os.getenv('DB_HOST', 'localhost').lower()
        is_remote = db_host not in ('localhost', '127.0.0.1', '.')
        
        # For remote/Docker SQL Server, upload the backup first
        if is_remote:
            remote_backup_path = cls._upload_backup_for_restore(backup_file)
            if remote_backup_path:
                restore_path = remote_backup_path
                print(f"   📁 Using remote path: {restore_path}")
            else:
                print(f"   ❌ Cannot restore: backup file must be uploaded to remote server first.")
                print(f"   💡 Configure SSH settings in .env: SSH_HOST, SSH_USER, SSH_PASSWORD or SSH_KEY_FILE")
                return False
        else:
            # Local SQL Server - use absolute local path
            restore_path = os.path.abspath(backup_file)
        
        try:
            conn_str = cls.get_master_connection_string()
            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM sys.databases WHERE name = ?", (db_name,))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                if force:
                    print(f"   Setting {db_name} to single user mode...")
                    try:
                        cursor.execute(f"""
                            ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE
                        """)
                    except:
                        pass
                else:
                    print(f"   ⚠️ Database {db_name} exists. Use --force to overwrite.")
                    return False
            
            cursor.execute(f"""
                RESTORE FILELISTONLY FROM DISK = N'{restore_path}'
            """)
            files = cursor.fetchall()
            
            cursor.execute("SELECT SERVERPROPERTY('InstanceDefaultDataPath')")
            result = cursor.fetchone()
            data_path = result[0] if result and result[0] else '/var/opt/mssql/data/'
            
            move_clauses = []
            for file_info in files:
                logical_name = file_info[0]
                file_type = file_info[2]
                
                if file_type == 'D':
                    new_path = f"{data_path.rstrip('/')}/{db_name}.mdf"
                else:
                    new_path = f"{data_path.rstrip('/')}/{db_name}_log.ldf"
                
                move_clauses.append(f"MOVE N'{logical_name}' TO N'{new_path}'")
            
            move_sql = ", ".join(move_clauses)
            
            restore_sql = f"""
                RESTORE DATABASE [{db_name}]
                FROM DISK = N'{restore_path}'
                WITH REPLACE, RECOVERY,
                {move_sql},
                STATS = 10
            """
            
            print(f"   Restoring...")
            cursor.execute(restore_sql)
            
            while cursor.nextset():
                pass
            
            # Switch database back to multi-user mode
            try:
                print(f"   Setting {db_name} to multi-user mode...")
                cursor.execute(f"""
                    ALTER DATABASE [{db_name}] SET MULTI_USER
                """)
            except:
                pass
            
            cursor.close()
            conn.close()
            
            print(f"   ✅ Restore completed: {db_name}")
            return True
            
        except Exception as e:
            print(f"   ❌ Restore failed: {e}")
            return False
    
    @classmethod
    def restore_to_server(
        cls,
        db_name: str,
        backup_file: str,
        target_host: str,
        target_port: str = '1433',
        target_user: str = None,
        target_password: str = None,
        force: bool = False
    ) -> bool:
        """
        Restore a database to a different SQL Server instance.
        
        Args:
            db_name: Name of the database to restore
            backup_file: Path to the backup file (local path)
            target_host: Target SQL Server hostname/IP
            target_port: Target SQL Server port
            target_user: Username for target server
            target_password: Password for target server
            force: If True, overwrite existing database
            
        Returns:
            True if restore was successful, False otherwise
        """
        if not os.path.exists(backup_file):
            print(f"   ❌ Backup file not found: {backup_file}")
            return False
        
        print(f"\n🔄 Cross-Server Restore")
        print(f"   Database: {db_name}")
        print(f"   From: {backup_file}")
        print(f"   To: {target_host}:{target_port}")
        
        config = cls._get_ssh_config()
        
        target_ssh_host = os.getenv('SSH_TARGET_HOST', config['host'])
        target_ssh_user = os.getenv('SSH_TARGET_USER', config['user'])
        target_ssh_password = os.getenv('SSH_TARGET_PASSWORD', config['password'])
        target_ssh_key = os.getenv('SSH_TARGET_KEY_FILE', config['key_file'])
        target_docker = os.getenv('DOCKER_TARGET_CONTAINER', config['docker_container'])
        target_backup_path = os.getenv('DB_TARGET_BACKUP_PATH', '/var/opt/mssql/data/')
        
        try:
            import paramiko
        except ImportError:
            print(f"   ❌ Install paramiko: pip install paramiko")
            return False
        
        try:
            print(f"\n   🔄 Connecting to target server via SSH...")
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': target_ssh_host,
                'port': int(os.getenv('SSH_TARGET_PORT', '22')),
                'username': target_ssh_user,
            }
            if target_ssh_key:
                connect_kwargs['key_filename'] = target_ssh_key
            elif target_ssh_password:
                connect_kwargs['password'] = target_ssh_password
            
            ssh.connect(**connect_kwargs)
            
            backup_filename = os.path.basename(backup_file)
            remote_temp_path = f"/tmp/{backup_filename}"
            
            print(f"   📤 Uploading backup file...")
            sftp = ssh.open_sftp()
            sftp.put(backup_file, remote_temp_path)
            sftp.close()
            
            if target_docker:
                print(f"   🐳 Copying to Docker container: {target_docker}")
                remote_backup_file = f"{target_backup_path.rstrip('/')}/{backup_filename}"
                
                _, stdout, stderr = ssh.exec_command(
                    f"docker cp {remote_temp_path} {target_docker}:{remote_backup_file}"
                )
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    error = stderr.read().decode()
                    print(f"   ❌ Docker copy failed: {error}")
                    ssh.close()
                    return False
                
                ssh.exec_command(f"rm -f {remote_temp_path}")
            else:
                remote_backup_file = remote_temp_path
            
            ssh.close()
            
        except Exception as e:
            print(f"   ❌ SSH upload failed: {e}")
            return False
        
        try:
            print(f"\n   🔧 Restoring on target server...")
            
            conn_str = cls.build_connection_string(
                host=target_host,
                port=target_port,
                user=target_user,
                password=target_password,
                database='master'
            )
            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM sys.databases WHERE name = ?", (db_name,))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                if force:
                    print(f"   ⚠️ Database exists, setting to single user mode...")
                    try:
                        cursor.execute(f"""
                            ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE
                        """)
                    except:
                        pass
                else:
                    print(f"   ⚠️ Database {db_name} exists. Use --force to overwrite.")
                    return False
            
            cursor.execute(f"""
                RESTORE FILELISTONLY FROM DISK = N'{remote_backup_file}'
            """)
            files = cursor.fetchall()
            
            cursor.execute("SELECT SERVERPROPERTY('InstanceDefaultDataPath')")
            result = cursor.fetchone()
            data_path = result[0] if result and result[0] else '/var/opt/mssql/data/'
            
            move_clauses = []
            for file_info in files:
                logical_name = file_info[0]
                file_type = file_info[2]
                
                if file_type == 'D':
                    new_path = f"{data_path.rstrip('/')}/{db_name}.mdf"
                else:
                    new_path = f"{data_path.rstrip('/')}/{db_name}_log.ldf"
                
                move_clauses.append(f"MOVE N'{logical_name}' TO N'{new_path}'")
            
            move_sql = ", ".join(move_clauses)
            
            restore_sql = f"""
                RESTORE DATABASE [{db_name}]
                FROM DISK = N'{remote_backup_file}'
                WITH REPLACE, RECOVERY,
                {move_sql},
                STATS = 10
            """
            
            cursor.execute(restore_sql)
            
            while cursor.nextset():
                pass
            
            # Switch database back to multi-user mode
            try:
                print(f"   Setting {db_name} to multi-user mode...")
                cursor.execute(f"""
                    ALTER DATABASE [{db_name}] SET MULTI_USER
                """)
            except:
                pass
            
            cursor.close()
            conn.close()
            
            print(f"   ✅ Restore completed on {target_host}")
            return True
            
        except Exception as e:
            print(f"   ❌ Restore failed: {e}")
            return False
    
    @classmethod
    def list_backups(cls, backup_path: str = None) -> list:
        """
        List available backup files.
        
        Args:
            backup_path: Optional path to backup directory
            
        Returns:
            List of backup file info
        """
        if backup_path is None:
            backup_path = cls.get_backup_path()
        
        if not os.path.exists(backup_path):
            return []
        
        backups = []
        for file in os.listdir(backup_path):
            if file.endswith('.bak'):
                full_path = os.path.join(backup_path, file)
                size = os.path.getsize(full_path)
                mtime = os.path.getmtime(full_path)
                backups.append({
                    'file': full_path,
                    'name': file,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'modified': mtime
                })
        
        return sorted(backups, key=lambda x: x['modified'], reverse=True)
    
    @classmethod
    def backup_all_databases(cls, databases: list) -> dict:
        """
        Backup multiple databases.
        
        Args:
            databases: List of database names
            
        Returns:
            Dict mapping database names to success status
        """
        results = {}
        
        print("=" * 60)
        print("Backing up databases")
        print("=" * 60)
        
        for db_name in databases:
            results[db_name] = cls.backup_database(db_name)
        
        print("\n" + "=" * 60)
        print("Backup Summary:")
        for db_name, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {db_name}")
        print("=" * 60)
        
        return results
