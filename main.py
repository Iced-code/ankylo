import argparse
from datetime import datetime
from pathlib import Path
from backend.commands import create_vault, unlock_vault, save_vault, add_entry, list_entries, get_entry, get_entry_index, delete_entry, delete_entry_index, gen_message
import typer
from typing import Optional

def success(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.GREEN, bold=True)

def error(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.RED, bold=True)

def info(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.YELLOW, bold=True)


LOGSFILE = Path("./logs/logs.txt")
def log_outputs(logsFilePath: Path, message):
    logsFilePath.parent.mkdir(parents=True, exist_ok=True)

    with open(logsFilePath, "a") as logFile:
        now = datetime.now()
        logFile.write(f"[{now.strftime("%Y-%m-%d %H:%M:%S")}]:{message.replace("\n", " ")}\n")

def output_message(message_protocol: dict):
    if message_protocol["status"] == "OK":
        success(message_protocol["message"])
    elif message_protocol["status"] == "ERROR": 
        error(message_protocol["message"])
    else:
        info(message_protocol["message"])

    log_outputs(logsFilePath=LOGSFILE, message=message_protocol["message"])


app = typer.Typer(help="ankylo - Secure API Key Vault")

@app.command("init")
def initialize_vault():
    result = create_vault()
    output_message(result)

@app.command("add")
def add_entry_to_vault(name:str):
    result = add_entry(name=name)
    output_message(result)

@app.command("list")
def list_vault_entries():
    result = list_entries()
    output_message(result)

@app.command("get")
def get_vault_entry(name:str=None, index:int=None):
    if (name and index) or not(name or (index != None)):
        result = gen_message(status="ERROR", message="Must provide either --name or --index")
    elif name:
        result = get_entry(name=name)
    elif index != None:
        result = get_entry_index(index=index)
        
    output_message(result)

@app.command("delete")
def delete_vault_entry(name:str=None, index:int=None):
    if (name and index) or not(name or (index != None)):
        result = gen_message(status="ERROR", message="Must provide either --name or --index")
    elif name:
        result = delete_entry(name=name)
    elif index != None:
        result = delete_entry_index(index=index)
        
    output_message(result)

def parsing():
    parser = argparse.ArgumentParser(description="ankylo - Secure API Key Vault")
    subparsers = parser.add_subparsers(dest="command", help="Use the following commands to interface with your keys.")

    subparsers.add_parser("init", help="Create vault")
    subparsers.add_parser("list", help="List all entries in vualt")

    common_parser = argparse.ArgumentParser(add_help=False)
    group = common_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", "--name", type=str, help='Name of entry to add')
    group.add_argument("-f", "--file", type=str, help='File path of keys to add')
    
    add_parser = subparsers.add_parser("add", parents=[common_parser], help="Add an entry")
    
    common_parser2 = argparse.ArgumentParser(add_help=False)
    group = common_parser2.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", "--name", type=str, help='Name of entry to delete')
    group.add_argument("-i", "--index", type=str, help='Index of entry to delete')

    del_parser = subparsers.add_parser("delete", parents=[common_parser2], help="Delete an entry")
    # del_parser.add_argument("-r", "--recursive", type=bool, required=False, help='Recursively delete all of entries')

    get_parser = subparsers.add_parser("get", parents=[common_parser2], help="Get an entry")

    args = parser.parse_args()

    if args.command == "init":
        initialize_vault()
    elif args.command == "add":
        add_entry_to_vault(args.name)
    elif args.command == "list":
        list_vault_entries()
    elif args.command == "get":
        if args.name:
            get_vault_entry(name=args.name)
        elif args.index:
            get_vault_entry(index=(int)(args.index))
    elif args.command == "delete":
        if args.name:
            delete_vault_entry(name=args.name)
        elif args.index:
            delete_vault_entry(index=(int)(args.index))
    else:
        parser.print_help()

if __name__ == "__main__":
    parsing()