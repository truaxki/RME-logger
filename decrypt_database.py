#!/usr/bin/env python3
"""
Database Decryption Tool for NAVMED Radiation Medical Examination System

This script decrypts a previously encrypted SQLite database file using the original passphrase.
The decrypted file will have the .enc extension removed.

Usage:
    python decrypt_database.py

The script will:
1. Check if the encrypted database file exists
2. Prompt for the decryption passphrase
3. Extract the salt from the encrypted file
4. Generate the same key from the passphrase using PBKDF2
5. Decrypt the database file using Fernet
6. Save the decrypted file without .enc extension
7. Optionally remove the encrypted file

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

# Hardcoded encrypted database path
ENCRYPTED_DATABASE_PATH = r"src\radiation_medical_exam\data\navmed_radiation_exam.db.enc"

def derive_key_from_passphrase(passphrase: str, salt: bytes) -> bytes:
    """
    Derive an encryption key from a passphrase using PBKDF2.
    
    Args:
        passphrase: User-provided passphrase
        salt: Salt extracted from encrypted file
        
    Returns:
        Base64-encoded encryption key suitable for Fernet
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,  # Must match encryption iterations
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return key

def decrypt_database():
    """
    Main decryption function that handles the complete decryption process.
    """
    print("NAVMED Database Decryption Tool")
    print("=" * 40)
    
    # Check if encrypted database file exists
    encrypted_path = Path(ENCRYPTED_DATABASE_PATH)
    if not encrypted_path.exists():
        print(f"❌ Error: Encrypted database file not found at {ENCRYPTED_DATABASE_PATH}")
        print("Please ensure the encrypted database file exists before running this script.")
        print("💡 Use encrypt_database.py to create an encrypted database first.")
        sys.exit(1)
    
    print(f"📁 Encrypted database found: {encrypted_path.absolute()}")
    print(f"📊 File size: {encrypted_path.stat().st_size:,} bytes")
    
    # Get passphrase from user
    print("\n🔓 Decryption Setup")
    passphrase = getpass.getpass("Enter decryption passphrase: ")
    if not passphrase:
        print("❌ Error: Passphrase cannot be empty")
        sys.exit(1)
    
    try:
        # Read the encrypted file
        print("📖 Reading encrypted database file...")
        with open(encrypted_path, 'rb') as file:
            encrypted_file_data = file.read()
        
        # Extract salt (first 16 bytes) and encrypted data
        if len(encrypted_file_data) < 16:
            print("❌ Error: Encrypted file is too small or corrupted")
            sys.exit(1)
        
        salt = encrypted_file_data[:16]
        encrypted_data = encrypted_file_data[16:]
        
        print("🧂 Extracted salt from encrypted file")
        
        # Derive decryption key from passphrase
        print("🔑 Generating decryption key from passphrase...")
        key = derive_key_from_passphrase(passphrase, salt)
        
        # Create Fernet cipher
        fernet = Fernet(key)
        
        # Decrypt the data
        print("🔓 Decrypting database...")
        try:
            decrypted_data = fernet.decrypt(encrypted_data)
        except Exception as e:
            print("❌ Decryption failed: Invalid passphrase or corrupted file")
            print(f"   Technical details: {str(e)}")
            sys.exit(1)
        
        # Prepare decrypted file path (remove .enc extension)
        decrypted_path = encrypted_path.with_suffix('')
        
        # Check if decrypted file already exists
        if decrypted_path.exists():
            print(f"\n⚠️  Warning: Decrypted file already exists: {decrypted_path.name}")
            response = input("Overwrite existing file? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ Decryption cancelled")
                sys.exit(1)
        
        # Write decrypted file
        print(f"💾 Saving decrypted database to {decrypted_path.name}...")
        with open(decrypted_path, 'wb') as file:
            file.write(decrypted_data)
        
        print(f"✅ Database successfully decrypted!")
        print(f"📁 Decrypted file: {decrypted_path.absolute()}")
        print(f"📊 Decrypted size: {decrypted_path.stat().st_size:,} bytes")
        
        # Verify it's a valid SQLite file
        if decrypted_data.startswith(b'SQLite format 3'):
            print("✅ Decrypted file appears to be a valid SQLite database")
        else:
            print("⚠️  Warning: Decrypted file may not be a valid SQLite database")
        
        # Ask if user wants to remove encrypted file
        print("\n🔐 Cleanup Options")
        response = input("Remove encrypted database file? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            encrypted_path.unlink()
            print(f"🗑️  Encrypted database file removed")
        else:
            print(f"ℹ️  Encrypted database file kept: {encrypted_path.name}")
        
        print("\n✨ Decryption completed successfully!")
        print("💡 Database is now ready for use with the NAVMED system")
        
    except Exception as e:
        print(f"❌ Decryption failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    decrypt_database() 