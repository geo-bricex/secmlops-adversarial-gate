# Adversarial Security Gate for MLOps Pipelines

Experimental, reproducible foundation for evaluating a configurable adversarial pre-deployment gate across independent IoT/IIoT intrusion-detection datasets.

## Research question

How effectively can an automated adversarial security gate integrated into an MLOps pipeline identify insufficiently robust intrusion-detection models before production deployment across heterogeneous IoT/IIoT datasets?

No effectiveness claim is made before experiments are executed.

## Architecture and methodology

Each of CICIoT2023, Edge-IIoTset, and ToN_IoT Network is an independent scenario with its own split, fitted preprocessing, model, perturbation constraints, evaluation, and gate decision. They share code, metric definitions, experiment tracking, and output schemas. Data are split before train-fitted imputation, encoding, or scaling to prevent leakage.

The intended flow is `data profile -> stratified sample -> train/validation/test split -> train-fitted preprocessing -> MLP -> clean evaluation -> FGSM/PGD constrained evaluation -> configurable PASS/BLOCK gate`. Phase 1 implements and tests the preparation foundation; final training and adversarial experiments are deliberately deferred.

## Docker

```powershell
docker compose build app
docker compose up -d mlflow
docker compose run --rm app python -m src.data.profile --dataset cic_iot_2023
docker compose run --rm app python -m src.data.prepare --dataset cic_iot_2023
docker compose run --rm app pytest -q
```

MLflow is exposed at <http://localhost:5000>. Project directories are bind-mounted so data, results, artifacts, runs, and logs remain inside this repository.

## Data acquisition

Official source information and manual actions are documented in [data/README.md](data/README.md). Put only official CSV files in each `data/<dataset>/raw/` directory. Data and model binaries are ignored by Git.

## Reproducibility

Configuration is YAML-based. Seeds, sampling, splits, source metadata, file SHA-256 hashes, environment versions, and Git commit are recorded or supported. Generate environment metadata with:

```powershell
docker compose run --rm app python -m src.utils.environment
```

## Security Gate

`configs/security_gate.yaml` contains explicit experimental promotion thresholds; they are not universal standards. `src/security_gate` emits a structured PASS/BLOCK decision with conditions and failed conditions.

## Results and limitations

No scientific results exist yet. Phase 1 is limited by official dataset access workflows and by the need for domain review of mutable features after real files are profiled. The epsilon values are provisional scaled-space candidates, not validated defaults.

## Citation

Citation metadata will be added after the study and manuscript are finalized.

