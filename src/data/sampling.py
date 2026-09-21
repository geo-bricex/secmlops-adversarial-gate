from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GroupShuffleSplit


def stratified_sample(frame: pd.DataFrame, target: str, n: int | None, seed: int) -> pd.DataFrame:
    if n is None or n >= len(frame):
        return frame.sample(frac=1, random_state=seed).reset_index(drop=True)
    sampled, _ = train_test_split(frame, train_size=n, stratify=frame[target], random_state=seed)
    return sampled.reset_index(drop=True)


def stratified_split(frame: pd.DataFrame, target: str, seed: int, train=0.70, validation=0.15, test=0.15):
    if abs(train + validation + test - 1.0) > 1e-9:
        raise ValueError("Split proportions must sum to 1")
    train_df, remainder = train_test_split(frame, train_size=train, stratify=frame[target], random_state=seed)
    val_fraction = validation / (validation + test)
    validation_df, test_df = train_test_split(remainder, train_size=val_fraction, stratify=remainder[target], random_state=seed)
    return tuple(part.reset_index(drop=True) for part in (train_df, validation_df, test_df))


def row_fingerprints(frame: pd.DataFrame, excluded: tuple[str, ...] = ()) -> pd.Series:
    columns = [column for column in frame.columns if column not in excluded]
    return pd.util.hash_pandas_object(frame[columns], index=False).astype("uint64")


def group_disjoint_split(frame: pd.DataFrame, groups: pd.Series, seed: int, train=.70, validation=.15, test=.15):
    """Deterministic group-disjoint split; class balance must be checked after use."""
    if abs(train + validation + test - 1.0) > 1e-9:
        raise ValueError("Split proportions must sum to 1")
    first = GroupShuffleSplit(n_splits=1, train_size=train, random_state=seed)
    train_idx, rest_idx = next(first.split(frame, groups=groups))
    rest = frame.iloc[rest_idx]
    rest_groups = groups.iloc[rest_idx]
    second = GroupShuffleSplit(n_splits=1, train_size=validation / (validation + test), random_state=seed)
    val_local, test_local = next(second.split(rest, groups=rest_groups))
    return (frame.iloc[train_idx].reset_index(drop=True), rest.iloc[val_local].reset_index(drop=True),
            rest.iloc[test_local].reset_index(drop=True))
