import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "jobs.db"


class Database:

    def __init__(self):
        DATABASE_PATH.parent.mkdir(exist_ok=True)

        self.connection = sqlite3.connect(DATABASE_PATH)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS jobs (

                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,

                title TEXT,
                company TEXT,

                source TEXT,
                status TEXT,

                details TEXT,

                created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.commit()

    def exists(self, url):

        cursor = self.connection.execute(
            "SELECT 1 FROM jobs WHERE url = ?",
            (url,)
        )

        return cursor.fetchone() is not None

    def add(
        self,
        url,
        title="",
        company="",
        source="",
        status="Found",
        details=""
    ):

        try:

            self.connection.execute("""
                INSERT INTO jobs (
                    url,
                    title,
                    company,
                    source,
                    status,
                    details
                )

                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                url,
                title,
                company,
                source,
                status,
                details
            ))

            self.connection.commit()

        except sqlite3.IntegrityError:
            pass

    def update_status(
        self,
        url,
        status,
        details=""
    ):

        self.connection.execute("""
            UPDATE jobs
            SET
                status = ?,
                details = ?
            WHERE url = ?
        """, (
            status,
            details,
            url
        ))

        self.connection.commit()

    def close(self):
        self.connection.close()