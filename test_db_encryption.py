#!/usr/bin/env python3
"""
Test script to check if the NAVMED database is properly encrypted.
"""

import sqlite3
import os
from pathlib import Path

try:
    import sqlcipher3
    SQLCIPHER_AVAILABLE = True
    print("✅ SQLCipher is available")
except ImportError:
    SQLCIPHER_AVAILABLE = False
    print("❌ SQLCipher is NOT available")

# Database path
db_path = Path("src/radiation_medical_exam/data/navmed_radiation_exam.db")

if not db_path.exists():
    print(f"❌ Database file does not exist: {db_path}")
    exit(1)

print(f"📁 Database file exists: {db_path}")
print(f"📊 File size: {db_path.stat().st_size:,} bytes")

# Test 1: Try to read with regular SQLite3 (should fail if encrypted)
print("\n🔍 Test 1: Attempting to read with regular SQLite3...")
try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        print(f"⚠️  Database is NOT encrypted - can read with regular SQLite3")
        print(f"   Found table: {result[0]}")
    else:
        print("✅ Database appears to be encrypted (no tables found)")
        
except Exception as e:
    print(f"✅ Database appears to be encrypted (error reading): {type(e).__name__}: {e}")

# Test 2: If SQLCipher available, try to read with it
if SQLCIPHER_AVAILABLE:
    print("\n🔍 Test 2: Attempting to read with SQLCipher...")
    try:
        conn = sqlcipher3.connect(str(db_path))
        # Try without key first
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print(f"⚠️  Database is NOT encrypted - can read with SQLCipher without key")
            print(f"   Found table: {result[0]}")
        else:
            print("✅ Database appears to be encrypted (no tables found)")
            
    except Exception as e:
        print(f"✅ Database appears to be encrypted (error reading): {type(e).__name__}: {e}")

print("\n📝 Summary:")
print("- If database is properly encrypted, both tests should fail")
print("- If database is NOT encrypted, Test 1 should succeed")
print("- The MCP tool should prompt for passphrase when creating/accessing encrypted databases") 