import math
import re
from datetime import datetime


RECORD_KEYS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
}
ALLOWED_KEYS = RECORD_KEYS | {
    "min_price",
    "sort_by",
    "order",
    "limit",
}
DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


def _valid_datetime(value):
    if not isinstance(value, str) or not DATETIME_PATTERN.fullmatch(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False


def _valid_query(query):
    if not isinstance(query, dict):
        return False

    if any(key not in ALLOWED_KEYS for key in query):
        return False

    for key in ("flight_id", "origin", "destination"):
        if key in query and not isinstance(query[key], str):
            return False

    for key in ("departure_datetime", "arrival_datetime"):
        if key in query and not _valid_datetime(query[key]):
            return False

    for key in ("price", "min_price"):
        if key in query:
            value = query[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False
            if not math.isfinite(value):
                return False

    if "sort_by" in query:
        if not isinstance(query["sort_by"], str) or query["sort_by"] not in RECORD_KEYS:
            return False

    if "order" in query:
        if query["order"] not in ("asc", "desc") or not isinstance(query["order"], str):
            return False
        if "sort_by" not in query:
            return False

    if "limit" in query:
        limit = query["limit"]
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            return False

    return True


def run_query(db: list[dict], query: dict) -> dict:
    if not _valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = []
    for flight in db:
        if "flight_id" in query and flight["flight_id"] != query["flight_id"]:
            continue
        if "origin" in query and flight["origin"] != query["origin"]:
            continue
        if "destination" in query and flight["destination"] != query["destination"]:
            continue
        if "departure_datetime" in query and flight["departure_datetime"] < query["departure_datetime"]:
            continue
        if "arrival_datetime" in query and flight["arrival_datetime"] > query["arrival_datetime"]:
            continue
        if "price" in query and flight["price"] > query["price"]:
            continue
        if "min_price" in query and flight["price"] < query["min_price"]:
            continue
        matches.append(flight)

    if "sort_by" in query:
        matches = sorted(
            matches,
            key=lambda flight: flight[query["sort_by"]],
            reverse=query.get("order", "asc") == "desc",
        )

    if "limit" in query:
        matches = matches[:query["limit"]]

    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    if isinstance(queries, dict):
        queries = [queries]
    if not isinstance(queries, list):
        raise ValueError("Queries must be an object or an array")
    return [run_query(db, query) for query in queries]
