import csv
import json
import urllib.error
import urllib.request
from pathlib import Path

API_BASE_URL = "https://everse-training.app.cern.ch/materials.json_api"
PER_PAGE = 100
REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "csv" / "keywords.csv"
COLUMN_NAME = "Keywords"


def load_existing_keywords(csv_path: Path) -> dict[str, str]:
    """
    Reads existing keywords from the CSV file.
    Returns a dict mapping `normalized_lowercase_keyword -> original_cased_keyword`
    to preserve existing casing while preventing case-insensitive duplicates.
    """
    existing: dict[str, str] = {}
    if not csv_path.exists():
        raise FileNotFoundError(f"Could not find target file at: {csv_path}")

    with csv_path.open(mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or COLUMN_NAME not in reader.fieldnames:
            raise ValueError(
                f"Expected column '{COLUMN_NAME}' in {csv_path}, found: {reader.fieldnames}"
            )

        for row in reader:
            raw_val = (row.get(COLUMN_NAME) or "").strip()
            if raw_val:
                norm_key = raw_val.lower()
                if norm_key not in existing:
                    existing[norm_key] = raw_val

    return existing


def fetch_api_keywords(base_url: str, per_page: int) -> dict[str, str]:
    """
    Paginates through the API from page 1 until the returned list is empty.
    Supports both JSON:API (`{"data": [...]}`) and flat list (`[...]`) payloads.
    """
    fetched: dict[str, str] = {}
    page = 1

    while True:
        url = f"{base_url}?per_page={per_page}&page={page}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "everse-keywords-sync"},
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to fetch page {page} from {url}: {e}") from e

        # Handle both `{"data": [...]}` and top-level `[...]` responses
        if isinstance(payload, dict):
            items = payload.get("data", [])
        elif isinstance(payload, list):
            items = payload
        else:
            raise ValueError(f"Unexpected JSON root type on page {page}: {type(payload)}")

        if not items:
            break

        for item in items:
            if not isinstance(item, dict):
                continue

            # Support keywords nested under `attributes` or directly on the item
            attributes = item.get("attributes")
            if isinstance(attributes, dict) and "keywords" in attributes:
                keywords = attributes.get("keywords") or []
            else:
                keywords = item.get("keywords") or []

            for kw in keywords:
                if not isinstance(kw, str):
                    continue
                cleaned = kw.strip()
                if not cleaned:
                    continue

                norm_key = cleaned.lower()
                if norm_key not in fetched:
                    fetched[norm_key] = norm_key

        page += 1

    return fetched


def save_keywords(csv_path: Path, keywords_map: dict[str, str]) -> None:
    """
    Writes the merged keywords sorted alphabetically (case-insensitive) back to the CSV.
    """
    sorted_keywords = sorted(keywords_map.values(), key=lambda s: s.lower())

    with csv_path.open(mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[COLUMN_NAME])
        writer.writeheader()
        for kw in sorted_keywords:
            writer.writerow({COLUMN_NAME: kw})


def main() -> None:
    existing_keywords = load_existing_keywords(CSV_PATH)
    api_keywords = fetch_api_keywords(API_BASE_URL, PER_PAGE)

    merged_keywords = {**api_keywords, **existing_keywords}
    added_count = len(merged_keywords) - len(existing_keywords)

    save_keywords(CSV_PATH, merged_keywords)
    print(
        f"Sync complete. Existing: {len(existing_keywords)}, "
        f"Added: {added_count}, Total: {len(merged_keywords)}."
    )


if __name__ == "__main__":
    main()