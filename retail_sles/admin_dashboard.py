from flask import Flask, render_template, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management


# Function to connect to the database
def get_db_connection():
    return sqlite3.connect('login_system.db')


# Admin Dashboard Route
@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("user_type") == "admin":
        return render_template("admin_dashboard.html")
    return redirect(url_for("login_page"))


# View Users Route (Admin Feature)
@app.route("/view-users")
def view_users():
    if session.get("user_type") == "admin":
        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve users from the database (admin, staff, customer)
        users = []
        for user_type in ["admin", "staff", "customer"]:
            cursor.execute(f"SELECT id, username, '{user_type}' AS role FROM {user_type}")
            users.extend(cursor.fetchall())

        conn.close()
        return render_template("view_users.html", users=users)

    return redirect(url_for("login_page"))


# Home Route
@app.route("/home")
def home():
    return render_template("home.html")


# Logout Route
@app.route("/logout")
def logout():
    session.clear()  # Clear session data
    return redirect(url_for("login_page"))


# Login Route
@app.route("/login")
def login_page():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)
