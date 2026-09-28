import hashlib
import hmac
import os
import re
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass


PBKDF2_ITERATIONS = 100_000
SESSION_TIMEOUT_SEC = 900


class User:
    def __init__(self, username, email, password, role="user"):
        self.username = username
        self.email = email
        self.role = role
        self.active = True

        self.__password_hash = None
        self.__password_salt = None

        self.set_password(password)

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, value):
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.match(pattern, value):
            raise ValueError("Invalid email address")

        self.__email = value

    def set_password(self, password):
        if not password:
            raise ValueError("Password cannot be empty")

        self.__password_salt = os.urandom(16)

        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password):
        if not self.__password_hash or not self.__password_salt:
            return False

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

        return hmac.compare_digest(
            password_hash,
            self.__password_hash,
        )

    def deactivate(self):
        self.active = False

    def __str__(self):
        return (
            f"User(username={self.username}, "
            f"email={self.email}, "
            f"role={self.role}, "
            f"active={self.active})"
        )



class Admin(User):
    def __init__(
        self,
        username,
        email,
        password,
        permissions=None,
    ):
        super().__init__(
            username,
            email,
            password,
            role="admin",
        )

        self.permissions = set(permissions or [])

    def grant_permission(self, permission):
        self.permissions.add(permission)

    def revoke_permission(self, permission):
        self.permissions.discard(permission)

    def has_permission(self, permission):
        return permission in self.permissions

    def __str__(self):
        return (
            f"Admin(username={self.username}, "
            f"email={self.email}, "
            f"permissions={self.permissions}, "
            f"active={self.active})"
        )


class Session:
    def __init__(self, ip):
        self.ip = ip
        self.login_time = datetime.now(timezone.utc)
        self.last_activity = self.login_time

    def touch(self):
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec):
        now = datetime.now(timezone.utc)

        return (
            now - self.last_activity
            < timedelta(seconds=timeout_sec)
        )


@dataclass
class AuditEntry:
    timestamp: datetime
    username: str
    action: str

class AuditLog:
    def __init__(self):
        self.entries = []

    def add_log(self, username, action):
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
        )

        self.entries.append(entry)

    def show_all(self):
        for entry in self.entries:
            print(
                f"{entry.timestamp} | "
                f"{entry.username} | "
                f"{entry.action}"
            )

class UserAccount:
    def __init__(self, user):
        self.user = user
        self.session = None
        self.audit_log = AuditLog()

    def login(self, username, password, ip):
        if username != self.user.username:
            self.audit_log.add_log(
                username,
                "login_failure",
            )
            return False

        if not self.user.active:
            self.audit_log.add_log(
                username,
                "login_failure",
            )
            return False

        if not self.user.check_password(password):
            self.audit_log.add_log(
                username,
                "login_failure",
            )
            return False

        self.session = Session(ip)

        self.audit_log.add_log(
            username,
            "login_success",
        )

        return True

    def is_authenticated(self):
        if self.session is None:
            return False

        return self.session.is_active(
            SESSION_TIMEOUT_SEC
        )

    def logout(self):
        if self.session is not None:
            self.audit_log.add_log(
                self.user.username,
                "logout",
            )

        self.session = None

    def __getitem__(self, key):
        if key == "user":
            return self.user

        if key == "session":
            return self.session

        if key == "audit_log":
            return self.audit_log

        if key in {
            "password",
            "password_hash",
            "password_salt",
        }:
            raise KeyError(
                f"Access to '{key}' is forbidden"
            )

        raise KeyError(f"Unknown key: {key}")

    def __setitem__(self, key, value):
        if key == "email":
            self.user.email = value
            return

        if key == "role":
            self.user.role = value
            return

        if key in {
            "password",
            "password_hash",
            "password_salt",
        }:
            raise KeyError(
                f"Access to '{key}' is forbidden"
            )

        raise KeyError(f"Unknown key: {key}")



