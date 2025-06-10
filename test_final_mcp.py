#!/usr/bin/env python3
"""
Final MCP Server Encrypted Database Test
"""

import sys
import asyncio
from pathlib import Path
import importlib.util

def load_module(name, file_path):
    """Load a module directly from file path."""
    spec = importlib.util.spec_from_file_location(name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

async def test_mcp_encrypted_workflow():
    """Test complete MCP encrypted workflow."""
    
    print("🚀 MCP Server Encrypted Database Test")
    print("=" * 50)
    
    # Load modules directly
    src_path = Path(__file__).parent / "src" / "radiation_medical_exam"
    
    # Load encrypted database manager
    encrypted_db_manager = load_module(
        "encrypted_db_manager",
        src_path / "database" / "encrypted_db_manager.py"
    )
    
    # Load security service
    security_service_module = load_module(
        "security_service",
        src_path / "services" / "security_service.py"
    )
    
    # Load database init
    init_db_module = load_module(
        "init_navmed_database",
        src_path / "utils" / "init_navmed_database.py"
    )
    
    print(f"1️⃣ SQLCipher Available: {encrypted_db_manager.USING_SQLCIPHER}")
    
    if not encrypted_db_manager.USING_SQLCIPHER:
        print("❌ SQLCipher not available")
        return False
    
    # Test Security Service
    print("\n2️⃣ Testing Security Service...")
    security_service = security_service_module.SecurityService()
    
    # Simulate user entering passphrase
    passphrase = "mcp-navmed-secure-2024"
    print(f"🔑 User enters passphrase: {passphrase[:10]}...")
    security_service.cached_key = passphrase
    security_service.key_source = 'user_input'
    
    # Test Database Creation
    print("\n3️⃣ Creating Encrypted NAVMED Database...")
    db_path = Path("final_mcp_test.db")
    
    if db_path.exists():
        db_path.unlink()
    
    # Create with encryption
    success = init_db_module.create_database(
        db_path=db_path,
        force=True,
        include_sample_data=True,
        passphrase=passphrase
    )
    
    if not success:
        print("❌ Database creation failed")
        return False
    
    print("✅ Encrypted database created")
    
    # Test Database Manager
    print("\n4️⃣ Testing Database Access...")
    db_manager = encrypted_db_manager.EncryptedDatabaseManager(db_path, security_service)
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM examinations")
            count = cursor.fetchone()[0]
            print(f"✅ Connected to encrypted DB - {count} examination records")
            
            # Query patient data
            cursor = conn.execute("""
                SELECT patient_last_name, patient_first_name, exam_date 
                FROM examinations 
                LIMIT 3
            """)
            patients = cursor.fetchall()
            
            print("📋 Sample encrypted patient data:")
            for patient in patients:
                print(f"   - {patient[1]} {patient[0]} ({patient[2]})")
                
    except Exception as e:
        print(f"❌ Database access failed: {e}")
        return False
    
    # Test Database Locking/Unlocking
    print("\n5️⃣ Testing Database Lock/Unlock...")
    
    # Lock database (clear key)
    security_service.cached_key = None
    print("🔒 Database locked (key cleared)")
    
    # Try to access locked database
    try:
        with db_manager.get_connection() as conn:
            conn.execute("SELECT * FROM examinations LIMIT 1")
        print("❌ Should not access locked database!")
        return False
    except Exception:
        print("✅ Database properly locked")
    
    # Unlock database
    print("🔓 Unlocking database...")
    security_service.cached_key = passphrase
    security_service.key_source = 'unlock'
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT patient_first_name FROM examinations LIMIT 1")
            first_patient = cursor.fetchone()[0]
            print(f"✅ Database unlocked - accessed patient: {first_patient}")
    except Exception as e:
        print(f"❌ Unlock failed: {e}")
        return False
    
    # Test Adding New Data
    print("\n6️⃣ Testing New Data Entry...")
    try:
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO examinations (
                    exam_type, exam_date, patient_last_name, patient_first_name,
                    patient_ssn, patient_dob, command_unit, rank_grade,
                    department_service, facility_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'PE', '2024-06-10', 'NewPatient', 'Test', '888-88-8888',
                '1985-01-01', 'USS Encrypted', 'E-7', 'Nuclear Medicine', 1
            ))
            conn.commit()
            
            # Verify new data
            cursor = conn.execute(
                "SELECT patient_first_name, patient_last_name FROM examinations WHERE patient_ssn = '888-88-8888'"
            )
            new_patient = cursor.fetchone()
            print(f"✅ New encrypted record added: {new_patient[0]} {new_patient[1]}")
            
    except Exception as e:
        print(f"❌ Data entry failed: {e}")
        return False
    
    # Test Wrong Passphrase Protection
    print("\n7️⃣ Testing Security Protection...")
    wrong_security = security_service_module.SecurityService()
    wrong_security.cached_key = "wrong-passphrase"
    wrong_security.key_source = 'test'
    
    wrong_db_manager = encrypted_db_manager.EncryptedDatabaseManager(db_path, wrong_security)
    
    try:
        with wrong_db_manager.get_connection() as conn:
            conn.execute("SELECT * FROM examinations LIMIT 1")
        print("❌ SECURITY BREACH: Wrong passphrase worked!")
        return False
    except Exception:
        print("✅ Wrong passphrase correctly rejected")
    
    # Final verification
    print("\n8️⃣ Final Verification...")
    encryption_status = db_manager.is_database_encrypted()
    print(f"🔐 Database encryption status: {encryption_status}")
    
    if not encryption_status:
        print("❌ Database should be encrypted!")
        return False
    
    print("\n🎉 MCP Server Encrypted Database Test: ALL TESTS PASSED!")
    print(f"📁 Database: {db_path.absolute()}")
    print(f"🔐 Encryption: SQLCipher transparent encryption")
    print(f"🛡️ Security: Medical data protected at rest")
    print(f"🚀 MCP Ready: Server can handle encrypted patient data")
    
    return True

async def main():
    try:
        success = await test_mcp_encrypted_workflow()
        return 0 if success else 1
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 