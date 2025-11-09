
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
#app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "change-this-secret")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback-secret")

# # MongoDB connection (set MONGO_URI in environment for Atlas, etc.)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
#app.secret_key = "mongo-movies"

# MongoDB connection mongodb+srv://kjayaraj_db_user:root@kjayarajcodingpractice.18lqgg8.mongodb.net/
#client = MongoClient("mongodb+srv://kjayaraj_db_user:root@kjayarajcodingpractice.18lqgg8.mongodb.net/")
db = client["moviesdb"]
movies = db["movies"]
ratings = db["ratings"]


def parse_rating(value):
    """Convert rating string to float and validate range 0–10."""
    try:
        r = float(value)
    except (TypeError, ValueError):
        return None
    if 0 <= r <= 10:
        return r
    return None


def parse_timestamp(ts_str):
    """Parse HTML datetime-local value to Python datetime (UTC naive)."""
    if not ts_str:
        return datetime.utcnow()
    try:
        # datetime-local comes as 'YYYY-MM-DDTHH:MM'
        return datetime.fromisoformat(ts_str)
    except ValueError:
        return datetime.utcnow()


@app.route("/")
def index():
    """Home page: list movies, optional search by title."""
    q = request.args.get("q", "").strip()
    query = {}
    if q:
        query["title"] = {"$regex": q, "$options": "i"}

    all_movies = list(movies.find(query).sort("title", 1))
    return render_template("movies_list.html", movies=all_movies, q=q)


# --------------------
# Movie CRUD
# --------------------

@app.route("/movies/new", methods=["GET", "POST"])
def movie_create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        release_year = request.form.get("release_year", "").strip()
        genre = request.form.get("genre", "").strip()
        overview = request.form.get("overview", "").strip()
        runtime = request.form.get("runtime", "").strip()

        if not title:
            flash("Title is required.", "danger")
            return redirect(url_for("movie_create"))

        doc = {
            "title": title,
            "release_year": int(release_year) if release_year.isdigit() else None,
            "genre": genre or None,
            "overview": overview or None,
            "runtime": int(runtime) if runtime.isdigit() else None,
        }

        try:
            movies.insert_one(doc)
            flash("Movie created successfully.", "success")
        except Exception as e:
            flash(f"Error creating movie: {e}", "danger")

        return redirect(url_for("index"))

    return render_template("movie_form.html", movie=None)


