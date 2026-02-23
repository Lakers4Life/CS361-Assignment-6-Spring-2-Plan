import csv
import json
import time
import uuid
from pathlib import Path
from datetime import datetime

REQUEST_FILE = Path("request.csv")
EXPORT_DIR = Path("exports")

FIELDS = [
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


def ensure_request_csv_header() -> None:
    if not REQUEST_FILE.exists() or REQUEST_FILE.stat().st_size == 0:
        with REQUEST_FILE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(FIELDS)


def read_all_rows() -> list[dict]:
    with REQUEST_FILE.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)


def find_row_by_request_id(rows: list[dict], request_id: str) -> dict | None:
    for row in rows:
        if row.get("request_id") == request_id:
            return row
    return None


def append_request_row(client: str, params: dict, action: str = "export_csv") -> str:
    ensure_request_csv_header()

    request_id = str(uuid.uuid4())
    row = {
        "status": "request",
        "request_id": request_id,
        "client": client,
        "action": action,
        "params": json.dumps(params),
        "created_at": now_iso(),
        "output_file": "",
        "error": "",
    }

    with REQUEST_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writerow(row)

    return request_id


def wait_for_response(request_id: str, timeout_seconds: int = 30, poll_seconds: float = 0.5) -> dict:
    start = time.time()
    while time.time() - start < timeout_seconds:
        rows = read_all_rows()
        row = find_row_by_request_id(rows, request_id)
        if row is None:
            time.sleep(poll_seconds)
            continue

        status = (row.get("status") or "").strip().lower()

        if status in ("done", "error"):
            return row

        time.sleep(poll_seconds)

    raise TimeoutError(f"Timed out waiting for request_id={request_id} after {timeout_seconds}s")


def preview_csv(csv_path: Path, max_lines: int = 6) -> None:
    if not csv_path.exists():
        print(f"\n❌ Exported CSV not found at: {csv_path}")
        return

    print(f"\n✅ CSV created at: {csv_path}")
    print("----- CSV preview -----")
    with csv_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            print(line.rstrip("\n"))
            if i + 1 >= max_lines:
                break
    print("-----------------------")


def main() -> None:
    EXPORT_DIR.mkdir(exist_ok=True)
    input_json = Path("amc_export_data.json")
    sample_rows = [
        {"title": "Interstellar", "date": "2026-02-21", "format": "IMAX"},
        {"title": "Dune", "date": "2026-02-20", "format": "Dolby"},
    ]
    input_json.write_text(json.dumps(sample_rows, indent=2), encoding="utf-8")
    print(f"Created sample input data: {input_json}")

    params = {
        "input_file": str(input_json),
        "columns": ["title", "date", "format"],
    }

    request_id = append_request_row(client="AMC_Movies", params=params)
    print(f"\n➡️  Sent export request. request_id={request_id}")

    print("⏳ Waiting for microservice response...")
    row = wait_for_response(request_id=request_id, timeout_seconds=30, poll_seconds=0.5)

    status = row.get("status", "")
    if status.lower() == "error":
        print("\n❌ Microservice returned ERROR")
        print(f"request_id={request_id}")
        print(f"error={row.get('error')}")
        return

    output_file = row.get("output_file", "").strip()
    if not output_file:
        print("\n❌ Microservice returned done but no output_file was provided in the row.")
        print("Check your microservice write-back logic.")
        return

    preview_csv(Path(output_file))


if __name__ == "__main__":
    main()