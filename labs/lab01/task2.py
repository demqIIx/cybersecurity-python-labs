users = {
    "iot_specialist": {
        "role": "iot_security",
        "clearance": 3,
        "department": "IoT",
        "active": True,
    },
    "mobile_analyst": {
        "role": "mobile_security",
        "clearance": 3,
        "department": "Mobile",
        "active": True,
    },
    "web_developer": {
        "role": "web_developer",
        "clearance": 2,
        "department": "Web",
        "active": True,
    },
    "api_consumer": {
        "role": "api_user",
        "clearance": 2,
        "department": "Integration",
        "active": True,
    },
    "demo_account": {
        "role": "demonstration",
        "clearance": 1,
        "department": "Demo",
        "active": False,
    },
}

resources = [
    ("iot_firmware", 3),
    ("mobile_policies", 3),
    ("web_applications", 2),
    ("api_gateway", 2),
    ("device_certificates", 3),
    ("app_store", 1),
    ("vulnerability_database", 3),
    ("device_management", 3),
    ("integration_docs", 2),
    ("demo_content", 1),
]

security_levels = (
    "Consumer",
    "Business",
    "Enterprise",
    "Critical Systems",
)

blocked_users = {
    "demo_account",
    "compromised_device",
    "malicious_app",
}


def check_access(username, resource_name, users, resources, blocked_users):

    if username not in users:
        return False, "Unknown user"

    user = users[username]

    if username in blocked_users:
        return False, "Blocked user"

    if not user["active"]:
        return False, "Inactive user"

    resource_level = None

    for name, level in resources:
        if name == resource_name:
            resource_level = level
            break

    if resource_level is None:
        return False, "Unknown resource"

    if user["clearance"] < resource_level:
        return False, "Insufficient clearance"

    return True, "Access granted"


print("=" * 50)
print("RESOURCES")
print("=" * 50)

for resource_name, level in resources:
    print(f"{resource_name:<25} -> {security_levels[level - 1]}")


print()
print("=" * 50)
print("ACCESS CHECKS")
print("=" * 50)

for username in users:
    for resource_name, _ in resources:
        allowed, reason = check_access(
            username,
            resource_name,
            users,
            resources,
            blocked_users,
        )

        if allowed:
            print(f"user={username:<18} resource={resource_name:<25} -> ALLOW")
        else:
            print(
                f"user={username:<18} resource={resource_name:<25} -> DENY ({reason})"
            )
