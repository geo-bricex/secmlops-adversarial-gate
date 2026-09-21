from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split


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

