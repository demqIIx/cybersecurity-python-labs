"""Параметри предметної області для варіанта 10."""

from typing import Literal, get_args

# Предметна область варіанта 10.
VARIANT_TITLE = "Облік навантаження серверних ресурсів"
UNIT = "percent"
THRESHOLD = 80.0
CATEGORY_NAMES = ("cpu", "memory", "disk")
RECORD_TITLE = "Вимірювання сервера"

# Межі числового значення value для варіантів 10–12.
VALUE_MIN = 0.0
VALUE_MAX = 100.0

# Максимальне значення SQLite INTEGER для ідентифікаторів.
SQLITE_MAX_INT = 2**63 - 1

# Дозволені стани опрацювання.
Status = Literal["new", "in_progress", "done"]
STATUSES: tuple[str, ...] = get_args(Status)

# Обмеження довжин рядків (мають відповідати schema.sql).
CATEGORY_NAME_MIN = 2
CATEGORY_NAME_MAX = 40
CODE_MIN = 3
CODE_MAX = 40
TITLE_MIN = 3
TITLE_MAX = 120

# Параметри списку та пакетного додавання.
SEARCH_MIN = 1
SEARCH_MAX = 120
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
MAX_BATCH_SIZE = 100
