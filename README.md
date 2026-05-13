# 🔥 FoodExpress — Online Food Ordering System

**DBS Project** | FAST NUCES Karachi  
**Group Members:** Bazil Uddin Khan (24K-0559), Daanial Tejani (24K-0671), Abdul Manan (23K-0829)

---

## Features

### Customer
- Register & login with secure password hashing
- Browse restaurants and menus (grouped by category)
- Search for food items
- Add items to cart, adjust quantities
- Checkout with Cash on Delivery or Online payment
- Track order status in real time

### Admin Panel
- Dashboard with stats (customers, orders, revenue)
- View and manage all orders (update status)
- View customer list
- View restaurant list
- Enable/disable menu items

### Database
- 9 normalized tables (1NF, 2NF, 3NF compliant)
- Foreign keys with CASCADE rules
- Triggers for auto-updating order totals and restaurant ratings
- Views for order summaries, revenue reports, popular items
- Advanced SQL queries (JOINs, GROUP BY, HAVING, aggregates)

---

## Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Frontend  | HTML5, CSS3, Bootstrap 5, JS      |
| Backend   | Python 3 + Flask                  |
| Database  | MySQL (schema provided)           |
| Fonts     | DM Sans, Playfair Display         |
| Icons     | Bootstrap Icons                   |

---

## Quick Start

### 1. Install Python dependencies

```bash
pip install flask werkzeug
```

### 2. Run the app

```bash
cd food_ordering
python app.py
```

The app will start at **http://localhost:5000**

### 3. Demo credentials

| Role     | Email / Username        | Password  |
|----------|------------------------|-----------|
| Customer | bazil@example.com      | pass123   |
| Customer | daanial@example.com    | pass123   |
| Customer | manan@example.com      | pass123   |
| Admin    | admin                  | admin123  |

---

## MySQL Setup (Optional)

The app runs with in-memory data by default (no MySQL needed for demo).  
To use MySQL in production:

1. Install MySQL and create the database:
```bash
mysql -u root -p < sql/schema.sql
```

2. Update `app.py` to use SQLAlchemy with your MySQL connection string.

The `sql/schema.sql` file includes:
- All 9 CREATE TABLE statements
- Triggers (auto order total, auto restaurant rating)
- Views (customer orders, restaurant revenue, popular items)
- Sample data (4 restaurants, 12 menu items, 3 customers, 4 orders)
- 5 advanced query examples (commented out, for your report)

---

## Project Structure

```
food_ordering/
├── app.py                  # Flask application (all routes)
├── sql/
│   └── schema.sql          # Complete MySQL schema + data
├── templates/
│   ├── base.html           # Base layout (navbar, footer, styles)
│   ├── index.html          # Home page (hero, categories, restaurants)
│   ├── menu.html           # Restaurant menu page
│   ├── login.html          # Customer login
│   ├── register.html       # Customer registration
│   ├── cart.html           # Shopping cart
│   ├── checkout.html       # Checkout page
│   ├── my_orders.html      # Customer order history
│   ├── track_order.html    # Order tracking with step indicator
│   ├── search_results.html # Search results page
│   ├── admin_login.html    # Admin login
│   ├── admin_dashboard.html# Admin dashboard with stats
│   ├── admin_orders.html   # Admin order management
│   ├── admin_customers.html# Admin customer list
│   ├── admin_restaurants.html # Admin restaurant list
│   └── admin_menu.html     # Admin menu item management
└── README.md
```

---

## Database Schema (9 Tables)

| Table          | Description                          |
|----------------|--------------------------------------|
| categories     | Food categories (Burgers, Pizza...) |
| restaurants    | Restaurant info and ratings          |
| customers      | Customer accounts                    |
| admins         | Admin accounts                       |
| menu_items     | Food items linked to restaurants     |
| orders         | Customer orders                      |
| order_details  | Items within each order              |
| payments       | Payment records                      |
| reviews        | Customer reviews for restaurants     |

---

## Advanced SQL Queries (for Report)

See `sql/schema.sql` — bottom section contains 5 commented queries:
1. Total revenue per restaurant (delivered orders)
2. Top 3 most ordered items
3. Customers who spent more than Rs. 1500
4. Average order value per restaurant
5. Monthly order count

---

© 2025 FoodExpress — FAST NUCES DBS Project
