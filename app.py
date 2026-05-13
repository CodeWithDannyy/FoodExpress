from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

import db
from db import query_all, query_one, execute, get_db
from config import SECRET_KEY, DEBUG, PORT



# App configuration
app = Flask(__name__)
app.secret_key = SECRET_KEY
db.init_app(app)


# Auth decorators
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            flash("Admin access required.", "danger")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


# Context processor — make data available in all templates
@app.context_processor
def inject_globals():
    cart = session.get("cart", [])
    cart_count = sum(item["quantity"] for item in cart)
    user = None
    if "user_id" in session:
        user = query_one(
            "SELECT * FROM customers WHERE customer_id = %s",
            (session["user_id"],),
        )
    categories = query_all("SELECT * FROM categories ORDER BY name")
    return dict(cart_count=cart_count, current_user=user, categories=categories)



#  PUBLIC ROUTES
@app.route("/")
def index():
    restaurants = query_all(
        "SELECT * FROM restaurants WHERE is_active = TRUE ORDER BY name"
    )
    categories = query_all("SELECT * FROM categories ORDER BY name")
    return render_template("index.html", restaurants=restaurants, categories=categories)


@app.route("/restaurant/<int:rid>")
def restaurant_menu(rid):
    rest = query_one(
        "SELECT * FROM restaurants WHERE restaurant_id = %s", (rid,)
    )
    if not rest:
        flash("Restaurant not found.", "danger")
        return redirect(url_for("index"))

    items = query_all(
        """
        SELECT mi.*, c.name AS category_name
        FROM menu_items mi
        JOIN categories c ON mi.category_id = c.category_id
        WHERE mi.restaurant_id = %s AND mi.is_available = TRUE
        ORDER BY c.name, mi.name
        """,
        (rid,),
    )
    # Group by category for the template
    grouped = {}
    for item in items:
        grouped.setdefault(item["category_name"], []).append(item)

    # Fetch reviews (joined with customer name)
    reviews = query_all(
        """
        SELECT  r.review_id, r.rating, r.comment, r.review_date,
                CONCAT(c.first_name, ' ', c.last_name) AS customer_name
        FROM    reviews r
        JOIN    customers c ON r.customer_id = c.customer_id
        WHERE   r.restaurant_id = %s
        ORDER BY r.review_date DESC
        """,
        (rid,),
    )

    # Has the current user already reviewed this restaurant? (one-per-customer rule)
    user_has_reviewed = False
    if "user_id" in session:
        existing = query_one(
            "SELECT 1 FROM reviews WHERE customer_id = %s AND restaurant_id = %s",
            (session["user_id"], rid),
        )
        user_has_reviewed = existing is not None

    return render_template(
        "menu.html",
        restaurant=rest,
        grouped_items=grouped,
        reviews=reviews,
        user_has_reviewed=user_has_reviewed,
    )

@app.route("/category/<int:cid>")
def category(cid):
    """Show all available menu items in a single category, across all restaurants."""
    cat = query_one("SELECT * FROM categories WHERE category_id = %s", (cid,))
    if not cat:
        flash("Category not found.", "danger")
        return redirect(url_for("index"))

    items = query_all(
        """
        SELECT  mi.*,
                r.name AS restaurant_name
        FROM    menu_items mi
        JOIN    restaurants r ON mi.restaurant_id = r.restaurant_id
        WHERE   mi.category_id  = %s
          AND   mi.is_available = TRUE
          AND   r.is_active     = TRUE
        ORDER BY r.name, mi.name
        """,
        (cid,),
    )

    return render_template(
        "search_results.html",
        results=results_to_compatible(items),
        query=cat["name"],
        get_restaurant=lambda rid: query_one(
            "SELECT * FROM restaurants WHERE restaurant_id = %s", (rid,)
        ),
    )


def results_to_compatible(items):
    """Helper — search_results.html expects the same shape regardless of source."""
    return items

