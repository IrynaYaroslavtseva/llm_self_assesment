import sqlite3

# Підключення до бази даних (створить файл, якщо його немає)
conn = sqlite3.connect('movies_actors.db')
cursor = conn.cursor()

# Створення таблиці Actors
cursor.execute('''
CREATE TABLE IF NOT EXISTS Actors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
''')

# Створення таблиці Movies
cursor.execute('''
CREATE TABLE IF NOT EXISTS Movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
''')

# Створення зв'язуючої таблиці ActorMovies
cursor.execute('''
CREATE TABLE IF NOT EXISTS ActorMovies (
    actor_id INTEGER,
    movie_id INTEGER,
    FOREIGN KEY (actor_id) REFERENCES Actors(id),
    FOREIGN KEY (movie_id) REFERENCES Movies(id)
);
''')

# Список акторів
actors = [
    "Leonardo DiCaprio",
    "Kate Winslet",
    "Tom Hanks",
    "Scarlett Johansson",
    "Robert Downey Jr."
]

# Список фільмів
movies = [
    "Titanic",
    "Inception",
    "The Revenant",
    "Forrest Gump",
    "Iron Man",
    "Avengers: Endgame",
    "Lost in Translation",
    "Captain America: Civil War"
]

# Додавання акторів
for name in actors:
    cursor.execute("INSERT INTO Actors (name) VALUES (?)", (name,))

# Додавання фільмів
for name in movies:
    cursor.execute("INSERT INTO Movies (name) VALUES (?)", (name,))

# Витягуємо ID акторів і фільмів
cursor.execute("SELECT id, name FROM Actors")
actor_map = {name: actor_id for actor_id, name in cursor.fetchall()}

cursor.execute("SELECT id, name FROM Movies")
movie_map = {name: movie_id for movie_id, name in cursor.fetchall()}

# Зв’язки акторів і фільмів (множинні перетини!)
links = {
    "Leonardo DiCaprio": ["Titanic", "Inception", "The Revenant"],
    "Kate Winslet": ["Titanic"],
    "Tom Hanks": ["Forrest Gump"],
    "Scarlett Johansson": ["Lost in Translation", "Avengers: Endgame", "Captain America: Civil War"],
    "Robert Downey Jr.": ["Iron Man", "Avengers: Endgame", "Captain America: Civil War"]
}

# Заповнення зв'язуючої таблиці
for actor, films in links.items():
    for film in films:
        cursor.execute("INSERT INTO ActorMovies (actor_id, movie_id) VALUES (?, ?)",
                       (actor_map[actor], movie_map[film]))

# Збереження змін
conn.commit()
conn.close()

print("✅ Database created and populated successfully!")
