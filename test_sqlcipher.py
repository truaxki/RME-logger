#!/usr/bin/env python3
"""
Test script to verify SQLCipher functionality before MCP integration.

Usage:
    python test_sqlcipher.py --create     # Create encrypted test database
    python test_sqlcipher.py --verify     # Verify encryption works
    python test_sqlcipher.py --wrong-key  # Test wrong passphrase
    python test_sqlcipher.py --all        # Run all tests
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