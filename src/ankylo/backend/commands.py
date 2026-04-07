import os
import json
import getpass
import pyperclip
import uuid
from datetime import datetime

from ankylo.backend.crypto import derive_key, encrypt_data, decrypt_data
from ankylo.backend.storage import vault_exists, load_vault_file, write_atomically, b64e, b64d, VAULT_FILE

VERSION = 1.1

'''
Called to generate formatted message protocols.

Args:
    status (str): Status message (or code) depending on success of function.
    message (str): Output message based on function results.
    result (dict= None):
    action (str= None):
    log_action (bool= True): log the message of this action.

Returns:
    Message protocol formatted as dict.
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
Initializes vault.

Returns:
    The formatted message protocol from the parameters passed into gen_message(...).
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
        "version": VERSION,
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
Unlocks and loads the vault.

Args:
    password (str= None): User's master password.

Returns:
    The derived key to the vault, the decrypted vault, and formatted message protocol.
'''
def unlock_vault(password:str=None):
    if not vault_exists():
        return None, None, gen_message("ERROR", "Vault not initialized.")
    
    vault_data = load_vault_file()

    if not vault_data:
        return None, None, gen_message("ERROR", "Failed to load vault.")

    if password is None:
        password = getpass.getpass("Master password: ")

    salt = b64d(vault_data["kdf"]["salt"])
    nonce = b64d(vault_data["nonce"])
    ciphertext = b64d(vault_data["ciphertext"])

    key = derive_key(password=password, salt=salt)

    try:
        decrypted_vault = decrypt_data(key=key, nonce=nonce, ciphertext=ciphertext)
    except Exception:
        return None, None, gen_message("ERROR", "Incorrect password or vault corrupted.")
    
    return key, json.loads(decrypted_vault), gen_message("OK", "Unlocked vault.")

