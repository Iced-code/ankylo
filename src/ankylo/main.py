from datetime import datetime
from pathlib import Path
from ankylo.backend.commands import create_vault, unlock_vault, save_vault, add_entry, list_entries, get_entry, get_entry_index, delete_entry, delete_entry_index, gen_message
import typer
from typing import Optional


app = typer.Typer()

VERSION = "ankylo-v1.0"

def success(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.GREEN, bold=True)

def error(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.RED, bold=True)

def info(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.YELLOW, bold=True)
def detail(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.BRIGHT_BLUE, bold=True)


BASE_DIR = Path.home() / ".ankylo"
LOGSFILE = BASE_DIR / "./logs/logs.txt"

def log_outputs(logsFilePath: Path, message: str):
    logsFilePath.parent.mkdir(parents=True, exist_ok=True)

    with open(logsFilePath, "a") as logFile:
        now = datetime.now()
        logFile.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}]:{message.replace('\n', ' ').strip()}\n")

def output_message(message_protocol: dict):
    status:str = message_protocol["status"]
    message:str = message_protocol["message"]

    if status == "OK":
        success(msg=message)
    elif status == "ERROR": 
        error(msg=message)
    else:
        info(msg=message)

    log_outputs(logsFilePath=LOGSFILE, message=message)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show current version.")
):
    if version:
        typer.echo(VERSION)
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        detail(msg="\nankylo - Secure API Key Vault")
        typer.echo(ctx.get_help())
        info(msg="Examples:")
        typer.echo("""  ankylo init\n  ankylo add github\n  ankylo get -n github --show""")
        raise typer.Exit()

@app.command("init", help="Create the vault.")
def initialize_vault():
    result = create_vault()
    output_message(result)

@app.command("add", help="Add an entry to the vault.")
def add_entry_to_vault(
    name: str = typer.Option(None, "--name", "-n", help="Name of entry to add."),
):
    result = add_entry(name=name)
    output_message(result)

@app.command("list", help="List all entries in the vault")
def list_vault_entries(
    show: bool = typer.Option(False, "--show", help="Display all entries' secret key.")
):
    result = list_entries(show=show)
    if result["result"]:
        print("")
        for index, entry in result["result"].items():
            if type(entry) is tuple:
                detail(f'[{index}] - {entry[0]}: {entry[1]}')
            else:
                detail(f'[{index}] - {entry}')
    output_message(result)

@app.command("get", help="Get an entry from the vault.")
def get_vault_entry(
    name: Optional[str] = typer.Option(None, "--name", "-n", help='Name of entry to get.'),
    index: Optional[int] = typer.Option(None, "--index", "-i", help='Index of entry to get.'),
    show: bool = typer.Option(False, "--show", help="Display the entry's secret key.")
):
    if (name and index) or (name is None and index is None):
        result = gen_message(status="ERROR", message="Must provide either --name or --index")
    elif name:
        result = get_entry(name=name, show=show)
    elif index is not None:
        result = get_entry_index(index=index, show=show)
    
    if result["result"]:
        print("")
        for name, api_key in result["result"].items():
            detail(f'[{name}] - {api_key}')
    output_message(result)

@app.command("delete", help="Delete an entry from the vault.")
def delete_vault_entry(
    name: Optional[str] = typer.Option(None, "--name", "-n", help='Name of entry to delete.'),
    index: Optional[int] = typer.Option(None, "--index", "-i", help='Index of entry to delete'),
):
    if (name and index) or (name is None and index is None):
        result = gen_message(status="ERROR", message="Must provide either --name or --index")
    elif name:
        result = delete_entry(name=name)
    elif index is not None:
        result = delete_entry_index(index=index)
        
    output_message(result)

def main():
    app()

if __name__ == "__main__":
    main()