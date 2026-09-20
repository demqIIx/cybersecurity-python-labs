import os
import random
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


from shared.student import STUDENT_NAME, GROUP_NAME, VARIANT_NUMBER

passwords = [
    "IoT@S3curity",
    "standard",
    "Blockchain@Pr0tect",
    "typical123",
    "AI@Cybersec",
    "normal",
    "Quantum@Crypt0",
    "general123",
    "Edge@S3curity",
    "common",
]

criteria = {
    "min_length": 8,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {
    "standard",
    "typical123",
    "normal",
    "general123",
    "common",
    "guest",
}


duplicate_indices = random.sample(range(len(passwords)), 3)

for index in duplicate_indices:
    passwords.append(passwords[index])


print(f"Student: {STUDENT_NAME}")
print(f"Group: {GROUP_NAME}")
print(f"Variant: {VARIANT_NUMBER}")
print(f"password length: {len(passwords)}")
print(f"duplicates: {duplicate_indices}")
print(f"passwords: {passwords}")


def analyze_password(password, criteria, forbidden_passwords, passwords):
    if password in forbidden_passwords or len(password) < criteria["min_length"]:
        return "Заборонений"

    has_digit = any(char.isdigit() for char in password)
    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)

    special_characters = "!@#$%^&*()_+-=[]{}|;:,.<>?/\\"
    has_special = any(char in special_characters for char in password)

    criteria_met = sum(
        [
            has_digit,
            has_upper,
            has_lower,
            has_special,
        ]
    )

    if criteria_met == 1:
        return "Слабкий"

    if criteria_met < 4:
        return "Середній"

    if len(password) < criteria["min_length"] + 4:
        return "Сильний"

    if passwords.count(password) == 1:
        return "Дуже сильний"

    return "Сильний"


print("-" * 50)


def print_results(passwords, criteria, forbidden_passwords):
    print()
    print("=" * 65)
    print("АНАЛІЗ НАДІЙНОСТІ ПАРОЛІВ")
    print("=" * 65)
    print(f"Student: {STUDENT_NAME}")
    print(f"Group:   {GROUP_NAME}")
    print(f"Variant: {VARIANT_NUMBER}")
    print("-" * 65)

    print(f"{'Password':<25} {'Length':<10} {'Category':<20}")
    print("-" * 65)

    for password in passwords:
        category = analyze_password(
            password,
            criteria,
            forbidden_passwords,
            passwords,
        )

        print(f"{password:<25} {len(password):<10} {category:<20}")

    print("=" * 65)


print_results(
    passwords,
    criteria,
    forbidden_passwords,
)
