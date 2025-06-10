"""
Encrypted database manager using SQLCipher.
"""

try:
    import sqlcipher3 as sqlite3
    USING_SQLCIPHER = True
except ImportError:
    import sqlite3
    USING_SQLCIPHER = False

from pathlib import Path
from typing import Optional, Any
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class EncryptedDatabaseManager:
    """Manages SQLCipher connections with automatic key handling."""
    
    def __init__(self, db_path: Path, security_service):
        self.db_path = db_path
        self.security_service = security_service
        
    @contextmanager
    def get_connection(self):
        """Get encrypted database connection with key applied."""
        conn = None
        try:
            # Get encryption key
            key = self.security_service.get_connection_key()
            if not key:
                raise ValueError("No encryption key available")
            
            # Open connection
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            
            # Apply encryption key if using SQLCipher
            if USING_SQLCIPHER:
                conn.execute(f"PRAGMA key = '{key}'")
                
                # Verify connection works
                conn.execute("SELECT 1")
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            yield conn
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def initialize_encrypted_db(self, passphrase: str, force: bool = False):
        """Create new encrypted database."""
        if self.db_path.exists() and not force:
            raise ValueError("Database already exists. Use force=True to overwrite.")
        
        # Remove existing if force
        if self.db_path.exists() and force:
            self.db_path.unlink()
        
        # Create new encrypted database
        conn = sqlite3.connect(str(self.db_path))
        if USING_SQLCIPHER:
            conn.execute(f"PRAGMA key = '{passphrase}'")
        
        # Database will be encrypted from the start (if SQLCipher available)
        conn.close()
        
        # Cache the key for subsequent operations
        self.security_service.cached_key = passphrase
        self.security_service.key_source = 'passphrase'
    
    def change_passphrase(self, old_passphrase: str, new_passphrase: str):
        """Re-encrypt database with new passphrase."""
        if not USING_SQLCIPHER:
            raise ValueError("SQLCipher not available for passphrase change")
            
        conn = sqlite3.connect(str(self.db_path))
        
        # Unlock with old passphrase
        conn.execute(f"PRAGMA key = '{old_passphrase}'")
        
        # Verify it works
        conn.execute("SELECT 1")
        
        # Change to new passphrase
        conn.execute(f"PRAGMA rekey = '{new_passphrase}'")
        
        conn.close()
        
        # Update cached key
        self.security_service.cached_key = new_passphrase
    
    def migrate_to_encrypted(self, unencrypted_path: Path, passphrase: str):
        """Convert existing unencrypted database to encrypted."""
        if not USING_SQLCIPHER:
            raise ValueError("SQLCipher not available for migration")
            
        if not unencrypted_path.exists():
            raise ValueError(f"Source database not found: {unencrypted_path}")
        
        # Open unencrypted database
        source_conn = sqlite3.connect(str(unencrypted_path))
        
        # Create new encrypted database
        encrypted_path = self.db_path.with_suffix('.encrypted')
        dest_conn = sqlite3.connect(str(encrypted_path))
        dest_conn.execute(f"PRAGMA key = '{passphrase}'")
        
        # Copy schema and data
        source_conn.backup(dest_conn)
        
        # Close connections
        source_conn.close()
        dest_conn.close()
        
        # Replace original with encrypted
        if self.db_path.exists():
            self.db_path.unlink()
        encrypted_path.rename(self.db_path)
        
        # Cache the key
        self.security_service.cached_key = passphrase
        self.security_service.key_source = 'passphrase'
    
    def is_database_encrypted(self) -> bool:
        """Check if database is encrypted."""
        if not self.db_path.exists():
            return False
        
        if not USING_SQLCIPHER:
            return False
        
        try:
            # Try to open without key
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            conn.close()
            # If this succeeds, database is NOT encrypted
            return False
        except:
            # If it fails, database is likely encrypted
            return True 