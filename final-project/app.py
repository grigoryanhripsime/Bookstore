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

def credit_card_checker(card_number):
    num = int(card_number)
    length = len(str(num))
    checksum = 0
    for i in range(1, length+1, 2):
        digit = ((num // 10**i) % 10) * 2
        if digit >= 10:
            checksum += 1 + (digit % 10)
        else:
            checksum += digit
        checksum += (num // 10**(i-1)) % 10
    if checksum % 10 == 0:
        if (length == 15 and (num // 10**13 == 34 or num // 10**13 == 37)) or (length == 16 and (num // 10**14 in range(51, 56))) or ((length == 16 or len == 13) and num // 10**(length-1) == 4) or (length == 16 and num // 10**14 == 90):
            return True
        else:
            return "Invalid Cridit card number"
    else:
        return "Please check your card number again"



#DONE
@app.route("/")
@login_required
def index():
    data = db.execute("SELECT * FROM books;")
    cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
    return render_template("index.html", data = data, cash = cash)

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
        cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
        return render_template("sell.html", cash = cash)
    else:
        book_name = request.form.get("book-name")
        book_author = request.form.get("book-author")
        book_price = float(request.form.get("book-price"))
        book_img = request.form.get("book-img")
        if not book_name or not book_author or not book_price or not book_img:
            return "Please fill in all fields"
        seller_id = session["user_id"]
        db.execute('INSERT INTO books (name, author, price, image, seller_id) VALUES (?, ?, ?, ?, ?);', book_name, book_author, book_price, book_img, seller_id)
        flash("Added")
        return redirect("/")

#DONE
@app.route("/item", methods=["GET", "POST"])
@login_required
def item():
    if request.method == "POST":
        #to get item's id from html
        item_id = request.form.get("item-id")

        #to find item, item's seller and that seller's other books in daabase
        item = db.execute("SELECT * FROM books WHERE id=?", item_id)
        seller = db.execute("SELECT username, email, phone_number FROM users WHERE id=?", item[0]["seller_id"])
        data = db.execute("SELECT * FROM books WHERE seller_id=?", item[0]["seller_id"])

        #for nav's cash item
        cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])

        return render_template("item.html", item = item, seller = seller, data = data, cash = cash)
#DONE
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        #to get item's id from html
        item_id = request.form.get("item_id")

        #to get info about item seller and buyer from database
        item = db.execute("SELECT * FROM books WHERE id=?", item_id)
        seller_id = item[0]["seller_id"]
        buyer_id = session["user_id"]
        buyer_cash = db.execute("SELECT cash FROM users WHERE id=?;", buyer_id)
        if item[0]['price'] > buyer_cash[0]['cash']:
            return "You haven't enough money!"

        #to add info about "shopping" to history and add_history
        date = datetime.datetime.now()
        db.execute("INSERT INTO history (name, author, price, seller_id, buyer_id, date) VALUES (?, ?, ?, ?, ?, ?);", item[0]['name'], item[0]['author'], item[0]['price'], seller_id, buyer_id, date)
        db.execute("INSERT INTO add_history (user_id, sign, cash, date) VALUES (?, '+(sold book)', ?, ?);", seller_id, item[0]['price'], date)
        db.execute("INSERT INTO add_history (user_id, sign, cash, date) VALUES (?, '-(bought book)', ?, ?);", buyer_id, item[0]['price'], date)

        #to delete book from book-self and Update buyer's and seller's cashes
        db.execute("DELETE FROM books WHERE id=?", item_id)
        db.execute("UPDATE users SET cash=(cash-?) WHERE id=?;", item[0]['price'], buyer_id)
        db.execute("UPDATE users SET cash=(cash+?) WHERE id=?;", item[0]['price'], seller_id)
        return redirect("/")

#DONE
@app.route("/history")
@login_required
def history():
    if request.method == "GET":
        id = session["user_id"]
        data = db.execute("SELECT history.name, history.author, history.price, history.date, users.username FROM history JOIN users ON history.seller_id=users.id WHERE buyer_id=?", id)

        #for nav's cash item
        cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
        return render_template("history.html", data=data, cash = cash)

# think about /history's cells   I don't want to change this page now

#DONE
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "GET":
        #for nav's cash item
        cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
        return render_template("add.html", cash = cash)
    else:
        card = request.form.get("card")
        try:
            card = int(card)
        except:
            return "Please check your inputed card number"
        check = credit_card_checker(card)
        if check == True:
            cash = request.form.get("cash")
            if not cash:
                return "Fill in all fields"
            id = session["user_id"]
            db.execute("UPDATE users SET cash=(cash+?) WHERE id=?", cash, id)
            date = datetime.datetime.now()
            db.execute("INSERT INTO add_history (user_id, sign, credit_card, cash, date) VALUES(?, '+', ?, ?, ?)", id, card, cash, date)
            return redirect("/")

#DONE
@app.route("/add_history")
@login_required
def add_history():
    if request.method == "GET":
        id = session["user_id"]

        #for nav's cash item
        cash = db.execute("SELECT cash FROM users WHERE id=?", id)

        #to get history about money from database
        data = db.execute("SELECT sign, credit_card, cash, date FROM add_history where user_id=?", id)

        return render_template("add_history.html", cash = cash, data=data)

#DONE
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

#DONE
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
