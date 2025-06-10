# SQLCipher Encryption Implementation Guide

## 📋 Overview

This guide provides step-by-step instructions for implementing SQLCipher transparent encryption in the NAVMED Radiation Medical Examination system. This replaces file-level encryption with always-encrypted database functionality.

**Created:** 2025-01-10  
**Target Branch:** Current working branch  
**Estimated Time:** 4-6 hours  

## 🎯 Goals

1. Replace file-level encryption with SQLCipher transparent encryption
2. Maintain compatibility with DB Browser for SQLite
3. Add passphrase caching for MCP session
4. Prepare structure for future security token support
5. Ensure zero data exposure on disk

## 🔧 Prerequisites

- Python 3.12+
- Access to the full project in Cursor
- Git backup of current branch
- DB Browser for SQLite (with SQLCipher support) for testing

## 📦 Phase 1: Setup and Testing

### Step 1.1: Install Dependencies

**File:** `pyproject.toml`

Add to dependencies section:
```toml
pysqlcipher3 = "^1.2.0"
cryptography = "^41.0.0"  # Already present
```

**Terminal Commands:**
```bash
# Update dependencies
uv sync

# Verify installation
python -c "import sqlcipher3; print('SQLCipher3 imported successfully')"
```

### Step 1.2: Create Command-Line Test Script

**Create File:** `test_sqlcipher.py` (in project root)

```python
#!/usr/bin/env python3
"""
Test script to verify SQLCipher functionality before MCP integration.

Usage:
    python test_sqlcipher.py --create     # Create encrypted test database
    python test_sqlcipher.py --verify     # Verify encryption works
    python test_sqlcipher.py --wrong-key  # Test wrong passphrase
"""

import argparse
import sys
import os
from pathlib import Path

try:
    import sqlcipher3 as sqlite3
    print("✅ Using SQLCipher3")
except ImportError:
    print("❌ SQLCipher3 not found, falling back to standard sqlite3")
    import sqlite3

TEST_DB_PATH = "test_encrypted.db"
TEST_PASSPHRASE = "test-passphrase-123"
WRONG_PASSPHRASE = "wrong-passphrase"


def create_encrypted_db():
    """Create a test encrypted database."""
    print(f"Creating encrypted database: {TEST_DB_PATH}")
    
    # Remove if exists
    if Path(TEST_DB_PATH).exists():
        os.remove(TEST_DB_PATH)
    
    # Create encrypted database
    conn = sqlite3.connect(TEST_DB_PATH)
    
    # Set encryption key
    conn.execute(f"PRAGMA key = '{TEST_PASSPHRASE}'")
    
    # Create test table
    conn.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            data TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert test data
    conn.execute("INSERT INTO test_table (data) VALUES ('Secret medical data')")
    conn.execute("INSERT INTO test_table (data) VALUES ('Encrypted successfully')")
    
    conn.commit()
    conn.close()
    
    print("✅ Encrypted database created successfully")
    print(f"📁 File: {Path(TEST_DB_PATH).absolute()}")
    print(f"🔑 Passphrase: {TEST_PASSPHRASE}")


def verify_encrypted_db():
    """Verify the encrypted database works."""
    print(f"Verifying encrypted database: {TEST_DB_PATH}")
    
    if not Path(TEST_DB_PATH).exists():
        print("❌ Test database not found. Run with --create first.")
        return False
    
    try:
        # Try to read without key (should fail)
        print("\n1️⃣ Testing without encryption key...")
        conn = sqlite3.connect(TEST_DB_PATH)
        try:
            cursor = conn.execute("SELECT * FROM test_table")
            print("❌ SECURITY ISSUE: Database is not encrypted!")
            return False
        except Exception as e:
            print(f"✅ Good: Database is encrypted (error: {type(e).__name__})")
        finally:
            conn.close()
        
        # Try with correct key
        print("\n2️⃣ Testing with correct passphrase...")
        conn = sqlite3.connect(TEST_DB_PATH)
        conn.execute(f"PRAGMA key = '{TEST_PASSPHRASE}'")
        
        cursor = conn.execute("SELECT * FROM test_table")
        rows = cursor.fetchall()
        print(f"✅ Decrypted successfully! Found {len(rows)} rows:")
        for row in rows:
            print(f"   - {row}")
        
        conn.close()
        
        # Verify file is actually encrypted
        print("\n3️⃣ Verifying file content is encrypted...")
        with open(TEST_DB_PATH, 'rb') as f:
            content = f.read(100)
            if b'SQLite format' in content:
                print("❌ SECURITY ISSUE: File header is not encrypted!")
                return False
            else:
                print("✅ File content is properly encrypted")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False


def test_wrong_passphrase():
    """Test accessing with wrong passphrase."""
    print(f"Testing wrong passphrase on: {TEST_DB_PATH}")
    
    if not Path(TEST_DB_PATH).exists():
        print("❌ Test database not found. Run with --create first.")
        return
    
    try:
        conn = sqlite3.connect(TEST_DB_PATH)
        conn.execute(f"PRAGMA key = '{WRONG_PASSPHRASE}'")
        
        # This should fail
        cursor = conn.execute("SELECT * FROM test_table")
        rows = cursor.fetchall()
        
        print("❌ SECURITY ISSUE: Wrong passphrase allowed access!")
        
    except Exception as e:
        print(f"✅ Good: Wrong passphrase rejected ({type(e).__name__})")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Test SQLCipher encryption")
    parser.add_argument("--create", action="store_true", help="Create test encrypted database")
    parser.add_argument("--verify", action="store_true", help="Verify encryption works")
    parser.add_argument("--wrong-key", action="store_true", help="Test wrong passphrase")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    if args.create or args.all:
        create_encrypted_db()
        print("\n" + "="*50 + "\n")
    
    if args.verify or args.all:
        verify_encrypted_db()
        print("\n" + "="*50 + "\n")
    
    if args.wrong_key or args.all:
        test_wrong_passphrase()
    
    if not any([args.create, args.verify, args.wrong_key, args.all]):
        parser.print_help()


if __name__ == "__main__":
    main()
```

