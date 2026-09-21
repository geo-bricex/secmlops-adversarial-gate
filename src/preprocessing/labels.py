import pandas as pd


def map_binary_labels(labels: pd.Series, benign_labels: list) -> pd.Series:
    normalized_benign = {str(value).strip().lower() for value in benign_labels}
    normalized = labels.astype(str).str.strip().str.lower()
    return (~normalized.isin(normalized_benign)).astype("int8")