'''
Save updates and changes to the vault.
'''
def save_vault(key:str, vault_dict:dict, original_data):
    data = json.dumps(vault_dict).encode()
    nonce, ciphertext = encrypt_data(key=key, data=data)

    updated = {
        "version": VERSION,
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
        return gen_message("ERROR", "Vault not initialized.")
    
    vault_data = load_vault_file()

    if vault_data is None:
        return gen_message("ERROR", "Vault could not be found.")

    password = getpass.getpass("Master password: ")

    salt = b64d(vault_data["kdf"]["salt"])
    nonce = b64d(vault_data["nonce"])
    ciphertext = b64d(vault_data["ciphertext"])

    key = derive_key(password=password, salt=salt)

    try:
        decrypted_vault = decrypt_data(key=key, nonce=nonce, ciphertext=ciphertext)
    except Exception:
        return gen_message("ERROR", "Incorrect password or vault corrupted.")
    
    VAULT_FILE.unlink()

    return gen_message("OK", "Vault was deleted.")

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
                replace = input(f"An entry named '{name}' already exists. Replace key for this entry? (y/N): ").strip().lower() == "y"
                if not replace:
                    return gen_message(status="", message=f"Key was not replaced for the entry.")
                else:
                    entry_index = index
                    break

    now = datetime.now()
    if (entry_index is not None) and entry_index != -1:   # Replaces api_key index for existing entry.   
        vault["entries"][entry_index] = ({
            "name": name,
            "key": api_key,
            "timestamp": f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
        })
    else:
        vault["entries"].append({
            "name": name,
            "key": api_key,
            "timestamp": f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
        })

    original_data = load_vault_file()
    save_vault(key=key, vault_dict=vault, original_data=original_data)

    return gen_message(status="OK", message=f"Added '{name}' to vault.")

'''
Add entries from a given file path to the vault.

Args:
    file_path (str): Path to file with the entries to add.
    key (str= None): The key to the vault.
    vault (dict= None): The vault.

Returns:
    The formatted message protocol from the parameters passed into gen_message(...).
'''
def add_entries_from_file(file_path:str, key:str=None, vault:dict=None):
    if not key: # when running CLI 
        key, vault, message = unlock_vault()
        if not key:
            return message

    try:
        with open(file_path, "r") as fileInput:
            for line in fileInput:
                entry = line.strip().split("=", 1)
                add_entry(name=entry[0], api_key=entry[-1], key=key, vault=vault)
    except FileNotFoundError:
        return gen_message(status="ERROR", message=f"File was not found.")

    return gen_message(status="OK", message=f"Added file contents to vault.")


'''
Lists all entries in the vault.

Args:
    key (str= None): Key to the vault.
    vault (dict= None): The vault.
    show (bool= False): Show the keys of all entries in the vault.

Returns:
    The formatted message protocol from the parameters passed into gen_message(...).
'''
def list_entries(key:str=None, vault:dict=None, show:bool=False):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    output = dict()
    for index, entry in enumerate(vault["entries"]):
        output[index] = entry["name"]

        if show:
            output[index] = (entry["name"], entry["key"])

    return gen_message(status="OK", message=f"Listed all vault entries.", result=output)

'''
Export entries to the specified file.

Args:
    outputFile (str): File to export entries to.
    names (list[str]= None): Names of entries to export.
    indices (list[int]= None): Indices of entries to export.
    key (str= None): Key to the vault.
    vault (dict= None): The vault.
    
Returns:
    The formatted message protocol from the parameters passed into gen_message(...).
'''
def export_entries_file(outputFile:str, names:list[str]=None, indices:list[int]=None, key:str=None, vault:dict=None):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message

    if len(vault) == 0:
        return gen_message(status="", message=f"Vault is empty.\nExport cancelled.")

    # export with -n
    if names:
        filtered_vault =  [entry for entry in vault["entries"] if entry["name"] in names]
    elif indices:   # export with -i
        filtered_vault = []
        for i in indices:
            if abs(i) >= len(vault["entries"]):
                return gen_message(status="ERROR", message=f"Invalid index '{i}'\nExport cancelled.")

            filtered_vault.append({"name": vault["entries"][i]["name"], "key": vault["entries"][i]["key"]})
    else:
        filtered_vault = [entry for entry in vault["entries"]]

    if len(filtered_vault) == 0:
        return gen_message(status="ERROR", message=f"Entry names do not exist.\nExport cancelled.")


    if outputFile and filtered_vault:
        with open(outputFile, "w") as file:
            for e in filtered_vault:
                file.write(f'\n{e["name"].upper().replace("-", "_").replace(" ", "_")}={e["key"].strip()}')
        return gen_message(status="OK", message=f"Entries successfully exported to file '{outputFile}'.")

    return gen_message(status="ERROR", message=f"Unable to export entries to this file.")


'''
Gets entry given its name. Entry's key is copied to the user's clipboard.

Args:
    name (str): Name of the entry to get.
    key (str= None): Key to the vault.
    vault (dict= None): The vault.

Returns:
    The formatted message protocol from the parameters passed into gen_message(...).
'''
def get_entry(name:str, key:str=None, vault:dict=None, show:bool=False):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    for entry in vault["entries"]:
        if entry["name"] == name:
            pyperclip.copy(entry["key"])
            output = gen_message(status="OK", message=f"Accessed '{name}' entry.\nAPI Key copied to clipboard.")
            if show:
                output["result"] = {"name": entry["name"], "key": entry["key"], "timestamp": entry["timestamp"]}
            else:
                output["result"] = {"name": entry["name"], "key": "", "timestamp": entry["timestamp"]}

            return output

    return gen_message(status="ERROR", message=f"Entry '{name}' not found.", log_action=True)

'''
Gets entry found at the given index. Entry's key is copied to the user's clipboard.

Args:
    index (int): Index of the entry to get.
    key (str= None): Key to the vault.
    vault (dict= None): The vault.

Returns:
    The formatted message protocol from the parameters passed into gen_message(...).
'''
def get_entry_index(index: int, key:str=None, vault:dict=None, show:bool=False):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    if abs(index) >= len(vault["entries"]):
        return gen_message("ERROR", "Invalid index for vault entry.")

    pyperclip.copy(vault["entries"][index]["key"])
    output = gen_message(status="OK", message=f"Accessed '{vault["entries"][index]["name"]}' entry.\nAPI Key copied to clipboard.")

    if show:
        output["result"] = {"name": vault["entries"][index]["name"], "key": vault["entries"][index]["key"], "timestamp": vault["entries"][index]["timestamp"]}
    else:
       output["result"] = {"name": vault["entries"][index]["name"], "key": "", "timestamp": vault["entries"][index]["timestamp"]}

    return output

'''
Export an entry given its name and in the format of the user's shell (default 'bash')

Args:
    name (str): Name of the entry to export.
    shell (str): Shell to format output to.
    key (str= None): Key to the vault.
    vault (dict= None): The vault.

Returns:
    The formatted message protocol from the parameters passed into gen_message(...).
'''
def export_entry(name:str, shell:str, key:str=None, vault:dict=None):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    for entry in vault["entries"]:
        if entry["name"] == name:
            var_name = name.upper().replace("-", "_").replace(" ", "_")

            output = gen_message(status="OK", message=f"Exported entry '{name}' as {shell} environment variable '{var_name}'.")
            if shell == "powershell" or shell == "ps":
                output["result"] = {"env_var": f'$env:{var_name}="{entry["key"]}"'}
            elif shell == "cmd":
                output["result"] = {"env_var": f'set {var_name}={entry["key"]}'}
            else:
                output["result"] = {"env_var": f'export {var_name}={entry["key"]}'}
            
            return output

    return gen_message(status="ERROR", message=f"Entry '{name}' not found.", log_action=True)

'''
Deletes entry given its name.

Args:
    name (str): Name of the entry to delete.
    key (str= None): Key to the vault.
    vault (dict= None): The vault.

Returns:
    The formatted message protocol from the parameters passed into gen_message(...).
'''
def delete_entry(name:str, key:str=None, vault:dict=None):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    num_entries = len(vault["entries"])
    confirm = input("Delete this entry and its key? This cannot be undone. (y/N): ").strip().lower() == "y"
    if confirm:
        vault["entries"] = [e for e in vault["entries"] if e["name"] != name]
    else:
        return gen_message(status="", message=f"Entry was not deleted.", log_action=False)

    original_data = load_vault_file()
    save_vault(key=key, vault_dict=vault, original_data=original_data)

    if num_entries <= len(vault["entries"]):
        return gen_message(status="", message=f"Entry '{name}' could not be found.")

    return gen_message(status="OK", message=f"Deleted '{name}' entry.")

'''
Deletes entry found at the given index. 

Args:
    index (int): Index of the entry to delete.
    key (str= None): Key to the vault.
    vault (dict= None): The vault.

Returns:
    The formatted message protocol from the parameters passed into gen_message(...).
'''
def delete_entry_index(index: int, key:str=None, vault:dict=None):
    if not key:
        key, vault, message = unlock_vault()
        if not key:
            return message
    
    index = int(index)

    if abs(index) >= len(vault["entries"]):
        return gen_message("ERROR", "Invalid index for vault entry.")

    confirm = input("Delete this entry and its key? This cannot be undone. (y/N): ").strip().lower() == "y"
    if confirm:
        entry_name = vault["entries"][index]["name"]
        vault["entries"] = [e for e in vault["entries"] if e["name"] != entry_name]
    else:
        return gen_message(status="", message=f"Entry was not deleted.", log_action=False)

    original_data = load_vault_file()
    save_vault(key=key, vault_dict=vault, original_data=original_data)
    
    return gen_message(status="OK", message=f"Deleted '{entry_name}' entry.")
