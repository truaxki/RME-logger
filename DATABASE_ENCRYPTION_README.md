# NAVMED Database Encryption Tools

## 🔐 Overview

This directory contains two companion scripts for encrypting and decrypting the NAVMED radiation medical examination database:

- `encrypt_database.py` - Encrypts the SQLite database file
- `decrypt_database.py` - Decrypts the encrypted database file

## 🛡️ Security Features

### Encryption Algorithm
- **Algorithm**: AES-128 (via Fernet symmetric encryption)
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Salt**: 16-byte random salt generated for each encryption
- **Library**: Python `cryptography` library (industry standard)

### Security Benefits
- ✅ **Strong Encryption**: AES-128 provides military-grade security
- ✅ **Salt Protection**: Each encryption uses a unique salt (prevents rainbow table attacks)
- ✅ **Key Stretching**: 100,000 PBKDF2 iterations slow down brute force attacks
- ✅ **Passphrase Confirmation**: Prevents typos during encryption
- ✅ **File Integrity**: Built-in authentication prevents tampering
- ✅ **No Key Storage**: Only the passphrase is needed (not stored anywhere)

## 📋 Requirements

```bash
pip install cryptography
```

Or if using this project's environment:
```bash
uv sync
```

## 🚀 Usage

### Encrypting the Database

```bash
python encrypt_database.py
```

**What it does:**
1. Checks if the database file exists at `src\radiation_medical_exam\data\navmed_radiation_exam.db`
2. Prompts for an encryption passphrase (hidden input)
3. Asks for passphrase confirmation
4. Generates a random salt and derives encryption key
5. Encrypts the entire database file
6. Saves encrypted file as `navmed_radiation_exam.db.enc`
7. Optionally removes the original unencrypted file

**Example Output:**
```
NAVMED Database Encryption Tool
========================================
📁 Database found: C:\...\navmed_radiation_exam.db
📊 File size: 102,400 bytes

🔒 Encryption Setup
Enter encryption passphrase: [hidden]
Confirm passphrase: [hidden]
🔑 Generating encryption key from passphrase...
📖 Reading database file...
🔐 Encrypting database...
💾 Saving encrypted database to navmed_radiation_exam.db.enc...
✅ Database successfully encrypted!
📁 Encrypted file: C:\...\navmed_radiation_exam.db.enc
📊 Encrypted size: 136,648 bytes

⚠️  Security Recommendation
Remove original unencrypted database file? (y/N): y
🗑️  Original database file removed

✨ Encryption completed successfully!
💡 Use decrypt_database.py to decrypt the file when needed
```

### Decrypting the Database

```bash
python decrypt_database.py
```

**What it does:**
1. Checks if the encrypted file exists at `src\radiation_medical_exam\data\navmed_radiation_exam.db.enc`
2. Prompts for the decryption passphrase
3. Extracts the salt from the encrypted file
4. Derives the same encryption key using the passphrase and salt
5. Decrypts the database file
6. Saves decrypted file as `navmed_radiation_exam.db`
7. Verifies the file is a valid SQLite database
8. Optionally removes the encrypted file

**Example Output:**
```
NAVMED Database Decryption Tool
========================================
📁 Encrypted database found: C:\...\navmed_radiation_exam.db.enc
📊 File size: 136,648 bytes

🔓 Decryption Setup
Enter decryption passphrase: [hidden]
📖 Reading encrypted database file...
🧂 Extracted salt from encrypted file
🔑 Generating decryption key from passphrase...
🔓 Decrypting database...
💾 Saving decrypted database to navmed_radiation_exam.db...
✅ Database successfully decrypted!
📁 Decrypted file: C:\...\navmed_radiation_exam.db
📊 Decrypted size: 102,400 bytes
✅ Decrypted file appears to be a valid SQLite database

🔐 Cleanup Options
Remove encrypted database file? (y/N): y
🗑️  Encrypted database file removed

✨ Decryption completed successfully!
💡 Database is now ready for use with the NAVMED system
```

## 🔒 Security Best Practices

### Passphrase Guidelines
- **Use a strong passphrase**: At least 12 characters with mixed case, numbers, and symbols
- **Don't write it down**: Memorize or use a secure password manager
- **Don't share it**: The passphrase is the only way to decrypt the database
- **Example strong passphrase**: `NavMed2025!SecureDB#`

### File Management
- **Keep encrypted files secure**: Store in protected directories
- **Remove originals**: After encryption, remove unencrypted database files
- **Backup encrypted files**: Keep multiple copies of the encrypted database
- **Test decryption**: Periodically verify you can decrypt your files

### Operational Security
- **Run on secure systems**: Don't use encryption tools on compromised machines
- **Clear clipboard**: Don't copy passphrases to clipboard
- **Monitor access**: Keep track of who has access to encrypted files
- **Update regularly**: Use the latest version of the cryptography library

## 📁 File Structure

```
radiation-medical-exam/
├── encrypt_database.py           # Encryption tool
├── decrypt_database.py           # Decryption tool
├── DATABASE_ENCRYPTION_README.md # This documentation
└── src/radiation_medical_exam/data/
    ├── navmed_radiation_exam.db      # Original database (unencrypted)
    ├── navmed_radiation_exam.db.enc  # Encrypted database
    └── navmed_radiation_exam copy.db # Backup copy
```

## 🚨 Emergency Recovery

### If You Forget the Passphrase
**Unfortunately, there is NO way to recover an encrypted database without the passphrase.** This is by design for security.

**Recovery options:**
1. **Use backup copy**: Restore from `navmed_radiation_exam copy.db` if available
2. **Re-initialize database**: Use `python -m radiation_medical_exam initialize-database --force`
3. **Import from other sources**: If you have data exports or backups

### If Decryption Fails
1. **Check passphrase**: Ensure you're using the exact same passphrase
2. **Check file integrity**: Verify the encrypted file isn't corrupted
3. **Check file path**: Ensure the encrypted file is in the correct location
4. **Try backup**: Use a different copy of the encrypted file if available

## 🔧 Technical Details

### Encryption Process
1. Generate 16-byte random salt
2. Use PBKDF2-HMAC-SHA256 with 100,000 iterations to derive key from passphrase
3. Create Fernet cipher with derived key
4. Encrypt database content
5. Prepend salt to encrypted data
6. Write to `.enc` file

### Decryption Process
1. Read encrypted file
2. Extract salt (first 16 bytes)
3. Extract encrypted data (remaining bytes)
4. Derive same key using passphrase and extracted salt
5. Create Fernet cipher with derived key
6. Decrypt data and verify integrity
7. Write decrypted database file

### File Format
```
[16 bytes: Salt][Variable length: Fernet-encrypted database]
```

## 📞 Support

For questions or issues with the encryption tools:
1. Check this README for common solutions
2. Verify all requirements are installed
3. Test with a copy of the database first
4. Report bugs to the project maintainer

---

**⚠️ IMPORTANT**: Always test encryption/decryption with a backup copy before using on production data! 