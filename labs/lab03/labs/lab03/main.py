import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

from . import repository
from .config import CATEGORY_NAMES, THRESHOLD, UNIT, VARIANT_TITLE
from .database import initialize_database
from .routers import categories, records
from .schemas import PingRead, StudentRead

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

CATEGORY_LIST = ", ".join(f"`{name}`" for name in CATEGORY_NAMES)
DESCRIPTION = f"""
**{VARIANT_TITLE}** (варіант {VARIANT_NUMBER}).

Сервіс зберігає навчальні вимірювання використання серверних ресурсів.
Категорії ({CATEGORY_LIST}) визначають ресурс: процесор, оперативну пам'ять
або дисковий простір. `value` — використання ресурсу у відсотках
(одиниця вимірювання: **{UNIT}**, допустимий діапазон: 0–100%).
`status` — стан перевірки спостереження (`new`, `in_progress`, `done`).
Навчальний поріг: **{THRESHOLD}%**; для пошуку значень не нижче порога
використовуйте `min_value={THRESHOLD}`.
"""

ERROR_STATUS_CODES: tuple[tuple[type[repository.RepositoryError], int], ...] = (
    (repository.RecordNotFoundError, 404),
    (repository.CategoryNotFoundError, 404),
    (repository.DuplicateError, 409),
    (repository.CategoryNotEmptyError, 409),
    (repository.DataConstraintError, 422),
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці, але не заповнювати й не перезаписувати дані."""
    initialize_database()
    yield


app = FastAPI(
    title=VARIANT_TITLE,
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", response_model=PingRead, tags=["service"], summary="Перевірка API")
def ping() -> dict[str, str]:
    """Перевірити доступність API."""
    return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentRead,
    tags=["service"],
    summary="Дані студента",
)
def student() -> dict[str, str | int]:
    """Повернути ПІБ, групу та номер варіанта з shared/student.py."""
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }


@app.exception_handler(repository.RepositoryError)
async def repository_error_handler(
    _request: Request, error: repository.RepositoryError
) -> JSONResponse:
    """Перетворити очікувані помилки шару даних на HTTP-коди."""
    for error_type, status_code in ERROR_STATUS_CODES:
        if isinstance(error, error_type):
            return JSONResponse(status_code=status_code, content={"detail": str(error)})
    logger.error("Невідома помилка шару даних: %s", error)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка сервера"},
    )


@app.exception_handler(sqlite3.Error)
async def sqlite_error_handler(
    _request: Request, error: sqlite3.Error
) -> JSONResponse:
    """Записати подробиці SQLite в лог, клієнту повернути загальне повідомлення."""
    logger.error("Помилка SQLite: %s", error, exc_info=error)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка сервера"},
    )
