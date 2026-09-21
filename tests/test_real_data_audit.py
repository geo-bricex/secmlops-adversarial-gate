import json
from pathlib import Path

import pandas as pd

from src.data.io import discover_csvs, sha256_file
from src.data.sampling import group_disjoint_split, row_fingerprints
from src.preprocessing.labels import map_binary_labels
from src.preprocessing.pipeline import build_preprocessor, split_features_target

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "results/data_profile"


def test_real_dataset_discovery_counts():
    assert len(discover_csvs(ROOT / "data/cic_iot_2023/raw/CIC_IOT_Dataset2023/CSV")) == 309
    assert len(discover_csvs(ROOT / "data/edge_iiotset/raw/Edge-IIoTset Cyber Security/Edge-IIoTset dataset")) == 23
    assert len(discover_csvs(ROOT / "data/ton_iot/raw/TON_IoT Network Dataset")) == 1


def test_raw_inventory_sizes_unchanged():
    for dataset, raw in {
        "cic_iot_2023": ROOT / "data/cic_iot_2023/raw/CIC_IOT_Dataset2023/CSV",
        "edge_iiotset": ROOT / "data/edge_iiotset/raw/Edge-IIoTset Cyber Security/Edge-IIoTset dataset",
        "ton_iot": ROOT / "data/ton_iot/raw/TON_IoT Network Dataset",
    }.items():
        manifest = pd.read_csv(REPORTS / f"{dataset}_manifest.csv")
        actual = {p.relative_to(raw).as_posix(): p.stat().st_size for p in raw.rglob("*") if p.is_file()}
        assert actual == dict(zip(manifest.relative_path, manifest.size_bytes))


def test_ton_hash_is_stable():
    manifest = pd.read_csv(REPORTS / "ton_iot_manifest.csv")
    path = ROOT / "data/ton_iot/raw/TON_IoT Network Dataset/train_test_network.csv"
    assert sha256_file(path) == manifest.loc[manifest.file_name == path.name, "sha256"].iloc[0]


def test_real_label_mappings():
    assert map_binary_labels(pd.Series(["Benign_Final", "DDoS-ICMP_Flood"]), ["Benign_Final"]).tolist() == [0, 1]
    assert map_binary_labels(pd.Series(["0", "1"]), [0, "0"]).tolist() == [0, 1]
    assert map_binary_labels(pd.Series([0, 1]), [0, "0"]).tolist() == [0, 1]


def test_group_split_has_no_overlap_and_is_reproducible():
    frame = pd.DataFrame({"x": [1, 1, 2, 3, 4, 5, 6, 7, 8, 9], "target": [0, 0, 1, 0, 1, 0, 1, 0, 1, 0]})
    groups = row_fingerprints(frame, excluded=("target",))
    first = group_disjoint_split(frame, groups, 42, .6, .2, .2)
    second = group_disjoint_split(frame, groups, 42, .6, .2, .2)
    assert [part.to_dict("list") for part in first] == [part.to_dict("list") for part in second]
    values = [set(part.x) for part in first]
    assert not values[0] & values[1] and not values[0] & values[2] and not values[1] & values[2]


def test_target_and_source_file_excluded_and_order_stable():
    frame = pd.DataFrame({"b": [1, 2], "a": [3, 4], "source_file": ["x", "y"], "target": [0, 1]})
    features, target = split_features_target(frame, "target", ("source_file",))
    assert features.columns.tolist() == ["b", "a"]
    assert target.tolist() == [0, 1]


def test_scaler_is_fitted_only_on_train_and_metadata_serializes():
    train = pd.DataFrame({"x": [0.0, 2.0]})
    test = pd.DataFrame({"x": [1000.0]})
    processor = build_preprocessor(["x"], [])
    processor.fit(train)
    processor.transform(test)
    assert processor.named_transformers_["numeric"].named_steps["scaler"].mean_[0] == 1.0
    json.dumps({"features": list(processor.feature_names_in_), "seed": 42})
