import io

import pandas as pd

MAX_ROWS = 3_000_000
MAX_COLS = 500


class DatasetValidationError(Exception):
    def __init__(self, message: str, code: str = "validation_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def load_dataframe(content: bytes, filename: str) -> pd.DataFrame:
    if len(content) == 0:
        raise DatasetValidationError("The uploaded file is empty.", "empty_file")

    ext = filename.lower().split(".")[-1]

    try:
        if ext == "csv":
            df = None
            for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"):
                for sep in [",", ";", "\t", "|", None]:
                    try:
                        kwargs = {
                            "encoding": encoding,
                            "low_memory": False,
                            "on_bad_lines": "skip",
                        }
                        if sep is not None:
                            kwargs["sep"] = sep
                        else:
                            kwargs["engine"] = "python"
                        temp_df = pd.read_csv(io.BytesIO(content), **kwargs)
                        if temp_df is not None and len(temp_df.columns) > 1:
                            df = temp_df
                            break
                        elif temp_df is not None and df is None:
                            df = temp_df
                    except Exception:
                        continue
                if df is not None and len(df.columns) > 1:
                    break
            if df is None:
                raise DatasetValidationError(
                    "Unsupported or corrupted file encoding.", "encoding_error"
                )
        elif ext in ["xls", "xlsx"]:
            df = pd.read_excel(io.BytesIO(content))
        elif ext == "json":
            df = pd.read_json(io.BytesIO(content))
        elif ext == "parquet":
            df = pd.read_parquet(io.BytesIO(content))
        elif ext == "feather":
            df = pd.read_feather(io.BytesIO(content))
        elif ext in ["tsv", "txt"]:
            df = pd.read_csv(io.BytesIO(content), sep="\t", low_memory=False)
        elif ext == "html":
            df = pd.read_html(io.BytesIO(content))[0]
        elif ext == "xml":
            df = pd.read_xml(io.BytesIO(content))
        else:
            try:
                # Fallback to CSV parsing for unknown text files
                df = pd.read_csv(io.BytesIO(content), low_memory=False)
            except Exception:
                raise DatasetValidationError(
                    f"Unsupported file format: .{ext}", "invalid_format"
                )
    except pd.errors.EmptyDataError:
        raise DatasetValidationError("The file contains no data.", "empty_dataset")
    except ValueError as e:
        if "No tables found" in str(e):
            raise DatasetValidationError(
                "No data tables found in file.", "empty_dataset"
            )
        raise DatasetValidationError(f"Could not parse file: {e}", "parse_error")
    except Exception as e:
        raise DatasetValidationError(f"Could not parse file: {e}", "parse_error")

    if df.empty or len(df.columns) == 0:
        raise DatasetValidationError(
            "The dataset has no rows or columns.", "empty_dataset"
        )

    if df.columns.duplicated().any():
        dupes = df.columns[df.columns.duplicated()].tolist()
        raise DatasetValidationError(
            f"Duplicate column headers found: {', '.join(map(str, dupes[:5]))}",
            "duplicate_headers",
        )

    unnamed = [c for c in df.columns if str(c).startswith("Unnamed")]
    if len(unnamed) == len(df.columns):
        raise DatasetValidationError(
            "CSV appears to lack a valid header row.", "invalid_headers"
        )

    if len(df) > MAX_ROWS:
        raise DatasetValidationError(
            f"Dataset exceeds maximum of {MAX_ROWS:,} rows.",
            "too_large",
        )

    if len(df.columns) > MAX_COLS:
        raise DatasetValidationError(
            f"Dataset exceeds maximum of {MAX_COLS} columns.",
            "too_many_columns",
        )

    df.columns = [str(c).strip() for c in df.columns]
    return df


def save_to_buffer(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()
