import os, json, requests, hashlib

from flask import Flask, session, render_template, request, jsonify, redirect, url_for
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "username" in session:
            return redirect(url_for("index"))
        return render_template("login.html")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db.execute(
            "SELECT * FROM users WHERE username = :username", {"username": username}
        ).fetchone()

        # Check that user exists in db and verify password
        if user:
            key = user.key.tobytes().decode()
            check_key = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), user.salt, 100000
            )
            check_key = check_key.hex()

        if user is None or key != check_key:
            error = "Invalid Credentials. Please try again."
            return render_template("login.html", error=error)

        session["username"] = user.username
        session["user_id"] = user.user_id
        return redirect(url_for("search"))


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    msg = None
    if request.method == "GET":
        if "username" in session:
            return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_confirm = request.form.get("confirm_password")
        user = db.execute(
            "SELECT user_id FROM users WHERE username = :username",
            {"username": username},
        )
        if user.rowcount != 0:
            error = "Username taken. Please choose another."
            return render_template("register.html", error=error)
        elif password and password_confirm:
            if password != password_confirm:
                error = "Both password fields must match."
                return render_template("register.html", error=error)

        # Hash user password, see https://docs.python.org/3/library/hashlib.html
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        key = key.hex()

        db.execute(
            "INSERT INTO users (username, key, salt) VALUES (:username, :key, :salt)",
            {"username": username, "key": key, "salt": salt},
        )
        db.commit()
        
        msg = "Thanks for registering!"
    return render_template("register.html", msg=msg)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/search")
def search():
    query = request.args.get("q")
    books = []

    # Return empty search page if no query or query contains only whitespaces
    if query is None or query is "" or (query and query.isspace() is True):
        return render_template("search.html")

    books = db.execute(
        "SELECT * FROM books WHERE \
                        UPPER(title) LIKE :query OR \
                        UPPER(author) LIKE :query OR \
                        UPPER(isbn) LIKE :query",
        {"query": "%" + query.upper() + "%"},
    )

    if books.rowcount == 0:
        return render_template(
            "error.html",
            message=f"Sorry, your search for '{query}' did not return any results.",
        )

    results = books.fetchall()

    return render_template("search.html", results=results, query=query)


@app.route("/random")
def random():
    rand = db.execute("SELECT book_id FROM books ORDER BY RANDOM() LIMIT 1").fetchone()
    rand = rand.book_id
    return redirect(url_for("book", book_id=rand))


@app.route("/books/<int:book_id>", methods=["GET", "POST"])
def book(book_id):
    error = None
    msg = None
    if "user_id" in session:
        user_id = session["user_id"]

    book = db.execute(
        "SELECT * FROM books WHERE book_id = :id", {"id": book_id}
    ).fetchone()

    # Get Goodreads review data
    key = os.getenv("GOODREADS_KEY")
    res = requests.get(
        "https://www.goodreads.com/book/review_counts.json",
        params={"key": key, "isbns": book.isbn},
    )
    data = res.json()

    reviews = db.execute(
        "SELECT users.username, comment, rating, reaction, \
                            to_char(time, 'HH:MI AM - DD Mon YY') as time \
                            FROM users INNER JOIN reviews \
                            ON users.user_id = reviews.user_id \
                            WHERE book_id = :book \
                            ORDER BY time",
        {"book": book_id},
    ).fetchall()

    if request.method == "POST" and "username" in session:
        row = db.execute(
            "SELECT book_id, user_id FROM reviews WHERE book_id = :book_id AND user_id = :user_id",
            {"book_id": book_id, "user_id": user_id},
        ).fetchone()

        if row != None:
            error = "You already submitted a review for this book."
            return render_template(
                "books.html", book=book, data=data, reviews=reviews, error=error
            )

        comment = request.form.get("review")
        rating = request.form.get("rating")

        # Return values of selected emoji(s) as a string
        value = request.form.getlist("emoji")
        if len(value) > 3:
            error = "Please limit your emoji selection to 3."
            return render_template(
                "books.html", book=book, data=data, reviews=reviews, error=error
            )
        emojis = "".join(value)

        db.execute(
            "INSERT INTO reviews (user_id, book_id, comment, rating, reaction) \
                VALUES (:user_id, :book_id, :comment, :rating, :reaction)",
            {
                "user_id": user_id,
                "book_id": book_id,
                "comment": comment,
                "rating": rating,
                "reaction": emojis,
            },
        )
        db.commit()
        
        msg = "Review submitted!"
    return render_template("books.html", book=book, data=data, reviews=reviews, msg=msg)


@app.route("/api/<book_isbn>")
def book_api(book_isbn):
    """Create an API that returns details about a single book."""

    book = db.execute(
        "SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}
    ).fetchone()

    # Make sure book exists.
    if book is None:
        return jsonify({"error": "Invalid book_isbn"}), 404

    row = db.execute(
        "SELECT COUNT(review_id) as review_count, AVG(rating) as avg_score FROM reviews WHERE book_id = :id",
        {"id": book.book_id},
    ).fetchone()

    if row.avg_score:
        avg_score = float(row.avg_score)
    else:
        avg_score = row.avg_score

    return jsonify(
        {
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": row.review_count,
            "average_score": avg_score,
        }
    )
