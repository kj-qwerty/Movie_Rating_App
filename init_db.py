"""
Initialize MongoDB database for the Movie Rating App with schema validation.

Run:
    export MONGO_URI="your-mongodb-uri"
    python init_db.py
"""

from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Get MongoDB URI from environment
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["moviesdb"]

# Drop existing collections
print("Dropping existing collections (if any)...")
db.drop_collection("movies")
db.drop_collection("ratings")

# ---------------------------
# Create Movies Collection with Constraints
# ---------------------------
print("Creating 'movies' collection with schema validation...")

db.create_collection(
    "movies",
    validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["title"],
            "properties": {
                "title": {
                    "bsonType": "string",
                    "description": "Movie title must be a string and is required."
                },
                "release_year": {
                    "bsonType": ["int", "null"],
                    "minimum": 1880,
                    "maximum": 2100,
                    "description": "Release year must be an integer between 1880 and 2100."
                },
                "genre": {
                    "bsonType": ["string", "null"],
                    "description": "Genre must be a string or null."
                },
                "runtime": {
                    "bsonType": ["int", "null"],
                    "minimum": 1,
                    "maximum": 600,
                    "description": "Runtime must be an integer (1–600 minutes)."
                },
                "overview": {
                    "bsonType": ["string", "null"],
                    "description": "Overview must be a string or null."
                }
            }
        }
    },
    validationLevel="strict"
)

movies = db["movies"]

# Add index for unique movie titles
movies.create_index("title", unique=True)

# ---------------------------
#  Create Ratings Collection with Constraints
# ---------------------------
print("Creating 'ratings' collection with schema validation...")

db.create_collection(
    "ratings",
    validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["userId", "movieId", "rating"],
            "properties": {
                "userId": {
                    "bsonType": "string",
                    "description": "User ID must be a string."
                },
                "movieId": {
                    "bsonType": "objectId",
                    "description": "movieId must reference a valid ObjectId from movies."
                },
                "rating": {
                    "bsonType": ["double", "int"],
                    "minimum": 0,
                    "maximum": 10,
                    "description": "Rating must be between 0 and 10."
                },
                "timestamp": {
                    "bsonType": ["date", "null"],
                    "description": "Timestamp must be a valid date or null."
                }
            }
        }
    },
    validationLevel="strict"
)

ratings = db["ratings"]

# Create helpful indexes for performance
ratings.create_index("movieId")
ratings.create_index("userId")
ratings.create_index("timestamp")

# ---------------------------
# Insert Sample Data
# ---------------------------
print("Inserting sample movies...")

movie_docs = [
    {
        "title": "The Shawshank Redemption",
        "release_year": 1994,
        "genre": "Drama",
        "overview": "Two imprisoned men bond over a number of years.",
        "runtime": 142,
    },
    {
        "title": "Inception",
        "release_year": 2010,
        "genre": "Sci-Fi",
        "overview": "A thief who steals corporate secrets through dream-sharing technology.",
        "runtime": 148,
    },
    {
        "title": "The Dark Knight",
        "release_year": 2008,
        "genre": "Action",
        "overview": "Batman faces the Joker, a criminal mastermind.",
        "runtime": 152,
    },
]

result = movies.insert_many(movie_docs)
movie_ids = result.inserted_ids

print("Inserting sample ratings...")

rating_docs = [
    {
        "userId": "alice",
        "movieId": movie_ids[0],
        "rating": 9.5,
        "timestamp": datetime.utcnow(),
    },
    {
        "userId": "bob",
        "movieId": movie_ids[0],
        "rating": 9.0,
        "timestamp": datetime.utcnow(),
    },
    {
        "userId": "carol",
        "movieId": movie_ids[1],
        "rating": 8.5,
        "timestamp": datetime.utcnow(),
    },
    {
        "userId": "dave",
        "movieId": movie_ids[2],
        "rating": 9.2,
        "timestamp": datetime.utcnow(),
    },
]

ratings.insert_many(rating_docs)

print("Database initialized successfully with constraints and sample data.")