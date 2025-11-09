
# Movie Rating Web Application (Flask + MongoDB)

This is a simple Movie Rating web application built with **Flask** and **MongoDB**.
It supports full **CRUD** operations for Movies and Ratings and includes an
**analytics dashboard** (average rating per movie) using Chart.js.

## Features

- Create / Read / Update / Delete **Movies**
- Create / Read / Update / Delete **Ratings**
- Link each rating to a **Movie** via a dropdown
- Analytics page showing:
  - Average rating per movie
  - Number of ratings per movie
  - Bar chart visualization (Chart.js)

## Tech Stack

- Backend: Flask (Python)
- Database: MongoDB (Atlas or local)
- Driver: PyMongo
- Frontend: HTML, Bootstrap, Chart.js

## Setup

1. Create and activate a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set the MongoDB connection string (for Atlas or local):

```bash
# Example for local MongoDB
export MONGO_URI="mongodb://localhost:27017"

# On Windows PowerShell
$env:MONGO_URI = "mongodb://localhost:27017"
```

4. Initialize the database with sample data:

```bash
python init_db.py
```

5. Run the Flask app:

```bash
python app.py
```

6. Open your browser at:

- Home / Movies list: `http://localhost:5000/`
- Ratings list: `http://localhost:5000/ratings`
- Analytics dashboard: `http://localhost:5000/analytics`

## Files

- `app.py` – main Flask application
- `init_db.py` – script to create collections, indexes, and insert sample data
- `templates/` – Jinja2 HTML templates
- `static/style.css` – custom styles
- `requirements.txt` – Python dependencies

## Notes for Assignment / Milestone

- **CRUD coverage**
  - Movies: `/`, `/movies/new`, `/movies/<id>/edit`, `/movies/<id>/delete`
  - Ratings: `/ratings`, `/ratings/new`, `/ratings/<id>/edit`, `/ratings/<id>/delete`
- **Analytics visualization**
  - Route `/analytics` uses MongoDB aggregation to compute average ratings and counts per movie.
  - Template `analytics.html` renders a bar chart using Chart.js.
