from __future__ import annotations

import numpy as np


def enforce_constraints(original: np.ndarray, adversarial: np.ndarray, immutable_indices=(), binary_indices=(), discrete_indices=(), lower=None, upper=None) -> np.ndarray:
    result = adversarial.copy()
    if lower is not None or upper is not None:
        result = np.clip(result, lower, upper)
    if binary_indices:
        result[:, list(binary_indices)] = np.rint(result[:, list(binary_indices)]).clip(0, 1)
    if discrete_indices:
        result[:, list(discrete_indices)] = np.rint(result[:, list(discrete_indices)])
    if immutable_indices:
        result[:, list(immutable_indices)] = original[:, list(immutable_indices)]
    return result


def constraints_hold(original: np.ndarray, candidate: np.ndarray, immutable_indices=(), lower=None, upper=None) -> bool:
    if immutable_indices and not np.array_equal(original[:, list(immutable_indices)], candidate[:, list(immutable_indices)]):
        return False
    if lower is not None and np.any(candidate < lower):
        return False
    if upper is not None and np.any(candidate > upper):
        return False
    return True

