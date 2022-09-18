from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import datetime
from functools import wraps
from cs50 import SQL
import re

app = Flask(__name__)

#Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///data.db")

def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

#DONE
@app.route("/")
@login_required
def index():
    data = db.execute("SELECT * FROM books;")
    return render_template("index.html", data = data)

#DONE
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/login")

#DONE
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        return render_template("sell.html")
    else:
        book_name = request.form.get("book-name")
        book_author = request.form.get("book-author")
        book_price = float(request.form.get("book-price"))
        book_img = request.form.get("book-img")
        if not book_name or not book_author or not book_price or not book_img:
            return "Please fill in all fields"
        id = session["user_id"]
        seller = db.execute("SELECT username FROM users WHERE id=?", id)
        db.execute('INSERT INTO books (name, author, price, image, seller) VALUES (?, ?, ?, ?, ?);', book_name, book_author, book_price, book_img, seller[0]["username"])
        flash("Added")
        return redirect("/")

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "GET":
        return render_template("search.html")
    else:
        book_search = request.form.get("booksearch")
        author_search = request.form.get("authorsearch")
        if not book_search and not author_search:
            return "Write book's and/or author's name for search"
        elif not book_search:
            data = db.execute("SELECT * FROM books WHERE author='?' ", author_search)
        elif not author_search:
            data = db.execute("SELECT * FROM books WHERE name='?' ", book_search)
        else:
            data = db.execute("SELECT * FROM books WHERE name='?' AND author='?' ", book_search, author_search)
        if len(data) == 0:
            return "There is nothing for you :("
        #TODO
        #this can wait for the first i wanna do /sell then /buy then /user then maybe do this because i will need to move this option in index

#DONE
@app.route("/item", methods=["GET", "POST"])
@login_required
def item():
    if request.method == "POST":
        item_id = request.form.get("item-id")
        item = db.execute("SELECT * FROM books WHERE id=?", item_id)
        seller = db.execute("SELECT username, email, phone_number FROM users WHERE username=?", item[0]["seller"])
        data = db.execute("SELECT * FROM books WHERE seller=?", item[0]["seller"])
        return render_template("item.html", item = item, seller = seller, data = data)

#TODO
#to make /buy for POST, that takes item's id from item.html, del that book from books - from buyer's cash +to seller's cash
#add that to history table with date, time book's info, seller and buyer
#make history table in sqlite
#make history.html
#make /history


@app.route("/login", methods=["GET", "POST"])
def login():
    #forget any user_id
    session.clear()

    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            return "Write username!"

        if not password:
            return "Write password!"

        users = db.execute("SELECT id, username, password FROM users;")
        for i in users:
            if i["username"] == username and i["password"] == password:
                session["user_id"] = i["id"]
                return redirect("/")
            return "Invalid Username or/and Password"


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        phone = request.form.get("phone")

        if not username:
            return "You missed username"

        if not password:
            return "You missed password"

        if password != request.form.get("confirm"):
            return "Try again"

        if not email:
            return "You missed email"

        if not phone:
            return "You missed phone number"

        # Make a regular expression
        # for validating an Email
        regex_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(regex_email, email):
            return "Invalid email address"

        regex_phone = "^\\+?[1-9][0-9]{7,14}$"
        if not re.match(regex_phone, phone):
            return "Invalid phone number"

        usernames = db.execute("SELECT username FROM users;")
        for i in usernames:
            if i["username"] == username:
                return "That username already exists!"

        try:
            id = db.execute("INSERT INTO users (username, password, email, phone_number, cash) VALUES(?, ?, ?, ?, 0);", username, password, email, phone)
        except:
            return "Error"

        session["user_id"] = id
        return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
