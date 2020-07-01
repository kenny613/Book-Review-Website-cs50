import os


from flask import Flask, session, render_template, request,  redirect, url_for,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from importcsv import writebook
import requests
import xmltodict
import json


app = Flask(__name__)
app.config['DATABASE_URL'] = "path_to_db"

class current():
    name=None
    def __init__(self):
        pass

a=current()
        



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



account = []


@app.route("/")
def index():
    if db.execute("SELECT * FROM books").rowcount == 0:
        writebook(db)
    a=current()
    return render_template("firstpage.html")


@app.route("/reg/<int:valid_name>/<int:valid_pw>")
def reg(valid_name, valid_pw):
    return render_template("reg.html", valid_name=valid_name, valid_pw=valid_pw)


@app.route("/welcome", methods=["GET", "POST"])
def login_try():
    if request.method == "GET":
        return redirect(url_for('login', correct1=1))
    name = request.form.get("name")
    pw = request.form.get("pw")
    users = db.execute("SELECT * FROM log").fetchall()
    for user in users:
        if(user.name == name and user.pw == pw):
            a.name=name
            return redirect(url_for('home'), code=307)
    return redirect(url_for('login', correct1=0))


@app.route("/reg_success", methods=["POST"])
def reg_success():

    name = request.form.get("name")
    pw = request.form.get("pw")
    pw2 = request.form.get("pw2")

    # Databse approach below:
    users = db.execute("SELECT * FROM log").fetchall()
    for user in users:
        if(user.name == name):
            return redirect(url_for('reg', valid_name=0, valid_pw=1))
    if pw2 != pw:
        return redirect(url_for('reg', valid_name=1, valid_pw=0))

    db.execute("INSERT INTO log (name, pw) VALUES (:name, :pw)",
               {"name": name, "pw": pw})
    db.commit()
    return render_template("reg_success.html", name=name, pw=pw)


@app.route("/login/<int:correct1>")
def login(correct1):
    return render_template("login.html", correct1=correct1)


@app.route("/search", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return "Please sign in or sign in again"
    return render_template("Firstpage_login.html", name=a.name)

@app.route("/search_result", methods=["GET", "POST"])
def search_result():
    if request.method == "GET":
        return "Please sign in or sign in again"
    title=request.form.get("title")
    author=request.form.get("author")
    isbn=request.form.get("isbn")
    if title is not None:
        books_result=db.execute("SELECT * FROM BOOKS WHERE title LIKE :title",{"title":'%'+title+'%'}) 
    if author is not None:
        books_result=db.execute("SELECT * FROM BOOKS WHERE author LIKE :author",{"author":'%'+author+'%'})
    if isbn is not None:
        books_result=db.execute("SELECT * FROM BOOKS WHERE isbn LIKE :isbn",{"isbn":'%'+isbn+'%'})

    return render_template("search.html", books_result=books_result)

@app.route("/<isbn>/<title>/<author>/<year>", methods=["POST"])
def book_info(isbn,title,author,year):
   

    #title=db.execute("SELECT title FROM BOOKS WHERE isbn=:isbn",{"isbn":isbn})
    #author=db.execute("SELECT author FROM BOOKS WHERE isbn=:isbn",{"isbn":isbn})
    #year=db.execute("SELECT year FROM BOOKS WHERE isbn=:isbn",{"isbn":isbn})
    res1=requests.get("https://www.goodreads.com/book/review_counts.json",params={"isbns":isbn, "key":"sEV5ZEtMuqtLv8nr4U4mtA"})
    if res1.status_code!=200:
        raise Exception("ERROR: API request unsuccesful")
    data1=res1.json()
    #get the dict inside array of json
    rating=data1["books"][0]["average_rating"]
    #rating_web=db.excute("SELECT AVG(rating) FROM review WHERE isbn=:isbn",{"isbn":isbn})
    ratings_count=data1["books"][0]["ratings_count"]

    
    res2=requests.get("https://www.goodreads.com/search/index.xml?key=sEV5ZEtMuqtLv8nr4U4mtA&q="+isbn)
    if res2.status_code!=200:
        raise Exception("ERROR: API request unsuccesful")
    dic=xmltodict.parse(res2.content)
    json_data=json.dumps(dic)
    #print(f"this is {json_data}")
    image=dic["GoodreadsResponse"]["search"]["results"]["work"]["best_book"]["image_url"]
    des=dic["GoodreadsResponse"]["search"]["results"]["work"]["best_book"]["image_url"]
    

    comment_no=db.execute("SELECT * FROM review WHERE isbn=:isbn",{"isbn":isbn,}).rowcount
    comments=db.execute("SELECT * FROM review WHERE isbn=:isbn",{"isbn":isbn,})
    if db.execute("SELECT * FROM review WHERE isbn=:isbn AND member=:member",{"isbn":isbn,"member":a.name}).rowcount==0:
        comment_b4=0
    else:
        comment_b4=1

    return render_template("book_info.html", isbn=isbn,title=title,author=author,year=year,rating=rating,image=image,comments=comments,comment_b4=comment_b4,comment_no=comment_no,ratings_count=ratings_count)

@app.route("/<isbn>/<title>/<author>/<year>/added", methods=["GET", "POST"])
def add_comment(isbn,title,author,year):
    book_review=request.form.get("book_review")
    your_rate=request.form.get("your_rate")

    db.execute("INSERT INTO review (isbn, member, comment, rating) VALUES (:isbn, :member, :comment, :rating)",
                    {"isbn": isbn, "member": a.name, "comment": book_review, "rating": int(your_rate)})


    db.commit()

    return redirect(url_for('book_info', isbn=isbn,title=title,author=author,year=year), code=307)

@app.route("/api/<isbn>")
def api(isbn):

    # Make sure book exists.
    book_isbn=db.execute("SELECT isbn FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchall
    if book_isbn is None:
        return jsonify({"error": "Invalid flight_id"}), 422
    book_title=db.execute("SELECT title FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchall
    book_author=db.execute("SELECT author FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchall
    book_year=db.execute("SELECT year FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchall
   

    comment_no=db.execute("SELECT * FROM review WHERE isbn=:isbn",{"isbn":isbn,}).rowcount
    avg_rating=db.execute("SELECT AVG(rating) FROM review WHERE isbn=:isbn",{"isbn":isbn,})
    

    return jsonify({
              "title": book_title,
              "author": book_author,
              "Publication year": book_year,
              "Number of reviews": comment_no,
              "Average rating":avg_rating

          })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


