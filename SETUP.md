# FoodExpress — Setup Guide for Demo Machine

**Total setup time:** ~25 minutes (most of it is just MySQL installer running)

This is a Flask + MySQL web application. Follow the steps in order. If anything errors out, scroll to the **Troubleshooting** section at the bottom.

---

## What you need to install (in this order)

1. MySQL Server 8 + MySQL Workbench (one installer, ~10 min)
2. Python 3.10+ (if not already installed)
3. Three Python packages via `pip`

---

## STEP 1 — Install MySQL Server + Workbench

1. Download the offline installer (~500 MB):
   <https://dev.mysql.com/downloads/installer/>
   Pick **Windows (x86, 32-bit) MSI Installer** — the bigger one. Click "No thanks, just start my download".

2. Run the installer. On the **Setup Type** screen choose **Custom** (not "Developer Default").

3. From the left tree, add these to "Products to be installed":
   - **MySQL Server 8.x**
   - **MySQL Workbench 8.x**

4. Click Next. On the **Type and Networking** screen leave defaults (Standalone, port `3306`, "Open Windows Firewall" checked).

5. **Authentication Method**: pick the recommended option ("Use Strong Password Encryption").

6. **Accounts and Roles**: set a **MySQL Root Password**. Type it twice. **WRITE IT DOWN — you'll need it constantly**.
   - Avoid `@`, `:`, `/`, `#` characters (URL-encoding headaches). Plain alphanumeric like `dbsproject2025` is fine.

7. **Windows Service**: leave defaults. Click through, hit Execute, wait for green checks, Finish.

8. Workbench should auto-open. If not, search "MySQL Workbench" in the Start menu.

9. In Workbench, double-click the **"Local instance MySQL80"** tile, enter your root password.

✅ When you see a SQL editor, MySQL is installed and running.

---

## STEP 2 — Install Python (skip if already on the machine)

1. Check first — open PowerShell and type:
   ```
   python --version
   ```
   If you see something like `Python 3.10.x` or higher, **skip to step 3**.

2. If you got "command not found": download Python from <https://www.python.org/downloads/>. **During install, tick the "Add python.exe to PATH" checkbox** at the bottom of the first screen.

3. Verify after install:
   ```
   python --version
   pip --version
   ```

---

## STEP 3 — Install Python packages

Open PowerShell and run:

```
pip install flask werkzeug mysql-connector-python python-docx
```

Should download a few packages and finish in 30 seconds.

---

## STEP 4 — Load the database schema

1. In **MySQL Workbench**, go to **File → Open SQL Script…**
2. Navigate to and open: `<path_to_this_folder>\sql\schema.sql`
3. Click the **lightning-bolt icon** in the script tab (or press `Ctrl + Shift + Enter`) to execute the entire script.
4. Watch the **Output** panel at the bottom — you should see a stream of green checkmarks for every CREATE TABLE, CREATE TRIGGER, CREATE VIEW, and INSERT.

5. **Verify** — paste this in a new query tab and hit lightning bolt:
   ```sql
   USE food_ordering_db;
   SHOW TABLES;
   SELECT 'Restaurants' AS what, COUNT(*) AS total FROM restaurants
   UNION ALL SELECT 'Menu Items', COUNT(*) FROM menu_items
   UNION ALL SELECT 'Customers',  COUNT(*) FROM customers;
   ```
   Expected:
   - `SHOW TABLES` → 12 rows (9 tables + 3 views)
   - Restaurants: **9**
   - Menu Items: **35**
   - Customers: **3**

✅ Database is loaded.

---

## STEP 5 — Configure your password

Open `config.py` (in the project root, next to `app.py`) in any text editor — Notepad, VS Code, whatever.

Find this line:
```python
"password": "PUT_YOUR_MYSQL_ROOT_PASSWORD_HERE",
```

Replace `PUT_YOUR_MYSQL_ROOT_PASSWORD_HERE` with your actual MySQL root password (the one from step 1.6). Keep the quotes.

Example:
```python
"password": "dbsproject2025",
```

