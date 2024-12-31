from datetime import datetime

import duckdb
import numpy as np
import polars as pl
from loguru import logger


class Database:
    """
    Database manager class for handling DuckDB operations

    Args:
        db_path: Path to the database file
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_image_data_table(self):
        """Create the ImageData table"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ImageData (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                create_date TIMESTAMP NOT NULL,
                focal_length FLOAT,
                f_number FLOAT,
                camera VARCHAR NOT NULL,
                lens VARCHAR,
                flag INTEGER NOT NULL,
                crop_factor FLOAT,
                equivalent_focal_length FLOAT,
                date DATE NOT NULL
            )
        """)

    def _create_keywords_table(self):
        """Create the Keywords table with foreign key to KeywordTypes"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS Keywords (
                id INTEGER PRIMARY KEY,
                keyword VARCHAR NOT NULL,
                type_id INTEGER NOT NULL,
                ai_tag BOOLEAN NOT NULL,
                category VARCHAR NOT NULL,
                FOREIGN KEY (type_id) REFERENCES KeywordTypes(id)
            )
        """)

    def _create_keyword_types_table(self):
        """Create the KeywordTypes table"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS KeywordTypes (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL
            )
        """)

    def _create_manual_tagged_images_table(self):
        """Create the ManualTaggedImages table with foreign keys"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ManualTaggedImages (
                id INTEGER PRIMARY KEY,
                keyword_id INTEGER NOT NULL,
                image_id INTEGER NOT NULL,
                FOREIGN KEY (keyword_id) REFERENCES Keywords(id),
                FOREIGN KEY (image_id) REFERENCES ImageData(id)
            )
        """)

    def _create_ai_tagged_images_table(self):
        """Create the AITaggedImages table with foreign keys"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS AITaggedImages (
                id INTEGER PRIMARY KEY,
                keyword_id INTEGER NOT NULL,
                image_id INTEGER NOT NULL,
                tagging_date TIMESTAMP NOT NULL,
                FOREIGN KEY (keyword_id) REFERENCES Keywords(id),
                FOREIGN KEY (image_id) REFERENCES ImageData(id)
            )
        """)

    def create_tables(self, drop: bool = False):
        """Create all necessary tables in the database.

        Args:
            drop: If True, drops existing tables before creating new ones.
        """

        if drop:
            self.drop_tables()
        # Create tables in order of dependencies
        self._create_keyword_types_table()  # First, as Keywords depends on it
        self._create_image_data_table()
        self._create_keywords_table()  # After KeywordTypes
        self._create_manual_tagged_images_table()
        self._create_ai_tagged_images_table()

    def drop_tables(self):
        """Drop all tables from the database in the correct order to handle foreign key dependencies"""
        # Drop tables in reverse order of creation to handle foreign key constraints
        self.conn.execute("DROP TABLE IF EXISTS AITaggedImages")
        self.conn.execute("DROP TABLE IF EXISTS ManualTaggedImages")
        self.conn.execute("DROP TABLE IF EXISTS Keywords")
        self.conn.execute("DROP TABLE IF EXISTS ImageData")
        self.conn.execute("DROP TABLE IF EXISTS KeywordTypes")

    def insert_image_data(self, data: pl.DataFrame):
        """Insert image data from a polars DataFrame into the database.

        Args:
            data: Polars DataFrame containing image metadata and keywords
        """
        # Insert into ImageData table
        image_data = data.select(
            ["name", "CreateDate", "FocalLength", "FNumber", "Camera", "Lens", "Flag", "CropFactor", "Date"]
        )

        imd = image_data.to_numpy()
        imd[:, 1] = np.vectorize(lambda x: datetime.fromtimestamp(x / 1000000000))(imd[:, 1])

        self.conn.executemany(
            """
            INSERT INTO ImageData (
                name, create_date, focal_length, f_number,
                camera, lens, flag, crop_factor, date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            imd.tolist(),
        )

        breakpoint()

        # Get image IDs for the inserted records
        image_ids = {row[0]: row[1] for row in self.conn.execute("SELECT name, id FROM ImageData").fetchall()}

        # Process keywords
        keywords_set = set()
        for keywords in data["Keywords"].to_list():
            keywords_set.update(keywords)

        # Insert keywords
        self.conn.executemany(
            """
            INSERT OR IGNORE INTO Keywords (keyword, type_id, ai_tag, category)
            VALUES (?, 1, false, 'manual')
        """,
            [(k,) for k in keywords_set],
        )

        # Get keyword IDs
        keyword_ids = {row[0]: row[1] for row in self.conn.execute("SELECT keyword, id FROM Keywords").fetchall()}

        # Build ManualTaggedImages records
        logger.warning("bad code")
        breakpoint("what is an image_id object below? this way we will be able t build that that row correctly")
        tagged_images = []
        for row in data.iter_rows(named=True):
            image_id = image_ids[row["name"]]
            for keyword in row["Keywords"]:
                keyword_id = keyword_ids[keyword]
                tagged_images.append((keyword_id, image_id))

        # Insert ManualTaggedImages records
        self.conn.executemany(
            """
            INSERT INTO ManualTaggedImages (keyword_id, image_id)
            VALUES (?, ?)
        """,
            tagged_images,
        )

        self.conn.commit()
        logger.success(f"Data for {len(data)} images inserted")


def reset_db():
    with Database("data/database.db") as db:
        db.create_tables(drop=True)


if __name__ == "__main__":
    reset_db()

    with Database("data/database.db") as db:
        db.insert_image_data(pl.read_parquet("data/data.parquet"))
        breakpoint()
