from datetime import datetime
from typing import Literal

import duckdb
import numpy as np
import polars as pl
from loguru import logger


class TableManager:
    """Handles table creation and schema management"""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn
        self._sequences = ["category", "image", "keyword", "tagging"]

    def create_all(self, drop: bool = False, default: bool = False):
        """Create all necessary tables

        Args:
            drop: If True, drops existing tables before creating new ones
            default: If True, creates default category values
        """
        if drop:
            self.drop_all()

        self._create_keyword_categories_tables()
        self._create_image_data_table()
        self._create_keywords_table()
        self._create_manual_tagged_images_table()
        self._create_ai_tagged_images_table()

        if default:
            self._create_defaults()

    def drop_all(self):
        """Drop all tables and sequences"""
        tables = ["AITaggedImages", "ManualTaggedImages", "Keywords", "ImageData", "KeywordCategories", "Categories"]

        for table in tables:
            self.conn.execute(f"DROP TABLE IF EXISTS {table}")

        for seq in self._sequences:
            self.conn.execute(f"DROP SEQUENCE IF EXISTS seq_{seq}id")

    def _add_incremental_id(self, name):
        """Create a sequence for auto-incrementing IDs

        Args:
            name: Base name for the sequence
        """
        self.conn.execute(f"CREATE SEQUENCE seq_{name}id START 1;")

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
        self._add_incremental_id("image")

    def _create_keywords_table(self):
        """Create the Keywords table with foreign key to KeywordTypes"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS Keywords (
                id INTEGER PRIMARY KEY,
                keyword VARCHAR NOT NULL,
                ai_tag BOOLEAN NOT NULL
            )
        """)
        self._add_incremental_id("keyword")

    def _create_keyword_categories_tables(self):
        """Create the KeywordCategories and Categories tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS Categories (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL
            )
        """)
        self._add_incremental_id("category")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS KeywordCategories (
                keyword_id INTEGER PRIMARY KEY,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (category_id) REFERENCES Categories(id)                              
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
        self._add_incremental_id("tagging")

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

    def _create_defaults(self):
        """Insert default category values"""
        self.conn.executemany(
            """
            INSERT OR IGNORE INTO Categories (id, name)
            VALUES (nextval('seq_categoryid'), ?)
            """,
            [
                ("unset",),
                ("description",),
                ("object",),
                ("private",),
            ],
        )
        self.conn.commit()


class DataInserter:
    """Handles data insertion operations"""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def insert_image_data(self, data: pl.DataFrame):
        """Insert image data from a polars DataFrame

        The image data DataFrame should contain the following columns:
        - name: Image filename
        - CreateDate: Creation timestamp in nanoseconds since epoch
        - FocalLength: Focal length in mm
        - FNumber: F-number/aperture value
        - Camera: Camera model name
        - Lens: Lens model name
        - Flag: Image flag/rating
        - CropFactor: Sensor crop factor
        - Date: Image date
        - Keywords: List of keywords/tags associated with the image

        Args:
            data: Polars DataFrame containing image metadata and keywords
        """
        self._insert_images(data)
        self._insert_keywords(data)
        self._link_images_to_keywords(data)
        self.conn.commit()
        logger.success(f"Data for {len(data)} images inserted")

    def _insert_images(self, data: pl.DataFrame):
        """Insert image metadata

        Args:
            data: Polars DataFrame containing image metadata
        """
        image_data = data.select(
            ["name", "CreateDate", "FocalLength", "FNumber", "Camera", "Lens", "Flag", "CropFactor", "Date"]
        )

        imd = image_data.to_numpy()
        imd[:, 1] = np.vectorize(lambda x: datetime.fromtimestamp(x / 1000000000))(imd[:, 1])

        self.conn.executemany(
            """
            INSERT INTO ImageData (
                id, name, create_date, focal_length, f_number,
                camera, lens, flag, crop_factor, date
            ) VALUES (nextval('seq_imageid'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            imd.tolist(),
        )

    def _insert_keywords(self, data: pl.DataFrame):
        """Insert unique keywords

        Args:
            data: Polars DataFrame containing keywords
        """
        keywords_set = set()
        for keywords in data["Keywords"].to_list():
            keywords_set.update(keywords)

        self.conn.executemany(
            """
            INSERT OR IGNORE INTO Keywords (id, keyword, ai_tag)
            VALUES (nextval('seq_keywordid'), ?, false)
        """,
            [(k,) for k in keywords_set],
        )

    def _link_images_to_keywords(self, data: pl.DataFrame):
        """Create relationships between images and keywords

        Args:
            data: Polars DataFrame containing image and keyword relationships
        """
        df_kws = self.conn.execute("select id, keyword from Keywords").pl()
        df_imgs = self.conn.execute("select id, name from ImageData").pl()

        manual_tags = (
            data.select(["Keywords", "name"])
            .explode("Keywords")
            .rename({"Keywords": "keyword"})
            .join(df_imgs, how="inner", on="name")
            .rename({"id": "image_id"})
            .drop("name")
            .drop_nulls()
            .join(df_kws, how="inner", on="keyword")
            .rename({"id": "keyword_id"})
            .drop(["keyword"])["keyword_id", "image_id"]
        )

        self.conn.executemany(
            """
            INSERT INTO ManualTaggedImages (id, keyword_id, image_id)
            VALUES (nextval('seq_taggingid'), ?, ?)
        """,
            manual_tags.to_numpy().tolist(),
        )


class Database:
    """
    Database manager class for handling DuckDB operations

    Args:
        db_path: Path to the database file
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self.tables = TableManager(self.conn)
        self.inserter = DataInserter(self.conn)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_tables(self, drop: bool = False, default: bool = True):
        """Create all necessary tables in the database.

        Args:
            drop: If True, drops existing tables before creating new ones.
            default: If True, creates default category values
        """
        self.tables.create_all(drop=drop, default=default)

    def drop_tables(self):
        """Drop all tables from the database in the correct order to handle foreign key dependencies"""
        self.tables.drop_all()

    def insert_image_data(self, data: pl.DataFrame):
        """Insert image data from a polars DataFrame into the database.

            The image data DataFrame should contain the following columns:

        - name: Image filename
        - CreateDate: Creation timestamp in nanoseconds since epoch
        - FocalLength: Focal length in mm
        - FNumber: F-number/aperture value
        - Camera: Camera model name
        - Lens: Lens model name
        - Flag: Image flag/rating
        - CropFactor: Sensor crop factor
        - Date: Image date
        - Keywords: List of keywords/tags associated with the image

        Args:
            data: Polars DataFrame containing image metadata and keywords
        """
        self.inserter.insert_image_data(data)

    def read_table(self, table: Literal["ImageData", "Images", "Keywords", "KeywordCategories", "Categories"]):
        """Read a table from the database into a Polars DataFrame

        Args:
            table: Name of the table to read

        Returns:
            Polars DataFrame containing the table data
        """
        return self.conn.execute(f"select * from {table}").pl()


def reset_db():
    """Reset the database to its initial state"""
    with Database("data/database.db") as db:
        db.create_tables(drop=True)


if __name__ == "__main__":
    reset_db()

    with Database("data/database.db") as db:
        db.insert_image_data(pl.read_parquet("data/data.parquet"))
