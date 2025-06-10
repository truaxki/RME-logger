#!/usr/bin/env python3
"""
MCP Server Encrypted Database Demonstration
Shows entering passphrase and unlocking database for medical examination data
"""

import sqlcipher3
from pathlib import Path
import sys

def simulate_mcp_workflow():
    """Simulate complete MCP server encrypted database workflow."""
    
    print("🏥 NAVMED Radiation Medical Examination - MCP Server Demo")
    print("=" * 60)
    
    # Step 1: User enters passphrase to unlock database
    print("1️⃣ MCP Server Startup - Database Locked")
    print("🔒 Medical examination database is encrypted")
    
    # Simulate user providing passphrase
    user_passphrase = "navmed-medical-secure-2024"
    print(f"🔑 User enters passphrase: {user_passphrase[:15]}...")
    
    # Step 2: Create/unlock encrypted database
    print("\n2️⃣ Creating Encrypted Medical Database...")
    db_path = Path("mcp_navmed_medical.db")
    
    if db_path.exists():
        db_path.unlink()
    
    # Create encrypted database with medical schema
    conn = sqlcipher3.connect(str(db_path))
    conn.execute(f"PRAGMA key = '{user_passphrase}'")
    
    # Create NAVMED examination table
    conn.execute("""
        CREATE TABLE examinations (
            exam_id INTEGER PRIMARY KEY,
            exam_date DATE,
            patient_last_name TEXT,
            patient_first_name TEXT,
            patient_ssn TEXT,
            radiation_exposure_history TEXT,
            medical_clearance_status TEXT,
            examining_physician TEXT,
            classified_level TEXT
        )
    """)
    
    # Insert sample encrypted medical data
    sample_data = [
        ('2024-01-15', 'Smith', 'John', '123-45-6789', 'Nuclear Reactor Operator', 'CLEARED', 'Dr. Johnson', 'CONFIDENTIAL'),
        ('2024-02-20', 'Davis', 'Sarah', '987-65-4321', 'Radiology Technician', 'PENDING', 'Dr. Martinez', 'CONFIDENTIAL'),
        ('2024-03-10', 'Brown', 'Michael', '555-12-3456', 'Nuclear Medicine Tech', 'CLEARED', 'Dr. Wilson', 'CONFIDENTIAL'),
    ]
    
    for data in sample_data:
        conn.execute("""
            INSERT INTO examinations (
                exam_date, patient_last_name, patient_first_name, patient_ssn,
                radiation_exposure_history, medical_clearance_status, 
                examining_physician, classified_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
    
    conn.commit()
    print("✅ Encrypted medical database created with classified patient data")
    conn.close()
    
    # Step 3: Verify database is encrypted
    print("\n3️⃣ Verifying Database Security...")
    try:
        conn = sqlcipher3.connect(str(db_path))
        conn.execute("SELECT * FROM examinations")
        print("❌ SECURITY BREACH: Database not encrypted!")
        conn.close()
        return False
    except Exception:
        print("✅ Database properly encrypted - unauthorized access blocked")
    
    # Step 4: MCP Server operations - unlock and access
    print("\n4️⃣ MCP Server: Processing Medical Examination Requests...")
    
    # Unlock database with passphrase
    conn = sqlcipher3.connect(str(db_path))
    conn.execute(f"PRAGMA key = '{user_passphrase}'")
    
    # Query encrypted medical data
    cursor = conn.execute("""
        SELECT patient_first_name, patient_last_name, medical_clearance_status, 
               radiation_exposure_history 
        FROM examinations
    """)
    
    patients = cursor.fetchall()
    print(f"📋 Retrieved {len(patients)} encrypted medical examination records:")
    
    for patient in patients:
        status_icon = "✅" if patient[2] == "CLEARED" else "⏳"
        print(f"   {status_icon} {patient[0]} {patient[1]} - {patient[2]} ({patient[3]})")
    
    # Step 5: Add new examination record
    print("\n5️⃣ Adding New Medical Examination...")
    new_exam = (
        '2024-06-10', 'TestPatient', 'Jane', '777-88-9999',
        'Nuclear Submarine Service', 'CLEARED', 'Dr. Anderson', 'CONFIDENTIAL'
    )
    
    conn.execute("""
        INSERT INTO examinations (
            exam_date, patient_last_name, patient_first_name, patient_ssn,
            radiation_exposure_history, medical_clearance_status,
            examining_physician, classified_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, new_exam)
    conn.commit()
    
    # Verify new record
    cursor = conn.execute(
        "SELECT patient_first_name, patient_last_name FROM examinations WHERE patient_ssn = '777-88-9999'"
    )
    new_patient = cursor.fetchone()
    print(f"✅ New encrypted record added: {new_patient[0]} {new_patient[1]}")
    
    # Step 6: Demonstrate database locking
    print("\n6️⃣ Demonstrating Database Security Lock...")
    conn.close()
    print("🔒 Database connection closed - data locked")
    
    # Try wrong passphrase
    print("🚫 Testing wrong passphrase protection...")
    try:
        wrong_conn = sqlcipher3.connect(str(db_path))
        wrong_conn.execute("PRAGMA key = 'wrong-passphrase'")
        wrong_conn.execute("SELECT * FROM examinations")
        print("❌ SECURITY ISSUE: Wrong passphrase worked!")
        wrong_conn.close()
        return False
    except Exception:
        print("✅ Wrong passphrase correctly rejected")
    
    # Step 7: Re-unlock for continued operations
    print("\n7️⃣ Re-unlocking for Continued Operations...")
    conn = sqlcipher3.connect(str(db_path))
    conn.execute(f"PRAGMA key = '{user_passphrase}'")
    
    cursor = conn.execute("SELECT COUNT(*) FROM examinations")
    total_exams = cursor.fetchone()[0]
    print(f"✅ Database unlocked - {total_exams} medical examinations accessible")
    
    conn.close()
    
    print("\n🎉 MCP Server Encrypted Database Demo: COMPLETE!")
    print(f"📁 Database: {db_path.absolute()}")
    print(f"🔐 Encryption: SQLCipher with medical-grade security")
    print(f"🛡️ Data Protection: Classified patient radiation exposure data secured")
    print(f"🚀 MCP Ready: Server successfully handles encrypted medical examinations")
    
    return True

def main():
    """Main demo execution."""
    try:
        success = simulate_mcp_workflow()
        if success:
            print("\n✅ MCP Server Demo: SUCCESS - Encrypted database operations working!")
            return 0
        else:
            print("\n❌ MCP Server Demo: FAILED - Security issues detected!")
            return 1
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 