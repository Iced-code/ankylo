import os
import json
import getpass
import time
import pyperclip
import uuid

from .crypto import derive_key, encrypt_data, decrypt_data
from .storage import vault_exists, load_vault_file, write_atomically, b64e, b64d


'''
Called other functions to generate message protocols.

Args:
    status (str): Status message (or code) depending on success of function.
    message (str): Output message based on function results.
    result (dict= None):
    action (str= None):
    log_action (bool= True): log the message of this action.

Returns:
    Message protocol formatted as dict. MESSAGE PROTOCOL format:
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
def gen_message(status:str, message:str, result:dict=None, action:str=None, log_action:bool=True) -> dict:
    return {
            "id": uuid.uuid4().hex[:8],
            "status": status,
            "message": f'\n{message}',
            "result": result,
            "action": action,
            "log_action": log_action
        }

'''
Initializes Vault
'''
def create_vault():
    if vault_exists():
        return gen_message("", "Vault already exists.")
    
    password = getpass.getpass("Create master password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        return gen_message("ERROR", "Invalid password.")
    
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
    return gen_message("OK", "Vault initialized successfully.")

'''
Unlock and load vault
'''
def unlock_vault(password:str=None):
    if not vault_exists():
        return None, None, gen_message("ERROR", "Vault not initialized.")
    
    vault_data = load_vault_file()

    if vault_data is None:
        return None, None, gen_message("ERROR", "Failed to load vault.")

    if not password:
        password = getpass.getpass("Master password: ")

    salt = b64d(vault_data["kdf"]["salt"])
    nonce = b64d(vault_data["nonce"])
    ciphertext = b64d(vault_data["ciphertext"])

    key = derive_key(password=password, salt=salt)

    try:
        decrypted_vault = decrypt_data(key=key, nonce=nonce, ciphertext=ciphertext)
    except Exception:
        return None, None, gen_message("ERROR", "Incorrect password or vault corrupted.")
    
    return key, json.loads(decrypted_vault), gen_message("OK", "Unlocked vault")

'''
Save vault
'''
def save_vault(key:str, vault_dict:dict, original_data):
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
        return None, None, gen_message("ERROR", "Vault not initialized.")
    
    vault_data = load_vault_file()

    if vault_data is None:
        print("Failed to load vault.")
        return None, None, gen_message("ERROR", "Failed to load vault.")

    password = getpass.getpass("Master password: ")

    salt = b64d(vault_data["kdf"]["salt"])
    nonce = b64d(vault_data["nonce"])
    ciphertext = b64d(vault_data["ciphertext"])

    key = derive_key(password=password, salt=salt)

    try:
        decrypted_vault = decrypt_data(key=key, nonce=nonce, ciphertext=ciphertext)
    except Exception:
        print("Incorrect password or vault corrupted")
        return None, None, gen_message("ERROR", "Incorrect password or vault corrupted.")
    
    os.remove("./vault.json")

    return
    
'''
Add an entry to the vault.

Args:
    name (str): Name of the entry.
    api_key (str= None): API key of the entry.
    key (str= None): The key to the vault.
    vault (dict= None): The vault.
    entry_index (int= None): The index of the entry if it already exist in the vault.

Returns:
    The formatted message protocol from the parameters passed into gen_message(...).
'''
def add_entry(name:str, api_key:str=None, key:str=None, vault:dict=None, entry_index:int=None):
    if not key: # when running CLI 
        key, vault, message = unlock_vault()
        if not key:
            return message

    name = name.strip()
    if name == "":
        return gen_message(status="ERROR", message=f"Invalid name.", log_action=False)

    if not api_key: # when running CLI
        api_key = getpass.getpass("Enter API key (hidden): ")

    # Checks if entry with same name already exists. 
    # Asks user whether to replace entry and saves that entry's index if so.
    if not entry_index: # when running CLI
        for index, entry in enumerate(vault["entries"]):
            if entry["name"].lower() == name.lower():
                replace = input("Entry already exists. Replace key for this entry? (Y/N): ").upper() == "Y"
                if not replace:
                    return gen_message(status="", message=f"Key was not replaced for the entry.")
                else:
                    entry_index = index
                    break

    if entry_index and entry_index != -1:   # Replaces api_key index for existing entry.   
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

    return gen_message(status="OK", message=f"Added '{name}' to vault.")

'''
List all entries
'''
def list_entries(key:str=None, vault:dict=None):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    print("")
    for index, entry in enumerate(vault["entries"]):
        print(f"[{index}] - {entry["name"]}")
    
    return gen_message(status="OK", message=f"Listed all vault entries.")


'''
Get entry
'''
def get_entry(name:str, key:str=None, vault:dict=None):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    for entry in vault["entries"]:
        if entry["name"] == name:
            pyperclip.copy(entry["key"])
            return gen_message(status="OK", message=f"Accessed {name} entry.\nAPI Key copied to clipboard.")

    return gen_message(status="ERROR", message=f"Entry '{name}' not found.", log_action=True)

'''
Get entry at the index
'''
def get_entry_index(index, key:str=None, vault:dict=None):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    index = int(index)
    if abs(index) >= len(vault["entries"]):
        return gen_message("ERROR", "Invalid index for vault entry.")

    pyperclip.copy(vault["entries"][index]["key"])
    return gen_message(status="OK", message=f"Accessed '{vault["entries"][index]["name"]}' entry.\nAPI Key copied to clipboard.")

'''
Delete entry
'''
def delete_entry(name:str, key:str=None, vault:dict=None):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    vault["entries"] = [e for e in vault["entries"] if e["name"] != name]

    original_data = load_vault_file()
    save_vault(key=key, vault_dict=vault, original_data=original_data)
    
    return gen_message(status="OK", message=f"Deleted '{name}' entry.")

'''
Delete entry at the index
'''
def delete_entry_index(index: int, key:str=None, vault:dict=None):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    index = int(index)

    if index >= len(vault["entries"]):
        return gen_message("ERROR", "Invalid index for vault entry.")

    entry_name = vault["entries"][index]["name"]
    vault["entries"] = [e for e in vault["entries"] if e["name"] != entry_name]

    original_data = load_vault_file()
    save_vault(key=key, vault_dict=vault, original_data=original_data)
    
    return gen_message(status="OK", message=f"Deleted '{entry_name}' entry.")
