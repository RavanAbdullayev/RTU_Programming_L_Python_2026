import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "251ADB100"
FIRST_NAME = "Ravan"
LAST_NAME = "Abdullayev"


def _build_parser():
    parser = argparse.ArgumentParser()

    source = parser.add_mutually_exclusive_group()
    source.add_argument("-i", metavar="FILE")
    source.add_argument("-d", metavar="FOLDER")
    source.add_argument("-j", metavar="FILE")

    parser.add_argument("-a", metavar="FILE")
    parser.add_argument("-o", metavar="FILE")
    parser.add_argument("-q", metavar="FILE")
    parser.add_argument("-r", metavar="FOLDER", default=".")

    return parser


def _get_exit_code(code):
    if isinstance(code, int):
        return code
    if code is None:
        return 0
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return _get_exit_code(exc.code)

    try:
        source_count = sum(value is not None for value in (args.i, args.d, args.j))

        if source_count != 1:
            parser.error("exactly one of -i, -d or -j is required")

        if (args.i or args.d) and not args.a:
            parser.error("-a is required with -i and -d")

        if args.j and args.o is not None:
            parser.error("-o cannot be used with -j")

    except SystemExit as exc:
        return _get_exit_code(exc.code)

    output_path = args.o or "db.json"

    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    handler = None

    try:
        if args.j:
            with open(args.j, "r", encoding="utf-8") as file:
                db = json.load(file)

            if not isinstance(db, list) or any(
                not isinstance(item, dict) for item in db
            ):
                raise ValueError("JSON database must be an array of objects")

        else:
            if args.i:
                paths = [args.i]
            else:
                if not os.path.isdir(args.d):
                    raise FileNotFoundError(args.d)

                paths = [
                    os.path.join(args.d, name)
                    for name in sorted(os.listdir(args.d))
                    if name.endswith(".csv")
                    and os.path.isfile(os.path.join(args.d, name))
                ]

                if not paths:
                    raise ValueError("folder contains no .csv files")

            airports = load_airports(args.a)

            log_path = os.path.join(
                os.path.dirname(os.path.abspath(output_path)),
                "errors.log",
            )

            handler = logging.FileHandler(
                log_path,
                mode="w",
                encoding="utf-8",
            )

            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )

            logger.addHandler(handler)

            db, errors = parse_files(paths, airports)

            for error in errors:
                logger.warning(error)

            with open(output_path, "w", encoding="utf-8") as file:
                json.dump(db, file, ensure_ascii=False, indent=2)

        if args.q:
            with open(args.q, "r", encoding="utf-8") as file:
                queries = json.load(file)

            if not isinstance(queries, (dict, list)):
                raise ValueError("Query file must contain an object or an array")

            responses = run_queries(db, queries)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M")

            response_name = (
                f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_" f"{timestamp}.json"
            )

            response_path = os.path.join(args.r, response_name)

            with open(response_path, "w", encoding="utf-8") as file:
                json.dump(
                    responses,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

        return 0

    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())
