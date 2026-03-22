"""Compatibility wrapper for encryption utilities.

The implementation lives in `truthound_dashboard.crypto` so DB bootstrap code can
import encryption helpers without forcing `truthound_dashboard.core` package
initialization and triggering circular imports.
"""

from truthound_dashboard.crypto import (  # noqa: F401
    EncryptionError,
    EncryptionKeyManager,
    Encryptor,
    decrypt_config,
    decrypt_value,
    encrypt_config,
    encrypt_value,
    get_encryptor,
    is_sensitive_field,
    mask_sensitive_value,
    redact_config,
    reset_encryptor,
)

__all__ = [
    "EncryptionError",
    "EncryptionKeyManager",
    "Encryptor",
    "decrypt_config",
    "decrypt_value",
    "encrypt_config",
    "encrypt_value",
    "get_encryptor",
    "is_sensitive_field",
    "mask_sensitive_value",
    "redact_config",
    "reset_encryptor",
]
