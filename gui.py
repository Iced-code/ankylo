import sys
from PySide6.QtWidgets import QApplication, QWidget, QListWidget, QVBoxLayout, QHBoxLayout, QInputDialog, QPushButton, QLabel, QFrame, QMessageBox, QLineEdit
from PySide6.QtCore import Qt

from backend.commands import create_vault, unlock_vault, save_vault, add_entry, list_entries, get_entry, get_entry_index, delete_entry, delete_entry_index, gen_message
# import backend.commands_api # import create_vault, unlock_vault, save_vault, add_entry, list_entries, get_entry, delete_entry

from backend.storage import load_vault_file, vault_exists, b64d
from backend.crypto import derive_key, decrypt_data

import json

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

SESSION = {
    "key": None,
    "vault": None
}


def refresh_list():
    list_widget.clear()
    for entry in SESSION["vault"]["entries"]:
        list_widget.addItem(entry["name"])

def login():
    if not vault_exists():
        print("Vault not initialized.")
        return None, None
    
    vault_data = load_vault_file()

    if vault_data is None:
        print("Failed to load vault.")
        return None, None
    

    window = QWidget()
    window.setWindowTitle("Ankylo")
    window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
    window.show()
    password, ok = QInputDialog.getText(window, "Login", "Enter password:")
    if not ok or not password:
        return
    
    key, vault, message = unlock_vault(password=password)
    SESSION["key"] = key
    SESSION["vault"] = vault

def add():
    name, ok = QInputDialog.getText(window, "Add Entry", "Enter name:")
    if not ok or not name:
        return
    
    api_key, ok = QInputDialog.getText(window, "API Key", "Enter API key:")
    if not ok or not api_key:
        return

    entry_index = -1
    for index, entry in enumerate(SESSION["vault"]["entries"]):
        if entry["name"] == name:
            confirm, ok = QInputDialog.getText(window, "API Key", "Entry already exists. Replace key for this entry? (Y/N):")
            if not confirm or not ok:
                return
            elif confirm and confirm.upper() == "Y":
                entry_index = index
                break

    add_entry(name=name, api_key=api_key, key=SESSION["key"], vault=SESSION["vault"], entry_index=entry_index)
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
    
    delete_entry(name=name, key=SESSION["key"], vault=SESSION["vault"])
    refresh_list()



print("Running Ankylo...")

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Ankylo")
window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

with open("./styles.qss", 'r') as styleFile:
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

login()
if not SESSION["key"]:
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





