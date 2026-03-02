import os
import json
import getpass
import time
import pyperclip
import uuid


from .crypto import derive_key, encrypt_data, decrypt_data
from .storage import vault_exists, load_vault_file, write_atomically, b64e, b64d


'''
MESSAGE PROTOCOL

{
    "id": uuid,
    "status": "OK",
    "message": "Created vault, add entry, etc."
    "result": {
        "key": key,
        "vault": vault,
        ...
    }
}
'''
def gen_message(status: int | str, message: str, result: dict=None, action: str=None, log_action: bool=True):
    if status is int:
        status = "OK"
    
    return {
            "id": uuid.uuid4().hex[:8],
            "status": status,
            "message": message,
            "result": result,
            "action": action,
            "log_action": log_action
        }

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
def unlock_vault(password:str = None):
    if not vault_exists():
        print("Vault not initialized.")
        return None, None
    
    vault_data = load_vault_file()

    if vault_data is None:
        print("Failed to load vault.")
        return None, None

    if not password:
        password = getpass.getpass("Master password: ")

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
Delete vault
'''
def delete_vault():
    if not vault_exists():
        print("Vault not initialized.")
        return None, None
    
    vault_data = load_vault_file()

    if vault_data is None:
        print("Failed to load vault.")
        return None, None

    password = getpass.getpass("Master password: ")

    salt = b64d(vault_data["kdf"]["salt"])
    nonce = b64d(vault_data["nonce"])
    ciphertext = b64d(vault_data["ciphertext"])

    key = derive_key(password=password, salt=salt)

    try:
        decrypted_vault = decrypt_data(key=key, nonce=nonce, ciphertext=ciphertext)
    except Exception:
        print("Incorrect password or vault corrupted")
        return None, None
    
    os.remove("./vault.json")

    return
    
'''
Add entry to vault
'''
def add_entry(name: str, api_key:str=None, key:str=None, vault=None, entry_index:int=None):
    if not key:
        key, vault = unlock_vault()
        if not key:
            return gen_message(status="ERROR", message=f"Invalid password.")

    name = name.strip()
    if name == "":
        return gen_message(status="ERROR", message=f"Invalid name.", log_action=False)

    if not api_key: 
        api_key = getpass.getpass("Enter API key (hidden): ")

    if not entry_index:
        for index, entry in enumerate(vault["entries"]):
            if entry["name"].lower() == name.lower():
                replace = input("Entry already exists. Replace key for this entry? (Y/N): ").upper() == "Y"
                if not replace:
                    return gen_message(status="OK", message=f"", log_action=False)
                else:
                    entry_index = index
                    break
            
    if entry_index and entry_index != -1:
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

    return gen_message(status="OK", message=f"Added '{name}' API key.")

'''
List all entries
'''
def list_entries(key:str=None, vault=None):
    if not key:
        key, vault = unlock_vault()
        if key is None:
            return
    
    for entry in vault["entries"]:
        print(f"- {entry["name"]}")
    
    return gen_message(status="OK", message=f"Listed all vault entries.")


'''
Get entry
'''
def get_entry(name:str, key:str=None, vault=None):
    if not key:
        key, vault = unlock_vault()
        if not key:
            return
    
    for entry in vault["entries"]:
        if entry["name"] == name:
            pyperclip.copy(entry["key"])
            print("API Key copied to clipboard.")
            return gen_message(status="OK", message=f"Accessed {name} entry.")

    print("Entry not found.")
    return gen_message(status="ERROR", message=f"Unable to get entry '{name}'.", log_action=True)

'''
Get entry at the index
'''
def get_entry_index(index, key:str=None, vault=None):
    if not key:
        key, vault = unlock_vault()
        if not key:
            return
    
    index = int(index)
    if abs(index) >= len(vault["entries"]):
        print("Invalid index.")
        return

    pyperclip.copy(vault["entries"][index]["key"])
    print("API Key copied to clipboard.")
    return gen_message(status="OK", message=f"Accessed '{vault["entries"][index]["key"]}' entry.")

'''
Delete entry
'''
def delete_entry(name:str, key:str=None, vault=None):
    if not key:
        key, vault = unlock_vault()
        if not key:
            return
    
    vault["entries"] = [e for e in vault["entries"] if e["name"] != name]

    original_data = load_vault_file()
    save_vault(key=key, vault_dict=vault, original_data=original_data)
    
    print("Entry deleted.")

'''
Delete entry at the index
'''
def delete_entry_index(index, key:str=None, vault=None):
    if not key:
        key, vault = unlock_vault()
        if not key:
            return
    
    index = int(index)
    if index >= len(vault["entries"]):
        print("Invalid index.")
        return

    print(vault["entries"][index]["name"])
    vault["entries"] = [e for e in vault["entries"] if e["name"] != vault["entries"][index]["name"]]

    original_data = load_vault_file()
    save_vault(key=key, vault_dict=vault, original_data=original_data)
    
    print("Entry deleted.")
