import json

import numpy as np
import pandas as pd
import torch

from src.adversarial.constraints import constraints_hold, enforce_constraints
from src.data.profile import profile_frame
from src.data.sampling import stratified_sample, stratified_split
from src.evaluation.metrics import binary_metrics
from src.models.mlp import MLP
from src.preprocessing.labels import map_binary_labels
from src.preprocessing.pipeline import build_preprocessor
from src.security_gate.gate import evaluate_gate
from src.utils.config import configuration_id, load_dataset_config, load_yaml
from src.utils.seeds import set_global_seed


def frame(n=200):
    return pd.DataFrame({"numeric": range(n), "category": ["a", "b"] * (n // 2), "label": [0, 1] * (n // 2)})


def test_configuration_loading_and_id():
    base = load_yaml("configs/base.yaml")
    assert base["splits"]["train"] == 0.70
    assert load_dataset_config("ton_iot")["id"] == "ton_iot"
    assert configuration_id(base) == configuration_id(base)


def test_binary_mapping():
    assert map_binary_labels(pd.Series(["Normal", "DDoS"]), ["normal"]).tolist() == [0, 1]


def test_stratified_sampling_is_reproducible():
    first = stratified_sample(frame(), "label", 100, 42)
    second = stratified_sample(frame(), "label", 100, 42)
    pd.testing.assert_frame_equal(first, second)
    assert first.label.value_counts().to_dict() == {0: 50, 1: 50}


def test_split_is_stratified_and_disjoint_by_rows():
    source = frame()
    train, validation, test = stratified_split(source, "label", 42)
    assert list(map(len, (train, validation, test))) == [140, 30, 30]
    assert all(part.label.mean() == 0.5 for part in (train, validation, test))


def test_preprocessor_fits_train_only():
    train = frame(100)
    validation = pd.DataFrame({"numeric": [1000], "category": ["unseen"], "label": [0]})
    processor = build_preprocessor(["numeric"], ["category"])
    processor.fit(train.drop(columns="label"))
    transformed = processor.transform(validation.drop(columns="label"))
    assert transformed.shape[0] == 1
    assert processor.named_transformers_["numeric"].named_steps["scaler"].mean_[0] == 49.5


def test_model_shape():
    assert MLP(4)(torch.zeros((3, 4))).shape == (3, 2)


def test_metrics():
    result = binary_metrics([0, 0, 1, 1], [0, 1, 1, 1], [.1, .7, .8, .9])
    assert result["attack_recall"] == 1.0 and result["false_positive_rate"] == 0.5


def test_constraints_preserve_immutable_clip_round():
    original = np.array([[0.2, 0.0, 2.0]])
    candidate = np.array([[0.9, 0.7, 2.7]])
    fixed = enforce_constraints(original, candidate, immutable_indices=(0,), binary_indices=(1,), discrete_indices=(2,), lower=0, upper=3)
    assert fixed.tolist() == [[0.2, 1.0, 3.0]]
    assert constraints_hold(original, fixed, immutable_indices=(0,), lower=0, upper=3)


def test_gate_pass_block_and_serialization():
    thresholds = {"min_clean_f1": .9, "min_clean_attack_recall": .9, "min_adversarial_attack_recall": .7, "max_relative_f1_drop": .2}
    clean = {"f1": .95, "attack_recall": .96}
    passed = evaluate_gate("m1", "d", clean, {"attack_recall": .8, "relative_f1_drop": .1}, thresholds, {})
    blocked = evaluate_gate("m1", "d", clean, {"attack_recall": .6, "relative_f1_drop": .3}, thresholds, {})
    assert passed["decision"] == "PASS" and blocked["decision"] == "BLOCK"
    json.dumps(passed)


def test_seed_reproducibility():
    set_global_seed(7); first = torch.rand(3)
    set_global_seed(7); second = torch.rand(3)
    assert torch.equal(first, second)


def test_profile_reports_quality():
    sample = pd.DataFrame({"x": [1.0, 1.0, np.inf], "constant": [2, 2, 2], "label": [0, 0, 1]})
    result = profile_frame(sample, "label")
    assert result["rows"] == 3 and result["infinite_values"]["x"] == 1 and "constant" in result["constant_features"]