**Test Commands:**
```bash
# Run all tests
python test_sqlcipher.py --all

# Or run individually
python test_sqlcipher.py --create
python test_sqlcipher.py --verify
python test_sqlcipher.py --wrong-key
```

## 📂 Phase 2: Core Implementation

### Step 2.1: Create Security Service

**Create File:** `src/radiation_medical_exam/services/security_service.py`

```python
"""
Security service for managing encryption keys and passphrases.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
import hashlib
import base64
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityService:
    """Handles all security operations including keys and tokens."""
    
    def __init__(self):
        self.cached_key = None
        self.key_source = None  # 'passphrase', 'token', or None
        
    def prompt_for_passphrase(self, title: str = "Database Authentication") -> Optional[str]:
        """Show GUI dialog for passphrase entry."""
        passphrase = None
        
        def on_submit():
            nonlocal passphrase
            passphrase = entry.get()
            root.quit()
        
        def on_cancel():
            root.quit()
        
        # Create GUI
        root = tk.Tk()
        root.title("NAVMED Medical Records")
        root.geometry("400x200")
        root.resizable(False, False)
        
        # Center window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (400 // 2)
        y = (root.winfo_screenheight() // 2) - (200 // 2)
        root.geometry(f"400x200+{x}+{y}")
        
        # Create frame
        frame = ttk.Frame(root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title label
        title_label = ttk.Label(frame, text=title, font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Instructions
        info_label = ttk.Label(frame, text="Enter passphrase to decrypt medical records:")
        info_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Passphrase entry
        entry = ttk.Entry(frame, show="*", width=40)
        entry.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        entry.focus()
        
        # Buttons
        cancel_button = ttk.Button(frame, text="Cancel", command=on_cancel)
        cancel_button.grid(row=3, column=0, padx=(0, 10), sticky=tk.E)
        
        submit_button = ttk.Button(frame, text="Unlock", command=on_submit)
        submit_button.grid(row=3, column=1, sticky=tk.W)
        
        # Bind Enter key
        root.bind('<Return>', lambda e: on_submit())
        root.bind('<Escape>', lambda e: on_cancel())
        
        # Make modal
        root.grab_set()
        root.mainloop()
        root.destroy()
        
        return passphrase
    
    def derive_key_from_passphrase(self, passphrase: str, salt: bytes = b'navmed-salt') -> str:
        """Convert passphrase to encryption key using PBKDF2."""
        # SQLCipher expects the passphrase directly, but we can pre-process if needed
        # For now, return passphrase as-is (SQLCipher handles key derivation)
        return passphrase
    
    def get_key_from_token(self, token_path: str = None) -> Optional[str]:
        """Read encryption key from security token (future feature)."""
        # Placeholder for future token implementation
        if token_path and Path(token_path).exists():
            # In future: Read and decrypt key from token file
            pass
        return None
    
    def get_connection_key(self) -> Optional[str]:
        """Get key from cache, prompt, or token."""
        # First try cached key
        if self.cached_key:
            return self.cached_key
        
        # Try token (future feature)
        token_key = self.get_key_from_token()
        if token_key:
            self.cached_key = token_key
            self.key_source = 'token'
            return token_key
        
        # Prompt for passphrase
        passphrase = self.prompt_for_passphrase()
        if passphrase:
            self.cached_key = self.derive_key_from_passphrase(passphrase)
            self.key_source = 'passphrase'
            return self.cached_key
        
        return None
    
    def clear_cached_key(self):
        """Clear the cached key from memory."""
        self.cached_key = None
        self.key_source = None
```

