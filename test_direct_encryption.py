#!/usr/bin/env python3
"""
Direct test of encrypted database functionality without package imports.
"""

import sys
import os
from pathlib import Path

# Add src to path and import directly
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Direct imports without triggering package __init__.py
from radiation_medical_exam.database.encrypted_db_manager import EncryptedDatabaseManager, USING_SQLCIPHER
from radiation_medical_exam.services.security_service import SecurityService

def test_direct_encryption():
    """Test SQLCipher functionality directly."""
    
    print(f"🔍 SQLCipher Available: {USING_SQLCIPHER}")
    
    if not USING_SQLCIPHER:
        print("❌ SQLCipher not available - using standard SQLite")
        return False
    
    # Test with security service
    security_service = SecurityService()
    test_passphrase = "direct-test-2024"
    security_service.cached_key = test_passphrase
    security_service.key_source = 'test'
    
    # Create database manager
    db_path = Path("direct_test_encrypted.db")
    if db_path.exists():
        db_path.unlink()
    
    db_manager = EncryptedDatabaseManager(db_path, security_service)
    
    try:
        print("🔐 Creating encrypted database...")
        db_manager.initialize_encrypted_db(test_passphrase, force=True)
        print("✅ Database created")
        
        print("📊 Testing operations...")
        with db_manager.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, data TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'encrypted data')")
            conn.commit()
            
            cursor = conn.execute("SELECT * FROM test")
            rows = cursor.fetchall()
            print(f"✅ Retrieved {len(rows)} encrypted records")
        
        print(f"🔒 Database encrypted: {db_manager.is_database_encrypted()}")
        
        print("🎉 Direct encryption test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_encryption()
    sys.exit(0 if success else 1) 