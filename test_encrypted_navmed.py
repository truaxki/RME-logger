#!/usr/bin/env python3
"""
Test encrypted NAVMED database functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from radiation_medical_exam.database.encrypted_db_manager import EncryptedDatabaseManager
from radiation_medical_exam.services.security_service import SecurityService

def test_encrypted_database():
    """Test creating and using encrypted NAVMED database."""
    
    # Initialize security service
    security_service = SecurityService()
    
    # Set up test passphrase
    test_passphrase = "navmed-test-encryption-2024"
    security_service.cached_key = test_passphrase
    security_service.key_source = 'test'
    
    # Create encrypted database manager
    db_path = Path("test_navmed_encrypted.db")
    if db_path.exists():
        db_path.unlink()
    
    db_manager = EncryptedDatabaseManager(db_path, security_service)
    
    try:
        # Initialize encrypted database
        print("🔐 Creating encrypted NAVMED database...")
        db_manager.initialize_encrypted_db(test_passphrase, force=True)
        print("✅ Encrypted database created")
        
        # Test connection and basic operations
        print("\n📊 Testing database operations...")
        with db_manager.get_connection() as conn:
            # Create a simple test table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_navmed (
                    id INTEGER PRIMARY KEY,
                    patient_name TEXT,
                    exam_date DATE,
                    classified_data TEXT
                )
            """)
            
            # Insert test data
            conn.execute("""
                INSERT INTO test_navmed (patient_name, exam_date, classified_data)
                VALUES (?, ?, ?)
            """, ("John Doe", "2024-01-15", "Radiation exposure: Class A"))
            
            conn.commit()
            
            # Query test data
            cursor = conn.execute("SELECT * FROM test_navmed")
            rows = cursor.fetchall()
            
            print(f"✅ Successfully inserted and retrieved {len(rows)} records:")
            for row in rows:
                print(f"   - ID: {row[0]}, Patient: {row[1]}, Date: {row[2]}")
        
        # Verify encryption status
        print(f"\n🔒 Encryption status: {db_manager.is_database_encrypted()}")
        
        # Test wrong key access
        print("\n🚫 Testing wrong passphrase...")
        wrong_security = SecurityService()
        wrong_security.cached_key = "wrong-passphrase"
        wrong_security.key_source = 'test'
        
        wrong_db_manager = EncryptedDatabaseManager(db_path, wrong_security)
        
        try:
            with wrong_db_manager.get_connection() as conn:
                conn.execute("SELECT * FROM test_navmed")
            print("❌ SECURITY ISSUE: Wrong passphrase allowed access!")
        except Exception as e:
            print(f"✅ Good: Wrong passphrase rejected ({type(e).__name__})")
        
        print(f"\n🎉 All tests passed! Database: {db_path.absolute()}")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_encrypted_database()
    sys.exit(0 if success else 1) 