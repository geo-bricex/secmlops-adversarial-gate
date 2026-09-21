# Phase 2 — Clean Baselines

Nine frozen clean-baseline runs were completed: CIC-IoT-2023 (3/3), Edge-IIoTset (3/3), and ToN-IoT (3/3). Every split is fingerprint-group-aware, with preprocessing fitted on TRAIN only and test data read after checkpoint selection. The complete run-level and aggregate values are versioned in `results/baseline/phase2_runs.csv` and `results/baseline/phase2_summary.csv`.

## Edge-IIoTset semantic contract

The canonical parser retained 18,752,706 structurally valid rows (four malformed CSV records excluded). The original semantic audit found 158,515 inconsistent unique rows (0.8452913408870165%). The row-exclusion-only policy failed the governing binary-balance and attack-type thresholds, so the selected strategy was `REMOVE_FEATURE_PLUS_SEMANTIC_ROW_EXCLUSION`.

`tcp.dstport` is the sole removed model feature. It accounted for 155,549 nonnumeric values and contained non-port representations for which no semantically unequivocal normalization was justified. After that minimal removal, residual validation excluded 3,361 rows (0.017922746722526337%), producing a clean canonical universe of 18,749,345 rows with zero nonnumeric retained numeric features. No generic coercion or hexadecimal conversion was used.

The frozen experiment contains 999,996 rows: train 699,997, validation 149,999, and test 150,000. Its contract has 22 raw features (18 numeric and 4 categorical), which expand to 38 train-fitted model inputs. Fingerprint overlap is zero for every split pair. `tcp.dstport`, source/provenance columns, labels, `Attack_type`, and fingerprints are excluded from X.

All Edge seeds achieved 1.000000 test accuracy, precision, attack recall, specificity, F1, ROC-AUC, PR-AUC, and MCC. The appropriate audit conclusion is `NO_DIRECT_LEAKAGE_WITH_DATASET_CONFOUNDING`: source-file lineage and split/preprocessing audits are clean, while the perfect performance remains documented as a dataset-confinement result rather than being artificially reduced by dropping legitimate features.

## Convergence

Edge seed 42 reached its best validation loss at epoch 14/15, seed 123 at 15/15, and seed 2026 at 9/12 (early stopping). Thus two runs touch the epoch cap and constitute possible truncation evidence, but no tuning or retraining was performed under the frozen protocol. The detailed losses and flags are in `results/baseline/phase2_convergence.csv`.

For CIC, one seed reached 15/15; all three ToN runs reached 15/15. These are recorded as possible truncation, not an authorization to alter the fixed 15-epoch protocol.

## Audit and tracking evidence

`phase2_leakage_audit.json` is produced for every dataset. It confirms no forbidden lineage and zero fingerprint overlap. MLflow experiment `secmlops-adversarial-gate-phase2` contains the nine completed artifacts-backed run records, tagged `phase=2` and `run_origin=artifact_backfill`; this preserves evidence without rerunning completed experiments.

No adversarial attack or Phase 3 operation was started.
