from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from nexora.io.remote import (
    load_from_clipboard,
    load_from_google_sheets,
    load_from_mongodb,
    load_from_postgres,
    load_from_s3,
    load_from_sklearn,
    load_from_sql,
    load_from_url,
)


def test_load_from_sklearn():
    df = load_from_sklearn("iris")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_load_from_sklearn_invalid():
    with pytest.raises(ValueError):
        load_from_sklearn("nonexistent_dataset")


@patch("requests.get")
def test_load_from_url_csv(mock_get):
    mock_response = MagicMock()
    mock_response.text = "col1,col2\n1,2\n3,4"
    mock_response.headers = {"Content-Type": "text/csv"}
    mock_get.return_value = mock_response

    df = load_from_url("http://example.com/data.csv")
    assert "col1" in df.columns
    assert len(df) == 2


def test_load_from_sql():
    try:
        import duckdb  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError, match="DuckDB is required"):
            load_from_sql("SELECT * FROM mock_table", "mock_engine")
        return

    with patch("duckdb.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_df = pd.DataFrame({"a": [1, 2]})
        mock_conn.execute.return_value.df.return_value = mock_df
        mock_connect.return_value = mock_conn

        df = load_from_sql("SELECT * FROM mock_table", "mock_db.duckdb")
        assert "a" in df.columns
        mock_connect.assert_called_once_with("mock_db.duckdb")
        mock_conn.execute.assert_called_once_with("SELECT * FROM mock_table")


def test_load_from_postgres():
    try:
        import psycopg2  # noqa: F401
        import sqlalchemy  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError, match="psycopg2 and sqlalchemy are required"):
            load_from_postgres("postgresql://user:pass@localhost/db", "my_table")
        return

    with (
        patch("pandas.read_sql_table") as mock_read_sql_table,
        patch("sqlalchemy.create_engine") as mock_create_engine,
    ):
        mock_df = pd.DataFrame({"a": [1, 2]})
        mock_read_sql_table.return_value = mock_df

        df = load_from_postgres("postgresql://user:pass@localhost/db", "my_table")
        assert "a" in df.columns
        mock_create_engine.assert_called_once_with(
            "postgresql://user:pass@localhost/db"
        )


def test_load_from_mongodb():
    try:
        import pymongo  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError, match="pymongo is required"):
            load_from_mongodb("mongodb://localhost", "mydb.mycollection")
        return

    with patch("pymongo.MongoClient") as mock_mongo:
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_mongo.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.find.return_value = [
            {"_id": 1, "name": "test", "nested": {"val": 5}}
        ]

        df = load_from_mongodb("mongodb://localhost", "mydb.mycollection")
        assert "name" in df.columns
        assert "nested.val" in df.columns
        assert "_id" not in df.columns


def test_load_from_s3_csv():
    try:
        import boto3  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError, match="boto3 is required"):
            load_from_s3("mybucket", "data.csv")
        return

    with patch("boto3.client") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_obj = {"Body": MagicMock()}
        mock_obj["Body"].read.return_value = b"col1,col2\n1,2\n3,4"
        mock_client.get_object.return_value = mock_obj

        df = load_from_s3("mybucket", "data.csv")
        assert "col1" in df.columns


@patch("pandas.read_csv")
def test_load_from_google_sheets(mock_read_csv):
    mock_df = pd.DataFrame({"col1": [1, 2]})
    mock_read_csv.return_value = mock_df
    df = load_from_google_sheets("test_id")
    assert "col1" in df.columns
    mock_read_csv.assert_called_once_with(
        "https://docs.google.com/spreadsheets/d/test_id/export?format=csv"
    )


@patch("pandas.read_clipboard")
def test_load_from_clipboard(mock_clipboard):
    mock_df = pd.DataFrame({"clip": [1, 2]})
    mock_clipboard.return_value = mock_df
    df = load_from_clipboard()
    assert "clip" in df.columns
