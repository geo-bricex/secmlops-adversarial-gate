# 4. Results

## 4.1 Clean IDS performance

Clean baselines are reported across three frozen seeds per dataset in `results/final/table_clean_baselines.csv`. Edge’s perfect within-distribution results retain the qualification `NO_DIRECT_LEAKAGE_WITH_DATASET_CONFOUNDING` and are not evidence of cross-scenario generalization.

## 4.2 Adversarial robustness

Constrained projected attacks reduced attack recall to varying extents across datasets and budgets. The seed-level and aggregate results are preserved in `table_adversarial_results.csv` and `table_worst_case_robustness.csv`.

## 4.3 Security Gate decisions

The frozen validation-only policy was applied unchanged to test artifacts. Clean-only and full-Gate decisions are compared in `table_gate_value_added.csv`.

## 4.4 Operational overhead

Attack-generation runtime is summarized in `table_operational_cost.csv`; gate logic itself is a lightweight artifact aggregation step.
