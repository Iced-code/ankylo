import os
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


aad = b"ankylo-v1.1"

'''
Key derivation using Argon2id.

Args:
    password (str): User's master password.
    salt (bytes): Salt for password hashing.

Returns:
    Key to the vault as a string of bytes.
'''
def derive_key(password: str, salt: bytes) -> bytes:
    return hash_secret_raw(
        secret = password.encode(),
        salt=salt,
        time_cost = 3,           # number of Argon2 iterations
        memory_cost = 65536,     # 64 MB
        parallelism = 2,
        hash_len = 32,           # 256 bit key
        type = Type.ID
    )

'''
Encrypts vault using AES-256-GCM

Args:
    key (bytes): Key to the vault.
    data (bytes): Data to be encrypted.

Returns:
    Nonce and ciphertext of user's encrypted keys.
'''
def encrypt_data(key: bytes, data: bytes):
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)       # 96 bit nonce (required for GCM)
    ciphertext = aesgcm.encrypt(nonce, data, aad)

    return nonce, ciphertext

'''
Decrypt vault

Args:
    key (bytes): Key to the vault.
    nonce (bytes): Random data necessary for decryption.
    ciphertext (bytes): Data to be decrypted.

Returns:
    Decrypted plaintext of user's keys.
'''
def decrypt_data(key: bytes, nonce: bytes, ciphertext: bytes):
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
    
    return plaintext
