"""
EXAMPLE configuration file.

To set up the project on your machine:
    1. Copy this file to `config.py` (in the same folder)
    2. Replace the placeholder values below with your real ones
    3. NEVER commit your real `config.py` — it's listed in .gitignore

Generate a fresh SECRET_KEY by running:
    python -c "import secrets; print(secrets.token_hex(32))"
"""

DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "YOUR_MYSQL_ROOT_PASSWORD",     # <-- EDIT
    "database": "food_ordering_db",
    "charset":  "utf8mb4",
    "use_pure": True,
    "autocommit": False,
}

# Flask app config
SECRET_KEY = "REPLACE_WITH_RANDOM_64_CHAR_HEX_STRING"  # <-- EDIT
DEBUG = True
PORT = 5000
