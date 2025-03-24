import os
import sqlite3

def get_db_path() -> str:
    """
    Returns the absolute path to the questions database file.
    """
    return os.path.abspath(os.path.join("Resources", "questions.db"))

def create_db() -> None:
    """
    Creates the questions database and its table if they do not exist.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            question TEXT PRIMARY KEY,
            answer TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_db_connection() -> sqlite3.Connection:
    """
    Returns a connection to the questions database.
    Ensures the database and table exist.
    """
    create_db()  # Ensure the DB is set up before connecting
    db_path = get_db_path()
    return sqlite3.connect(db_path)