@app.route("/movies/<movie_id>/edit", methods=["GET", "POST"])
def movie_edit(movie_id):
    try:
        _id = ObjectId(movie_id)
    except Exception:
        flash("Invalid movie id.", "danger")
        return redirect(url_for("index"))

    movie = movies.find_one({"_id": _id})
    if not movie:
        flash("Movie not found.", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        release_year = request.form.get("release_year", "").strip()
        genre = request.form.get("genre", "").strip()
        overview = request.form.get("overview", "").strip()
        runtime = request.form.get("runtime", "").strip()

        if not title:
            flash("Title is required.", "danger")
            return redirect(url_for("movie_edit", movie_id=movie_id))

        update_doc = {
            "title": title,
            "release_year": int(release_year) if release_year.isdigit() else None,
            "genre": genre or None,
            "overview": overview or None,
            "runtime": int(runtime) if runtime.isdigit() else None,
        }

        try:
            movies.update_one({"_id": _id}, {"$set": update_doc})
            flash("Movie updated successfully.", "success")
        except Exception as e:
            flash(f"Error updating movie: {e}", "danger")

        return redirect(url_for("index"))

    return render_template("movie_form.html", movie=movie)


@app.route("/movies/<movie_id>/delete", methods=["POST"])
def movie_delete(movie_id):
    try:
        _id = ObjectId(movie_id)
    except Exception:
        flash("Invalid movie id.", "danger")
        return redirect(url_for("index"))

    try:
        movies.delete_one({"_id": _id})
        # also delete ratings for this movie
        ratings.delete_many({"movieId": _id})
        flash("Movie and its ratings deleted.", "success")
    except Exception as e:
        flash(f"Error deleting movie: {e}", "danger")

    return redirect(url_for("index"))


@app.route("/movies/<movie_id>")
def movie_detail(movie_id):
    try:
        _id = ObjectId(movie_id)
    except Exception:
        flash("Invalid movie id.", "danger")
        return redirect(url_for("index"))

    movie = movies.find_one({"_id": _id})
    if not movie:
        flash("Movie not found.", "warning")
        return redirect(url_for("index"))

    movie_ratings = list(ratings.find({"movieId": _id}).sort("timestamp", -1))

    return render_template("movie_detail.html", movie=movie, ratings=movie_ratings)


# --------------------
# Rating CRUD
# --------------------

@app.route("/ratings")
def rating_list():
    all_ratings = list(ratings.find().sort("timestamp", -1))
    movie_map = {
        str(m["_id"]): m.get("title", "(untitled)")
        for m in movies.find({}, {"title": 1})
    }
    return render_template("ratings_list.html", ratings=all_ratings, movie_map=movie_map)


@app.route("/ratings/new", methods=["GET", "POST"])
def rating_create():
    all_movies = list(movies.find({}, {"title": 1}).sort("title", 1))

    if not all_movies:
        flash("Please add a movie before creating ratings.", "warning")
        return redirect(url_for("movie_create"))

    if request.method == "POST":
        user_id = request.form.get("userId", "").strip()
        movie_id = request.form.get("movieId", "").strip()
        rating_str = request.form.get("rating", "").strip()
        timestamp_str = request.form.get("timestamp", "").strip()

        if not user_id:
            flash("User ID is required.", "danger")
            return redirect(url_for("rating_create"))

        try:
            movie_obj_id = ObjectId(movie_id)
        except Exception:
            flash("Invalid movie selected.", "danger")
            return redirect(url_for("rating_create"))

        rating_val = parse_rating(rating_str)
        if rating_val is None:
            flash("Rating must be a number between 0 and 10.", "danger")
            return redirect(url_for("rating_create"))

        ts = parse_timestamp(timestamp_str)

        doc = {
            "userId": user_id,
            "movieId": movie_obj_id,
            "rating": rating_val,
            "timestamp": ts,
        }

        try:
            ratings.insert_one(doc)
            flash("Rating created successfully.", "success")
        except Exception as e:
            flash(f"Error creating rating: {e}", "danger")

        return redirect(url_for("rating_list"))

    return render_template("rating_form.html", rating=None, movies=all_movies)


@app.route("/ratings/<rating_id>/edit", methods=["GET", "POST"])
def rating_edit(rating_id):
    try:
        _id = ObjectId(rating_id)
    except Exception:
        flash("Invalid rating id.", "danger")
        return redirect(url_for("rating_list"))

    rating_doc = ratings.find_one({"_id": _id})
    if not rating_doc:
        flash("Rating not found.", "warning")
        return redirect(url_for("rating_list"))

    all_movies = list(movies.find({}, {"title": 1}).sort("title", 1))

    if request.method == "POST":
        user_id = request.form.get("userId", "").strip()
        movie_id = request.form.get("movieId", "").strip()
        rating_str = request.form.get("rating", "").strip()
        timestamp_str = request.form.get("timestamp", "").strip()

        if not user_id:
            flash("User ID is required.", "danger")
            return redirect(url_for("rating_edit", rating_id=rating_id))

        try:
            movie_obj_id = ObjectId(movie_id)
        except Exception:
            flash("Invalid movie selected.", "danger")
            return redirect(url_for("rating_edit", rating_id=rating_id))

        rating_val = parse_rating(rating_str)
        if rating_val is None:
            flash("Rating must be a number between 0 and 10.", "danger")
            return redirect(url_for("rating_edit", rating_id=rating_id))

        ts = parse_timestamp(timestamp_str)

        update_doc = {
            "userId": user_id,
            "movieId": movie_obj_id,
            "rating": rating_val,
            "timestamp": ts,
        }

        try:
            ratings.update_one({"_id": _id}, {"$set": update_doc})
            flash("Rating updated successfully.", "success")
        except Exception as e:
            flash(f"Error updating rating: {e}", "danger")

        return redirect(url_for("rating_list"))

    # For editing, convert timestamp to datetime-local friendly string
    ts_val = rating_doc.get("timestamp")
    ts_str = ""
    if isinstance(ts_val, datetime):
        ts_str = ts_val.strftime("%Y-%m-%dT%H:%M")

    return render_template(
        "rating_form.html",
        rating=rating_doc,
        movies=all_movies,
        ts_str=ts_str,
    )


@app.route("/ratings/<rating_id>/delete", methods=["POST"])
def rating_delete(rating_id):
    try:
        _id = ObjectId(rating_id)
    except Exception:
        flash("Invalid rating id.", "danger")
        return redirect(url_for("rating_list"))

    try:
        ratings.delete_one({"_id": _id})
        flash("Rating deleted.", "success")
    except Exception as e:
        flash(f"Error deleting rating: {e}", "danger")

    return redirect(url_for("rating_list"))


# --------------------
# Analytics
# --------------------

@app.route("/analytics")
def analytics():
    # Aggregate average rating and count per movie
    pipeline = [
        {
            "$group": {
                "_id": "$movieId",
                "avgRating": {"$avg": "$rating"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"avgRating": -1}},
    ]
    agg = list(ratings.aggregate(pipeline))

    labels = []
    avg_values = []
    count_values = []

    for doc in agg:
        movie = movies.find_one({"_id": doc["_id"]})
        if not movie:
            continue
        labels.append(movie.get("title", "(untitled)"))
        avg_values.append(round(doc.get("avgRating", 0), 2))
        count_values.append(doc.get("count", 0))

    return render_template(
        "analytics.html",
        labels=labels,
        avg_values=avg_values,
        count_values=count_values,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
