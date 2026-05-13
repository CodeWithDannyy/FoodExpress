CREATE DATABASE IF NOT EXISTS food_ordering_db;
USE food_ordering_db;

CREATE TABLE categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    description   TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


CREATE TABLE restaurants (
    restaurant_id INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    address       VARCHAR(255) NOT NULL,
    phone         VARCHAR(20),
    email         VARCHAR(100) UNIQUE,
    rating        DECIMAL(2,1) DEFAULT 0.0,
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;



CREATE TABLE customers (
    customer_id   INT AUTO_INCREMENT PRIMARY KEY,
    first_name    VARCHAR(50) NOT NULL,
    last_name     VARCHAR(50) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone         VARCHAR(20),
    address       VARCHAR(255),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


CREATE TABLE admins (
    admin_id      INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) NOT NULL UNIQUE,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE menu_items (
    item_id       INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id INT NOT NULL,
    category_id   INT NOT NULL,
    name          VARCHAR(150) NOT NULL,
    description   TEXT,
    price         DECIMAL(10,2) NOT NULL,
    image_url     VARCHAR(255),
    is_available  BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_restaurant (restaurant_id),
    INDEX idx_category   (category_id)
) ENGINE=InnoDB;

CREATE TABLE orders (
    order_id      INT AUTO_INCREMENT PRIMARY KEY,
    customer_id   INT NOT NULL,
    restaurant_id INT NOT NULL,
    order_date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status        ENUM('Pending','Confirmed','Preparing','Out for Delivery','Delivered','Cancelled')
                  DEFAULT 'Pending',
    total_amount  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    delivery_address VARCHAR(255),

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_customer   (customer_id),
    INDEX idx_restaurant (restaurant_id),
    INDEX idx_status     (status)
) ENGINE=InnoDB;


CREATE TABLE order_details (
    detail_id     INT AUTO_INCREMENT PRIMARY KEY,
    order_id      INT NOT NULL,
    item_id       INT NOT NULL,
    quantity      INT NOT NULL DEFAULT 1,
    unit_price    DECIMAL(10,2) NOT NULL,
    subtotal      DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,

    FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (item_id) REFERENCES menu_items(item_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_order (order_id)
) ENGINE=InnoDB;


CREATE TABLE payments (
    payment_id    INT AUTO_INCREMENT PRIMARY KEY,
    order_id      INT NOT NULL UNIQUE,
    payment_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount        DECIMAL(10,2) NOT NULL,
    method        ENUM('Cash on Delivery','Online') NOT NULL,
    status        ENUM('Pending','Completed','Failed','Refunded') DEFAULT 'Pending',

    FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE reviews (
    review_id     INT AUTO_INCREMENT PRIMARY KEY,
    customer_id   INT NOT NULL,
    restaurant_id INT NOT NULL,
    rating        INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment       TEXT,
    review_date   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;



-- TRIGGERS


-- Auto-update order total when order_details are inserted
DELIMITER //
CREATE TRIGGER trg_update_order_total_insert
AFTER INSERT ON order_details
FOR EACH ROW
BEGIN
    UPDATE orders
    SET total_amount = (
        SELECT COALESCE(SUM(subtotal), 0)
        FROM order_details
        WHERE order_id = NEW.order_id
    )
    WHERE order_id = NEW.order_id;
END //

-- Auto-update order total when order_details are deleted
CREATE TRIGGER trg_update_order_total_delete
AFTER DELETE ON order_details
FOR EACH ROW
BEGIN
    UPDATE orders
    SET total_amount = (
        SELECT COALESCE(SUM(subtotal), 0)
        FROM order_details
        WHERE order_id = OLD.order_id
    )
    WHERE order_id = OLD.order_id;
END //

-- Update restaurant avg rating when a review is added
CREATE TRIGGER trg_update_restaurant_rating
AFTER INSERT ON reviews
FOR EACH ROW
BEGIN
    UPDATE restaurants
    SET rating = (
        SELECT ROUND(AVG(rating), 1)
        FROM reviews
        WHERE restaurant_id = NEW.restaurant_id
    )
    WHERE restaurant_id = NEW.restaurant_id;
END //
DELIMITER ;


-- ============================================================
-- VIEWS
-- ============================================================

-- Customer order summary
CREATE VIEW vw_customer_orders AS
SELECT
    o.order_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.email AS customer_email,
    r.name AS restaurant_name,
    o.order_date,
    o.status,
    o.total_amount,
    p.method AS payment_method,
    p.status AS payment_status
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN restaurants r ON o.restaurant_id = r.restaurant_id
LEFT JOIN payments p ON o.order_id = p.order_id;

-- Restaurant revenue report
CREATE VIEW vw_restaurant_revenue AS
SELECT
    r.restaurant_id,
    r.name AS restaurant_name,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_revenue,
    r.rating
FROM restaurants r
LEFT JOIN orders o ON r.restaurant_id = o.restaurant_id
    AND o.status = 'Delivered'
GROUP BY r.restaurant_id, r.name, r.rating;

-- Popular items
CREATE VIEW vw_popular_items AS
SELECT
    mi.item_id,
    mi.name AS item_name,
    r.name AS restaurant_name,
    mi.price,
    COUNT(od.detail_id) AS times_ordered,
    SUM(od.quantity) AS total_qty_sold
FROM menu_items mi
JOIN order_details od ON mi.item_id = od.item_id
JOIN restaurants r ON mi.restaurant_id = r.restaurant_id
GROUP BY mi.item_id, mi.name, r.name, mi.price
ORDER BY times_ordered DESC;



-- SAMPLE DATA


-- Categories
INSERT INTO categories (name, description) VALUES
('Burgers',    'Beef, chicken, and veggie burgers'),
('Pizza',      'Classic and gourmet pizzas'),
('Biryani',    'Authentic desi rice dishes'),
('Chinese',    'Noodles, rice, and stir-fry'),
('Desserts',   'Sweets and ice cream'),
('Beverages',  'Drinks and refreshments');

-- Restaurants (original 4)
INSERT INTO restaurants (name, address, phone, email) VALUES
('Burger Lab',      'Shahrah-e-Faisal, Karachi',  '0321-1234567', 'info@burgerlab.pk'),
('Pizza Point',     'Tariq Road, Karachi',         '0333-7654321', 'hello@pizzapoint.pk'),
('Student Biryani', 'Bahadurabad, Karachi',         '0300-1112233', 'order@studentbiryani.pk'),
('Ginsoy',          'Clifton, Karachi',             '0312-9998877', 'eat@ginsoy.pk');

-- Additional restaurants (5 more — beverage-focused expansion)
INSERT INTO restaurants (name, address, phone, email) VALUES
('Howdy',          'Khadda Market, DHA, Karachi',     '0321-5556677', 'eat@howdy.pk'),
('The Juice Box',  'Zamzama, DHA Phase 5, Karachi',   '0322-1239876', 'orders@juicebox.pk'),
('Cinnabon',       'Dolmen Mall Clifton, Karachi',    '0300-1122334', 'hello@cinnabon.pk'),
('Karachi Broast', 'Tariq Road, Karachi',             '0333-9988776', 'orders@karachibroast.pk'),
('OPTP',           'Bukhari Commercial, DHA, Karachi','0345-4561230', 'order@optp.pk');

-- Customers
INSERT INTO customers (first_name, last_name, email, password_hash, phone, address) VALUES
('Bazil',   'Khan',    'bazil@example.com',   'pbkdf2:sha256:hashed_pw_1', '0321-1111111', 'FAST NUCES, Karachi'),
('Daniyal', 'Tejani',  'daniyal@example.com', 'pbkdf2:sha256:hashed_pw_2', '0333-2222222', 'Gulshan, Karachi'),
('Abdul',   'Manan',   'manan@example.com',   'pbkdf2:sha256:hashed_pw_3', '0300-3333333', 'North Nazimabad, Karachi');

-- Admin
INSERT INTO admins (username, email, password_hash) VALUES
('admin', 'admin@foodorder.pk', 'pbkdf2:sha256:hashed_admin_pw');

-- Menu Items
INSERT INTO menu_items (restaurant_id, category_id, name, description, price, image_url) VALUES
-- Burger Lab
(1, 1, 'Classic Smash Burger',   'Double smashed patty with cheese',            650.00,  'burger1.jpg'),
(1, 1, 'Mushroom Swiss Burger',  'Sauteed mushrooms and swiss cheese',          750.00,  'burger2.jpg'),
(1, 6, 'Chocolate Shake',        'Thick chocolate milkshake',                   350.00,  'shake1.jpg'),
-- Pizza Point
(2, 2, 'Pepperoni Pizza',        'Classic pepperoni with mozzarella — Large',   1200.00, 'pizza1.jpg'),
(2, 2, 'BBQ Chicken Pizza',      'Grilled chicken with BBQ sauce — Large',     1350.00, 'pizza2.jpg'),
(2, 6, 'Mint Lemonade',          'Fresh mint with lemon',                        250.00, 'drink1.jpg'),
-- Student Biryani
(3, 3, 'Chicken Biryani',        'Aromatic spiced rice with chicken',            350.00, 'biryani1.jpg'),
(3, 3, 'Beef Biryani',           'Tender beef with fragrant rice',              400.00, 'biryani2.jpg'),
(3, 6, 'Raita',                  'Yogurt side with cucumber',                   100.00, 'raita.jpg'),
-- Ginsoy
(4, 4, 'Chicken Manchurian',     'Fried chicken in tangy sauce',                550.00, 'chinese1.jpg'),
(4, 4, 'Egg Fried Rice',         'Classic egg fried rice',                      450.00, 'chinese2.jpg'),
(4, 5, 'Fried Ice Cream',        'Crispy coated ice cream',                     300.00, 'dessert1.jpg');

-- Additional menu items for the 5 new restaurants (uses subqueries so IDs don't matter)
INSERT INTO menu_items (restaurant_id, category_id, name, description, price, image_url) VALUES
-- Howdy (Burgers + Beverages)
((SELECT restaurant_id FROM restaurants WHERE name='Howdy'),
 (SELECT category_id   FROM categories  WHERE name='Burgers'),
 'Big Howdy Burger',     'Quarter-pound beef patty with cheddar and bacon',  850.00, 'howdy1.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='Howdy'),
 (SELECT category_id   FROM categories  WHERE name='Burgers'),
 'Spicy Chicken Howdy',  'Crispy fried chicken with jalapeño mayo',          780.00, 'howdy2.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='Howdy'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Oreo Shake',           'Thick milkshake blended with crushed Oreos',       400.00, 'howdy3.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='Howdy'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Iced Lemon Tea',       'Refreshing chilled lemon tea',                     250.00, 'howdy4.jpg'),

-- The Juice Box (Beverages-focused)
((SELECT restaurant_id FROM restaurants WHERE name='The Juice Box'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Mango Smoothie',       'Fresh mango blended with yoghurt',                 350.00, 'jb1.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='The Juice Box'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Strawberry Banana',    'Strawberry-banana smoothie with honey',            380.00, 'jb2.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='The Juice Box'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Watermelon Cooler',    'Iced watermelon juice with mint',                  280.00, 'jb3.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='The Juice Box'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Mojito (Virgin)',      'Lime, mint, soda — non-alcoholic',                 320.00, 'jb4.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='The Juice Box'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Espresso',             'Single-shot Italian espresso',                     220.00, 'jb5.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='The Juice Box'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Cappuccino',           'Espresso with steamed milk and foam',              300.00, 'jb6.jpg'),

-- Cinnabon (Desserts + Beverages)
((SELECT restaurant_id FROM restaurants WHERE name='Cinnabon'),
 (SELECT category_id   FROM categories  WHERE name='Desserts'),
 'Classic Roll',         'Original Cinnabon cinnamon roll',                  450.00, 'cb1.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='Cinnabon'),
 (SELECT category_id   FROM categories  WHERE name='Desserts'),
 'Caramel PecanBon',     'Cinnabon with caramel and pecans',                 550.00, 'cb2.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='Cinnabon'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Chillata',             'Frozen blended coffee drink',                      380.00, 'cb3.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='Cinnabon'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Hot Chocolate',        'Rich, creamy hot chocolate',                       320.00, 'cb4.jpg'),

-- Karachi Broast (Burgers + Biryani + Beverages)
((SELECT restaurant_id FROM restaurants WHERE name='Karachi Broast'),
 (SELECT category_id   FROM categories  WHERE name='Burgers'),
 'Broast Burger',        'Crispy chicken broast burger with garlic mayo',    520.00, 'kb1.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='Karachi Broast'),
 (SELECT category_id   FROM categories  WHERE name='Burgers'),
 'Zinger Burger',        'Spicy crispy chicken zinger',                      550.00, 'kb2.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='Karachi Broast'),
 (SELECT category_id   FROM categories  WHERE name='Biryani'),
 'Special Chicken Biryani','Karachi-style biryani with raita',               380.00, 'kb3.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='Karachi Broast'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Pepsi (Regular)',      '500ml bottle',                                     180.00, 'kb4.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='Karachi Broast'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Mineral Water',        'Nestle 500ml',                                     80.00,  'kb5.jpg'),

-- OPTP (Burgers + Beverages)
((SELECT restaurant_id FROM restaurants WHERE name='OPTP'),
 (SELECT category_id   FROM categories  WHERE name='Burgers'),
 'Truffle Mushroom',     'Beef patty with truffle aioli and mushrooms',     1100.00, 'optp1.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='OPTP'),
 (SELECT category_id   FROM categories  WHERE name='Burgers'),
 'Crispy Chicken Slider','Mini fried chicken sliders (3 pcs)',                850.00, 'optp2.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='OPTP'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Strawberry Lemonade',  'Fresh strawberry & lemon mix',                     320.00, 'optp3.jpg'),
((SELECT restaurant_id FROM restaurants WHERE name='OPTP'),
 (SELECT category_id   FROM categories  WHERE name='Beverages'),
 'Cold Brew Coffee',     'Slow-steeped 16oz cold brew',                      350.00, 'optp4.jpg');

-- Sample Orders
INSERT INTO orders (customer_id, restaurant_id, status, delivery_address) VALUES
(1, 1, 'Delivered',        'FAST NUCES, Karachi'),
(2, 3, 'Preparing',        'Gulshan, Karachi'),
(3, 4, 'Pending',          'North Nazimabad, Karachi'),
(1, 2, 'Confirmed',        'FAST NUCES, Karachi');

-- Order Details
INSERT INTO order_details (order_id, item_id, quantity, unit_price) VALUES
(1, 1, 2, 650.00),
(1, 3, 1, 350.00),
(2, 7, 3, 350.00),
(2, 9, 3, 100.00),
(3, 10, 1, 550.00),
(3, 11, 2, 450.00),
(4, 4, 1, 1200.00),
(4, 6, 2, 250.00);

-- Payments
INSERT INTO payments (order_id, amount, method, status) VALUES
(1, 1650.00, 'Online',            'Completed'),
(2, 1350.00, 'Cash on Delivery',  'Pending'),
(3, 1450.00, 'Online',            'Pending'),
(4, 1700.00, 'Cash on Delivery',  'Pending');

-- Reviews
INSERT INTO reviews (customer_id, restaurant_id, rating, comment) VALUES
(1, 1, 5, 'Best burgers in Karachi!'),
(2, 3, 4, 'Great biryani, slightly oily though'),
(3, 4, 4, 'Manchurian was amazing');



-- SAMPLE ADVANCED QUERIES


-- Q1: Total revenue per restaurant (delivered orders only)
-- SELECT * FROM vw_restaurant_revenue;

-- Q2: Top 3 most ordered items
-- SELECT * FROM vw_popular_items LIMIT 3;

-- Q3: Customers who have spent more than Rs. 1500 in total
SELECT CONCAT(c.first_name,' ',c.last_name) AS customer,
       SUM(o.total_amount) AS total_spent
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'Delivered'
GROUP BY c.customer_id
HAVING total_spent > 1500;

-- Q4: Average order value per restaurant
-- SELECT r.name, ROUND(AVG(o.total_amount),2) AS avg_order_value
-- FROM restaurants r
-- JOIN orders o ON r.restaurant_id = o.restaurant_id
-- GROUP BY r.restaurant_id;

-- Q5: Monthly order count
-- SELECT DATE_FORMAT(order_date, '%Y-%m') AS month,
--        COUNT(*) AS order_count
-- FROM orders
-- GROUP BY month
-- ORDER BY month;

USE food_ordering_db;

SHOW TABLES;
SELECT COUNT(*) AS restaurants_count FROM restaurants;
SELECT COUNT(*) AS menu_items_count FROM menu_items;
SELECT COUNT(*) AS orders_count FROM orders;
SELECT * FROM vw_restaurant_revenue;
SELECT * FROM vw_popular_items LIMIT 3;