### Step 2.2: Create Encrypted Database Manager

**Create File:** `src/radiation_medical_exam/database/encrypted_db_manager.py`

```python
"""
Encrypted database manager using SQLCipher.
"""

import sqlcipher3 as sqlite3
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
            
            # Apply encryption key
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
        conn.execute(f"PRAGMA key = '{passphrase}'")
        
        # Database will be encrypted from the start
        conn.close()
        
        # Cache the key for subsequent operations
        self.security_service.cached_key = passphrase
        self.security_service.key_source = 'passphrase'
    
    def change_passphrase(self, old_passphrase: str, new_passphrase: str):
        """Re-encrypt database with new passphrase."""
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
        self.db_path.unlink() if self.db_path.exists() else None
        encrypted_path.rename(self.db_path)
        
        # Cache the key
        self.security_service.cached_key = passphrase
        self.security_service.key_source = 'passphrase'
    
    def is_database_encrypted(self) -> bool:
        """Check if database is encrypted."""
        if not self.db_path.exists():
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
```

## 🔄 Phase 3: Server Integration

### Step 3.1: Update Database Initialization

**File:** `src/radiation_medical_exam/utils/init_navmed_database.py`

Add at the top:
```python
try:
    import sqlcipher3 as sqlite3
    USING_SQLCIPHER = True
except ImportError:
    import sqlite3
    USING_SQLCIPHER = False
```

Modify `create_database` function to accept optional passphrase:
```python
def create_database(db_path: Path, force: bool = False, include_sample_data: bool = True, passphrase: str = None) -> bool:
    """
    Create and initialize the NAVMED database.
    
    Args:
        db_path: Path where the database should be created
        force: If True, overwrite existing database
        include_sample_data: If True, insert sample data for testing
        passphrase: If provided and using SQLCipher, create encrypted database
        
    Returns:
        True if database was created successfully, False otherwise
    """
    
    # ... existing checks ...
    
    try:
        with sqlite3.connect(db_path) as conn:
            # If passphrase provided and SQLCipher available, encrypt
            if passphrase and USING_SQLCIPHER:
                conn.execute(f"PRAGMA key = '{passphrase}'")
                print("🔐 Creating encrypted database")
            
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            
            # ... rest of existing code ...
```

### Step 3.2: Update Server Initialize Handler

