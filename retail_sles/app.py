from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def login(username, password, user_type):
    conn = sqlite3.connect('login_system.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM {user_type} WHERE username = ? AND password = ?"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    conn.close()
    return result is not None

@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")  # Render the home page

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_type = request.form["userType"]
        if login(username, password, user_type):
            if user_type == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user_type == "staff":
                return redirect(url_for("staff_dashboard"))
            elif user_type == "customer":
                return redirect(url_for("customer_dashboard"))
        else:
            return "Invalid credentials or user type."
    return render_template("login.html")  # Render the login page

@app.route("/admin_dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route("/staff_dashboard")
def staff_dashboard():
    return render_template("staff_dashboard.html")

@app.route("/customer_dashboard")
def customer_dashboard():
    return render_template("customer_dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
    
