import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from functools import wraps


sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../")
    )
)

from shared.student import VARIANT_NUMBER


HASH_ALGORITHM = "sha3_384"
MIN_PASSWORD_LENGTH = 10
SALT = f"{VARIANT_NUMBER:05d}"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
LOG_FILE = os.path.join(DATA_DIR, "log.json")


class ValidationError(Exception):
    """Помилка валідації пароля."""


users_to_register = (
    ("alice", "SecurePass123!"),
    ("bob", "StrongPassword1!"),
    ("charlie", "MySecret2026!"),
    ("david", "CyberSecure99!"),
    ("emma", "PythonSecure1!"),
    ("frank", "NetworkPass22!"),
    ("grace", "SecurityKey7!"),
    ("henry", "SafePassword8!"),
    ("irene", "AdminSecure9!"),
    ("jack", "UserPassword5!"),
)

users_db = []


def generate_hash(password: str, salt: str = "00000") -> str:
    if not password or not salt:
        raise ValueError("Пароль або сіль не можуть бути порожніми.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль має містити щонайменше "
            f"{MIN_PASSWORD_LENGTH} символів."
        )

    hash_function = hashlib.new(HASH_ALGORITHM)
    hash_function.update(
        (password + salt).encode("utf-8")
    )

    return hash_function.hexdigest()


def create_user(username: str, password: str) -> tuple[str, str]:
    hash_value = generate_hash(password, SALT)
    return username, hash_value


def create_users(users_list: tuple[tuple[str, str], ...]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(
        USERS_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        for username, password in users_list:
            writer.writerow(create_user(username, password))


def read_users() -> list[tuple[str, str]]:
    users = []

    with open(
        USERS_FILE,
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) == 2:
                users.append((row[0], row[1]))

    return users


def print_users(users: list[tuple[str, str]]) -> None:
    print()
    print("=" * 80)
    print("USER DATABASE")
    print("=" * 80)
    print(f"{'Username':<20} {'Hash':<60}")
    print("-" * 80)

    for username, hash_value in users:
        print(f"{username:<20} {hash_value:<60}")

    print("=" * 80)


def log_event(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        result = None

        try:
            result = function(*args, **kwargs)
            return result
        finally:
            username = kwargs.get("username")

            if username is None and args:
                username = args[0]

            event = {
                "event": "login",
                "user": username,
                "result": "success" if result else "failure",
                "timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "args": list(args),
                "kwargs": kwargs,
            }

            os.makedirs(DATA_DIR, exist_ok=True)

            try:
                with open(
                    LOG_FILE,
                    "r",
                    encoding="utf-8",
                ) as file:
                    logs = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                logs = []

            logs.append(event)

            with open(
                LOG_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    logs,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

    return wrapper


@log_event
def login(username: str, password: str) -> bool:
    if not username or not password:
        raise ValueError(
            "Логін і пароль не можуть бути порожніми."
        )

    entered_hash = generate_hash(password, SALT)

    for stored_username, stored_hash in users_db:
        if stored_username == username:
            return entered_hash == stored_hash

    return False


def main() -> None:
    global users_db

    try:
        print(f"Hash algorithm: {HASH_ALGORITHM}")
        print(f"Minimum password length: {MIN_PASSWORD_LENGTH}")
        print(f"Personal salt: {SALT}")

        create_users(users_to_register)
        print("\nUsers successfully registered.")

        users_db = read_users()
        print_users(users_db)

        print("\nAUTHENTICATION TESTS")
        print("=" * 50)

        result = login("alice", "SecurePass123!")
        print(f"alice / correct password -> {result}")

        result = login("alice", "WrongPassword123!")
        print(f"alice / wrong password -> {result}")

        result = login("unknown", "SecurePass123!")
        print(f"unknown user -> {result}")

        try:
            login("", "SecurePass123!")
        except ValueError as error:
            print(f"Empty username -> ValueError: {error}")

        try:
            login("alice", "")
        except ValueError as error:
            print(f"Empty password -> ValueError: {error}")

        print(f"\nLog file: {LOG_FILE}")

    except FileNotFoundError as error:
        print(f"FileNotFoundError: {error}")
    except PermissionError as error:
        print(f"PermissionError: {error}")
    except IOError as error:
        print(f"IOError: {error}")
    except ValidationError as error:
        print(f"ValidationError: {error}")
    except ValueError as error:
        print(f"ValueError: {error}")


if __name__ == "__main__":
    main()