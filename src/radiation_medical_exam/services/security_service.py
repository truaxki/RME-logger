"""
Security service for managing encryption keys and passphrases.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
import hashlib
import base64
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityService:
    """Handles all security operations including keys and tokens."""
    
    def __init__(self):
        self.cached_key = None
        self.key_source = None  # 'passphrase', 'token', or None
        
    def prompt_for_passphrase(self, title: str = "Database Authentication") -> Optional[str]:
        """Show GUI dialog for passphrase entry."""
        passphrase = None
        
        def on_submit():
            nonlocal passphrase
            passphrase = entry.get()
            root.quit()
        
        def on_cancel():
            root.quit()
        
        # Create GUI
        root = tk.Tk()
        root.title("NAVMED Medical Records")
        root.geometry("400x200")
        root.resizable(False, False)
        
        # Center window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (400 // 2)
        y = (root.winfo_screenheight() // 2) - (200 // 2)
        root.geometry(f"400x200+{x}+{y}")
        
        # Create frame
        frame = ttk.Frame(root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title label
        title_label = ttk.Label(frame, text=title, font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Instructions
        info_label = ttk.Label(frame, text="Enter passphrase to decrypt medical records:")
        info_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Passphrase entry
        entry = ttk.Entry(frame, show="*", width=40)
        entry.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        entry.focus()
        
        # Buttons
        cancel_button = ttk.Button(frame, text="Cancel", command=on_cancel)
        cancel_button.grid(row=3, column=0, padx=(0, 10), sticky=tk.E)
        
        submit_button = ttk.Button(frame, text="Unlock", command=on_submit)
        submit_button.grid(row=3, column=1, sticky=tk.W)
        
        # Bind Enter key
        root.bind('<Return>', lambda e: on_submit())
        root.bind('<Escape>', lambda e: on_cancel())
        
        # Make modal
        root.grab_set()
        root.mainloop()
        root.destroy()
        
        return passphrase
    
    def derive_key_from_passphrase(self, passphrase: str, salt: bytes = b'navmed-salt') -> str:
        """Convert passphrase to encryption key using PBKDF2."""
        # SQLCipher expects the passphrase directly, but we can pre-process if needed
        # For now, return passphrase as-is (SQLCipher handles key derivation)
        return passphrase
    
    def get_key_from_token(self, token_path: str = None) -> Optional[str]:
        """Read encryption key from security token (future feature)."""
        # Placeholder for future token implementation
        if token_path and Path(token_path).exists():
            # In future: Read and decrypt key from token file
            pass
        return None
    
    def get_connection_key(self) -> Optional[str]:
        """Get key from cache, prompt, or token."""
        # First try cached key
        if self.cached_key:
            return self.cached_key
        
        # Try token (future feature)
        token_key = self.get_key_from_token()
        if token_key:
            self.cached_key = token_key
            self.key_source = 'token'
            return token_key
        
        # Prompt for passphrase
        passphrase = self.prompt_for_passphrase()
        if passphrase:
            self.cached_key = self.derive_key_from_passphrase(passphrase)
            self.key_source = 'passphrase'
            return self.cached_key
        
        return None
    
    def clear_cached_key(self):
        """Clear the cached key from memory."""
        self.cached_key = None
        self.key_source = None 