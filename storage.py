import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "smogzilla.db")


def _get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create tables if they don't exist."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                chat_id     INTEGER NOT NULL,
                city_key    TEXT    NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, city_key)
            )
        """)
        conn.commit()


def add_subscription(chat_id: int, city_key: str) -> bool:
    """Add a subscription. Returns False if already exists."""
    try:
        with _get_connection() as conn:
            conn.execute(
                "INSERT INTO subscriptions (chat_id, city_key) VALUES (?, ?)",
                (chat_id, city_key)
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False  # PRIMARY KEY violation — already subscribed


def remove_subscription(chat_id: int, city_key: str) -> bool:
    """Remove a subscription. Returns False if it didn't exist."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM subscriptions WHERE chat_id = ? AND city_key = ?",
            (chat_id, city_key)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_subscriptions_by_chat(chat_id: int) -> list[str]:
    """Get all city subscriptions for a given chat."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT city_key FROM subscriptions WHERE chat_id = ?",
            (chat_id,)
        )
        return [row[0] for row in cursor.fetchall()]


def get_all_subscriptions() -> list[tuple[int, str]]:
    """Get all subscriptions — used by the scheduler."""
    with _get_connection() as conn:
        cursor = conn.execute("SELECT chat_id, city_key FROM subscriptions")
        return cursor.fetchall()