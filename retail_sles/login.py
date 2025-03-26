from flask import Flask, render_template, request, redirect, url_for,flash,Response
import sqlite3
import matplotlib
matplotlib.use('Agg')  # Ensure non-GUI backend
# For database connection
import matplotlib.pyplot as plt  # For generating product charts
import seaborn as sns
import io                              # For handling in-memory image data
import base64    
import os# For encoding chart images to base64
from matplotlib import table


app = Flask(__name__)
app.secret_key = os.urandom(24)  # 24-byte random key


# Database connection helper
def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect('login_system.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create admin, staff, and customer tables if they don't exist
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS customer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
        
        DROP TABLE IF EXISTS products;

        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            stock_available INTEGER NOT NULL,
            required_stock INTEGER NOT NULL,
            sales INTEGER NOT NULL,
            profit REAL NOT NULL,
            loss REAL NOT NULL,
            shipment_date TEXT NOT NULL
        );

    ''')

    # Insert sample data if empty
    cursor.execute("INSERT OR IGNORE INTO admin (username, password) VALUES ('admin1', 'admin123')")
    cursor.execute("INSERT OR IGNORE INTO staff (username, password) VALUES ('staff1', 'staff123')")
    cursor.execute("INSERT OR IGNORE INTO customer (username, password) VALUES ('customer1', 'customer123')")
    
    cursor.execute('''
        INSERT OR IGNORE INTO products (id,product_name, price, stock_available, required_stock, sales, profit, loss, shipment_date)
        VALUES 
        (101,'Laptop', 1200.0, 50, 100, 200, 5000.0, 200.0, '2023-10-01'),
        (102,'Smartphone', 800.0, 100, 150, 300, 7000.0, 100.0, '2023-10-05'),
        (103,'Tablet', 600.0, 75, 120, 150, 3000.0, 50.0, '2023-10-10')
    ''')

    conn.commit()
    conn.close()

# Validate user login
def login(username, password, user_type):
    table = {"admin": "admin", "staff": "staff", "customer": "customer"}.get(user_type)
    if not table:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table} WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    conn.close()
    return user is not None

# Fetch all users from all roles
def fetch_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, 'admin' AS role FROM admin
        UNION
        SELECT id, username, 'staff' AS role FROM staff
        UNION
        SELECT id, username, 'customer' AS role FROM customer
    ''')
    users = cursor.fetchall()

    conn.close()
    return users

