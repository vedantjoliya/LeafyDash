import sys
import os
import sqlite3
import datetime
import bcrypt

# Ensure we use the proper hashing method
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

db_path = "database.db"
if not os.path.exists(db_path):
    print("Database file not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Clean up existing tables of user ID 3 (contactsvedant@gmail.com) if they exist
# Get user ID
cursor.execute("SELECT id FROM users WHERE email = 'contactsvedant@gmail.com'")
user_row = cursor.fetchone()

if user_row:
    user_id = user_row[0]
    print(f"Found existing user contactsvedant@gmail.com with ID: {user_id}")
    # Reset password
    pw_hash = get_password_hash("Joliya@283")
    cursor.execute("UPDATE users SET password_hash = ?, status = 'onboarded', business_name = 'LeafyDash Garden Co', industry = 'E-Commerce & Online Sales' WHERE id = ?", (pw_hash, user_id))
    print("Updated user password and business info.")
else:
    # Create user
    pw_hash = get_password_hash("Joliya@283")
    cursor.execute("""
        INSERT INTO users (email, password_hash, business_name, industry, status) 
        VALUES ('contactsvedant@gmail.com', ?, 'LeafyDash Garden Co', 'E-Commerce & Online Sales', 'onboarded')
    """, (pw_hash,))
    user_id = cursor.lastrowid
    print(f"Created new user contactsvedant@gmail.com with ID: {user_id}")

# Cascaded cleanup for this user
cursor.execute("DELETE FROM active_modules WHERE user_id = ?", (user_id,))
cursor.execute("DELETE FROM employees WHERE user_id = ?", (user_id,))
cursor.execute("DELETE FROM operational_expenses WHERE user_id = ?", (user_id,))
cursor.execute("DELETE FROM sales WHERE user_id = ?", (user_id,))
cursor.execute("DELETE FROM products WHERE user_id = ?", (user_id,))
cursor.execute("DELETE FROM locations WHERE user_id = ?", (user_id,))
cursor.execute("DELETE FROM marketing_campaigns WHERE user_id = ?", (user_id,))
cursor.execute("DELETE FROM contact_messages WHERE user_id = ?", (user_id,))
cursor.execute("DELETE FROM admin_messages WHERE user_id = ?", (user_id,))
conn.commit()

# 2. Seed active modules
modules = ["Overview", "Analytics", "Sales", "Inventory", "Reviews", "CRM", "Customers", "Inbox", "Operations", "Settings"]
for mod in modules:
    cursor.execute("INSERT INTO active_modules (user_id, module_name, is_active) VALUES (?, ?, 1)", (user_id, mod))
print("Seeded active modules.")

# 3. Seed locations
locations_data = [
    ("Downtown Garden Center", "101 Greenery St, Downtown", "+1 555-9001", "DowntownGarden@example.com", "Sarah Moss"),
    ("Uptown Plant Boutique", "702 Blossom Ave, Uptown", "+1 555-9002", "UptownBoutique@example.com", "Marcus Leaf")
]

loc_ids = []
for loc in locations_data:
    cursor.execute("""
        INSERT INTO locations (user_id, name, address, phone, email, manager) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, loc[0], loc[1], loc[2], loc[3], loc[4]))
    loc_ids.append(cursor.lastrowid)
print(f"Seeded locations: {loc_ids}")

# 4. Seed products
products_data = [
    (loc_ids[0], "Monstera Deliciosa", "MONST-01", 24, 35.00, 15.00, "/uploads/placeholder_monstera.jpg"),
    (loc_ids[0], "Fiddle Leaf Fig", "FIDDLE-02", 15, 55.00, 25.00, "/uploads/placeholder_fiddle.jpg"),
    (loc_ids[0], "Snake Plant", "SNAKE-03", 40, 20.00, 8.00, "/uploads/placeholder_snake.jpg"),
    (loc_ids[1], "Gardening Gloves", "GLOVE-04", 50, 12.50, 5.00, "/uploads/placeholder_gloves.jpg"),
    (loc_ids[1], "Watering Can", "CAN-05", 30, 22.00, 9.00, "/uploads/placeholder_can.jpg"),
    (loc_ids[1], "Succulent Set", "SUCC-06", 100, 15.00, 6.00, "/uploads/placeholder_succulent.jpg")
]

prod_ids = []
for prod in products_data:
    cursor.execute("""
        INSERT INTO products (user_id, location_id, name, sku, stock, price, buying_price, image_path) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, prod[0], prod[1], prod[2], prod[3], prod[4], prod[5], prod[6]))
    prod_ids.append(cursor.lastrowid)
print(f"Seeded products: {prod_ids}")

