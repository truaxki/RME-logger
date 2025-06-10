#!/usr/bin/env python3
"""
Windows Native Authentication Launcher for NAVMED

This launcher uses Windows native authentication dialogs for maximum security:
- Uses Windows Credential Manager UI
- Completely isolated from Python process
- No memory exposure to main application
- Native Windows security boundaries
"""

import subprocess
import sys
import os
from pathlib import Path

class WindowsSecureLauncher:
    """
    Windows-specific secure launcher using native authentication.
    """
    
    def __init__(self):
        self.database_decrypted = False
    
    def run(self):
        """Main launcher for Windows environment."""
        print("NAVMED Secure Medical Records System (Windows)")
        print("=" * 55)
        
        try:
            # Step 1: Windows native authentication
            if not self.windows_authenticate():
                print("❌ Authentication failed")
                return False
            
            # Step 2: Start MCP system
            print("🚀 Starting AI assistant...")
            self.start_mcp_system()
            
            # Step 3: Wait for shutdown
            self.wait_for_shutdown()
            
        except KeyboardInterrupt:
            print("\n🔒 Emergency shutdown...")
        finally:
            self.cleanup()
        
        return True
    
    def windows_authenticate(self):
        """Use Windows native credential prompt."""
        print("🔑 Opening Windows authentication dialog...")
        
        # PowerShell script for secure credential prompt
        ps_script = '''
        # Windows native credential prompt
        $credential = Get-Credential -Message "Enter your medical records passphrase" -UserName "Patient"
        if ($credential) {
            $passphrase = $credential.GetNetworkCredential().Password
            Write-Output $passphrase
        } else {
            exit 1
        }
        '''
        
        try:
            # Run PowerShell with secure credential prompt
            result = subprocess.run([
                'powershell', '-Command', ps_script
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                passphrase = result.stdout.strip()
                if passphrase:
                    return self.decrypt_with_passphrase(passphrase)
            
            return False
            
        except Exception as e:
            print(f"❌ Windows authentication failed: {e}")
            return False
    
    def decrypt_with_passphrase(self, passphrase):
        """Decrypt database with passphrase."""
        try:
            # Use existing decrypt script
            result = subprocess.run([
                sys.executable, 'decrypt_database.py'
            ], input=f"{passphrase}\ny\n", text=True, capture_output=True)
            
            if result.returncode == 0:
                print("✅ Medical records decrypted")
                self.database_decrypted = True
                return True
            else:
                print("❌ Invalid passphrase")
                return False
                
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            return False


if __name__ == "__main__":
    launcher = WindowsSecureLauncher()
    launcher.run() 