# Fetch all products from the database
def fetch_products():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, product_name, price, stock_available, required_stock, 
               sales, profit, loss, shipment_date 
        FROM products
    ''')
    products = cursor.fetchall()

    conn.close()
    return products

# Home Page
@app.route("/")
def home():
    return render_template("home.html")

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_type = request.form["userType"]

        if login(username, password, user_type):
            return redirect(url_for(f"{user_type}_dashboard"))
        else:
            return "Invalid credentials or user type."
    return render_template("login.html")

# Admin Dashboard
@app.route("/admin_dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

# Staff Dashboard
@app.route("/staff_dashboard")
def staff_dashboard():
    return render_template("staff_dashboard.html")

# Customer Dashboard
@app.route("/customer_dashboard")
def customer_dashboard():
    conn = sqlite3.connect('login_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, product_name, price, stock_available FROM products")
    products = cursor.fetchall()
    conn.close()
    print(products)  # Debugging: Check the output in the terminal
    return render_template("customer_dashboard.html", products=products)


# View Users (Admin Only)
@app.route("/view_users")
def view_users():
    users = fetch_all_users()
    return render_template("view_users.html", users=users)

# Add User (Admin Only)
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        user_type = request.form.get("user_type")
        username = request.form.get("username")
        password = request.form.get("password")

        role_table_map = {"admin": "admin", "staff": "staff", "customer": "customer"}

        if user_type not in role_table_map:
            return "Invalid user type.", 400

        table = role_table_map[user_type]

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(f"INSERT INTO {table} (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()

            return redirect(url_for("view_users"))

        except sqlite3.IntegrityError:
            return "Username already exists!", 400

    return render_template("add_user.html")

# Edit User
@app.route("/edit_user/<role>/<int:user_id>", methods=["GET", "POST"])
def edit_user(role, user_id):
    role_table_map = {"admin": "admin", "staff": "staff", "customer": "customer"}
    if role not in role_table_map:
        return "Invalid role.", 400

    table = role_table_map[role]

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        new_username = request.form["username"]
        new_password = request.form["password"]

        cursor.execute(f"UPDATE {table} SET username = ?, password = ? WHERE id = ?", (new_username, new_password, user_id))
        conn.commit()
        conn.close()

        return redirect(url_for("view_users"))

    cursor.execute(f"SELECT id, username FROM {table} WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return "User not found.", 404

    return render_template("edit_user.html", user=user, role=role)

# Delete User
@app.route("/delete_user/<role>/<int:user_id>", methods=["GET"])
def delete_user(role, user_id):
    role_table_map = {"admin": "admin", "staff": "staff", "customer": "customer"}
    if role not in role_table_map:
        return "Invalid role.", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("view_users"))

# Change User Role
@app.route("/change_role/<old_role>/<int:user_id>", methods=["POST"])
def change_role(old_role, user_id):
    new_role = request.form["new_role"]

    role_table_map = {"admin": "admin", "staff": "staff", "customer": "customer"}
    if old_role not in role_table_map or new_role not in role_table_map:
        return "Invalid role.", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT username, password FROM {role_table_map[old_role]} WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return "User not found.", 404

    username, password = user

    cursor.execute(f"DELETE FROM {role_table_map[old_role]} WHERE id = ?", (user_id,))
    cursor.execute(f"INSERT INTO {role_table_map[new_role]} (username, password) VALUES (?, ?)", (username, password))

    conn.commit()
    conn.close()

    return redirect(url_for("view_users"))

# View Products (Admin Only)
@app.route("/view_products")
def view_products():
    products = fetch_products()
    chart_url = generate_product_chart(products)
    return render_template("view_products.html", products=products)


# Generate product chart using matplotlib
def generate_product_chart(products):
    product_names = [product['product_name'] for product in products]
    sales = [product['sales'] for product in products]
    profits = [product['profit'] for product in products]
    losses = [product['loss'] for product in products]

    plt.figure(figsize=(10, 6))
    plt.bar(product_names, sales, label='Sales (₹)', color='blue', alpha=0.7)
    plt.plot(product_names, profits, marker='o', color='green', label='Profit (₹)')
    plt.plot(product_names, losses, marker='x', color='red', label='Loss (₹)')

    plt.title('Product Sales and Profit/Loss Overview', fontsize=16)
    plt.xlabel('Products', fontsize=14)
    plt.ylabel('Values in ₹', fontsize=14)
    plt.legend()
    plt.grid(True)

    # Save chart as base64 image
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return f"data:image/png;base64,{chart_url}"

# Route: Display Add Product Form (GET Method)
@app.route('/add_product_form', methods=['GET'])
def add_product_form():
    return render_template('add_product.html')

# Route: Handle Product Addition (POST Method)
# Add Product (Admin Only)
@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        # Get form data
        id=int(request.form.get("id")or 0)
        product_name = request.form.get("product_name")
        price = float(request.form.get("price") or 0)
        stock_available = int(request.form.get("stock_available") or 0)
        required_stock = int(request.form.get("required_stock") or 0)
        sales = max(0, int(request.form.get("sales") or 0))  # Ensure non-negative
        profit = float(request.form.get("profit") or 0)
        loss = float(request.form.get("loss") or 0)
        shipment_date = request.form.get("shipment_date")

        # Basic validation: Ensure required fields
        if not product_name or not shipment_date:
            return "Product name and shipment date are required!", 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert product data into 'products' table
            cursor.execute("""
                INSERT INTO products 
                (id,product_name, price, stock_available, required_stock, sales, profit, loss, shipment_date) 
                VALUES (?,?, ?, ?, ?, ?, ?, ?, ?)
            """, (id,product_name, price, stock_available, required_stock, sales, profit, loss, shipment_date))

            conn.commit()
            conn.close()

            return redirect(url_for("view_products"))  # Redirect to products view page

        except sqlite3.IntegrityError:
            return "Product with this name already exists!", 400
        except Exception as e:
            return f"Error: {str(e)}", 500

    return render_template("add_product.html")


# Edit Product
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if request.method == 'POST':
        id=request.form.get("id")
        product_name = request.form['product_name']
        price = float(request.form['price'])
        stock_available = int(request.form['stock_available'])
        required_stock = int(request.form['required_stock'])
        shipment_date = request.form['shipment_date']

        conn.execute('''
            UPDATE products
            SET id=?, product_name = ?, price = ?, stock_available = ?, required_stock = ?, shipment_date = ?
            WHERE id = ?
        ''', (id,product_name, price, stock_available, required_stock, shipment_date, product_id))
        conn.commit()
        conn.close()

        flash('Product Updated Successfully!', 'success')
        return redirect(url_for('view_products'))
    conn.close()
    return render_template('edit_product.html', product=product)

# Delete Product
@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

    flash('Product Deleted Successfully!', 'danger')
    return redirect(url_for('view_products'))

# Route to view reports
@app.route("/view_reports")
def view_reports():
    return render_template("view_reports.html")

# Chart: Sales Analysis (Pie + Bar Chart)
@app.route("/sales_chart")
def sales_chart():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, sales FROM products")
    data = cursor.fetchall()
    conn.close()

    product_names = [row["product_name"] for row in data]
    sales = [row["sales"] for row in data]

    # Create Pie and Bar Chart
    fig, axs = plt.subplots(1, 2, figsize=(14, 6))

    # Pie Chart
    axs[0].pie(sales, labels=product_names, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("Set2"))
    axs[0].set_title("Sales Distribution (Pie Chart)")

    # Bar Chart
    sns.barplot(x=sales, y=product_names, ax=axs[1], palette="Greens_d")
    axs[1].set_title("Total Sales Per Product")
    axs[1].set_xlabel("Sales")
    axs[1].set_ylabel("Product Name")

    plt.tight_layout()

    # Save to memory and return image
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return Response(img.getvalue(), mimetype="image/png")


# Chart: Profit & Loss Overview
@app.route("/profit_loss_chart")
def profit_loss_chart():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, profit, loss FROM products")
    data = cursor.fetchall()
    conn.close()

    labels = [row["product_name"] for row in data]
    profit = [row["profit"] for row in data]
    loss = [row["loss"] for row in data]

    plt.figure(figsize=(10, 6))
    plt.pie(profit, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title("Profit Distribution")
    plt.axis("equal")

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return Response(img.getvalue(), mimetype="image/png")

# Chart: Stock Distribution
@app.route("/stock_chart")
def stock_chart():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, stock_available FROM products")
    data = cursor.fetchall()
    conn.close()

    labels = [row["product_name"] for row in data]
    stock = [row["stock_available"] for row in data]

    plt.figure(figsize=(10, 6))
    sns.barplot(x=stock, y=labels, palette="Greens_r")
    plt.title("Stock Availability by Product")
    plt.xlabel("Stock Available")
    plt.ylabel("Product Name")

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return Response(img.getvalue(), mimetype="image/png")


# Logout
@app.route("/logout")
def logout():
    return redirect(url_for("login_page"))

# Initialize database and run the app
if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)