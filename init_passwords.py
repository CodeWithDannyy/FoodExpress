"""
One-time script: fix the seed customers' and admin's password hashes
so you can log in with the demo credentials.

The schema.sql ships with literal placeholder strings (e.g. 'hashed_pw_1')
that aren't real hashes — werkzeug will reject them. Run this once after
loading the schema to set proper hashes.

Demo logins after running:
    bazil@example.com    / pass123
    daanial@example.com  / pass123
    manan@example.com    / pass123
    admin (username)     / admin123

Usage:
    python init_passwords.py
"""

import mysql.connector
from werkzeug.security import generate_password_hash
from config import DB_CONFIG


SEED_CUSTOMERS = [
    # (email, plain_text_password)  — change these to whatever you want
    ("bazil@example.com",   "bazil123"),
    ("daanial@example.com", "daanial123"),
    ("manan@example.com",   "manan123"),
]
SEED_ADMIN = ("admin", "admin123")   # username, plain_text_password


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Customers
    for email, plain in SEED_CUSTOMERS:
        cur.execute(
            "UPDATE customers SET password_hash = %s WHERE email = %s",
            (generate_password_hash(plain), email),
        )
        print(f"  customer {email}: {cur.rowcount} row(s) updated")

    # Admin
    username, plain = SEED_ADMIN
    cur.execute(
        "UPDATE admins SET password_hash = %s WHERE username = %s",
        (generate_password_hash(plain), username),
    )
    print(f"  admin {username}: {cur.rowcount} row(s) updated")

    conn.commit()
    cur.close()
    conn.close()
    print("\nDone. You can now log in with the demo credentials.")


if __name__ == "__main__":
    main()
