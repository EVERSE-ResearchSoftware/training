import csv
import yaml
import json
from pathlib import Path

# Colors
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
    input_dir = Path('csv')
    output_dir = Path('json')
    output_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = Path('src/config.yaml')

    with open(mapping_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    spreadsheet_entries = config['spreadsheet']

    # It will not convert the `spreadsheet.name` where `spreadsheet.skip == True`
    skip = []
    for e in spreadsheet_entries:
        if e['skip'] is True:
            skip.append(e['name'])

    mapping_list = config['mapping']
    mapping = {item['tess']: item['schema'] for item in mapping_list}

    # For each csv in "./<input_dir>", for each row, it changes it as a json objet
    for csv_file in input_dir.glob('*.csv'):
        name = str(csv_file).removeprefix('csv/').removesuffix('.csv')
        if name in skip:
            continue

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            mapped_fields = [k for k in mapping if k in reader.fieldnames]
            materials = []

            for row in reader:
                resource = {
                    '@context': 'http://schema.org',
                    '@type': next(
                        (entry.get("schemaType") for entry in spreadsheet_entries if entry.get("name") == name),
                        None
                        )
                }
                for src_key in mapped_fields:
                    dst_key = mapping[src_key]
                    value = row.get(src_key, '').strip()
                    if value:
                        resource[dst_key] = value
                materials.append(resource)

        output_path = output_dir / f'{csv_file.stem}.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(materials, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()
