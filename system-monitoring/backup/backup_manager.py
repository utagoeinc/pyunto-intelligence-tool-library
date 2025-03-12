"""
Backup utility for Pyunto Intelligence configurations and data.

This module provides tools for backing up and managing Pyunto Intelligence
configurations, API results, and other critical data.
"""

import os
import re
import sys
import json
import time
import shutil
import logging
import hashlib
import zipfile
import requests
import threading
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union, Any, Callable, Tuple, Tuple
from typing import Dict, List, Optional, Set, Union, Any, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pyunto_backup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pyunto_backup")


class BackupManager:
    """
    Manages backups for Pyunto Intelligence configurations and data.
    
    Features:
    - Scheduled automated backups
    - Configuration backup
    - Results data backup
    - Database backup integration
    - Backup rotation and cleanup
    - Backup verification
    - Restoration capabilities
    """
    
    def __init__(
        self,
        api_key: str,
        storage_path: str = "backups",
        retention_days: int = 30,
        enable_encryption: bool = False,
        encryption_password: Optional[str] = None,
        remote_storage: Optional[Dict] = None
    ):
        """
        Initialize the backup manager.
        
        Args:
            api_key: Pyunto Intelligence API key
            storage_path: Base directory for storing backups
            retention_days: Number of days to retain backups
            enable_encryption: Whether to encrypt backup files
            encryption_password: Password for encryption (required if enable_encryption is True)
            remote_storage: Remote storage configuration (optional)
        """
        self.api_key = api_key
        self.storage_path = os.path.abspath(storage_path)
        self.retention_days = retention_days
        self.enable_encryption = enable_encryption
        self.encryption_password = encryption_password
        self.remote_storage = remote_storage
        
        # Validate encryption settings
        if self.enable_encryption and not self.encryption_password:
            raise ValueError("Encryption password is required when encryption is enabled")
        
        # Create backup directories
        self.config_backup_dir = os.path.join(self.storage_path, "config")
        self.results_backup_dir = os.path.join(self.storage_path, "results")
        self.database_backup_dir = os.path.join(self.storage_path, "database")
        
        os.makedirs(self.config_backup_dir, exist_ok=True)
        os.makedirs(self.results_backup_dir, exist_ok=True)
        os.makedirs(self.database_backup_dir, exist_ok=True)
        
        # Scheduled jobs
        self.scheduled_jobs = []
        self.is_running = False
        self.scheduler_thread = None
        
        # Default file paths for backup
        self.config_files = []
        self.results_dirs = []
        self.database_config = None
        
        logger.info(f"Backup Manager initialized with storage path: {self.storage_path}")
    
    def add_config_file(self, file_path: str):
        """
        Add a configuration file to be backed up.
        
        Args:
            file_path: Path to the configuration file
        """
        if os.path.exists(file_path):
            self.config_files.append(os.path.abspath(file_path))
            logger.info(f"Added configuration file for backup: {file_path}")
        else:
            logger.warning(f"Configuration file does not exist: {file_path}")
    
    def add_results_directory(self, directory_path: str):
        """
        Add a directory containing results data to be backed up.
        
        Args:
            directory_path: Path to the results directory
        """
        if os.path.isdir(directory_path):
            self.results_dirs.append(os.path.abspath(directory_path))
            logger.info(f"Added results directory for backup: {directory_path}")
        else:
            logger.warning(f"Results directory does not exist: {directory_path}")
    
    def configure_database_backup(
        self,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str
    ):
        """
        Configure database backup settings.
        
        Args:
            db_type: Database type ('postgresql', 'mysql', etc.)
            host: Database host
            port: Database port
            database: Database name
            username: Database username
            password: Database password
        """
        self.database_config = {
            "type": db_type,
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "password": password
        }
        
        logger.info(f"Configured {db_type} database backup for {database} on {host}:{port}")
    
    def schedule_config_backup(
        self,
        frequency: str = "daily",
        time: str = "00:00",
        retention_days: Optional[int] = None
    ):
        """
        Schedule regular configuration backups.
        
        Args:
            frequency: Backup frequency ('hourly', 'daily', 'weekly', 'monthly')
            time: Time of day to run backup (HH:MM format, for non-hourly frequencies)
            retention_days: Number of days to retain these backups (overrides default)
        """
        job = {
            "type": "config",
            "frequency": frequency,
            "time": time,
            "retention_days": retention_days or self.retention_days,
            "last_run": None
        }
        
        self.scheduled_jobs.append(job)
        logger.info(f"Scheduled {frequency} configuration backup at {time}")
    
    def schedule_results_backup(
        self,
        frequency: str = "daily",
        time: str = "01:00",
        retention_days: Optional[int] = None
    ):
        """
        Schedule regular results data backups.
        
        Args:
            frequency: Backup frequency ('hourly', 'daily', 'weekly', 'monthly')
            time: Time of day to run backup (HH:MM format, for non-hourly frequencies)
            retention_days: Number of days to retain these backups (overrides default)
        """
        job = {
            "type": "results",
            "frequency": frequency,
            "time": time,
            "retention_days": retention_days or self.retention_days,
            "last_run": None
        }
        
        self.scheduled_jobs.append(job)
        logger.info(f"Scheduled {frequency} results backup at {time}")
    
    def schedule_database_backup(
        self,
        frequency: str = "daily",
        time: str = "02:00",
        retention_days: Optional[int] = None
    ):
        """
        Schedule regular database backups.
        
        Args:
            frequency: Backup frequency ('hourly', 'daily', 'weekly', 'monthly')
            time: Time of day to run backup (HH:MM format, for non-hourly frequencies)
            retention_days: Number of days to retain these backups (overrides default)
        """
        if not self.database_config:
            logger.warning("Cannot schedule database backup without database configuration")
            return
        
        job = {
            "type": "database",
            "frequency": frequency,
            "time": time,
            "retention_days": retention_days or self.retention_days,
            "last_run": None
        }
        
        self.scheduled_jobs.append(job)
        logger.info(f"Scheduled {frequency} database backup at {time}")
    
    def start(self):
        """Start the backup scheduler."""
        if self.is_running:
            logger.warning("Backup scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Backup scheduler started")
    
    def stop(self):
        """Stop the backup scheduler."""
        if not self.is_running:
            logger.warning("Backup scheduler is not running")
            return
        
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=60)
        
        logger.info("Backup scheduler stopped")
    
    def backup_configs_now(self) -> str:
        """
        Perform an immediate backup of configurations.
        
        Returns:
            str: Path to the backup file
        """
        if not self.config_files:
            logger.warning("No configuration files specified for backup")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"config_backup_{timestamp}.zip"
        backup_path = os.path.join(self.config_backup_dir, backup_filename)
        
        try:
            # Create a temporary directory for staging
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy all config files to the temp directory
                for config_file in self.config_files:
                    if os.path.exists(config_file):
                        shutil.copy2(config_file, temp_dir)
                    else:
                        logger.warning(f"Config file not found: {config_file}")
                
                # Create a manifest file
                manifest = {
                    "timestamp": timestamp,
                    "files": [os.path.basename(f) for f in self.config_files if os.path.exists(f)],
                    "backup_type": "config",
                    "created_by": "PyuntoBackupManager"
                }
                
                with open(os.path.join(temp_dir, "manifest.json"), "w") as f:
                    json.dump(manifest, f, indent=2)
                
                # Create the zip archive
                self._create_archive(temp_dir, backup_path)
            
            logger.info(f"Configuration backup created: {backup_path}")
            
            # Verify the backup
            if self._verify_backup(backup_path):
                # Upload to remote storage if configured
                if self.remote_storage:
                    self._upload_to_remote(backup_path)
                
                return backup_path
            else:
                logger.error(f"Backup verification failed for {backup_path}")
                return ""
            
        except Exception as e:
            logger.error(f"Configuration backup failed: {str(e)}")
            return ""
    
    def backup_results_now(self) -> str:
        """
        Perform an immediate backup of results data.
        
        Returns:
            str: Path to the backup file
        """
        if not self.results_dirs:
            logger.warning("No results directories specified for backup")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"results_backup_{timestamp}.zip"
        backup_path = os.path.join(self.results_backup_dir, backup_filename)
        
        try:
            # Create a temporary directory for staging
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy all results directories to the temp directory
                for results_dir in self.results_dirs:
                    if os.path.exists(results_dir):
                        dir_name = os.path.basename(results_dir)
                        dest_dir = os.path.join(temp_dir, dir_name)
                        shutil.copytree(results_dir, dest_dir)
                    else:
                        logger.warning(f"Results directory not found: {results_dir}")
                
                # Create a manifest file
                manifest = {
                    "timestamp": timestamp,
                    "directories": [os.path.basename(d) for d in self.results_dirs if os.path.exists(d)],
                    "backup_type": "results",
                    "created_by": "PyuntoBackupManager"
                }
                
                with open(os.path.join(temp_dir, "manifest.json"), "w") as f:
                    json.dump(manifest, f, indent=2)
                
                # Create the zip archive
                self._create_archive(temp_dir, backup_path)
            
            logger.info(f"Results backup created: {backup_path}")
            
            # Verify the backup
            if self._verify_backup(backup_path):
                # Upload to remote storage if configured
                if self.remote_storage:
                    self._upload_to_remote(backup_path)
                
                return backup_path
            else:
                logger.error(f"Backup verification failed for {backup_path}")
                return ""
            
        except Exception as e:
            logger.error(f"Results backup failed: {str(e)}")
            return ""
    
    def backup_database_now(self) -> str:
        """
        Perform an immediate backup of the database.
        
        Returns:
            str: Path to the backup file
        """
        if not self.database_config:
            logger.warning("Database configuration not specified for backup")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_type = self.database_config["type"].lower()
        backup_filename = f"database_backup_{db_type}_{timestamp}.dump"
        backup_path = os.path.join(self.database_backup_dir, backup_filename)
        
        try:
            # Create database dump based on database type
            if db_type == "postgresql":
                self._backup_postgresql(backup_path)
            elif db_type == "mysql":
                self._backup_mysql(backup_path)
            else:
                logger.error(f"Unsupported database type: {db_type}")
                return ""
            
            # Create a compressed version
            compressed_path = f"{backup_path}.zip"
            with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, os.path.basename(backup_path))
            
            # Remove the uncompressed version
            os.unlink(backup_path)
            
            logger.info(f"Database backup created: {compressed_path}")
            
            # Verify the backup
            if self._verify_backup(compressed_path):
                # Upload to remote storage if configured
                if self.remote_storage:
                    self._upload_to_remote(compressed_path)
                
                return compressed_path
            else:
                logger.error(f"Backup verification failed for {compressed_path}")
                return ""
            
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            return ""
    
    def backup_all_now(self) -> List[str]:
        """
        Perform an immediate backup of all configured data.
        
        Returns:
            List[str]: Paths to all backup files
        """
        backup_paths = []
        
        # Backup configurations
        if self.config_files:
            config_backup = self.backup_configs_now()
            if config_backup:
                backup_paths.append(config_backup)
        
        # Backup results
        if self.results_dirs:
            results_backup = self.backup_results_now()
            if results_backup:
                backup_paths.append(results_backup)
        
        # Backup database
        if self.database_config:
            db_backup = self.backup_database_now()
            if db_backup:
                backup_paths.append(db_backup)
        
        logger.info(f"Created {len(backup_paths)} backups")
        return backup_paths
    
    def restore_backup(self, backup_path: str, target_path: Optional[str] = None) -> bool:
        """
        Restore a backup file.
        
        Args:
            backup_path: Path to the backup file
            target_path: Target directory for restoration (if None, use original paths)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Create a temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract the backup
                if backup_path.endswith('.zip'):
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        zipf.extractall(temp_dir)
                else:
                    logger.error(f"Unsupported backup format: {backup_path}")
                    return False
                
                # Check for manifest file
                manifest_path = os.path.join(temp_dir, "manifest.json")
                if os.path.exists(manifest_path):
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    
                    backup_type = manifest.get("backup_type")
                    
                    # Restore based on backup type
                    if backup_type == "config":
                        return self._restore_config(temp_dir, target_path)
                    elif backup_type == "results":
                        return self._restore_results(temp_dir, target_path)
                    else:
                        logger.error(f"Unknown backup type: {backup_type}")
                        return False
                
                # Handle database backup (no manifest)
                elif "database_backup" in os.path.basename(backup_path):
                    # Find the .dump file
                    dump_files = [f for f in os.listdir(temp_dir) if f.endswith('.dump')]
                    if dump_files:
                        dump_path = os.path.join(temp_dir, dump_files[0])
                        return self._restore_database(dump_path)
                    else:
                        logger.error("No database dump file found in backup")
                        return False
                
                else:
                    logger.error("No manifest found in backup")
                    return False
                
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return False
    
    def list_backups(self, backup_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available backups.
        
        Args:
            backup_type: Filter by backup type ('config', 'results', 'database')
            
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        # Determine directories to scan
        dirs_to_scan = []
        if backup_type == "config" or backup_type is None:
            dirs_to_scan.append(self.config_backup_dir)
        if backup_type == "results" or backup_type is None:
            dirs_to_scan.append(self.results_backup_dir)
        if backup_type == "database" or backup_type is None:
            dirs_to_scan.append(self.database_backup_dir)
        
        # Scan directories for backup files
        for directory in dirs_to_scan:
            if not os.path.exists(directory):
                continue
            
            for filename in os.listdir(directory):
                if not filename.endswith('.zip'):
                    continue
                
                file_path = os.path.join(directory, filename)
                file_stats = os.stat(file_path)
                
                # Determine backup type from filename
                if filename.startswith('config_backup_'):
                    backup_type = "config"
                elif filename.startswith('results_backup_'):
                    backup_type = "results"
                elif filename.startswith('database_backup_'):
                    backup_type = "database"
                else:
                    backup_type = "unknown"
                
                # Parse timestamp from filename
                timestamp_match = re.search(r'_(\d{8}_\d{6})\.', filename)
                if timestamp_match:
                    timestamp_str = timestamp_match.group(1)
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except ValueError:
                        timestamp = datetime.fromtimestamp(file_stats.st_mtime)
                else:
                    timestamp = datetime.fromtimestamp(file_stats.st_mtime)
                
                backups.append({
                    "filename": filename,
                    "path": file_path,
                    "type": backup_type,
                    "size": file_stats.st_size,
                    "size_human": self._format_size(file_stats.st_size),
                    "created": timestamp.isoformat(),
                    "age_days": (datetime.now() - timestamp).days
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)
        
        return backups
    
    def cleanup_old_backups(self, backup_type: Optional[str] = None, days: Optional[int] = None):
        """
        Delete backups older than the specified retention period.
        
        Args:
            backup_type: Filter by backup type ('config', 'results', 'database')
            days: Override default retention days
        """
        retention_days = days or self.retention_days
        backups = self.list_backups(backup_type)
        
        deleted_count = 0
        for backup in backups:
            if backup["age_days"] > retention_days:
                try:
                    os.remove(backup["path"])
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup['filename']} (age: {backup['age_days']} days)")
                except Exception as e:
                    logger.error(f"Failed to delete backup {backup['path']}: {str(e)}")
        
        logger.info(f"Cleaned up {deleted_count} old backups (older than {retention_days} days)")
    
    def _scheduler_loop(self):
        """Internal scheduler loop that runs continuously."""
        while self.is_running:
            try:
                now = datetime.now()
                
                for job in self.scheduled_jobs:
                    # Check if job should run
                    if self._should_run_job(job, now):
                        # Execute the job
                        if job["type"] == "config":
                            self.backup_configs_now()
                        elif job["type"] == "results":
                            self.backup_results_now()
                        elif job["type"] == "database":
                            self.backup_database_now()
                        
                        # Update last run time
                        job["last_run"] = now
                        
                        # Clean up old backups
                        self.cleanup_old_backups(job["type"], job["retention_days"])
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
            
            # Sleep for 1 minute
            time.sleep(60)
    
    def _should_run_job(self, job: Dict[str, Any], now: datetime) -> bool:
        """
        Check if a scheduled job should run now.
        
        Args:
            job: Job configuration
            now: Current datetime
            
        Returns:
            bool: True if the job should run, False otherwise
        """
        frequency = job["frequency"]
        last_run = job["last_run"]
        
        # If never run before, run it
        if last_run is None:
            return True
        
        # Check based on frequency
        if frequency == "hourly":
            # Run if in a new hour
            return now.hour != last_run.hour or now.day != last_run.day
            
        elif frequency == "daily":
            # Check if it's the scheduled time
            scheduled_hour, scheduled_minute = map(int, job["time"].split(":"))
            
            # Run if it's the scheduled time and hasn't run today
            return (now.hour == scheduled_hour and 
                    now.minute >= scheduled_minute and 
                    (now.day != last_run.day or now.month != last_run.month))
            
        elif frequency == "weekly":
            # Check if it's the scheduled time and day (Monday is 0)
            scheduled_hour, scheduled_minute = map(int, job["time"].split(":"))
            
            # Run if it's Monday, the scheduled time, and hasn't run this week
            return (now.weekday() == 0 and
                    now.hour == scheduled_hour and 
                    now.minute >= scheduled_minute and 
                    (now - last_run).days >= 7)
            
        elif frequency == "monthly":
            # Check if it's the first day of the month and the scheduled time
            scheduled_hour, scheduled_minute = map(int, job["time"].split(":"))
            
            # Run if it's the 1st, the scheduled time, and hasn't run this month
            return (now.day == 1 and
                    now.hour == scheduled_hour and 
                    now.minute >= scheduled_minute and 
                    (now.month != last_run.month or now.year != last_run.year))
        
        return False
    
    def _create_archive(self, source_dir: str, target_path: str):
        """
        Create a zip archive of the source directory.
        
        Args:
            source_dir: Source directory
            target_path: Target zip file path
        """
        # Create a regular zip file
        if not self.enable_encryption:
            with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
            
            return
        
        # Create an encrypted zip file
        # Note: This is a simple encryption for demonstration
        # In a real implementation, consider using a more robust encryption method
        
        # First create a temporary zip file
        temp_zip = f"{target_path}.temp"
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
        
        # Read the zip file into memory
        with open(temp_zip, 'rb') as f:
            data = f.read()
        
        # Generate a key from the password
        key = hashlib.sha256(self.encryption_password.encode()).digest()
        
        # Simple XOR encryption (for demonstration only)
        # In a real implementation, use a proper encryption library
        encrypted_data = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
        
        # Write the encrypted data
        with open(target_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Remove the temporary file
        os.unlink(temp_zip)
    
    def _verify_backup(self, backup_path: str) -> bool:
        """
        Verify that a backup file is valid.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        # For encrypted backups, we can only check if the file exists
        if self.enable_encryption:
            return True
        
        # For regular zip files, check if it's a valid zip file
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Check if the zip file is valid
                bad_file = zipf.testzip()
                if bad_file:
                    logger.error(f"Corrupted file in backup: {bad_file}")
                    return False
                
                # Check for manifest file (except for database backups)
                if not "database_backup" in os.path.basename(backup_path):
                    if "manifest.json" not in zipf.namelist():
                        logger.error("No manifest file found in backup")
                        return False
            
            return True
            
        except zipfile.BadZipFile:
            logger.error(f"Invalid zip file: {backup_path}")
            return False
        except Exception as e:
            logger.error(f"Backup verification failed: {str(e)}")
            return False
    
    def _upload_to_remote(self, file_path: str) -> bool:
        """
        Upload a file to remote storage.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.remote_storage:
            return False
        
        storage_type = self.remote_storage.get("type", "").lower()
        
        try:
            if storage_type == "s3":
                return self._upload_to_s3(file_path)
            elif storage_type == "ftp":
                return self._upload_to_ftp(file_path)
            else:
                logger.error(f"Unsupported remote storage type: {storage_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to upload to remote storage: {str(e)}")
            return False
    
    def _upload_to_s3(self, file_path: str) -> bool:
        """
        Upload a file to Amazon S3.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Dynamically import boto3 to avoid hard dependency
            import boto3
            from botocore.exceptions import ClientError
            
            bucket = self.remote_storage.get("bucket")
            prefix = self.remote_storage.get("prefix", "")
            aws_access_key = self.remote_storage.get("access_key")
            aws_secret_key = self.remote_storage.get("secret_key")
            
            if not all([bucket, aws_access_key, aws_secret_key]):
                logger.error("Missing required S3 configuration")
                return False
            
            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            
            # Determine S3 key
            filename = os.path.basename(file_path)
            s3_key = f"{prefix}/{filename}" if prefix else filename
