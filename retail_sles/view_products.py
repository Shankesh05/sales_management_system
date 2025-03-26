from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3

# Blueprint setup for modular structure
view_products_bp = Blueprint('view_products', __name__)

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route: Display products and analytics
@view_products_bp.route('/view_products', methods=['GET', 'POST'])
def view_products():
    conn = get_db_connection()

    try:
        # Fetch all products from the database
        products = conn.execute('SELECT * FROM products').fetchall()
    except Exception as e:
        flash(f'Error fetching products: {str(e)}', 'danger')
        products = []
    finally:
        conn.close()

    return render_template('view_products.html', products=products)

# Route: Add a new product
@view_products_bp.route('/add_product', methods=['POST'])
def add_product():
    try:
        id=request.form.get('id')
        product_name = request.form.get('name')
        price = float(request.form.get('price') or 0)
        stock_available = int(request.form.get('stock_available') or 0)
        stock_required = int(request.form.get('stock_required') or 0)
        sales = int(request.form.get('sales') or 0)  # ✅ Ensure fallback to 0
        profit = float(request.form.get('profit') or 0)
        loss = float(request.form.get('loss') or 0)
        shipment_date = request.form.get('shipment_date')

        # Validate mandatory fields
        if not all([product_name, shipment_date]):
            flash('Missing required fields.', 'danger')
            return redirect(url_for('view_products.view_products'))

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO products (id,product_name, price, stock_available, stock_required, sales, profit, loss, shipment_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (id,product_name, price, stock_available, stock_required, sales, profit, loss, shipment_date))
        
        conn.commit()
        flash('Product added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding product: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('view_products.view_products'))


# Route: Update a product by ID
@view_products_bp.route('/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    try:
        conn = get_db_connection()
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

        if not product:
            flash('Product not found.', 'danger')
            return redirect(url_for('view_products.view_products'))

        # Retrieve updated fields from form (fallback to current values if missing)
        price = float(request.form.get('price') or product['price'])
        stock_available = int(request.form.get('stock_available') or product['stock_available'])
        stock_required = int(request.form.get('stock_required') or product['stock_required'])
        sales = int(request.form.get('sales') or product['sales'])
        profit = float(request.form.get('profit') or product['profit'])
        loss = float(request.form.get('loss') or product['loss'])
        shipment_date = request.form.get('shipment_date') or product['shipment_date']

        # Update the product
        conn.execute('''
            UPDATE products
            SET price = ?, stock_available = ?, stock_required = ?, sales = ?, profit = ?, loss = ?, shipment_date = ?
            WHERE id = ?
        ''', (price, stock_available, stock_required, sales, profit, loss, shipment_date, product_id))
        
        conn.commit()
        flash('Product updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating product: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('view_products.view_products'))

# Route: Delete a product by ID
@view_products_bp.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting product: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('view_products.view_products'))

# Function: Initialize the database (if required)
def initialize_database():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                stock_available INTEGER NOT NULL,
                stock_required INTEGER NOT NULL,
                sales INTEGER NOT NULL DEFAULT 0,
                profit REAL NOT NULL DEFAULT 0,
                loss REAL NOT NULL DEFAULT 0,
                shipment_date TEXT NOT NULL
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()