@app.route("/restaurant/<int:rid>/review", methods=["POST"])
@login_required
def submit_review(rid):
    """Insert a customer review. Trigger trg_update_restaurant_rating
    automatically recomputes restaurants.rating after the INSERT."""
    rest = query_one(
        "SELECT restaurant_id FROM restaurants WHERE restaurant_id = %s", (rid,)
    )
    if not rest:
        flash("Restaurant not found.", "danger")
        return redirect(url_for("index"))

    try:
        rating = int(request.form.get("rating", 0))
    except ValueError:
        rating = 0

    if rating < 1 or rating > 5:
        flash("Please pick a rating between 1 and 5 stars.", "warning")
        return redirect(url_for("restaurant_menu", rid=rid))

    comment = request.form.get("comment", "").strip()
    uid = session["user_id"]

    # Enforce one review per customer per restaurant
    existing = query_one(
        "SELECT review_id FROM reviews WHERE customer_id = %s AND restaurant_id = %s",
        (uid, rid),
    )
    if existing:
        flash("You have already reviewed this restaurant.", "info")
        return redirect(url_for("restaurant_menu", rid=rid))

    execute(
        """
        INSERT INTO reviews (customer_id, restaurant_id, rating, comment)
        VALUES (%s, %s, %s, %s)
        """,
        (uid, rid, rating, comment),
    )
    flash("Thank you for your review!", "success")
    return redirect(url_for("restaurant_menu", rid=rid))


