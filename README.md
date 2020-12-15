# NOVEL REACTION

(This is my design and implementation of Project 1 for [HarvardX CS50W 2018](https://courses.edx.org/courses/course-v1:HarvardX+CS50W+Web/course/).)

NOVEL REACTION is a web application for reviewing books.

View app on Heroku: https://novel-reaction.herokuapp.com/

## Write-Up

- `layout.html` contains the `<head>` section, the navbar, the search bar, and all the necessary Bootstrap files. All the pages in the site inherit `layout.html`.
- `books.html` is the template for individual book pages, providing information about the book and showing any reviews it has. When the user is logged in, a form is displayed for submitting reviews, which includes a five-star rating system, an option to "react" with emojis, and a textbox.
- `error.html` is a simple template that renders when a user provides a search query that does not match any books.
- `index.html` is the template for the home page.
- `login.html` and `register.html` each contain a `post` request form so the user can login/register.
- `search.html` has a simple search bar at the top. This template also renders all the results for a user's search. Users can search books by title, author, or ISBN.
- `application.py` contains all the backend code for the Flask server. Added some fun features like hashing the password before storing in the database and a route that sends the user to a random book (great for helping them find their next summer read).
- `import.py` is a Python file that inserts all the book data from books.csv to the database.
- `styles.css` contains all the styling for the front-end of the web application.
- `memphis-mini.png` is a background pattern courtesy of [Toptal Subtle Patterns](https://www.toptal.com/designers/subtlepatterns/)
- The app features its own API in JSON format accessed through https://novel-reaction.herokuapp.com/api/isbn where isbn is the book's ISBN 

## Getting Started

```cmd
:: Clone repo
git clone https://github.com/julia-kim/novel-reaction.git

cd novel-reaction

:: Install all dependencies
pip install -r requirements.txt

:: Setup environmental variables
set FLASK_APP=application.py
set DATABASE_URL=<DB URI> &:: e.g., postgres://username:password@hostname:port/database
set FLASK_DEBUG=1
set GOODREADS_KEY=<GOODREADS API KEY> &:: more info: https://www.goodreads.com/api

:: Start up the application
flask run
```

### Additional Info
- The [Goodreads API](https://www.goodreads.com/api) was used to fetch Goodreads ratings and rating count information
- The [Open Library Covers API](https://openlibrary.org/dev/docs/api/covers) provided all the book covers 
