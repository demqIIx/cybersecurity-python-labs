from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt

from .config import (
    CATEGORY_NAME_MAX,
    CATEGORY_NAME_MIN,
    CODE_MAX,
    CODE_MIN,
    SQLITE_MAX_INT,
    TITLE_MAX,
    TITLE_MIN,
    VALUE_MAX,
    VALUE_MIN,
    Status,
)


class CategoryCreate(BaseModel):
    

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        min_length=CATEGORY_NAME_MIN,
        max_length=CATEGORY_NAME_MAX,
        description="Унікальна назва серверного ресурсу",
        examples=["cpu"],
    )


class CategoryRead(BaseModel):
    

    id: int
    name: str


class RecordCreate(BaseModel):
    

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(
        min_length=CODE_MIN,
        max_length=CODE_MAX,
        description="Унікальний код вимірювання",
        examples=["V10-TEST"],
    )
    title: str = Field(
        min_length=TITLE_MIN,
        max_length=TITLE_MAX,
        description="Назва вимірювання серверного ресурсу",
        examples=["Вимірювання сервера 09"],
    )
    category_id: StrictInt = Field(
        gt=0,
        le=SQLITE_MAX_INT,
        description="Ідентифікатор категорії (cpu, memory або disk)",
        examples=[1],
    )
    value: StrictFloat = Field(
        ge=VALUE_MIN,
        le=VALUE_MAX,
        allow_inf_nan=False,
        description="Використання ресурсу у відсотках, від 0 до 100",
        examples=[82.5],
    )
    status: Status = Field(description="Стан перевірки: new, in_progress або done")


class RecordReplace(RecordCreate):
    """Тіло PUT: усі змінювані поля обов'язкові, id не змінюється."""


class RecordRead(RecordCreate):
    """Запис у відповіді API: усі поля, id та назва категорії."""

    id: int
    category_name: str


class PingRead(BaseModel):
    """Відповідь перевірки доступності API."""

    status: str


class StudentRead(BaseModel):
    """Дані студента з shared/student.py."""

    student_name: str
    group_name: str
    variant_number: int


class ErrorDetail(BaseModel):
    """Тіло відповіді для очікуваної HTTP-помилки."""

    detail: str