**File:** `src/radiation_medical_exam/server.py`

Add imports at top:
```python
from .services.security_service import SecurityService
from .database.encrypted_db_manager import EncryptedDatabaseManager

# Initialize security service
security_service = SecurityService()
db_manager = EncryptedDatabaseManager(Path(DB_PATH), security_service)
```

Replace the `handle_initialize_database` section (around line 430):
```python
elif name == "initialize-database":
    force = arguments.get("force", False) if arguments else False
    include_sample_data = arguments.get("include_sample_data", True) if arguments else True
    
    try:
        db_path = Path(DB_PATH)
        
        # Check if database exists
        if db_path.exists():
            # Check if encrypted
            is_encrypted = db_manager.is_database_encrypted()
            
            if is_encrypted:
                # Need passphrase to proceed
                if not security_service.cached_key:
                    key = security_service.get_connection_key()
                    if not key:
                        return [types.TextContent(
                            type="text",
                            text="❌ Cannot initialize encrypted database without passphrase"
                        )]
            
            if not force:
                # Show existing database info
                try:
                    with db_manager.get_connection() as conn:
                        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        existing_tables = [row[0] for row in cursor.fetchall()]
                        navmed_tables = [t for t in existing_tables if t != 'sqlite_sequence']
                        
                        return [types.TextContent(
                            type="text",
                            text=f"⚠️ Database already exists at {db_path}\n"
                                 f"🔐 Encrypted: {'Yes' if is_encrypted else 'No'}\n"
                                 f"📋 Tables ({len(navmed_tables)}): {', '.join(navmed_tables)}\n\n"
                                 f"Use force=true to overwrite"
                        )]
                except:
                    pass
        
        else:
            # No database exists - prompt for passphrase for new encrypted DB
            passphrase = security_service.prompt_for_passphrase("Create passphrase for new encrypted database:")
            if not passphrase:
                return [types.TextContent(
                    type="text",
                    text="❌ Database creation cancelled - no passphrase provided"
                )]
            
            # Initialize encrypted database
            db_manager.initialize_encrypted_db(passphrase, force=force)
        
        # Create database with encryption if we have a key
        passphrase = security_service.cached_key
        success = create_database(db_path, force=force, include_sample_data=include_sample_data, passphrase=passphrase)
        
        if success:
            return [types.TextContent(
                type="text",
                text=f"✅ Database successfully created at {db_path}\n"
                     f"🔐 Encrypted: {'Yes' if passphrase else 'No'}\n"
                     f"📊 Force overwrite: {'Yes' if force else 'No'}\n"
                     f"📝 Sample data included: {'Yes' if include_sample_data else 'No'}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"❌ Failed to create database at {db_path}"
            )]
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Error creating database: {str(e)}"
        )]
```

### Step 3.3: Add New Security Tools

Add to `handle_list_tools()`:
```python
types.Tool(
    name="change-database-passphrase",
    description="Change the encryption passphrase for the database",
    inputSchema={
        "type": "object",
        "properties": {
            "old_passphrase": {
                "type": "string",
                "description": "Current passphrase (leave empty to prompt)"
            },
            "new_passphrase": {
                "type": "string", 
                "description": "New passphrase (leave empty to prompt)"
            }
        },
        "required": []
    }
),
types.Tool(
    name="verify-database-encryption",
    description="Check if the database is encrypted",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": []
    }
),
```

### Step 3.4: Update NavmedDatabase Class

**File:** `src/radiation_medical_exam/utils/navmed_database.py`

Replace sqlite3 import and update connection method:
```python
try:
    import sqlcipher3 as sqlite3
except ImportError:
    import sqlite3

# Add to __init__:
def __init__(self, db_path: str, db_manager=None):
    self.db_path = db_path
    self.db_manager = db_manager  # Optional encrypted manager

# Update connection method:
def _get_connection(self):
    """Get database connection (encrypted if manager provided)."""
    if self.db_manager:
        # Use encrypted connection
        return self.db_manager.get_connection()
    else:
        # Fallback to regular connection
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
```

