#!/usr/bin/env python3
"""
MSSQL Backup Manager
====================
A standalone tool for managing SQL Server database backups and restores.

Usage:
    python backup_manager.py --databases              # List all databases
    python backup_manager.py --info MyDatabase        # Database details
    python backup_manager.py --history                # Backup history
    python backup_manager.py --backup MyDB            # Backup a database
    python backup_manager.py --restore MyDB --file backup.bak  # Restore
    python backup_manager.py --list                   # List local backups
"""

import os
import sys
import argparse
import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import database service
from database_service import DatabaseService


def list_local_backups():
    """List all available local backup files."""
    print("=" * 70)
    print("Local Backup Files")
    print("=" * 70)
    
    backups = DatabaseService.list_backups()
    
    if not backups:
        print("No backups found.")
        print(f"Backup path: {DatabaseService.get_backup_path()}")
        return
    
    print(f"Path: {DatabaseService.get_backup_path()}\n")
    
    for backup in backups:
        mtime = datetime.datetime.fromtimestamp(backup['modified'])
        print(f"  📦 {backup['name']:<45} {backup['size_mb']:>8.2f} MB   {mtime.strftime('%Y-%m-%d %H:%M')}")


def list_all_databases(include_system: bool = False):
    """List all databases on the SQL Server."""
    print("=" * 70)
    print("Databases on SQL Server")
    print("=" * 70)
    
    databases = DatabaseService.list_all_databases(include_system=include_system)
    
    if not databases:
        print("No databases found or connection failed.")
        return
    
    print(f"\n{'Database Name':<30} {'State':<12} {'Size (MB)':>12} {'Recovery':>12}")
    print("-" * 70)
    
    total_size = 0
    for db in databases:
        print(f"{db['name']:<30} {db['state']:<12} {db['size_mb']:>12.2f} {db['recovery_model']:>12}")
        total_size += db['size_mb']
    
    print("-" * 70)
    print(f"{'Total':<30} {'':<12} {total_size:>12.2f}")
    print(f"\nFound {len(databases)} databases")


def show_database_info(db_name: str):
    """Show detailed information about a database."""
    print("=" * 70)
    print(f"Database Info: {db_name}")
    print("=" * 70)
    
    info = DatabaseService.get_database_info(db_name)
    
    if not info:
        print(f"Database '{db_name}' not found or error occurred.")
        return
    
    print(f"\n📊 General Information:")
    print(f"   Name:           {info['name']}")
    print(f"   State:          {info['state']}")
    print(f"   Recovery Model: {info['recovery_model']}")
    print(f"   Created:        {info['created']}")
    
    print(f"\n💾 Size Information:")
    print(f"   Data Size:      {info['data_size_mb']:.2f} MB")
    print(f"   Log Size:       {info['log_size_mb']:.2f} MB")
    print(f"   Total Size:     {info['total_size_mb']:.2f} MB")
    
    print(f"\n📦 Last Backup:")
    if info['last_backup_date']:
        print(f"   Date:           {info['last_backup_date']}")
        print(f"   Type:           {info['last_backup_type']}")
        print(f"   Size:           {info['last_backup_size_mb']:.2f} MB")
        print(f"   Compressed:     {info['last_backup_compressed_mb']:.2f} MB")
        if info['last_backup_size_mb'] > 0:
            ratio = (1 - info['last_backup_compressed_mb'] / info['last_backup_size_mb']) * 100
            print(f"   Compression:    {ratio:.1f}% reduction")
    else:
        print("   ⚠️ No backup found!")
    
    print(f"\n📈 Estimated Backup Size:")
    if info['last_backup_compressed_mb'] > 0:
        print(f"   Based on last:  ~{info['last_backup_compressed_mb']:.2f} MB (compressed)")
    else:
        print(f"   Estimated:      ~{info['data_size_mb']:.2f} MB (uncompressed)")