#  AUTH ROUTES
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        existing = query_one(
            "SELECT customer_id FROM customers WHERE email = %s", (email,)
        )
        if existing:
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        execute(
            """
            INSERT INTO customers
                (first_name, last_name, email, password_hash, phone, address)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                request.form["first_name"].strip(),
                request.form["last_name"].strip(),
                email,
                generate_password_hash(request.form["password"]),
                request.form.get("phone", ""),
                request.form.get("address", ""),
            ),
        )
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = query_one("SELECT * FROM customers WHERE email = %s", (email,))
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["customer_id"]
            flash(f"Welcome back, {user['first_name']}!", "success")
            return redirect(url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))



#  CART ROUTES (cart lives in the session — not the DB)
@app.route("/cart/add", methods=["POST"])
@login_required
def cart_add():
    item_id = int(request.form["item_id"])
    qty = int(request.form.get("quantity", 1))
    item = query_one("SELECT * FROM menu_items WHERE item_id = %s", (item_id,))
    if not item:
        flash("Item not found.", "danger")
        return redirect(url_for("index"))

    cart = session.get("cart", [])
    existing = next((c for c in cart if c["item_id"] == item_id), None)
    if existing:
        existing["quantity"] += qty
    else:
        cart.append({
            "item_id": item_id,
            "name": item["name"],
            "price": float(item["price"]),
            "quantity": qty,
            "restaurant_id": item["restaurant_id"],
        })
    session["cart"] = cart
    flash(f"Added {item['name']} to cart!", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/cart/remove/<int:item_id>")
@login_required
def cart_remove(item_id):
    cart = session.get("cart", [])
    cart = [c for c in cart if c["item_id"] != item_id]
    session["cart"] = cart
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart_view"))


@app.route("/cart")
@login_required
def cart_view():
    cart = session.get("cart", [])
    total = sum(c["price"] * c["quantity"] for c in cart)
    return render_template("cart.html", cart=cart, total=total)


#  CHECKOUT — wrapped in a single MySQL TRANSACTION
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = session.get("cart", [])
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("index"))

    user = query_one(
        "SELECT * FROM customers WHERE customer_id = %s",
        (session["user_id"],),
    )

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "Cash on Delivery")
        address = request.form.get("address") or user["address"]

        # Group cart items by restaurant — one order per restaurant
        by_restaurant = {}
        for item in cart:
            by_restaurant.setdefault(item["restaurant_id"], []).append(item)

        conn = get_db()
        cur = conn.cursor()
        try:
            # Earlier SELECTs in this request opened an implicit transaction
            # (because autocommit=False). Close it before starting our own
            # explicit one for the atomic checkout.
            if conn.in_transaction:
                conn.commit()

            # ---- BEGIN TRANSACTION (atomic checkout) ----
            conn.start_transaction()

            for rid, items in by_restaurant.items():
                order_total = sum(i["price"] * i["quantity"] for i in items)

                # 1. Create the order row
                cur.execute(
                    """
                    INSERT INTO orders
                        (customer_id, restaurant_id, status,
                         total_amount, delivery_address)
                    VALUES (%s, %s, 'Pending', %s, %s)
                    """,
                    (session["user_id"], rid, order_total, address),
                )
                new_order_id = cur.lastrowid

                # 2. Insert each line item
                #    (the trg_update_order_total_insert trigger will recompute
                #     orders.total_amount automatically)
                cur.executemany(
                    """
                    INSERT INTO order_details
                        (order_id, item_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    [
                        (new_order_id, i["item_id"], i["quantity"], i["price"])
                        for i in items
                    ],
                )

                # 3. Create the payment row
                cur.execute(
                    """
                    INSERT INTO payments
                        (order_id, amount, method, status)
                    VALUES (%s, %s, %s, 'Pending')
                    """,
                    (new_order_id, order_total, payment_method),
                )

            conn.commit()                     # ---- COMMIT ----
        except Exception as exc:
            conn.rollback()                   # ---- ROLLBACK on failure ----
            cur.close()
            flash(f"Checkout failed: {exc}", "danger")
            return redirect(url_for("cart_view"))

        cur.close()
        session["cart"] = []
        flash("Order placed successfully!", "success")
        return redirect(url_for("my_orders"))

    total = sum(c["price"] * c["quantity"] for c in cart)
    return render_template("checkout.html", cart=cart, total=total, user=user)


#  CUSTOMER ORDER VIEWS
@app.route("/my-orders")
@login_required
def my_orders():
    uid = session["user_id"]

    user_orders = query_all(
        """
        SELECT  o.*,
                r.name AS restaurant_name
        FROM    orders o
        JOIN    restaurants r ON o.restaurant_id = r.restaurant_id
        WHERE   o.customer_id = %s
        ORDER BY o.order_id DESC
        """,
        (uid,),
    )

    # Attach line items + payment for each order
    for order in user_orders:
        order["order_items"] = query_all(
            """
            SELECT  od.*,
                    mi.name AS item_name
            FROM    order_details od
            JOIN    menu_items mi ON od.item_id = mi.item_id
            WHERE   od.order_id = %s
            """,
            (order["order_id"],),
        )
        order["payment"] = query_one(
            "SELECT * FROM payments WHERE order_id = %s",
            (order["order_id"],),
        )

    return render_template("my_orders.html", orders=user_orders)


@app.route("/order/<int:oid>/track")
@login_required
def track_order(oid):
    order = query_one(
        """
        SELECT  o.*,
                r.name AS restaurant_name
        FROM    orders o
        JOIN    restaurants r ON o.restaurant_id = r.restaurant_id
        WHERE   o.order_id = %s AND o.customer_id = %s
        """,
        (oid, session["user_id"]),
    )
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("my_orders"))

    statuses = ["Pending", "Confirmed", "Preparing", "Out for Delivery", "Delivered"]
    current_step = statuses.index(order["status"]) if order["status"] in statuses else 0
    return render_template(
        "track_order.html",
        order=order, statuses=statuses, current_step=current_step,
    )


