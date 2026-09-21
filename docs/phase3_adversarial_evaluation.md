# Phase 3 — Constrained adversarial robustness evaluation

Phase 2 models, splits, samples, features, preprocessors, checkpoints, and clean metrics remain frozen. The initial `MUTABLE_CONTINUOUS_ONLY` proposal was too restrictive for these tabular network datasets. Phase 3 therefore uses `PROJECTED_CONSTRAINED_TABULAR_EVASION`: gradients are calculated in train-fitted model space, then candidates are clipped to TRAIN-derived bounds and projected to the valid feature domain.

The targeted evasion objective is ATTACK (1) to BENIGN (0). Only attack samples are perturbed; benign examples remain unchanged. Categorical one-hot outputs, targets, metadata, identifiers, immutable predictors, and direct categorical encodings are never attacked.

Conservative feasibility choices are: CIC `Time_To_Live` (integer, rounded and clipped); Edge `udp.time_delta` (continuous, clipped); ToN `duration` (continuous, clipped). These attributes are operationally influenceable traffic attributes and have direct single-feature projections. Their full mapping, bounds, and justifications are stored in each dataset's `feature_attack_map.csv`.

FGSM and targeted PGD (20 iterations, random initialization, alpha epsilon/4) use relative budgets 1%, 3%, and 5% of each feature's observed TRAIN range. A deterministic, stratified test subset (seed 314159; at most 20,000 observations) is shared by all three model seeds per dataset. The same protocol was validated first on validation batches. Zero semantic-constraint violations were permitted or observed.

Results are recorded per condition in `results/adversarial/`, with the long table and seed aggregate in `adversarial_results_long.csv` and `adversarial_summary.csv`. Edge results retain the Phase-2 qualification `NO_DIRECT_LEAKAGE_WITH_DATASET_CONFOUNDING`; clean perfection is not interpreted as universal generalization.

No Security Gate decision or Phase 4 operation is included here.
