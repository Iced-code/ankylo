import os
import json
import base64
import tempfile

VAULT_FILE = os.path.join( os.path.dirname(os.path.abspath(__file__)), "vault.json" )  # "vault.json"

def vault_exists() -> bool:
    return os.path.exists(VAULT_FILE)

def load_vault_file():
    with open(VAULT_FILE, "r") as fileVault:
        return json.load(fileVault)

def write_atomically(data: dict):
    dir_name = os.path.dirname(VAULT_FILE) or "."
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as tmp:
        json.dump(data, tmp)
        temp_name = tmp.name
    
    os.replace(temp_name, VAULT_FILE)

def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode()

def b64d(data: str) -> bytes:
    return base64.b64decode(data)