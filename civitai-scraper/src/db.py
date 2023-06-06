import sqlite3
from typing import Optional, Generator

import settings


class DB:
    def __init__(self) -> None:
        conn = sqlite3.connect(settings.SQLITE_NAME)
        conn.row_factory = sqlite3.Row
        self._conn = conn
        self._create_tables()
        print("Database connection established.")

    def close(self) -> None:
        self._conn.close()
        print("Database connection closed.")

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            BEGIN;
            CREATE TABLE IF NOT EXISTS app (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                current_page INTEGER NOT NULL,
                page_size INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS image (
                image_id INTEGER UNIQUE,
                response TEXT NOT NULL,
                done INTEGER NOT NULL
            );
            COMMIT; 
            """
        )

    def start_job(self, current_page: int = 1, page_size: int = 100) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO app
            VALUES (1, ?, ?)
            """,
            (current_page, page_size),
        )

        self._conn.commit()

    def get_job(self) -> Optional[sqlite3.Row]:
        curr = self._conn.execute(
            """
            SELECT * FROM app
            WHERE id = 1
            """
        )

        return curr.fetchone()

    def update_job_current_page(self, page: int) -> None:
        self._conn.execute(
            """
            UPDATE app
            SET current_page = ?
            WHERE id = 1
            """,
            (page,),
        )

        self._conn.commit()

    def delete_job(self) -> None:
        self._conn.execute(
            """
            DELETE FROM app
            WHERE id = 1
            """
        )

        self._conn.commit()

    def insert_image(self, image_id: int, response: str) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO image
            VALUES (?, ?, 0)
            """,
            (image_id, response),
        )

        self._conn.commit()

    def get_images(self) -> Generator:
        curr = self._conn.execute(
            """
            SELECT * FROM image
            WHERE done = 0
            """
        )

        while True:
            row = curr.fetchone()
            if row is None:
                break

            yield row

    def update_image_status(self, image_id: int) -> None:
        self._conn.execute(
            """
            UPDATE image
            SET done = 1
            WHERE image_id = ?
            """,
            (image_id,),
        )

        self._conn.commit()
