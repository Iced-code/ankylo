from flask import Flask, request, jsonify, render_template
from backend.commands import create_vault, unlock_vault, save_vault, add_entry, list_entries, get_entry, delete_entry

#from backend.commands_api import create_vault, unlock_vault, save_vault, add_entry, list_entries, get_entry, delete_entry

SESSION = {
    "key": None,
    "vault": None
}

app = Flask(__name__)

@app.route("/")
def check():
    print("HELLO!")
    return render_template("index.html")

@app.route("/unlock", methods=["POST"])
def unlock():
    data = request.get_json()
    password = data.get("password")

    key, vault, message = unlock_vault(password=password)

    if not key:
        print("Invalid password")
        return jsonify({
            "ERROR": "Invalid password"
        }), 401

    SESSION["key"] = key
    SESSION["vault"] = vault

    print(f'{SESSION["key"]}')

    return jsonify({
            "status": "OK"
        }), 200

@app.route("/entries", methods=["GET"])
def listEntries():
    if SESSION["vault"]:
        return jsonify(SESSION["vault"]["entries"])
    
    return jsonify({"ERROR": "Vault not found"}), 404

@app.route("/add", methods=["POST"])
def add():
    data = request.get_json()
    name = data.get("name")
    api_key = data.get("api_key")

    add_entry(name=name, api_key=api_key, key=SESSION["key"], vault=SESSION["vault"]) 
    print("output!!")   
    return jsonify({
        "status": "ok"
    })

@app.route("/get/<entry_name>", methods=["GET"])
def getEntry(entry_name):
    if SESSION["vault"]:
        data = request.get_json()
        entry_name = data.get("name")

        get_entry(name=entry_name, key=SESSION["key"], vault=SESSION["vault"])
    
    return jsonify({
        "entry": entry_name,
        "status":"OK"
        }), 200

if __name__ == "__main__":
    app.run(debug=True)