## 🧪 Phase 4: Testing

### Step 4.1: Command Line Testing

```bash
# 1. Test SQLCipher is working
python test_sqlcipher.py --all

# 2. Test database creation with encryption
python -m radiation_medical_exam.server initialize-database

# 3. Test with DB Browser
# Open DB Browser for SQLite
# File -> Open Database -> Select navmed_radiation_exam.db
# Enter passphrase when prompted
```

### Step 4.2: MCP Testing

```python
# Create test script: test_mcp_encryption.py
import asyncio
from radiation_medical_exam.server import handle_call_tool

async def test_encrypted_operations():
    # Test initialize
    result = await handle_call_tool("initialize-database", {})
    print("Initialize:", result)
    
    # Test table schema
    result = await handle_call_tool("get-table-schema", {"table_name": "examinations"})
    print("Schema:", result)
    
    # Test data operations
    result = await handle_call_tool("get-exam-data", {"table_name": "examinations"})
    print("Data:", result)

asyncio.run(test_encrypted_operations())
```

## 🚀 Phase 5: Deployment

### Step 5.1: Update Documentation

Update README.md with:
- SQLCipher requirement
- Passphrase setup instructions
- DB Browser for SQLite configuration

### Step 5.2: Migration Guide

For existing unencrypted databases:
```python
# Add migration tool to server
types.Tool(
    name="migrate-to-encrypted",
    description="Convert existing unencrypted database to encrypted",
    inputSchema={
        "type": "object", 
        "properties": {
            "source_path": {
                "type": "string",
                "description": "Path to unencrypted database"
            },
            "passphrase": {
                "type": "string",
                "description": "Passphrase for encrypted database"
            }
        },
        "required": ["source_path"]
    }
)
```

## 🔒 Security Considerations

1. **Passphrase Storage**: Never store passphrases in code or config files
2. **Memory Security**: Clear cached keys on shutdown
3. **Backup Security**: Ensure backups are also encrypted
4. **Key Rotation**: Use change-passphrase tool regularly
5. **Access Logging**: Log all database access attempts

## 📝 Future Enhancements

### Security Token Support

```python
# Token structure (future)
# /path/to/token/navmed.key
{
    "key_id": "navmed-2025-01",
    "encrypted_key": "base64-encrypted-key",
    "expiry": "2025-12-31",
    "hardware_binding": "optional-hardware-id"
}
```

### Implementation approach:
1. Check for token file at startup
2. Decrypt key using hardware-specific data
3. Fall back to passphrase if no token
4. Allow token + PIN for extra security

## ✅ Success Criteria

- [ ] SQLCipher installed and working
- [ ] Command line test script passes all tests
- [ ] Database created with encryption
- [ ] Existing MCP tools work with encrypted DB
- [ ] DB Browser can open encrypted database
- [ ] Passphrase change functionality works
- [ ] No unencrypted data on disk
- [ ] Graceful handling of wrong passphrase
- [ ] Clear documentation for users

## 🆘 Troubleshooting

### Common Issues:

1. **Import Error**: "No module named sqlcipher3"
   - Solution: Run `uv sync` or `pip install pysqlcipher3`

2. **Database is not encrypted**
   - Check if using sqlcipher3, not sqlite3
   - Ensure PRAGMA key is set before any operations

3. **Wrong passphrase not detected**
   - SQLCipher may create new DB instead of failing
   - Always verify with test query after setting key

4. **Performance issues**
   - Expected 5-15% overhead
   - Use connection pooling for better performance

5. **DB Browser can't open**
   - Ensure you have SQLCipher-enabled version
   - Download from: https://sqlitebrowser.org/dl/

## 📞 Support

For implementation questions:
1. Review this guide thoroughly
2. Check test_sqlcipher.py output
3. Verify all imports are correct
4. Test with DB Browser for SQLite

Remember: The beauty of SQLCipher is that once the key is set, everything else works exactly like normal SQLite!