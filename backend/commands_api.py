import os
import json
import getpass
import time
import pyperclip
import sys

from crypto import derive_key, encrypt_data, decrypt_data
from storage import vault_exists, load_vault_file, write_atomically, b64e, b64d

'''
Initialize Vault
'''
def create_vault():
    if vault_exists():
        print("Vault already exists")
        return
    
    password = getpass.getpass("Create master password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.")
        return
    
    salt = os.urandom(16)
    key = derive_key(password=password, salt=salt)

    empty_data = json.dumps(
        {"entries": []}
    ).encode()

    nonce, ciphertext = encrypt_data(key=key, data=empty_data)

    vault = {
        "version": 0.5,
        "kdf": {
            "type": "argon2id",
            "salt": b64e(salt),
            "time_cost": 3,
            "memory_cost": 65536,
            "parallelism": 2
        },
        "nonce": b64e(nonce),
        "ciphertext": b64e(ciphertext)
    }

    write_atomically(vault)
    print("Vault initialized successfully")

'''
Unlock and load vault
'''
def unlock_vault(password: str):
    if not vault_exists():
        print("Vault not initialized.")
        return None, None
    
    vault_data = load_vault_file()

    if vault_data is None:
        print("Failed to load vault.")
        return None, None

    salt = b64d(vault_data["kdf"]["salt"])
    nonce = b64d(vault_data["nonce"])
    ciphertext = b64d(vault_data["ciphertext"])

    key = derive_key(password=password, salt=salt)

    try:
        decrypted_vault = decrypt_data(key=key, nonce=nonce, ciphertext=ciphertext)
    except Exception:
        print("Incorrect password or vault corrupted")
        return None, None
    
    return key, json.loads(decrypted_vault)

'''
Save vault
'''
def save_vault(key, vault_dict, original_data):
    data = json.dumps(vault_dict).encode()
    nonce, ciphertext = encrypt_data(key=key, data=data)

    updated = {
        "version": 0.5,
        "kdf": original_data["kdf"],
        "nonce": b64e(nonce),
        "ciphertext": b64e(ciphertext)
    }

    write_atomically(updated)
    
'''
Add entry to vault
'''
def add_entry(name: str, api_key: str, key, vault):
    entry_index = None

    for index, entry in enumerate(vault["entries"]):
        if entry["name"] == name:
            replace = input("Entry already exists. Replace key for this entry? (Y/N): ").upper() == "Y"
            if not replace:
                return
            else:
                entry_index = index
                break
            
    if entry_index != None:
        vault["entries"][entry_index] = ({
            "name": name,
            "key": api_key
        })
    else:
        vault["entries"].append({
            "name": name,
            "key": api_key
        })

    original_data = load_vault_file()
    save_vault(key=key, vault_dict=vault, original_data=original_data)

    print("\nAdded API key.")

'''
List all entries
'''
def list_entries(key, vault):
    if not key:
        return
    
    for entry in vault["entries"]:
        print(f"- {entry["name"]}")

'''
Get entry
'''
def get_entry(name: str, key:str , vault):
    for entry in vault["entries"]:
        if entry["name"] == name:
            pyperclip.copy(entry["key"])
            print("API Key copied to clipboard.")
            return

    print("Entry not found.")

'''
Delete entry
'''
def delete_entry(name):
    key, vault = unlock_vault()
    if not key:
        return
    
    vault["entries"] = [e for e in vault["entries"] if e["name"] != name]

    original_data = load_vault_file()
    save_vault(key=key, vault_dict=vault, original_data=original_data)
    
    print("Entry deleted.")



for line in sys.stdin:
    data = json.loads(line)

    result = {
        "message": f"output"
    }

    print(json.dumps(result))
    sys.stdout.flush()
    