import argparse
from datetime import datetime
from pathlib import Path
from backend.commands import create_vault, unlock_vault, save_vault, add_entry, list_entries, get_entry, get_entry_index, delete_entry, delete_entry_index


def main():
    parser = argparse.ArgumentParser(description="ankylo - Secure API Key Vault")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Create vault")
    subparsers.add_parser("list", help="List all entries in vualt")

    add_parser = subparsers.add_parser("add", help="Add an entry")
    add_parser.add_argument("-n", "--name", type=str, required=True, help='Name of entry to add')

    common_parser = argparse.ArgumentParser(add_help=False)
    group = common_parser.add_mutually_exclusive_group()
    group.add_argument("-n", "--name", type=str, help='Name of entry to delete')
    group.add_argument("-i", "--index", type=str, help='Index of entry to delete')

    del_parser = subparsers.add_parser("delete", parents=[common_parser], help="Delete an entry")
    get_parser = subparsers.add_parser("get", parents=[common_parser], help="Get an entry")

    args = parser.parse_args()

    logsFilePath = "./logs/logs.txt"
    logs_path = Path(logsFilePath)
    logs_path.parent.mkdir(parents=True, exist_ok=True)

    output = ""

    if args.command == "init":
        result = create_vault()
        output = "Created vault."
    elif args.command == "add":
        result = add_entry(args.name)
        output = result["message"]
    elif args.command == "list":
        result = list_entries()
        output = f'Listed all vault contents.'
    elif args.command == "get":
        if args.name:
            result = get_entry(args.name)
        else:
            result = get_entry_index(args.index)
        output = result["message"]
    elif args.command == "delete":
        if args.name:
            result = delete_entry(args.name)
        else:
            result = delete_entry_index(args.index)
        output = f'Deleted "{args.name}" from vault.'
    else:
        parser.print_help()

    print(output)
    with open(logsFilePath, "a") as logFile:
        if output.strip() != "":
            now = datetime.now()
            logFile.write(f"[{now.strftime("%Y-%m-%d %H:%M:%S")}]: {output}\n")


if __name__ == "__main__":
    main()