# 5. Seed employees
employees_data = [
    ("Alice Smith", "General Manager", 3500.00, "alice@leafydash.com", "+1 555-0122", "Active"),
    ("Bob Vance", "Sales Representative", 2400.00, "bob@leafydash.com", "+1 555-0144", "Active"),
    ("Charlie Brown", "Cashier", 1800.00, "charlie@leafydash.com", "+1 555-0166", "Inactive")
]
for emp in employees_data:
    cursor.execute("""
        INSERT INTO employees (user_id, name, role, salary, email, phone, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, emp[0], emp[1], emp[2], emp[3], emp[4], emp[5]))
print("Seeded employees.")

# 6. Seed expenses
expenses_data = [
    ("Rent", 1500.00, "Downtown retail store lease", datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=10)),
    ("Utilities", 250.00, "Power and water monthly bills", datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=8)),
    ("Software", 85.00, "LeafyDash platform subscription", datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=5)),
    ("Marketing", 400.00, "Local flyers and social media ads", datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=2))
]
for exp in expenses_data:
    cursor.execute("""
        INSERT INTO operational_expenses (user_id, category, amount, description, date) 
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, exp[0], exp[1], exp[2], exp[3].strftime("%Y-%m-%d %H:%M:%S")))
print("Seeded expenses.")

# 7. Seed campaigns
campaigns_data = [
    ("Spring Welcome Promo", "all", "email", "SPRING10", "percentage", 10.0, "Welcome to spring! Get 10% off all plants.", 3),
    ("VIP Greenery Care", "vip", "whatsapp", "VIPCARE", "amount", 20.0, "Thanks for being a loyal customer. Enjoy $20 off your next order.", 1)
]

camp_ids = []
for camp in campaigns_data:
    cursor.execute("""
        INSERT INTO marketing_campaigns (user_id, name, segment, channel, coupon_code, discount_type, discount_value, message_body, recipients_count) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, camp[0], camp[1], camp[2], camp[3], camp[4], camp[5], camp[6], camp[7]))
    camp_ids.append(cursor.lastrowid)
print(f"Seeded campaigns: {camp_ids}")

# 8. Seed sales and sale items
now = datetime.datetime.now(datetime.UTC)

sales_data = [
    # 5 days ago
    {
        "days_ago": 5, "amount": 120.00, "location_id": loc_ids[0], "location": "Downtown Garden Center",
        "name": "Emma Watson", "email": "emma@example.com", "phone": "+1 555-1111", "address": "12 Hollywood Blvd, LA",
        "items": [(prod_ids[1], 1, 55.00, "Fiddle Leaf Fig"), (prod_ids[2], 2, 40.00, "Snake Plant"), (prod_ids[3], 2, 25.00, "Gardening Gloves")]
    },
    # 4 days ago
    {
        "days_ago": 4, "amount": 70.00, "location_id": loc_ids[0], "location": "Downtown Garden Center",
        "name": "Brad Pitt", "email": "brad@example.com", "phone": "+1 555-2222", "address": "45 Sunset Dr, Malibu",
        "items": [(prod_ids[0], 2, 70.00, "Monstera Deliciosa")]
    },
    # 3 days ago
    {
        "days_ago": 3, "amount": 247.00, "location_id": loc_ids[1], "location": "Uptown Plant Boutique",
        "name": "Angelina Jolie", "email": "angelina@example.com", "phone": "+1 555-3333", "address": "78 French Riviera Rd, Nice",
        "items": [(prod_ids[1], 3, 165.00, "Fiddle Leaf Fig"), (prod_ids[5], 4, 60.00, "Succulent Set"), (prod_ids[4], 1, 22.00, "Watering Can")]
    },
    # 2 days ago
    {
        "days_ago": 2, "amount": 15.00, "location_id": loc_ids[1], "location": "Uptown Plant Boutique",
        "name": "Keanu Reeves", "email": "keanu@example.com", "phone": "+1 555-4444", "address": "99 Matrix Way, Neo City",
        "items": [(prod_ids[5], 1, 15.00, "Succulent Set")]
    },
    # 1 day ago
    {
        "days_ago": 1, "amount": 185.00, "location_id": loc_ids[0], "location": "Downtown Garden Center",
        "name": "Johnny Depp", "email": "johnny@example.com", "phone": "+1 555-5555", "address": "3 Pirate Cove, Caribbean",
        "items": [(prod_ids[0], 1, 35.00, "Monstera Deliciosa"), (prod_ids[1], 2, 110.00, "Fiddle Leaf Fig"), (prod_ids[4], 2, 40.00, "Watering Can")]
    },
    # Today
    {
        "days_ago": 0, "amount": 110.00, "location_id": loc_ids[0], "location": "Downtown Garden Center",
        "name": "Emma Watson", "email": "emma@example.com", "phone": "+1 555-1111", "address": "12 Hollywood Blvd, LA",
        "items": [(prod_ids[2], 2, 40.00, "Snake Plant"), (prod_ids[5], 2, 30.00, "Succulent Set"), (prod_ids[4], 2, 40.00, "Watering Can")]
    }
]

for s in sales_data:
    sale_time = now - datetime.timedelta(days=s["days_ago"])
    cursor.execute("""
        INSERT INTO sales (user_id, location_id, amount, location, customer_name, customer_email, customer_phone, customer_address, timestamp) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, s["location_id"], s["amount"], s["location"], s["name"], s["email"], s["phone"], s["address"], sale_time.strftime("%Y-%m-%d %H:%M:%S")))
    sale_id = cursor.lastrowid
    
    # Decrement stock and add items
    for item in s["items"]:
        cursor.execute("UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?", (item[1], item[0]))
        cursor.execute("""
            INSERT INTO sale_items (sale_id, product_id, quantity, amount, item_name) 
            VALUES (?, ?, ?, ?, ?)
        """, (sale_id, item[0], item[1], item[2], item[3]))
