from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3

view_users_bp = Blueprint("view_users", __name__)

# Database connection function
def get_db_connection():
    return sqlite3.connect("login_system.db")

# Ensure tables exist with all required fields
def ensure_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create admin, staff, and customer tables if they don't exist
    tables = {
        "admin": "CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)",
        "staff": "CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)",
        "customer": "CREATE TABLE IF NOT EXISTS customer (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)"
    }
    for query in tables.values():
        cursor.execute(query)

    # Add additional columns if they do not exist (ALTER query example)
    for table in ["admin", "staff", "customer"]:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [column[1] for column in cursor.fetchall()]
        if "email" not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN email TEXT")

    conn.commit()
    conn.close()

# Fetch all users with their roles
def fetch_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    # UNION to combine multiple user tables with roles
    cursor.execute("""
        SELECT id, username, 'admin' AS role FROM admin
        UNION
        SELECT id, username, 'staff' AS role FROM staff
        UNION
        SELECT id, username, 'customer' AS role FROM customer
    """)
    users = cursor.fetchall()
    conn.close()
    return users

# Add a new user
def add_user(username, password, role, email):
    if role not in ["admin", "staff", "customer"]:
        return False

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {role} (username, password, email) VALUES (?, ?, ?)", (username, password, email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# Update user credentials
def update_user(role, user_id, new_username, new_password):
    if role not in ["admin", "staff", "customer"]:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {role} SET username = ?, password = ? WHERE id = ?", (new_username, new_password, user_id))
    conn.commit()
    conn.close()
    return True

# Delete a user
def delete_user(role, user_id):
    if role not in ["admin", "staff", "customer"]:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {role} WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True

# Change user role (Move user between tables)
def change_user_role(old_role, new_role, user_id):
    if old_role == new_role or old_role not in ["admin", "staff", "customer"] or new_role not in ["admin", "staff", "customer"]:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the user data
    cursor.execute(f"SELECT username, password, email FROM {old_role} WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return False

    username, password, email = user

    # Insert into new role table
    cursor.execute(f"INSERT INTO {new_role} (username, password, email) VALUES (?, ?, ?)", (username, password, email))
    # Delete from old role table
    cursor.execute(f"DELETE FROM {old_role} WHERE id = ?", (user_id,))

    conn.commit()
    conn.close()
    return True

# Route to view, add, update, delete users
@view_users_bp.route("/view-users", methods=["GET", "POST"])
def view_users():
    if session.get("user_type") != "admin":
        return redirect(url_for("login_page"))

    ensure_tables()

    # Add a new user
    if request.method == "POST" and "add_user" in request.form:
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        email = request.form["email"]
        if add_user(username, password, role, email):
            flash("User added successfully!")
        else:
            flash("Error adding user. Username might already exist.")

    # Update user
    if request.method == "POST" and "update_user" in request.form:
        role = request.form["role"]
        user_id = request.form["user_id"]
        new_username = request.form["new_username"]
        new_password = request.form["new_password"]
        if update_user(role, user_id, new_username, new_password):
            flash("User updated successfully!")
        else:
            flash("Error updating user.")

    # Delete user
    if request.method == "POST" and "delete_user" in request.form:
        role = request.form["role"]
        user_id = request.form["user_id"]
        if delete_user(role, user_id):
            flash("User deleted successfully!")
        else:
            flash("Error deleting user.")

    # Change user role
    if request.method == "POST" and "change_role" in request.form:
        old_role = request.form["old_role"]
        new_role = request.form["new_role"]
        user_id = request.form["user_id"]
        if change_user_role(old_role, new_role, user_id):
            flash("User role changed successfully!")
        else:
            flash("Error changing user role.")

    users = fetch_users()
    return render_template("view_users.html", users=users)
