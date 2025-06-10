#!/usr/bin/env python3
"""
Minimal test of SQLCipher by directly importing the module file.
"""

import sys
from pathlib import Path

# Direct file import to avoid package init issues
module_path = Path(__file__).parent / "src" / "radiation_medical_exam" / "database" / "encrypted_db_manager.py"

# Load the module directly
import importlib.util
spec = importlib.util.spec_from_file_location("encrypted_db_manager", module_path)
encrypted_db_manager = importlib.util.module_from_spec(spec)
sys.modules["encrypted_db_manager"] = encrypted_db_manager
spec.loader.exec_module(encrypted_db_manager)

def test_minimal():
    """Minimal SQLCipher test."""
    print(f"🔍 SQLCipher Available: {encrypted_db_manager.USING_SQLCIPHER}")
    
    if encrypted_db_manager.USING_SQLCIPHER:
        print("✅ SQLCipher successfully imported and available!")
        
        # Test basic SQLCipher functionality
        import sqlcipher3 as sqlite3
        
        # Create a simple test
        db_path = "minimal_test.db"
        if Path(db_path).exists():
            Path(db_path).unlink()
        
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA key = 'test123'")
        conn.execute("CREATE TABLE test (id INTEGER, data TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'encrypted')")
        conn.commit()
        conn.close()
        
        # Verify it's encrypted
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT * FROM test")
            print("❌ Database not encrypted!")
        except:
            print("✅ Database properly encrypted!")
        finally:
            conn.close()
        
        # Test with correct key
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA key = 'test123'")
        cursor = conn.execute("SELECT * FROM test")
        rows = cursor.fetchall()
        conn.close()
        
        print(f"✅ Retrieved {len(rows)} records with correct key")
        return True
    else:
        print("❌ SQLCipher not available")
        return False

if __name__ == "__main__":
    success = test_minimal()
    print(f"\n🎯 SQLCipher Migration: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1) 