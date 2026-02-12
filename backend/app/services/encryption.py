from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def encrypt_aes_gcm(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt with AES-256-GCM. Returns nonce(12) + ciphertext + tag(16)."""
    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return nonce + ciphertext + tag


def decrypt_aes_gcm(data: bytes, key: bytes) -> bytes:
    """Decrypt AES-256-GCM. Expects nonce(12) + ciphertext + tag(16)."""
    nonce = data[:12]
    tag = data[-16:]
    ciphertext = data[12:-16]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)
