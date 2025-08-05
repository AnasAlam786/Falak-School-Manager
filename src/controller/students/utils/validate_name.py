# src/controller/utills/validate_name.py
import re

def validate_name(name, field_name):
    """
    - Must be non-empty after stripping.
    - Must only contain letters, spaces, hyphens or apostrophes.
    - Length between 2 and 50 characters (adjust as you like).
    """

    if not name or not name.strip():
        return f"{field_name} is required."
    name = name.strip()
    # Regex: start with a letter, then letters/spaces/'/- allowed

    if not re.match(r"^[A-Za-z0-9\s.+-]+$", name):
        return (f"{field_name} must start and end with a letter, and only contain letters, spaces, hyphens or apostrophes.")
    return None  # no error
