"""Remote loaders for fetching datasets into Nexora."""

from __future__ import annotations

import io

import pandas as pd


def load_from_url(url: str) -> pd.DataFrame:
    """Download and load a CSV/JSON file from a URL.

    Args:
        url: Public URL to dataset.

    Returns:
        Loaded DataFrame.
    """
    import requests

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Simple heuristic to determine file type based on url extension or content type
    content_type = response.headers.get("Content-Type", "")
    if "json" in content_type or url.endswith(".json"):
        return pd.read_json(io.StringIO(response.text))
    elif url.endswith(".parquet"):
        return pd.read_parquet(io.BytesIO(response.content))
    else:
        # Default to CSV
        return pd.read_csv(io.StringIO(response.text))


def load_from_sql(query: str, connection_string: str | None = None) -> pd.DataFrame:
    """Run a SQL query via DuckDB.

    Args:
        query: SQL string.
        connection_string: Optional connection string for DuckDB extensions.

    Returns:
        Loaded DataFrame.
    """
    try:
        import duckdb
    except ImportError as e:
        raise ImportError(
            "DuckDB is required for from_sql. It should be installed with nexora."
        ) from e

    if connection_string:
        # Connect to a specific file or database
        conn = duckdb.connect(connection_string)
        return conn.execute(query).df()

    return duckdb.query(query).df()


def load_from_postgres(uri: str, table: str) -> pd.DataFrame:
    """Connect to Postgres and load a full table.

    Args:
        uri: Connection URI, e.g., postgresql://user:pw@host:port/db
        table: Table name to extract.

    Returns:
        Loaded DataFrame.
    """
    try:
        import psycopg2  # noqa: F401
        import sqlalchemy
    except ImportError as e:
        raise ImportError(
            "psycopg2 and sqlalchemy are required for from_postgres. Run `pip install nexora[sql]`"
        ) from e

    engine = sqlalchemy.create_engine(uri)
    return pd.read_sql_table(table, engine)


def load_from_mongodb(uri: str, collection: str) -> pd.DataFrame:
    """Connect to MongoDB and flatten documents from a collection.

    Args:
        uri: MongoDB connection string.
        collection: The collection namespace in format `db.collection`.

    Returns:
        Flattened DataFrame.
    """
    try:
        import pymongo
    except ImportError as e:
        raise ImportError(
            "pymongo is required for from_mongodb. Run `pip install nexora[mongo]`"
        ) from e

    db_name, coll_name = collection.split(".", 1)
    client = pymongo.MongoClient(uri)
    cursor = client[db_name][coll_name].find()

    # json_normalize flattens nested dictionaries
    df = pd.json_normalize(list(cursor))
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    return df


def load_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """Load a dataset from an AWS S3 bucket.

    Args:
        bucket: S3 bucket name.
        key: File key in bucket.

    Returns:
        Loaded DataFrame.
    """
    try:
        import boto3
    except ImportError as e:
        raise ImportError(
            "boto3 is required for from_s3. Run `pip install nexora[cloud]`"
        ) from e

    client = boto3.client("s3")
    obj = client.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read()

    if key.endswith(".json"):
        return pd.read_json(io.BytesIO(body))
    elif key.endswith(".parquet"):
        return pd.read_parquet(io.BytesIO(body))
    else:
        # Default to CSV
        return pd.read_csv(io.BytesIO(body))


def load_from_google_sheets(sheet_id: str) -> pd.DataFrame:
    """Load a public Google Sheet using pandas.

    Args:
        sheet_id: The ID component from the Google Sheets URL.

    Returns:
        Loaded DataFrame.
    """
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        return pd.read_csv(url)
    except Exception as e:
        raise RuntimeError(
            f"Could not read Google Sheet (ensure it is accessible via link): {e}"
        ) from e


def load_from_sklearn(dataset_name: str) -> pd.DataFrame:
    """Load a built-in scikit-learn dataset.

    Args:
        dataset_name: Name of dataset (e.g., 'iris', 'breast_cancer', 'diabetes').

    Returns:
        Loaded DataFrame containing both features and target.
    """
    try:
        import sklearn.datasets
    except ImportError as e:
        raise ImportError(
            "scikit-learn is required. It should be installed with nexora."
        ) from e

    # Map friendly names to sklearn load functions
    loaders = {
        "iris": sklearn.datasets.load_iris,
        "breast_cancer": sklearn.datasets.load_breast_cancer,
        "diabetes": sklearn.datasets.load_diabetes,
        "wine": sklearn.datasets.load_wine,
        "california_housing": getattr(
            sklearn.datasets, "fetch_california_housing", None
        ),
    }

    name = dataset_name.lower().replace("-", "_")
    if name not in loaders or loaders[name] is None:
        raise ValueError(
            f"Sklearn dataset '{dataset_name}' not supported. Options: {list(loaders.keys())}"
        )

    data = loaders[name](as_frame=True)
    df = data.frame
    # By convention, if we know it's a sklearn dataset, the target column is usually the last one,
    # but we just return the full frame and let the user specify target
    return df


def load_from_clipboard() -> pd.DataFrame:
    """Load tabular data from the system clipboard.

    Returns:
        Loaded DataFrame.
    """
    try:
        return pd.read_clipboard()
    except Exception as e:
        raise RuntimeError(
            f"Failed to read from clipboard. Make sure text is copied: {e}"
        ) from e
