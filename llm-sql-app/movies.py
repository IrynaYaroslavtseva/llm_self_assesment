from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import openai
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")  # Access OpenAI API key from .env file

# Initialize Flask app + CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DB_PATH = 'movies_actors.db'


####
def is_safe_sql(sql):

    sql_cleaned = sql.strip().lower()

    # Дозволяємо лише SELECT-запити
    if not sql_cleaned.startswith("select"):
        return False

    # Заборонені ключові слова
    forbidden_keywords = [
        "drop", "delete", "insert", "update", "alter",
        "create", "truncate", "replace", "attach", "detach",
        "pragma"  # може змінювати налаштування SQLite
    ]

    for keyword in forbidden_keywords:
        if keyword in sql_cleaned:
            return False

    return True
####

# Route for a simple greeting
@app.route("/")
def hello():
    return "👋 Hello from your Flask API!"

# Route to get all users from the Actors table
@app.route("/actors", methods=["GET"])
def get_actors():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Actors")
    actors = cursor.fetchall()
    conn.close()
    return jsonify(actors)

# Route to get all orders from the Movies table
@app.route("/movies", methods=["GET"])
def get_movies():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Movies")
    movies = cursor.fetchall()
    conn.close()
    return jsonify(movies)

# Route to convert natural language to SQL query using OpenAI's LLM
@app.route("/post_movies", methods=["POST", "GET"])
def natural_language_to_sql():
    data = request.json
    print(f"Received data: {data}")  # Adding logs
    prompt = data.get("query")  # Get the actor's query from the request body

    if not prompt:
        return jsonify({"error": "Missing query"}), 400

    system_msg = (
        "You are an assistant that converts natural language into safe SQL for a SQLite database with tables: "
        "Actors(id, name), Movies(id, name), ActorMovies(actor_id, movie_id). Only return the SQL query."
    )

    user_msg = f"Convert this to SQL: {prompt}"

    # Викликаємо OpenAI
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    )

    raw_sql = response.choices[0].message.content.strip()

    # Очистка SQL
    cleaned_sql = re.sub(r"^```sql", "", raw_sql, flags=re.IGNORECASE).strip()
    cleaned_sql = re.sub(r"^```", "", cleaned_sql).strip()
    cleaned_sql = re.sub(r"```$", "", cleaned_sql).strip()
    cleaned_sql = cleaned_sql.replace('\n', ' ').strip()

    # 🔒 Перевірка SQL на безпеку — всередині функції!
    if not is_safe_sql(cleaned_sql):
        return jsonify({"error": "Unsafe SQL detected"}), 400

    # Виконання SQL
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(cleaned_sql)
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"generated_sql": cleaned_sql, "results": rows})
    except Exception as e:
        return jsonify({"error": str(e), "generated_sql": cleaned_sql}), 400


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
