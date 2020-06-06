import os
import requests
import hashlib

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


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


#--------------------------------------#
#
@app.route("/")
def index():
    return render_template("index.html")

#
@app.route("/login")
def login():
    return render_template("login.html")

#
@app.route("/signup")
def signup():
    return render_template("join.html")
#
@app.route("/contact")
def contact():
    return render_template("contact.html")

#--------------------------------------#


#--------------------------------------#
#
@app.route("/main", methods=["POST"])
def main():
    return render_template("main.html")

#
@app.route("/register", methods=["POST"])
def register():
    
    """ Register New User """
    session.clear()

    """ Grab user information from form """
    if request.method == "POST":
        eInput = request.form.get("eInput")
        pInput = request.form.get("pInput")

    """ Check input field for null """
    if eInput == None or pInput == None:
        return render_template("error.html")

    accountCheck = db.execute("Select * FROM userAccount WHERE username = :username", {"username": eInput})

    if accountCheck:
        return render_template("error.html", message="Email has already been registered!")

    tempNum = os.urandom(32)

    password = str(pInput)

    key = hashlib.pbkdf2_hmac('potato',
                               password.encode('utf-8'),
                               tempNum,
                               100000,
                               dklen=128)

    hashPassword = tempNum + key

    db.execute("INSERT INTO " + "userAccount " + "(username, password) VALUES (:username, :password)",
                {":username": eInput, ":password": hashPassword})
    db.commit()

    return render_template("index.html")

#--------------------------------------#
    


    



