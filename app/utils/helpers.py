from datetime import datetime
import pandas as pd


def parse_date(date_str):
    """Parse a date string with multiple formats."""
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return None


def clean_numeric(value, default=None):
    """Convert a value to a float or int if possible, otherwise return the default."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