#  ADMIN ROUTES
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        admin = query_one(
            "SELECT * FROM admins WHERE username = %s", (username,)
        )
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["admin_id"]
            flash("Admin login successful.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "danger")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    # Single aggregate query for the four counters
    counts = query_one(
        """
        SELECT
            (SELECT COUNT(*) FROM customers)                                  AS total_customers,
            (SELECT COUNT(*) FROM restaurants WHERE is_active = TRUE)         AS total_restaurants,
            (SELECT COUNT(*) FROM orders)                                     AS total_orders,
            (SELECT COALESCE(SUM(total_amount),0) FROM orders
                WHERE status = 'Delivered')                                   AS total_revenue,
            (SELECT COUNT(*) FROM orders WHERE status = 'Pending')            AS pending_orders
        """
    )

    recent_orders = query_all(
        """
        SELECT  o.*,
                CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
                r.name AS restaurant_name
        FROM    orders o
        JOIN    customers   c ON o.customer_id   = c.customer_id
        JOIN    restaurants r ON o.restaurant_id = r.restaurant_id
        ORDER BY o.order_id DESC
        LIMIT   10
        """
    )

    return render_template(
        "admin_dashboard.html",
        stats=counts,
        recent_orders=recent_orders,
    )


@app.route("/admin/orders")
@admin_required
def admin_orders():
    all_orders = query_all(
        """
        SELECT  o.*,
                CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
                r.name AS restaurant_name
        FROM    orders o
        JOIN    customers   c ON o.customer_id   = c.customer_id
        JOIN    restaurants r ON o.restaurant_id = r.restaurant_id
        ORDER BY o.order_id DESC
        """
    )
    return render_template("admin_orders.html", orders=all_orders)


@app.route("/admin/order/<int:oid>/update", methods=["POST"])
@admin_required
def admin_update_order(oid):
    new_status = request.form["status"]
    execute(
        "UPDATE orders SET status = %s WHERE order_id = %s",
        (new_status, oid),
    )
    if new_status == "Delivered":
        execute(
            "UPDATE payments SET status = 'Completed' WHERE order_id = %s",
            (oid,),
        )
    flash(f"Order #{oid} updated to {new_status}.", "success")
    return redirect(url_for("admin_orders"))


@app.route("/admin/customers")
@admin_required
def admin_customers():
    customers = query_all(
        "SELECT * FROM customers ORDER BY customer_id"
    )
    return render_template("admin_customers.html", customers=customers)


@app.route("/admin/restaurants")
@admin_required
def admin_restaurants():
    restaurants = query_all(
        "SELECT * FROM restaurants ORDER BY restaurant_id"
    )
    return render_template("admin_restaurants.html", restaurants=restaurants)


@app.route("/admin/menu")
@admin_required
def admin_menu():
    items = query_all(
        """
        SELECT  mi.*,
                r.name AS restaurant_name,
                c.name AS category_name
        FROM    menu_items mi
        JOIN    restaurants r ON mi.restaurant_id = r.restaurant_id
        JOIN    categories  c ON mi.category_id   = c.category_id
        ORDER BY r.name, mi.name
        """
    )
    restaurants = query_all("SELECT * FROM restaurants ORDER BY name")
    categories = query_all("SELECT * FROM categories ORDER BY name")
    return render_template(
        "admin_menu.html",
        items=items, restaurants=restaurants, categories=categories,
    )


@app.route("/admin/menu/toggle/<int:iid>")
@admin_required
def admin_toggle_item(iid):
    item = query_one(
        "SELECT * FROM menu_items WHERE item_id = %s", (iid,)
    )
    if item:
        new_state = not item["is_available"]
        execute(
            "UPDATE menu_items SET is_available = %s WHERE item_id = %s",
            (new_state, iid),
        )
        status = "available" if new_state else "unavailable"
        flash(f"{item['name']} is now {status}.", "info")
    return redirect(url_for("admin_menu"))


#  SEARCH
@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return redirect(url_for("index"))

    pattern = f"%{q}%"
    results = query_all(
        """
        SELECT  mi.*,
                r.name AS restaurant_name
        FROM    menu_items mi
        JOIN    restaurants r ON mi.restaurant_id = r.restaurant_id
        WHERE   mi.is_available = TRUE
          AND  (mi.name        LIKE %s
                OR mi.description LIKE %s)
        ORDER BY mi.name
        """,
        (pattern, pattern),
    )

    # Provide a get_restaurant helper for the template (kept for compatibility)
    def get_restaurant(rid):
        return query_one(
            "SELECT * FROM restaurants WHERE restaurant_id = %s", (rid,)
        )

    return render_template(
        "search_results.html",
        results=results, query=q, get_restaurant=get_restaurant,
    )

#  RUN
if __name__ == "__main__":
    app.run(debug=DEBUG, port=PORT)
