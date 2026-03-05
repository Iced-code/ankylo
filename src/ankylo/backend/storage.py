import os
import json
import base64
import tempfile
from pathlib import Path

BASE_DIR = Path.home() / "ankylo"
VAULT_FILE = BASE_DIR / "vault.json"

'''
Checks if vault exists.

Returns:
    Whether file path to the "vault.json" file exists.
'''
def vault_exists() -> bool:
    return os.path.exists(VAULT_FILE)

'''
Loads vault file.

Returns:
    Whether vault as json.
'''
def load_vault_file():
    with open(VAULT_FILE, "r") as fileVault:
        return json.load(fileVault)

'''
Writes changes to the vault atomically (completely or not at all).

Args:
    data (dict): Vault data to write into the "vault.json" file.
'''
def write_atomically(data: dict):
    dir_name = os.path.dirname(VAULT_FILE) or "."
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as tmp:
        json.dump(data, tmp)
        temp_name = tmp.name
    
    os.replace(temp_name, VAULT_FILE)

'''
Base64 encryption of data.

Args:
    data (bytes): Data to be encrpted.

Returns:
    Data encrypted in Base64.
'''
def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode()

'''
Base64 decryption of data.

Args:
    data (str): Data to be decrypted.

Returns:
    Data decrypted from Base64.
'''
def b64d(data: str) -> bytes:
    return base64.b64decode(data)