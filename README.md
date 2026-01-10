# MSSQL Backup Manager

A standalone Python tool for managing SQL Server database backups and restores, with support for:
- Local and remote SQL Server instances
- Docker containerized SQL Server
- Cross-server backup and restore
- SSH/SFTP file transfer for remote operations
- Backup history and database info

## Features

- 📦 **Backup databases** - Create full backups with compression
- 📥 **Restore databases** - Restore from backup files
- 🔄 **Cross-server restore** - Backup from server A, restore to server B
- 🐳 **Docker support** - Works with SQL Server in Docker containers
- 📋 **Database info** - View database sizes, backup history
- 🔐 **SSH/SFTP** - Automatic file transfer for remote servers

## Installation

```bash
# Clone or copy this folder
cd mssql-backup-manager

# Create virtual environment (optional)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Required Settings

```bash
# SQL Server connection
DB_HOST=localhost
DB_PORT=1433
DB_USER=sa
DB_PASSWORD=YourPassword
DB_DRIVER=ODBC Driver 17 for SQL Server

# Backup paths
BACKUP_PATH=./backups
```

### Remote/Docker SQL Server

```bash
# For SQL Server in Docker on remote server
DB_BACKUP_SERVER_PATH=/var/opt/mssql/data/

# SSH for auto-download
SSH_HOST=your-server.com
SSH_PORT=22
SSH_USER=ubuntu
SSH_PASSWORD=yourpassword
DOCKER_CONTAINER=mssql
```

### Target Server (for cross-server restore)

```bash
# Target server SSH (if different from source)
SSH_TARGET_HOST=target-server.com
SSH_TARGET_USER=ubuntu
SSH_TARGET_PASSWORD=password
DOCKER_TARGET_CONTAINER=mssql-target
DB_TARGET_BACKUP_PATH=/var/opt/mssql/data/
```

## Usage

### List all databases

```bash
python backup_manager.py --databases
python backup_manager.py --databases --include-system
```

### Get database info

```bash
python backup_manager.py --info MyDatabase
```

### View backup history

```bash
python backup_manager.py --history
python backup_manager.py --history MyDatabase --limit 20
```

### Backup operations

```bash
# Backup a single database
python backup_manager.py --backup MyDatabase

# Backup multiple databases
python backup_manager.py --backup MyDB1 MyDB2 MyDB3

# List local backup files
python backup_manager.py --list
```

### Restore operations

```bash
# Restore to same server
python backup_manager.py --restore MyDatabase --file ./backups/MyDatabase.bak

# Force restore (overwrite existing)
python backup_manager.py --restore MyDatabase --file ./backups/MyDatabase.bak --force

# Cross-server restore
python backup_manager.py --restore MyDatabase --file ./backups/MyDatabase.bak \
    --target-host 192.168.1.100 \
    --target-port 1433 \
    --target-user sa \
    --target-password YourPassword \
    --force
```

## Examples

### Complete workflow: Backup from Dev, Restore to QA

```bash
# 1. Backup from development server
python backup_manager.py --backup ProductionDB

# 2. Restore to QA server
python backup_manager.py --restore ProductionDB \
    --file ./backups/ProductionDB_20241225.bak \
    --target-host qa-server.com \
    --target-port 1433 \
    --target-user sa \
    --target-password QAPassword \
    --force
```

### Scheduled backups (Windows Task Scheduler)

```batch
@echo off
cd /d C:\path\to\mssql-backup-manager
python backup_manager.py --backup MyDB1 MyDB2 MyDB3
```

### Scheduled backups (Linux cron)

```bash
0 2 * * * cd /path/to/mssql-backup-manager && python backup_manager.py --backup MyDB1 MyDB2 >> /var/log/backup.log 2>&1
```

## Requirements

- Python 3.8+
- ODBC Driver 17 for SQL Server
- pyodbc
- python-dotenv
- paramiko (for remote operations)

## License

MIT License
