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
    expected_tables = {"ImageData", "Keywords", "KeywordTypes", "ManualTaggedImages", "AITaggedImages"}

    result = db.conn.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main'
    """).fetchall()

    actual_tables = {row[0] for row in result}
    assert expected_tables.issubset(actual_tables)


def test_table_schemas(db):
    """Test that tables have correct columns and constraints"""
    # Test ImageData columns
    image_data_cols = db.conn.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'ImageData'
    """).fetchall()

    assert any(col for col in image_data_cols if col[0] == "id" and col[1] == "INTEGER")
    assert any(col for col in image_data_cols if col[0] == "name" and col[2] == "NO")

    # Test Keywords foreign key
    keywords_fk = db.conn.execute("""
        SELECT *
        FROM information_schema.table_constraints
        WHERE table_name = 'Keywords'
        AND constraint_type = 'FOREIGN KEY'
    """).fetchall()

    assert len(keywords_fk) > 0


def test_double_creation(temp_db_path):
    """Test that creating tables twice doesn't raise errors"""
    db1 = Database(temp_db_path)
    db1.close()

    # Should not raise any errors
    db2 = Database(temp_db_path)
    db2.close()


def test_database_close(temp_db_path):
    """Test database close behavior"""
    db = Database(temp_db_path)
    assert db.conn is not None

    db.close()
    assert db.conn is None

    # Test double close doesn't raise error
    db.close()


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


def test_referential_integrity(db):
    """Test that foreign key constraints are enforced"""
    # First create a valid KeywordType to reference
    db.conn.execute("""
        INSERT INTO KeywordTypes (id, name)
        VALUES (1, 'test_type')
    """)

    # Try to insert into Keywords with invalid type_id
    with pytest.raises(Exception):
        db.conn.execute("""
            INSERT INTO Keywords (id, keyword, type_id, ai_tag, category)
            VALUES (1, 'test', 999, false, 'test')
        """)

    # Try to insert into ManualTaggedImages with invalid keyword_id and image_id
    with pytest.raises(Exception):
        db.conn.execute("""
            INSERT INTO ManualTaggedImages (id, keyword_id, image_id)
            VALUES (1, 999, 999)
        """)

    # Try to insert into AITaggedImages with invalid keyword_id and image_id
    with pytest.raises(Exception):
        db.conn.execute("""
            INSERT INTO AITaggedImages (id, keyword_id, image_id, tagging_date)
            VALUES (1, 999, 999, CURRENT_TIMESTAMP)
        """)


def test_foreign_key_relationships(db):
    """Test that all foreign key relationships are properly set up"""
    # Test each foreign key relationship individually

    # Test Keywords -> KeywordTypes relationship
    db.conn.execute("""
        INSERT INTO KeywordTypes (id, name) VALUES (999, 'test_type')
    """)
    db.conn.execute("""
        INSERT INTO Keywords (id, keyword, type_id, ai_tag, category)
        VALUES (999, 'test', 999, false, 'test')
    """)

    # Test that invalid foreign keys are rejected
    with pytest.raises(Exception):
        db.conn.execute("""
            INSERT INTO Keywords (id, keyword, type_id, ai_tag, category)
            VALUES (1000, 'test', 1000, false, 'test')
        """)

    # Test ManualTaggedImages relationships
    with pytest.raises(Exception):
        db.conn.execute("""
            INSERT INTO ManualTaggedImages (id, keyword_id, image_id)
            VALUES (1, 1000, 1000)
        """)

    # Test AITaggedImages relationships
    with pytest.raises(Exception):
        db.conn.execute("""
            INSERT INTO AITaggedImages (id, keyword_id, image_id, tagging_date)
            VALUES (1, 1000, 1000, CURRENT_TIMESTAMP)
        """)

    # Clean up test data
    db.conn.execute("DELETE FROM Keywords WHERE id = 999")
    db.conn.execute("DELETE FROM KeywordTypes WHERE id = 999")


def test_create_db():
    data = pl.read_parquet("tests/testdata/sample_ImageData.parquet")

    with Database("data/database.db") as conn:
        conn.create_tables(drop=True)
        conn.insert_image_data(data=data)


if __name__ == "__main__":
    test_create_db()
