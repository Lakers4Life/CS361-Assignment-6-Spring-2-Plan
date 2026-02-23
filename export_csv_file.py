# Microservice Functionality to Export a CSV File
import csv
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

REQUEST_FILE = Path("request.csv")
EXPORT_DIR = Path("exports")
POLL_SECONDS = 1.0

# These columns are what the microservice expects request.csv to have.
REQUEST_COLUMNS = [
    "status",
    "request_id",
    "client",
    "action",
    "params",
    "created_at",
    "output_file",
    "error",
]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_request_file_header() -> None:
    """Create request.csv with header if it doesn't exist or is empty."""
    if not REQUEST_FILE.exists() or REQUEST_FILE.stat().st_size == 0:
        REQUEST_FILE.write_text(",".join(REQUEST_COLUMNS) + "\n", encoding="utf-8")


def read_requests() -> List[Dict[str, str]]:
    with REQUEST_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # If the file has a different header, this will still read,
        return list(reader)


def write_requests(rows: List[Dict[str, str]]) -> None:
    """Atomic-ish write: write temp then replace."""
    tmp = REQUEST_FILE.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUEST_COLUMNS)
        writer.writeheader()
        for r in rows:
            # Ensure all expected keys exist
            out = {k: r.get(k, "") for k in REQUEST_COLUMNS}
            writer.writerow(out)
    tmp.replace(REQUEST_FILE)


def safe_parse_params(params_str: str) -> Dict[str, Any]:
    """
    params is stored as JSON in a single CSV cell.
    """
    if not params_str.strip():
        return {}
    try:
        return json.loads(params_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"params is not valid JSON: {e}")


def load_input_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Loads input data to export.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"input_file not found: {input_path}")

    text = input_path.read_text(encoding="utf-8")
    data = json.loads(text)

    if isinstance(data, list):
        # list of dict rows
        if not all(isinstance(x, dict) for x in data):
            raise ValueError("input_file JSON list must contain objects (dicts).")
        return data

    if isinstance(data, dict):
        rows = data.get("rows")
        if isinstance(rows, list) and all(isinstance(x, dict) for x in rows):
            return rows

    raise ValueError(
        "Unsupported input JSON format. Use a list of objects or {\"rows\": [...]}."
    )


def export_rows_to_csv(rows: List[Dict[str, Any]], columns: List[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in rows:
            # Write missing columns as blank
            writer.writerow({c: r.get(c, "") for c in columns})


def process_one_request(row: Dict[str, str]) -> Dict[str, str]:
    """
    Processes a single request row.
    Returns an updated row dict.
    """
    params = safe_parse_params(row.get("params", ""))

    input_file = params.get("input_file")
    if not input_file:
        raise ValueError("params must include 'input_file'.")

    columns = params.get("columns")

    output_file = params.get("output_file")

    input_path = Path(input_file)

    # Load data (JSON)
    rows_data = load_input_data(input_path)

    if not rows_data:
        raise ValueError("input_file contained zero rows to export.")

    if not columns:
        # Infer columns from first row
        columns = list(rows_data[0].keys())
        if not columns:
            raise ValueError("Could not infer columns (first row has no keys).")

    if not isinstance(columns, list) or not all(isinstance(c, str) for c in columns):
        raise ValueError("params['columns'] must be a list of strings if provided.")

    if not output_file:
        EXPORT_DIR.mkdir(exist_ok=True)
        output_file = str(EXPORT_DIR / f"{row.get('client','client')}_{row.get('request_id','req')}.csv")

    output_path = Path(output_file)

    export_rows_to_csv(rows_data, columns, output_path)

    # success
    row["status"] = "done"
    row["output_file"] = str(output_path)
    row["error"] = ""
    return row


def run_microservice() -> None:
    ensure_request_file_header()
    EXPORT_DIR.mkdir(exist_ok=True)

    print("CSV Export Microservice running.")
    print(f"- Watching: {REQUEST_FILE.resolve()}")
    print(f"- Export dir: {EXPORT_DIR.resolve()}")
    print(f"- Poll interval: {POLL_SECONDS}s\n")

    while True:
        rows = read_requests()

        # Find the first pending request
        idx = next((i for i, r in enumerate(rows) if r.get("status") == "request"), None)

        if idx is None:
            time.sleep(POLL_SECONDS)
            continue

        rows[idx]["status"] = "processing"
        rows[idx]["error"] = ""
        write_requests(rows)

        # Process
        try:
            updated = process_one_request(rows[idx])
            rows[idx] = updated
        except Exception as e:
            rows[idx]["status"] = "error"
            rows[idx]["error"] = str(e)
        finally:
            write_requests(rows)

        time.sleep(0.1)


if __name__ == "__main__":
    run_microservice()