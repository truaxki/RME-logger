#!/usr/bin/env python3
"""
Test MCP Server Encrypted Database Functionality
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import our modules
from radiation_medical_exam.database.encrypted_db_manager import EncryptedDatabaseManager, USING_SQLCIPHER
from radiation_medical_exam.services.security_service import SecurityService
from radiation_medical_exam.utils.init_navmed_database import create_database

async def test_encrypted_navmed_workflow():
    """Test the complete encrypted NAVMED database workflow."""
    
    print("🚀 Testing MCP Server Encrypted Database Workflow")
    print("=" * 60)
    
    # Test 1: Check SQLCipher availability
    print(f"1️⃣ SQLCipher Available: {USING_SQLCIPHER}")
    if not USING_SQLCIPHER:
        print("❌ SQLCipher not available - cannot test encryption")
        return False
    
    # Test 2: Initialize Security Service
    print("\n2️⃣ Initializing Security Service...")
    security_service = SecurityService()
    
    # Simulate user providing passphrase
    test_passphrase = "navmed-encrypted-2024-secure"
    print(f"🔑 Setting passphrase: {test_passphrase[:10]}...")
    security_service.cached_key = test_passphrase
    security_service.key_source = 'user_input'
    
    # Test 3: Create Encrypted NAVMED Database
    print("\n3️⃣ Creating Encrypted NAVMED Database...")
    db_path = Path("test_mcp_navmed_encrypted.db")
    
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        print("🗑️ Removed existing database")
    
    # Create encrypted database with NAVMED schema
    success = create_database(
        db_path=db_path,
        force=True,
        include_sample_data=True,
        passphrase=test_passphrase
    )
    
    if not success:
        print("❌ Failed to create encrypted database")
        return False
    
    print("✅ Encrypted NAVMED database created")
    
    # Test 4: Test Database Manager Connection
    print("\n4️⃣ Testing Database Manager Connection...")
    db_manager = EncryptedDatabaseManager(db_path, security_service)
    
    try:
        with db_manager.get_connection() as conn:
            # Query sample examination data
            cursor = conn.execute("""
                SELECT e.exam_id, e.patient_last_name, e.patient_first_name, e.exam_date
                FROM examinations e
                LIMIT 5
            """)
            examinations = cursor.fetchall()
            
            print(f"✅ Retrieved {len(examinations)} examination records:")
            for exam in examinations:
                print(f"   - Exam {exam[0]}: {exam[1]}, {exam[2]} ({exam[3]})")
    
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 5: Verify Encryption Status
    print("\n5️⃣ Verifying Database Encryption...")
    is_encrypted = db_manager.is_database_encrypted()
    print(f"🔒 Database encrypted: {is_encrypted}")
    
    if not is_encrypted:
        print("❌ Database should be encrypted but isn't!")
        return False
    
    # Test 6: Test Wrong Passphrase Protection
    print("\n6️⃣ Testing Wrong Passphrase Protection...")
    wrong_security = SecurityService()
    wrong_security.cached_key = "wrong-passphrase-123"
    wrong_security.key_source = 'test'
    
    wrong_db_manager = EncryptedDatabaseManager(db_path, wrong_security)
    
    try:
        with wrong_db_manager.get_connection() as conn:
            conn.execute("SELECT * FROM examinations LIMIT 1")
        print("❌ SECURITY ISSUE: Wrong passphrase allowed access!")
        return False
    except Exception:
        print("✅ Wrong passphrase correctly rejected")
    
    # Test 7: Test Adding New Encrypted Data
    print("\n7️⃣ Testing New Data Entry...")
    try:
        with db_manager.get_connection() as conn:
            # Insert a new examination record
            conn.execute("""
                INSERT INTO examinations (
                    exam_type, exam_date, patient_last_name, patient_first_name,
                    patient_ssn, patient_dob, command_unit, rank_grade,
                    department_service, facility_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'PE', '2024-06-10', 'TestPatient', 'John', '999-99-9999',
                '1990-01-01', 'USS Test Ship', 'E-6', 'Nuclear Engineering', 1
            ))
            conn.commit()
            
            # Verify the data was encrypted and stored
            cursor = conn.execute("""
                SELECT patient_last_name, patient_first_name 
                FROM examinations 
                WHERE patient_ssn = '999-99-9999'
            """)
            new_patient = cursor.fetchone()
            
            if new_patient:
                print(f"✅ New encrypted record: {new_patient[1]} {new_patient[0]}")
            else:
                print("❌ Failed to retrieve new record")
                return False
                
    except Exception as e:
        print(f"❌ Failed to add new data: {e}")
        return False
    
    # Test 8: Simulate Database Unlock Scenario
    print("\n8️⃣ Simulating Database Unlock Scenario...")
    
    # Clear cached key (simulate server restart)
    security_service.cached_key = None
    security_service.key_source = None
    
    print("🔓 Cached key cleared - database locked")
    
    # Try to access without key
    try:
        with db_manager.get_connection() as conn:
            conn.execute("SELECT * FROM examinations LIMIT 1")
        print("❌ Should not be able to access without key!")
        return False
    except Exception:
        print("✅ Database properly locked without key")
    
    # Unlock with correct passphrase
    print("🔑 Unlocking with correct passphrase...")
    security_service.cached_key = test_passphrase
    security_service.key_source = 'unlock'
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM examinations")
            count = cursor.fetchone()[0]
            print(f"✅ Database unlocked - {count} examination records accessible")
    except Exception as e:
        print(f"❌ Failed to unlock database: {e}")
        return False
    
    print("\n🎉 All Encrypted Database Tests Passed!")
    print(f"📁 Database file: {db_path.absolute()}")
    print(f"🔐 Encryption: SQLCipher with PRAGMA key")
    print(f"🛡️ Security: DoD-grade patient data protection")
    
    return True

async def main():
    """Main test execution."""
    try:
        success = await test_encrypted_navmed_workflow()
        if success:
            print("\n✅ MCP Server Encrypted Database Test: SUCCESS")
            return 0
        else:
            print("\n❌ MCP Server Encrypted Database Test: FAILED")
            return 1
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 