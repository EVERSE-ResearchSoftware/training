import yaml
import subprocess
from pathlib import Path

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def main():
    config_path = Path("src/config.yaml")
    output_dir = Path("csv")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    spreadsheet_id = config['id']
    spreadsheet_entries = config['spreadsheet']

    for s in spreadsheet_entries:
        name = s['name']
        gid = s['gid']
        if name == "id":
            continue

        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?gid={gid}&exportFormat=csv"
        output_file = output_dir / f"{name}.csv"
        print(f"{bcolors.OKBLUE}[INFO]{bcolors.ENDC} Fetching '{name}' from gid {gid}...")

        try:
            result = subprocess.run(["curl", "-L", url, "-o", str(output_file)], check=True, capture_output=True)
            print(f"{bcolors.OKGREEN}[SUCCESS]{bcolors.ENDC} Saved to {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"{bcolors.FAIL}[FAILED]{bcolors.ENDC} Could not download '{name}'")
            print(f"{bcolors.WARNING}URL:{bcolors.ENDC} {url}")
            print(f"{bcolors.WARNING}Curl stderr:{bcolors.ENDC} {e.stderr.decode().strip()}")

if __name__ == "__main__":
    main()