import sys
from PySide6.QtWidgets import QApplication, QWidget, QListWidget, QVBoxLayout, QHBoxLayout, QInputDialog, QPushButton, QLabel, QFrame, QMessageBox, QLineEdit
from PySide6.QtCore import Qt

import backend
from backend.commands import create_vault, unlock_vault, save_vault, add_entry, list_entries, get_entry, delete_entry
from backend.storage import load_vault_file, vault_exists, b64d
from backend.crypto import derive_key, decrypt_data

import json

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

def main():
    def refresh_list():
        list_widget.clear()
        for entry in vault["entries"]:
            list_widget.addItem(entry["name"])

    def add():
        name, ok = QInputDialog.getText(window, "Add Entry", "Enter name:")
        if not ok or not name:
            return
        
        api_key, ok = QInputDialog.getText(window, "API Key", "Enter API key:")
        if not ok or not api_key:
            return
            
        entry_index = None
        for index, entry in enumerate(vault["entries"]):
            if entry["name"] == name:
                confirm, ok = QInputDialog.getText(window, "API Key", "Entry already exists. Replace key for this entry? (Y/N):")
                if not confirm or not ok:
                    return
                elif confirm and confirm.upper() == "Y":
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

        refresh_list()

    def delete():
        name, ok = QInputDialog.getText(window, "Delete Entry", "Enter name:")
        if not ok or not name:
            return
        
        confirm, ok = QInputDialog.getText(window, "Delete Entry", "Are you sure you want to delete this entry? (Y/N):")
        if not ok or not confirm:
            return
        elif confirm and confirm.upper() != "Y":
            return
        
        vault["entries"] = [e for e in vault["entries"] if e["name"] != name]

        original_data = load_vault_file()
        save_vault(key=key, vault_dict=vault, original_data=original_data)

        refresh_list()

    def login():
        if not vault_exists():
            print("Vault not initialized.")
            return None, None
        
        vault_data = load_vault_file()

        if vault_data is None:
            print("Failed to load vault.")
            return None, None
        
        password, ok = QInputDialog.getText(window, "Login", "Enter password:")
        if not ok or not password:
            return

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


    print("Running Ankylo...")

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Ankylo")
    window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

    with open("./templates/styles.qss", 'r') as styleFile:
        app.setStyleSheet(styleFile.read())

    overlay = QFrame(window)
    overlay.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    overlay.setStyleSheet("background-color: rgba(0, 0, 0, 120);")
    overlay.lower()

    main_layout = QVBoxLayout(window)

    container = QWidget()
    container.setObjectName("container")

    layout = QVBoxLayout(container)

    label = QLabel("Ankylo")
    label.setAlignment(Qt.AlignLeft)

    key, vault = login()
    if not key:
        sys.exit()

    button_layout = QHBoxLayout()
    button_layout.setObjectName("button_layout")

    button = QPushButton("Add")
    button.clicked.connect(add)
    button_layout.addWidget(button)

    button1 = QPushButton("Delete")
    button1.clicked.connect(delete)
    button_layout.addWidget(button1)

    layout.addLayout(button_layout)

    list_widget = QListWidget()
    layout.addWidget(list_widget)

    main_layout.addWidget(container)
    refresh_list()

    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()