print("Seeded sales logs and decremented product stocks.")

# 9. Seed campaign customer tracking
# Link to today's sale for converted campaign
cursor.execute("SELECT id FROM sales WHERE customer_email = 'emma@example.com' AND user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
emma_sale_id = cursor.fetchone()[0]

cursor.execute("""
    INSERT INTO campaign_customer_tracking (campaign_id, customer_email, clicked, clicked_at, converted, sale_id) 
    VALUES (?, 'emma@example.com', 1, ?, 1, ?)
""", (camp_ids[0], (now - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), emma_sale_id))

cursor.execute("""
    INSERT INTO campaign_customer_tracking (campaign_id, customer_email, clicked, clicked_at, converted, sale_id) 
    VALUES (?, 'brad@example.com', 1, ?, 0, NULL)
""", (camp_ids[0], (now - datetime.timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")))

cursor.execute("""
    INSERT INTO campaign_customer_tracking (campaign_id, customer_email, clicked, clicked_at, converted, sale_id) 
    VALUES (?, 'johnny@example.com', 0, NULL, 0, NULL)
""", (camp_ids[0],))

cursor.execute("""
    INSERT INTO campaign_customer_tracking (campaign_id, customer_email, clicked, clicked_at, converted, sale_id) 
    VALUES (?, 'angelina@example.com', 0, NULL, 0, NULL)
""", (camp_ids[1],))
print("Seeded campaign customer tracking.")

# 10. Seed support inbox messages
cursor.execute("""
    INSERT INTO admin_messages (user_id, subject, message, is_read, created_at) 
    VALUES (?, 'Welcome to LeafyDash Platform!', 'Hi there! Welcome to your new business dashboard. Please explore our onboarding and configuration guides under the Settings module if you have any questions.', 0, ?)
""", (user_id, (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")))

cursor.execute("""
    INSERT INTO admin_messages (user_id, subject, message, is_read, created_at) 
    VALUES (?, 'Scheduled System Maintenance', 'We will perform regular backend system upgrades tonight at 02:00 AM UTC. Expect brief interruptions in storefront checkout connectivity.', 1, ?)
""", (user_id, (now - datetime.timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")))

cursor.execute("""
    INSERT INTO contact_messages (user_id, category, subject, message, status, created_at) 
    VALUES (?, 'Feature Request', 'Adding customer loyalty points', 'It would be great to track customer loyalty points on the Customers tab. Any plans to add this?', 'New', ?)
""", (user_id, (now - datetime.timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")))
print("Seeded support messages and inbox notifications.")

# 11. Seed reviews for customers so they exist in CRM and reviews dashboard
cursor.execute("""
    INSERT INTO reviews (user_id, location_id, customer_name, rating, comment, status, created_at) 
    VALUES (?, ?, 'Brad Pitt', 4, 'Excellent Monstera plants, very healthy and fast shipping.', 'New', ?)
""", (user_id, loc_ids[0], (now - datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")))

cursor.execute("""
    INSERT INTO reviews (user_id, location_id, customer_name, rating, comment, status, created_at) 
    VALUES (?, ?, 'Johnny Depp', 5, 'Highly recommend. The fiddle leaf figs are thriving in my living room.', 'Resolved', ?)
""", (user_id, loc_ids[0], (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")))
print("Seeded customer reviews.")

conn.commit()
conn.close()
print("All mock data seeded for user contactsvedant@gmail.com successfully.")
