# Dataset provenance and acquisition

Access checked on 2026-09-21. The three datasets must remain separate. Original multiclass labels must be retained; `binary_target` is an added derived column where benign/normal is `0` and every verified attack label is `1`.

## CICIoT2023

- Official landing page: https://www.unb.ca/cic/datasets/iotdataset-2023.html
- Official download workflow: https://cicresearch.ca/IOTDataset/CIC_IOT_Dataset2023/
- Desired material: prepared ML CSV only; no PCAP.
- Local status: downloaded manually and audited read-only. The local collection contains 309 ML CSV files plus the provider PDF.
- Destination: `data/cic_iot_2023/raw/`
- Real mapping: parent directory `Benign_Final -> 0`; the 33 observed attack directories -> `1`. The CSVs contain no label column.

## Edge-IIoTset

- Authoritative publication: https://doi.org/10.1109/ACCESS.2022.3165809
- Authors' published dataset listing: https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot
- Desired file: `DNN-EdgeIIoT-dataset.csv` (reported by the host as approximately 1.22 GB; verify locally after download).
- Local status: downloaded manually and audited read-only. The package contains raw scenario CSV/PCAP files but does not contain the advertised preselected DNN/ML CSV files.
- Destination: `data/edge_iiotset/raw/`
- Real mapping: `Attack_label` 0/1; retain `Attack_type` only as metadata. The audit selects all 23 CSVs and excludes 22 PCAPs.

## ToN_IoT Network

- Official landing page: https://research.unsw.edu.au/projects/toniot-datasets
- Desired material: processed network CSV only; exclude Windows, Linux, and telemetry datasets.
- Local status: `train_test_network.csv` downloaded manually and audited read-only.
- Destination: `data/ton_iot/raw/`
- Real mapping: binary `label` 0/1; retain `type` only as multiclass metadata.

## Integrity and profiling

After official files are placed, run `python -m src.data.profile --dataset <id>`. The report records each path, byte size, SHA-256, schema, target distribution, missing/infinite values, duplicates, constants, inferred feature classes, cardinalities, and numeric percentiles. No dataset statistics are claimed until those reports exist.
