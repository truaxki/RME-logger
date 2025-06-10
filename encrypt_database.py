#!/usr/bin/env python3
"""
Database Encryption Tool for NAVMED Radiation Medical Examination System

This script encrypts the SQLite database file using AES encryption with a user-provided passphrase.
The encrypted file will have a .enc extension added to the original filename.

Usage:
    python encrypt_database.py

The script will:
1. Check if the database file exists
2. Prompt for an encryption passphrase
3. Generate a key from the passphrase using PBKDF2
4. Encrypt the database file using Fernet (AES 128)
5. Save the encrypted file with .enc extension
6. Optionally remove the original file

Requirements:
    pip install cryptography
"""

import os
import sys
import getpass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Hardcoded database path
DATABASE_PATH = r"src\radiation_medical_exam\data\navmed_radiation_exam.db"

def derive_key_from_passphrase(passphrase: str, salt: bytes) -> bytes:
    """
    Derive an encryption key from a passphrase using PBKDF2.
    
    Args:
        passphrase: User-provided passphrase
        salt: Random salt for key derivation
        
    Returns:
        Base64-encoded encryption key suitable for Fernet
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,  # OWASP recommended minimum
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return key

def encrypt_database():
    """
    Main encryption function that handles the complete encryption process.
    """
    print("NAVMED Database Encryption Tool")
    print("=" * 40)
    
    # Check if database file exists
    db_path = Path(DATABASE_PATH)
    if not db_path.exists():
        print(f"❌ Error: Database file not found at {DATABASE_PATH}")
        print("Please ensure the database file exists before running this script.")
        sys.exit(1)
    
    print(f"📁 Database found: {db_path.absolute()}")
    print(f"📊 File size: {db_path.stat().st_size:,} bytes")
    
    # Get passphrase from user
    print("\n🔒 Encryption Setup")
    passphrase = getpass.getpass("Enter encryption passphrase: ")
    if not passphrase:
        print("❌ Error: Passphrase cannot be empty")
        sys.exit(1)
    
    # Confirm passphrase
    confirm_passphrase = getpass.getpass("Confirm passphrase: ")
    if passphrase != confirm_passphrase:
        print("❌ Error: Passphrases do not match")
        sys.exit(1)
    
    try:
        # Generate random salt
        salt = os.urandom(16)
        
        # Derive encryption key from passphrase
        print("🔑 Generating encryption key from passphrase...")
        key = derive_key_from_passphrase(passphrase, salt)
        
        # Create Fernet cipher
        fernet = Fernet(key)
        
        # Read the database file
        print("📖 Reading database file...")
        with open(db_path, 'rb') as file:
            database_data = file.read()
        
        # Encrypt the data
        print("🔐 Encrypting database...")
        encrypted_data = fernet.encrypt(database_data)
        
        # Prepare encrypted file path
        encrypted_path = db_path.with_suffix(db_path.suffix + '.enc')
        
        # Write encrypted file (salt + encrypted data)
        print(f"💾 Saving encrypted database to {encrypted_path.name}...")
        with open(encrypted_path, 'wb') as file:
            file.write(salt + encrypted_data)
        
        print(f"✅ Database successfully encrypted!")
        print(f"📁 Encrypted file: {encrypted_path.absolute()}")
        print(f"📊 Encrypted size: {encrypted_path.stat().st_size:,} bytes")
        
        # Ask if user wants to remove original
        print("\n⚠️  Security Recommendation")
        response = input("Remove original unencrypted database file? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            db_path.unlink()
            print(f"🗑️  Original database file removed")
        else:
            print(f"ℹ️  Original database file kept: {db_path.name}")
        
        print("\n✨ Encryption completed successfully!")
        print("💡 Use decrypt_database.py to decrypt the file when needed")
        
    except Exception as e:
        print(f"❌ Encryption failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    encrypt_database() 