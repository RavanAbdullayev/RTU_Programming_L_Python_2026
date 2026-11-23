import csv
import os

from validator import validate_row, to_record


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    records = []
    errors = []
    seen = set()

    for path in paths:
        with open(path, "r", encoding="utf-8", newline="") as file:
            for line_number, raw_line in enumerate(file, start=1):
                if line_number == 1:
                    continue
                if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                    continue

                try:
                    fields = next(csv.reader([raw_line]))
                except csv.Error:
                    fields = []

                stripped_fields = [field.strip() for field in fields]
                error_code = validate_row(stripped_fields, airports)

                if error_code is None:
                    record = to_record(stripped_fields)
                    duplicate_key = (
                        record["flight_id"],
                        record["departure_datetime"],
                    )
                    if duplicate_key in seen:
                        error_code = "DUPLICATE_FLIGHT"
                    else:
                        seen.add(duplicate_key)
                        records.append(record)

                if error_code is not None:
                    errors.append(
                        f"{os.path.basename(path)}:{line_number}: "
                        f"{error_code} | {raw_line.rstrip(chr(13) + chr(10))}"
                    )

    return records, errors
