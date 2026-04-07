from datetime import datetime
from pathlib import Path
from ankylo.backend.commands import create_vault, add_entry, list_entries, get_entry, get_entry_index, delete_entry, delete_entry_index, gen_message, add_entries_from_file, delete_vault, export_entry, export_entries_file
from ankylo.backend.storage import BASE_DIR
import typer
from typing import Optional, List

# Developed by Ayaan Modak (GitHub: Iced-code)

app = typer.Typer()

VERSION = "ankylo-v1.1"

def success(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.GREEN, bold=True)

def error(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.RED, bold=True)

def info(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.YELLOW, bold=True)
def detail(msg: str):
    typer.secho(f"{msg}", fg=typer.colors.BRIGHT_BLUE, bold=True)


# BASE_DIR = Path.home() / "ankylo"
LOGSFILE = BASE_DIR / "logs" / "logs.txt"

def log_outputs(logsFilePath: Path, message: str):
    logsFilePath.parent.mkdir(parents=True, exist_ok=True)

    with open(logsFilePath, "a") as logFile:
        now = datetime.now()
        logFile.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}]: {message.replace('\n', ' ').strip()}\n")

def output_message(message_protocol: dict):
    status:str = message_protocol["status"]
    message:str = message_protocol["message"]

    if status == "OK":
        success(msg=message)
    elif status == "ERROR": 
        error(msg=message)
    else:
        info(msg=message)

    if message_protocol["log_action"]:
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
        detail(msg="\nankylo - Secure key vault right in your terminal.")
        typer.echo(ctx.get_help())
        info(msg="Examples:")
        typer.echo("""  ankylo init\n  ankylo add openai\n  ankylo get openai --show""")
        raise typer.Exit()

@app.command("init", help="Create the vault.")
def initialize_vault():
    result = create_vault()
    output_message(result)

@app.command("add", help="Add an entry to the vault.")
def add_entry_to_vault(
    name: Optional[str] = typer.Argument(None, help="Name of entry to add."),
    file: Optional[str] = typer.Option(None, "-in", help="File path for the content to add."),
):
    if (name and file) or (name is None and file is None):
        result = gen_message(status="ERROR", message="Must provide either <name> or -in <file_path>", log_action=False)
    elif name:
        result = add_entry(name=name)
    elif file is not None:
        result = add_entries_from_file(file_path=file)
    
    output_message(result)

@app.command("list", help="List all entries in the vault.")
def list_vault_entries(
    show: bool = typer.Option(False, "--show", help="Display all entries' secret key."),
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
    name: Optional[str] = typer.Argument(None, help='Name of entry to get.'),
    index: Optional[int] = typer.Option(None, "--index", "-i", help='Index of entry to get.'),
    show: bool = typer.Option(False, "--show", help="Display the entry's secret key.")
):
    if (name and index) or (name is None and index is None):
        result = gen_message(status="ERROR", message="Must provide either <name> or --index <entry_index>", log_action=False)
    elif name:
        result = get_entry(name=name, show=show)
    elif index is not None:
        result = get_entry_index(index=index, show=show)
    
    if result["result"]:
        print("")
        detail(f'- {result["result"]["name"]}: {result["result"]["key"]} (created: {result["result"]["timestamp"]})')

    output_message(result)

@app.command("export", help="Export entries to a file.")
def export_vault_entries(
    outputFile: str = typer.Option(None, "-out", help="File to write entries and their keys to."),
    names: Optional[List[str]] = typer.Argument(None, help='Names of entries to export.'),
    indices: Optional[List[int]] = typer.Option(None, "--index", "-i", help='Indices of entries to export.'),
    all_entries: Optional[str] = typer.Argument(None, help='Use "." to export all entries.'),
):
    if not outputFile:
        result = gen_message(status="ERROR", message="Must provide -out", log_action=False)        
    elif all_entries == '.':
        result = export_entries_file(outputFile=outputFile, names=None)
    elif names and indices:
        result = gen_message(status="ERROR", message="Must provide either <name> or --index <index>", log_action=False)
    elif names:
        result = export_entries_file(outputFile=outputFile, names=names)
    elif indices:
        result = export_entries_file(outputFile=outputFile, indices=indices)
    else:
        result = gen_message(status="ERROR", message="Must provide <name> or '.'", log_action=False)

    output_message(result)

@app.command("delete", help="Delete an entry from the vault.")
def delete_vault_entry(
    name: Optional[str] = typer.Argument(None, help='Name of entry to delete.'),
    index: Optional[int] = typer.Option(None, "--index", "-i", help='Index of entry to delete'),
):
    if (name and index) or (name is None and index is None):
        result = gen_message(status="ERROR", message="Must provide either <name> or --index <index>", log_action=False)
    elif name:
        result = delete_entry(name=name)
    elif index is not None:
        result = delete_entry_index(index=index)
        
    output_message(result)

@app.command("delete-vault", help="Permanently delete the vault and all contents.")
def delete_entire_vault():
    error("\nThis will permanently delete your vault and ALL stored keys. This cannot be undone.")

    confirm = typer.confirm("Are you sure you want to delete your vault? ")
    if not confirm:
        info("Vault was not deleted.")
        raise typer.Exit()
    
    result = delete_vault()
    output_message(result)

@app.command("env", help="Export an entry as an environment variable.")
def export_entry_env(
    name: Optional[str] = typer.Argument(None, help='Name of entry to export.'),
    shell: Optional[str] = typer.Option("bash", "--shell", "-s", help='Shell format: bash, powershell, cmd')
):
    if name is None:
        result = gen_message(status="ERROR", message="Must provide <name>", log_action=False)
    elif name:
        result = export_entry(name=name, shell=shell)
    
    if result["result"]:
        detail(f"{result["result"]["env_var"]}")

    if result["status"] == "OK":
        log_outputs(logsFilePath=LOGSFILE, message=result["message"])
    else:
        output_message(result)


def main():
    app()

if __name__ == "__main__":
    main()