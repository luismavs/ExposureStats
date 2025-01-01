from pathlib import Path

import polars as pl
import pytest

from exposurestats.db import Database


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path"""
    return str(tmp_path / "test.db")


@pytest.fixture
def db(temp_db_path):
    """Create a database instance"""
    database = Database(temp_db_path)
    database.create_tables()
    yield database
    database.close()


def test_database_creation(temp_db_path):
    """Test that database file is created"""
    db = Database(temp_db_path)
    assert Path(temp_db_path).exists()
    db.close()


def test_context_manager(temp_db_path):
    """Test database context manager"""
    with Database(temp_db_path) as db:
        assert db.conn is not None
    assert db.conn is None


def test_tables_exist(db):
    """Test that all required tables are created"""
    expected_tables = {
        "ImageData",
        "Keywords",
        "Categories",
        "KeywordCategories",
        "ManualTaggedImages",
        "AITaggedImages",
    }

    result = db.conn.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main'
    """).fetchall()

    actual_tables = {row[0] for row in result}
    assert expected_tables.issubset(actual_tables)


def test_table_schemas(db):
    """Test that tables have correct columns"""
    # Test ImageData columns
    image_data_cols = db.conn.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'ImageData'
    """).fetchall()

    assert any(col for col in image_data_cols if col[0] == "id" and col[1] == "INTEGER")
    assert any(col for col in image_data_cols if col[0] == "name" and col[2] == "NO")


def test_create_and_drop_tables(temp_db_path):
    """Test creating and dropping tables"""
    with Database(temp_db_path) as db:
        db.create_tables()
        # Check tables exist
        result = db.conn.execute("SELECT table_name FROM information_schema.tables").fetchall()
        assert len(result) > 0

        # Drop tables
        db.drop_tables()
        result = db.conn.execute("SELECT table_name FROM information_schema.tables").fetchall()
        assert len(result) == 0


def test_database_close(temp_db_path):
    """Test database close behavior"""
    db = Database(temp_db_path)
    assert db.conn is not None
    db.close()
    assert db.conn is None


def test_connection_after_error(temp_db_path):
    """Test that connection is closed even if an error occurs"""
    try:
        with Database(temp_db_path) as db:
            raise Exception("Test error")
    except Exception:
        pass
    assert db.conn is None


def test_invalid_path():
    """Test that invalid database path raises appropriate error"""
    with pytest.raises(Exception):
        Database("/nonexistent/path/to/db.db")


def test_insert_and_read_data(db):
    """Test inserting and reading data"""
    # Create sample data
    data = pl.DataFrame(
        {
            "name": ["test.jpg"],
            "CreateDate": [1609459200000000000],  # 2021-01-01 in nanoseconds
            "FocalLength": [50.0],
            "FNumber": [2.8],
            "Camera": ["Test Camera"],
            "Lens": ["Test Lens"],
            "Flag": [0],
            "CropFactor": [1.0],
            "Date": ["2021-01-01"],
            "Keywords": [["test", "photo"]],
        }
    )

    # Insert data
    db.insert_image_data(data)

    # Read and verify data
    image_data = db.read_table("ImageData")
    assert len(image_data) == 1
    assert image_data["name"][0] == "test.jpg"

    keywords = db.read_table("Keywords")
    assert len(keywords) == 2


if __name__ == "__main__":
    pytest.main([__file__])
