import os
import requests
import hashlib
import xml.etree.ElementTree as ET

from flask import Flask, session, render_template, jsonify, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


from book import bookImport

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


key = 'gvYmaNmhEPnKa9nqURLH6w'

#--------------------------------------#
#
@app.route("/")
def index():
    return render_template("index.html")

#
@app.route("/login")
def login():
    try:
        if session.get("log"):
            return render_template("main.html")
    except ValueError:
        return render_template("error.html", message="Error has occurrr, please try again later.")
    
    return render_template("login.html")

#
@app.route("/signup")
def signup():
    return render_template("join.html")
#
@app.route("/contact")
def contact():
    session.clear()
    return render_template("error.html")

#
@app.route("/logout")
def logout():
    session.clear()
    return render_template("index.html")


#--------------------------------------#


#--------------------------------------#
#

@app.route("/main", methods=["POST"])
def main():

    if request.method == "POST":
        eInput = request.form.get("eInput")
        pInput = request.form.get("pInput")

    if eInput == None or pInput == None:
        return render_template("error.html", message="Email and Password is empty.")
    
    accountCheck = db.execute("SELECT password FROM users WHERE username = :username AND password = :password", {"username": eInput, "password": pInput}).fetchone()

    try:
        if accountCheck == None:
            return render_template("login.html", message="Invalid Email or Password")
        else:
            session["log"] = True
            session["user"] = eInput
            return render_template("main.html")
    except ValueError:
        return render_template("error.html", message="Error has occurrr, please try again later.")

#
@app.route("/register", methods=["POST"])
def register():
    
    """ Register New User """
    session.clear()

    """ Grab user information from form """
    if request.method == "POST":
        eInput = request.form.get("eInput")
        pInput = request.form.get("pInput")

    checkEmail = str(eInput)
    checkPass  = str(pInput)

    """ Check input field for null """
    if eInput == None or pInput == None:
        return render_template("error.html", message="Email and Password is empty.")
    elif (checkEmail.count("@") != 1) or (checkEmail.count(".") != 1):
        return render_template("error.html", message="Email is empty.")
    elif len(checkPass) == 0:
        return render_template("error.html", message="Email and Password is empty.")


    accountCheck = db.execute("Select * FROM users WHERE username = :username", {"username": eInput}).fetchone()

    try:
        if accountCheck != None:
            return render_template("error.html", message="Email has already been registered!")
    except ValueError:
        return render_template("error.html", message="Error has occurrr, please try again later.")

    session["log"] = True

    db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": eInput, "password": pInput})

    db.commit()

    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    if request.method == "POST":
         radInput = int(request.form.get("radOption"))
         searchInfo = request.form.get("bookSearch")

    userChoice = ""

    if radInput == 1:
        userChoice = "ISBN"
    elif radInput == 2:
        userChoice = "TITLE"
    elif radInput == 3:
        userChoice = "Author"
    elif radInput == 4:
        userChoice = "YEAR"
    else:
        return render_template("error.html", message="Error has occurrr, please try again later.")


    results = db.execute("SELECT * FROM books WHERE LOWER(" + userChoice + ") LIKE LOWER(:userChoice)", {"userChoice": "%"+searchInfo+"%"}).fetchall()

    if results is not None:
        return render_template("result.html", results=results)
    else:
        return render_template("error.html", message="not found")

@app.route("/book/<bookISBN>")
def book(bookISBN):

    bookCheck = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": bookISBN}).fetchone()

    url = f"https://www.goodreads.com/book/review_counts.json?key={key}&isbns={bookISBN.strip()}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
    else:
        return render_template("search.html")
    
    reviewC = data["books"][0]["reviews_count"]
    averageR = data["books"][0]["average_rating"]

    reviews = db.execute("SELECT * FROM bookrev WHERE isbn = :isbn", {"isbn": bookISBN}).fetchall()

    return render_template("book.html", averageR=averageR, reviewC=reviewC, book=bookCheck, dup="", reviews=reviews)

@app.route("/book/<bookISBN>/review", methods=["POST"])
def review(bookISBN):
    user = str(session.get("user"))

    dupReview = db.execute("SELECT * FROM bookrev WHERE username = :username AND isbn = :isbn", {"username": user, "isbn": bookISBN}).fetchone()

    bookCheck = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": bookISBN}).fetchone()

    url = f"https://www.goodreads.com/book/review_counts.json?key={key}&isbns={bookISBN.strip()}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
    else:
        return render_template("search.html")
    
    reviewC = data["books"][0]["reviews_count"]
    averageR = data["books"][0]["average_rating"]

    if dupReview != None:
        return render_template("book.html", book=bookCheck, averageR=averageR, reviewC=reviewC, dup="You cannot enter mulitple reviews", reviews="1")

    review = request.form.get("txtReview")
    rate   = request.form.get("rate")

    db.execute("INSERT INTO bookrev (username, review, isbn, rate) VALUES (:username, :review, :isbn, :rate)", {"username": user, "review": review, "isbn": bookISBN, "rate": rate})
    
    db.commit()

    reviews = db.execute("SELECT * FROM bookrev WHERE isbn = :isbn", {"isbn": bookISBN}).fetchall()

    return render_template("book.html", book=bookCheck, averageR=session.get("ar"), reviewC=session.get("rc"), dup="", reviews=reviews)

@app.route("/api/book/<isbn>")
def book_api(isbn):
    """Return details about a single flight."""

    # Make sure flight exists.
    bookInfo = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    bookScore = db.execute("SELECT * FROM bookrev WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    averageScore = 0
    reviewCount = 0

    if bookInfo is None:
        return jsonify({"error": "Invalid isbn"}), 422

        # Get all passengers.

    for bScore in bookScore:
        averageScore += int(bScore.rate)
        reviewCount += 1

    if reviewCount != 0:
        averageScore /= reviewCount

    return jsonify({
        "title": bookInfo.title,
        "author": bookInfo.author,
        "year": bookInfo.year,
        "review_count": reviewCount,
        "average_score": averageScore
    })
#--------------------------------------#
    


    



