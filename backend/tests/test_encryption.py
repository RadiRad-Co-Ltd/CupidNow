import base64
import os
from app.services.encryption import decrypt_aes_gcm, encrypt_aes_gcm


def test_encrypt_decrypt_roundtrip():
    key = os.urandom(32)
    plaintext = "Hello, 你好！這是測試訊息。".encode("utf-8")

    encrypted = encrypt_aes_gcm(plaintext, key)
    decrypted = decrypt_aes_gcm(encrypted, key)

    assert decrypted == plaintext


def test_decrypt_with_base64_key():
    key = os.urandom(32)
    key_b64 = base64.b64encode(key).decode()
    plaintext = "測試".encode("utf-8")

    encrypted = encrypt_aes_gcm(plaintext, key)
    key_decoded = base64.b64decode(key_b64)
    decrypted = decrypt_aes_gcm(encrypted, key_decoded)

    assert decrypted == plaintext


def test_wrong_key_fails():
    key = os.urandom(32)
    wrong_key = os.urandom(32)
    plaintext = b"secret"

    encrypted = encrypt_aes_gcm(plaintext, key)

    try:
        decrypt_aes_gcm(encrypted, wrong_key)
        assert False, "Should have raised"
    except Exception:
        pass