def show_backup_history(db_name: str = None, limit: int = 10):
    """Show backup history."""
    title = f"Backup History: {db_name}" if db_name else "Backup History (All Databases)"
    print("=" * 90)
    print(title)
    print("=" * 90)
    
    history = DatabaseService.get_backup_history(db_name=db_name, limit=limit)
    
    if not history:
        print("No backup history found.")
        return
    
    print(f"\n{'Database':<25} {'Type':<8} {'Size (MB)':>10} {'Compressed':>12} {'Date':<20}")
    print("-" * 90)
    
    for record in history:
        date_str = record['end_time'].strftime('%Y-%m-%d %H:%M') if record['end_time'] else 'N/A'
        print(f"{record['database']:<25} {record['type']:<8} {record['size_mb']:>10.2f} {record['compressed_mb']:>12.2f} {date_str:<20}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='MSSQL Backup Manager - Backup, restore and manage SQL Server databases',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List all databases:       python backup_manager.py --databases
  Database info:            python backup_manager.py --info MyDB
  Backup history:           python backup_manager.py --history
  Backup single DB:         python backup_manager.py --backup MyDB
  Backup multiple DBs:      python backup_manager.py --backup MyDB1 MyDB2 MyDB3
  Restore:                  python backup_manager.py --restore MyDB --file backup.bak
  Cross-server restore:     python backup_manager.py --restore MyDB --file backup.bak \\
                               --target-host 192.168.1.100 --target-port 1433 \\
                               --target-user sa --target-password Password --force
"""
    )
    
    # Info commands
    parser.add_argument(
        '--databases', '--dbs',
        action='store_true',
        help='List all databases on the SQL Server'
    )
    parser.add_argument(
        '--include-system',
        action='store_true',
        help='Include system databases when listing'
    )
    parser.add_argument(
        '--info', '-i',
        type=str,
        metavar='DB',
        help='Show detailed info about a database (size, backups, etc.)'
    )
    parser.add_argument(
        '--history', '-H',
        nargs='?',
        const='__all__',
        metavar='DB',
        help='Show backup history (optionally for specific database)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Limit number of history records (default: 10)'
    )
    
    # Backup commands
    parser.add_argument(
        '--backup', '-b',
        nargs='+',
        metavar='DB',
        help='Database name(s) to backup'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Custom backup output path'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available local backup files'
    )
    
    # Restore commands
    parser.add_argument(
        '--restore', '-r',
        type=str,
        metavar='DB',
        help='Database name to restore'
    )
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Backup file path for restore'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force restore (overwrite existing database)'
    )
    
    # Cross-server restore options
    parser.add_argument(
        '--target-host',
        type=str,
        help='Target SQL Server hostname for cross-server restore'
    )
    parser.add_argument(
        '--target-port',
        type=str,
        default='1433',
        help='Target SQL Server port (default: 1433)'
    )
    parser.add_argument(
        '--target-user',
        type=str,
        help='Target SQL Server username'
    )
    parser.add_argument(
        '--target-password',
        type=str,
        help='Target SQL Server password'
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    # List all databases
    if args.databases:
        list_all_databases(include_system=args.include_system)
        return 0
    
    # Database info
    if args.info:
        show_database_info(args.info)
        return 0
    
    # Backup history
    if args.history:
        db_name = None if args.history == '__all__' else args.history
        show_backup_history(db_name=db_name, limit=args.limit)
        return 0
    
    # List local backups
    if args.list:
        list_local_backups()
        return 0
    
    # Restore database
    if args.restore:
        if not args.file:
            print("❌ Please specify --file for restore")
            return 1
        
        # Cross-server restore if target-host is specified
        if args.target_host:
            success = DatabaseService.restore_to_server(
                args.restore,
                args.file,
                target_host=args.target_host,
                target_port=args.target_port,
                target_user=args.target_user,
                target_password=args.target_password,
                force=args.force
            )
        else:
            success = DatabaseService.restore_database(
                args.restore,
                args.file,
                force=args.force
            )
        return 0 if success else 1
    
    # Backup database(s)
    if args.backup:
        if len(args.backup) == 1:
            success = DatabaseService.backup_database(args.backup[0])
            return 0 if success else 1
        else:
            results = DatabaseService.backup_all_databases(args.backup)
            return 0 if all(results.values()) else 1
    
    # No action specified
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