Save the file.

---

## STEP 6 — Set demo user passwords

Open PowerShell, navigate to the project folder, and run:

```
cd <path_to_this_folder>
python init_passwords.py
```

You should see output like:
```
  customer bazil@example.com:   1 row(s) updated
  customer daanial@example.com: 1 row(s) updated
  customer manan@example.com:   1 row(s) updated
  admin admin: 1 row(s) updated

Done. You can now log in with the demo credentials.
```

✅ Demo accounts are ready.

---

## STEP 7 — Run the Flask app

Still in the same PowerShell window:

```
python app.py
```

You should see:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

**Leave this window open** — closing it shuts down the server.

---

## STEP 8 — Open the app in a browser

Visit: **<http://localhost:5000>**

You should see the FoodExpress homepage with 9 restaurant cards.

---

## Demo credentials

| Role     | Login                                         | Password    |
|----------|-----------------------------------------------|-------------|
| Customer | `bazil@example.com`                           | `bazil123`  |
| Customer | `daanial@example.com`                         | `daanial123`|
| Customer | `manan@example.com`                           | `manan123`  |
| Admin    | `admin` (username, not email — at `/admin/login`) | `admin123`  |

---

## Suggested demo flow

1. Visit homepage → see all 9 restaurants
2. Click any **category pill** (e.g., Beverages) → see all items in that category across restaurants
3. **Register** a fresh user, or log in as `daanial@example.com / daanial123`
4. Click any restaurant → browse menu (grouped by category) → scroll down to see the **Reviews section**
5. Add 2-3 items to cart → click cart → **Checkout** → choose payment method → place order
6. Go to **My Orders** → click **Track** on the new order
7. Open a new tab → go to `/admin/login` → log in as `admin / admin123`
8. **Admin → Orders** → change the order status from Pending to Delivered (proves the UPDATE query)
9. Switch back to customer tab → refresh My Orders → status reflects the change
10. Open Workbench → run `SELECT * FROM orders ORDER BY order_id DESC LIMIT 1;` → proves the order is real, in the real database

---

## Troubleshooting

### "Access denied for user 'root'@'localhost'"
- Your password in `config.py` doesn't match the MySQL root password. Edit `config.py` and try again.

### "ModuleNotFoundError: No module named 'flask'"
- You skipped Step 3. Run `pip install flask werkzeug mysql-connector-python`.

### "Can't connect to MySQL server on 'localhost'"
- The MySQL service isn't running. Open Services (Win+R → `services.msc`), find **MySQL80**, right-click → Start.

### Schema fails with "Unknown database 'food_ordering_db'"
- The first line of `schema.sql` is `CREATE DATABASE IF NOT EXISTS food_ordering_db;` — make sure that ran. If you started running from the middle, run the whole file from the top.

### `python init_passwords.py` errors with "1146: Table 'food_ordering_db.customers' doesn't exist"
- You ran `init_passwords.py` before loading `schema.sql`. Run schema.sql first.

### Port 5000 already in use
- Edit `config.py` — change `PORT = 5000` to `PORT = 5050` (or any free port). Restart `python app.py`.

### Can't log in as a demo user
- Did you run `python init_passwords.py`? The seed data has placeholder hashes that need to be replaced with real ones.

---

## Project structure

```
FoodExpress_Share/
├── SETUP.md                ← this file
├── README.md               ← short project description
├── app.py                  ← Flask routes and views
├── config.py               ← EDIT YOUR PASSWORD HERE
├── db.py                   ← MySQL connection helper
├── init_passwords.py       ← run once after schema load
├── sql/
│   └── schema.sql          ← full database schema + seed data
├── templates/              ← 18 Jinja2 HTML templates
└── docs/
    ├── DBS_Project_Report.docx   ← project report for the viva
    ├── erd.png                   ← Entity Relationship Diagram
    └── use_case.png              ← Use Case Diagram
```

---

## Stopping the server when done

Go to the PowerShell window running `python app.py` and press **Ctrl + C**. Done.
