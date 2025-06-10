#!/usr/bin/env python3
"""
Simple debug test for SQLCipher
"""

import sqlcipher3
from pathlib import Path

def test_simple_sqlcipher():
    """Test basic SQLCipher functionality."""
    
    print("🔍 Testing SQLCipher step by step...")
    
    # Test 1: Basic connection
    db_path = "simple_debug.db"
    if Path(db_path).exists():
        Path(db_path).unlink()
    
    try:
        print("1️⃣ Creating connection...")
        conn = sqlcipher3.connect(db_path)
        print("✅ Connection created")
        
        print("2️⃣ Setting encryption key...")
        conn.execute("PRAGMA key = 'test123'")
        print("✅ Encryption key set")
        
        print("3️⃣ Creating table...")
        conn.execute("CREATE TABLE test (id INTEGER, data TEXT)")
        print("✅ Table created")
        
        print("4️⃣ Inserting data...")
        conn.execute("INSERT INTO test VALUES (1, 'encrypted data')")
        conn.commit()
        print("✅ Data inserted")
        
        print("5️⃣ Querying data...")
        cursor = conn.execute("SELECT * FROM test")
        rows = cursor.fetchall()
        print(f"✅ Retrieved {len(rows)} rows: {rows}")
        
        conn.close()
        print("✅ Connection closed")
        
        # Test 2: Verify encryption
        print("\n6️⃣ Testing encryption verification...")
        try:
            conn = sqlcipher3.connect(db_path)
            conn.execute("SELECT * FROM test")
            print("❌ Database not encrypted!")
            conn.close()
            return False
        except Exception as e:
            print(f"✅ Database encrypted (error: {type(e).__name__})")
        
        # Test 3: Unlock with key
        print("7️⃣ Testing unlock with key...")
        conn = sqlcipher3.connect(db_path)
        conn.execute("PRAGMA key = 'test123'")
        cursor = conn.execute("SELECT data FROM test")
        result = cursor.fetchone()[0]
        print(f"✅ Unlocked successfully: {result}")
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_sqlcipher()
    print(f"\n🎯 Simple SQLCipher Test: {'SUCCESS' if success else 'FAILED'}") 