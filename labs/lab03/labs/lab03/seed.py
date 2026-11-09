import json
import logging
import math
import sqlite3
import sys
from pathlib import Path
from typing import Any

from . import repository
from .config import (
    CATEGORY_NAME_MAX,
    CATEGORY_NAME_MIN,
    CATEGORY_NAMES,
    CODE_MAX,
    CODE_MIN,
    SQLITE_MAX_INT,
    STATUSES,
    TITLE_MAX,
    TITLE_MIN,
    VALUE_MAX,
    VALUE_MIN,
)
from .database import BASE_DIR, initialize_database

logger = logging.getLogger(__name__)

SEED_PATH = BASE_DIR / "data" / "seed.json"
CATEGORY_KEYS = {"id", "name"}
RECORD_KEYS = {"code", "title", "category_id", "value", "status"}
EXIT_OK = 0
EXIT_ERROR = 1

SeedParts = tuple[list[dict[str, Any]], list[dict[str, Any]]]


class SeedDataError(ValueError):
    """Початкові дані мають неправильну структуру або значення."""


def _is_int(value: object) -> bool:
    """Перевірити ціле число; bool у Python не вважаємо цілим для ID."""
    return isinstance(value, int) and not isinstance(value, bool)


def _text(value: object, where: str, name: str, low: int, high: int) -> str:
    """Перевірити тип і довжину текстового поля після обрізання пробілів."""
    if not isinstance(value, str):
        raise SeedDataError(f"{where}: поле {name} має бути рядком")
    cleaned = value.strip()
    if not low <= len(cleaned) <= high:
        raise SeedDataError(
            f"{where}: довжина поля {name} має бути від {low} до {high}"
        )
    return cleaned


def _object(item: object, where: str, keys: set[str]) -> dict[str, Any]:
    """Перевірити, що елемент є об'єктом із точним набором ключів."""
    if not isinstance(item, dict):
        raise SeedDataError(f"{where}: очікується JSON-об'єкт")
    if set(item) != keys:
        raise SeedDataError(f"{where}: потрібні рівно поля {sorted(keys)}")
    return item


def _array(data: dict[str, Any], key: str, expected: int) -> list[Any]:
    """Перевірити масив і його кількість елементів за методичкою."""
    items = data.get(key)
    if not isinstance(items, list) or len(items) != expected:
        raise SeedDataError(f"'{key}' має містити рівно {expected} елемент(и)")
    return items


def validate_seed(data: object) -> SeedParts:
    """Перевірити seed.json і повернути списки (категорії, записи)."""
    if not isinstance(data, dict) or set(data) != {"categories", "records"}:
        raise SeedDataError("JSON має містити лише поля categories та records")

    categories: list[dict[str, Any]] = []
    for index, raw in enumerate(_array(data, "categories", 3), start=1):
        where = f"categories[{index}]"
        item = _object(raw, where, CATEGORY_KEYS)
        if not _is_int(item["id"]) or not 0 < item["id"] <= SQLITE_MAX_INT:
            raise SeedDataError(f"{where}: id має бути додатним цілим числом")
        name = _text(
            item["name"], where, "name", CATEGORY_NAME_MIN, CATEGORY_NAME_MAX
        )
        categories.append({"id": item["id"], "name": name})

    category_ids = [item["id"] for item in categories]
    category_names = [item["name"] for item in categories]
    if category_ids != [1, 2, 3]:
        raise SeedDataError("Категорії мають мати id 1, 2 та 3 у вказаному порядку")
    if tuple(category_names) != CATEGORY_NAMES:
        raise SeedDataError(
            f"Для варіанта 10 потрібні категорії {', '.join(CATEGORY_NAMES)}"
        )

    records: list[dict[str, Any]] = []
    for index, raw in enumerate(_array(data, "records", 8), start=1):
        where = f"records[{index}]"
        item = _object(raw, where, RECORD_KEYS)
        code = _text(item["code"], where, "code", CODE_MIN, CODE_MAX)
        title = _text(item["title"], where, "title", TITLE_MIN, TITLE_MAX)

        category_id = item["category_id"]
        if not _is_int(category_id) or category_id not in category_ids:
            raise SeedDataError(f"{where}: category_id має посилатися на категорію 1–3")

        value = item["value"]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or not VALUE_MIN <= value <= VALUE_MAX
        ):
            raise SeedDataError(
                f"{where}: value має бути скінченним числом від {VALUE_MIN} до {VALUE_MAX}"
            )

        status = item["status"]
        if not isinstance(status, str) or status not in STATUSES:
            raise SeedDataError(f"{where}: status має бути одним із {list(STATUSES)}")

        expected_code = f"V10-{index:02d}"
        if code != expected_code:
            raise SeedDataError(f"{where}: очікується code {expected_code}")

        records.append(
            {
                "code": code,
                "title": title,
                "category_id": category_id,
                "value": float(value),
                "status": status,
            }
        )

    codes = [item["code"] for item in records]
    if len(set(codes)) != len(codes):
        raise SeedDataError("Коди записів мають бути унікальними")

    return categories, records


def load_seed(path: Path = SEED_PATH) -> SeedParts:
    """Прочитати JSON-файл і перевірити його вміст."""
    with path.open(encoding="utf-8") as handle:
        return validate_seed(json.load(handle))


def main() -> int:
    """Створити таблиці за потреби й заповнити лише порожню базу."""
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    try:
        initialize_database()
        categories, records = load_seed()
        inserted = repository.seed_database(categories, records)
    except FileNotFoundError:
        print(f"Файл початкових даних не знайдено: {SEED_PATH}")
        return EXIT_ERROR
    except json.JSONDecodeError as error:
        print(f"seed.json не є коректним JSON: {error}")
        return EXIT_ERROR
    except SeedDataError as error:
        print(f"Початкові дані некоректні, базу не змінено: {error}")
        return EXIT_ERROR
    except repository.RepositoryError as error:
        print(f"Заповнення скасовано, базу не змінено: {error}")
        return EXIT_ERROR
    except sqlite3.Error:
        logger.exception("Помилка SQLite під час початкового заповнення")
        print("Помилка бази даних: заповнення скасовано (подробиці в журналі).")
        return EXIT_ERROR

    if not inserted:
        print("База вже містить дані: заповнення пропущено, нічого не змінено.")
        return EXIT_OK

    print(f"Додано категорій: {len(categories)}, записів: {len(records)}.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
