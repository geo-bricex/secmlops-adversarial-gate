# Dataset provenance and acquisition

Access checked on 2026-09-21. The three datasets must remain separate. Original multiclass labels must be retained; `binary_target` is an added derived column where benign/normal is `0` and every verified attack label is `1`.

## CICIoT2023

- Official landing page: https://www.unb.ca/cic/datasets/iotdataset-2023.html
- Official download workflow: https://cicresearch.ca/IOTDataset/CIC_IOT_Dataset2023/
- Desired material: prepared ML CSV only; no PCAP.
- Access status: blocked pending manual completion of the CIC statistical form (first/last name, email, organization, job title, country). The page also returned a server-error banner during inspection.
- Destination: `data/cic_iot_2023/raw/`
- Mapping candidate: exact `BenignTraffic -> 0`; verified attack labels -> `1`.

## Edge-IIoTset

- Authoritative publication: https://doi.org/10.1109/ACCESS.2022.3165809
- Authors' published dataset listing: https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot
- Desired file: `DNN-EdgeIIoT-dataset.csv` (reported by the host as approximately 1.22 GB; verify locally after download).
- Access status: blocked pending Kaggle authentication/API credentials or manual browser download.
- Destination: `data/edge_iiotset/raw/`
- Mapping candidate: exact `Normal -> 0`; verified attack types -> `1`.

## ToN_IoT Network

- Official landing page: https://research.unsw.edu.au/projects/toniot-datasets
- Desired material: processed network CSV only; exclude Windows, Linux, and telemetry datasets.
- Access status: official SharePoint link redirects to Microsoft authentication and needs manual access.
- Destination: `data/ton_iot/raw/`
- Mapping candidate: documented binary label `0 -> 0`, `1 -> 1`; retain attack `type` as multiclass metadata.

## Integrity and profiling

After official files are placed, run `python -m src.data.profile --dataset <id>`. The report records each path, byte size, SHA-256, schema, target distribution, missing/infinite values, duplicates, constants, inferred feature classes, cardinalities, and numeric percentiles. No dataset statistics are claimed until those reports exist.

