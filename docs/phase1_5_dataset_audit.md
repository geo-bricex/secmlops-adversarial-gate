# Phase 1.5 — Real dataset audit

Audit date: 2026-09-21. Raw inputs were read only. SHA-256, byte sizes, schemas and row counts are recorded in the manifests under `results/data_profile`. Exact counts are identified below; feature cardinalities and percentiles use DuckDB approximate algorithms and are marked as such in the feature-statistics CSVs.

## Comparative result

| Dataset | N original | N recommended | Original columns* | Modelable candidates | Benign | Attack | Exact duplicate % | Split strategy | Mutable independently | Immutable/rejected | Leakage fields |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| CICIoT2023 | 46,776,700 | 1,000,000 | 39 | 39 before near-constant review | 1,098,191 | 45,678,509 | 53.6208% | GROUP by row fingerprint, then monitor stratification | 1 | 25 | `source_file`, derived `original_label` |
| Edge-IIoTset | 20,192,714 | 1,000,000 | 63 | 48 after mandatory removals | 10,463,005 | 9,729,709 | 0.0130% | GROUP by row fingerprint, then monitor stratification | 0 | 16 removals plus categorical immutables | labels, timestamp, IPs, payload/content, sequence identifiers |
| ToN_IoT Network | 211,043 | Full dataset after duplicate policy | 44 | 34 after mandatory removals | 50,000 | 161,043 | 9.7464% | GROUP by row fingerprint, then monitor stratification | 0 | 10 removals plus categorical immutables | labels, IPs, content identifiers, `source_file` |

\* Excludes audit-only `source_file` and CIC's derived `original_label`.

The modelable counts are candidates, not a claim that every retained field is adversarially mutable. `REVIEW` decisions must be frozen before Phase 2.

## CICIoT2023

### Files and selected population

- Found 310 files: 309 ML CSV files and one `README_CSV.pdf`, totalling 8,943,841,070 bytes.
- Selected all 309 CSV files below `CIC_IOT_Dataset2023/CSV`; the PDF is documentation only.
- The CSVs have a common 39-column numerical schema and no explicit label column.
- Class is encoded by the parent directory. The audit adds `source_file` and `original_label` only as metadata. Neither may enter `X`.
- Exact population: 46,776,700 rows, 34 observed attack/normal directory labels, 1,098,191 benign (2.3477%) and 45,678,509 attack (97.6523%). Full class counts are in the profile JSON.

### Quality

- Exact duplicates excluding provenance: 25,082,062 rows (53.6208%). This is a serious train/test leakage risk.
- Missing: one row across most flag/count fields; `Std` has 704, `Variance` 705, `AVG` 2, and `IAT`, `Tot size`, `Number` 3 each.
- `Rate` contains 1,037 positive infinities; no negative infinities were found.
- Near-constant at 99.5%: `ece_flag_number`, `cwr_flag_number`, `Telnet`, `SMTP`, `SSH`, `IRC`, `IGMP`.
- No constant model feature was detected.

### Leakage, split and sampling

Mandatory REMOVE: `source_file`, `original_label`. Near-constant fields require ablation/review, not silent deletion. Filename/folder is the target source and therefore direct leakage.

`source_file` is not a defensible primary split group: files are class-homogeneous fragments and rare attacks have only one file, so grouping by file can make class support impossible or turn the evaluation into unseen-class testing. There is no timestamp/capture identifier proving that numbered fragments are independent captures. Recommended strategy: compute a feature-row fingerprint, keep every duplicate cluster in one partition, and assign groups reproducibly while checking class balance. Only if upstream capture provenance is recovered should capture-level grouping replace this policy.

Recommended CPU sample: 1,000,000 rows, stratified by binary label after applying the duplicate-group policy. This still yields roughly 23,000 benign records while keeping repeated MLP/FGSM/PGD runs feasible. The full 46.8M rows are not recommended for repeated adversarial experiments on this CPU-only host.

### Adversarial semantics

- Independently mutable candidate: `Time_To_Live`, clipped to the observed integer-valid range and subject to protocol feasibility.
- Conditionally mutable: `Header_Length`, `IAT`, counts and all statistical aggregates (`Rate`, `Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`, `Number`, `Variance`).
- Immutable under a continuous attack: protocol identity, protocol indicators and flags.
- Derived relations must hold: `Min <= AVG <= Max`; `Std >= 0`; variance must agree with dispersion; sums/averages/sizes/counts/rates/IAT must remain mutually consistent; counts and lengths are nonnegative and discrete; flags/protocol indicators must remain in their observed domains.

## Edge-IIoTset

### Files and selected population

- Found 45 files totalling 9,477,403,788 bytes: 23 CSV and 22 PCAP files.
- `DNN-EdgeIIoT-dataset.csv` and `ML-EdgeIIoT-dataset.csv` are not present anywhere in the downloaded tree.
- Selected the 23 CSV files: 14 attack CSVs and nine normal-device CSVs. PCAPs are excluded because tabular CSV exists.
- Exact population: 20,192,714 rows and 63 original columns; audit adds `source_file`.
- Labels: `Attack_label` is binary and `Attack_type` has 15 observed values. There are 10,463,005 normal (51.8157%) and 9,729,709 attack rows (48.1843%).

### Quality

- Exact duplicates excluding provenance: 2,622 (0.0130%).
- No SQL NULL values or infinities were found. However, missing protocol fields are encoded predominantly as textual/numeric zero rather than NULL, so zero is often structural absence and must not be median-imputed as if observed.
- `icmp.unused` is constant. Near-constant: `dns.qry.type`, DNS retransmission fields, `mqtt.msg_decoded_as`, and `mbtcp.unit_id`.
- `tcp.checksum` mixes hexadecimal representations with numeric-looking values. The audit intentionally loaded Edge as text and used explicit numeric conversion only for appropriate columns.
- Some nominal flag columns contain impossible-looking maxima (for example `tcp.connection.syn=1440`, `tcp.flags.ack=5900`), requiring protocol/domain review before modeling.

### Leakage, split and sampling

Mandatory REMOVE: `Attack_label`, `Attack_type`, `source_file`, `frame.time`, IPs, ARP IPs, checksums, TCP payload/options, HTTP file/query/referer/full URI, MQTT message, TCP ACK/sequence fields and UDP stream ID. These are target, provenance, identifiers, content/payload or session-sequence fields with high memorization risk.

Each source CSV is essentially class/scenario-specific, so a naïve source-file group split changes the question to unseen attack/device scenarios and cannot preserve all rare classes. Timestamp is also acquisition/scenario-confounded. For the binary within-dataset experiment, use duplicate row fingerprints as groups and reproducibly balance binary labels. A separate leave-one-scenario/device-out sensitivity analysis is valuable but must not replace the primary experiment without changing the research claim.

Recommended sample: 1,000,000 rows after mandatory feature removal and duplicate grouping. The complete 20.2M-row raw collection is technically processable out-of-core but not efficient for repeated CPU adversarial evaluation.

### Adversarial semantics

No field is accepted as unconditionally mutable. Timing, lengths, ports, counters and protocol-specific fields are only conditionally mutable. Protocol/category/flag fields remain immutable. Relationships include valid port and integer ranges, TCP sequence/ack consistency, packet-length/payload consistency, DNS/MQTT/Modbus fields being meaningful only when their protocol is active, and checksum recomputation after packet changes. Payload/content fields are removed, not perturbed.

## ToN_IoT Network

### Files and selected population

- Found and selected exactly `train_test_network.csv`, 29,902,775 bytes.
- Exact population: 211,043 rows and 44 original columns; audit adds `source_file`.
- Labels: `label` is binary; `type` contains normal plus nine attack types.
- Normal: 50,000 (23.6919%); attack: 161,043 (76.3081%).

### Quality

- Exact duplicates excluding provenance: 20,569 (9.7464%).
- No SQL NULL or infinite numeric values were found.
- Protocol absence is encoded with `-` and zeros, not NULL; these sentinel values must be preserved/encoded explicitly.
- `source_file` is constant. Numerous HTTP/SSL/weird fields are at least 99.5% dominated by one sentinel value.

### Leakage, split and sampling

Mandatory REMOVE: `label`, `type`, `source_file`, `src_ip`, `dst_ip`, `dns_query`, `http_uri`, `http_user_agent`, `ssl_subject`, `ssl_issuer`. IP and content fields can memorize collection topology, hosts or attack scripts.

The filename says `train_test`, but it contains no split indicator and is one combined table; therefore no verifiable official train/test boundary can be reconstructed. There is also no timestamp. Recommended strategy: group identical row fingerprints, then reproducibly assign groups with class-balance checks. The entire dataset is viable on CPU after the duplicate policy; no sampling is recommended.

### Adversarial semantics

No feature is independently mutable. Duration, byte/packet counters, ports and application fields are conditionally mutable; protocols, services and connection state are immutable categorical choices for gradient perturbation. Preserve nonnegativity and integer constraints, `src_ip_bytes >= src_bytes`, `dst_ip_bytes >= dst_bytes`, packet/byte consistency, port ranges, and conditional applicability of DNS/SSL/HTTP fields.

## Preprocessing decision

1. Apply the documented removal list before creating `X`; retain labels and provenance only in metadata.
2. Resolve duplicate clusters before splitting so an identical feature row cannot cross partitions.
3. Fit missing/inf treatment, categorical vocabulary and scaler on train only.
4. CIC: convert positive infinity to missing using a train-defined rule; median imputation and scaling are train-fitted.
5. Edge: parse approved numerical fields explicitly; preserve structural zero; categorical vocabularies are train-fitted.
6. ToN_IoT: treat `-` as an explicit absent category rather than learned missingness unless train-only analysis justifies another treatment.
7. Persist ordered feature names and fitted preprocessing. Test remains untouched until final evaluation.

No SMOTE, over/undersampling, training, FGSM or PGD was performed in this phase.

## Scientific conclusions and required answers

1. All three are usable as independent scenarios in the same article, but not as a merged dataset and not with identical perturbation masks.
2. CICIoT2023 should use all 309 CSV files under `CIC_IOT_Dataset2023/CSV`, deriving label from the parent directory and preserving file provenance only as metadata.
3. The downloaded Edge package lacks the preferred DNN file. Under the no-download constraint, use all 23 available CSVs to build the tabular binary dataset; exclude all PCAPs. Document that this is not the authors' preselected DNN CSV.
4. ToN_IoT should use `train_test_network.csv` only.
5. CIC: duplicate-fingerprint GROUP split with class-balance constraints; do not group solely by source file.
6. Edge: duplicate-fingerprint GROUP split for the primary binary experiment; scenario/file holdout only as a separately named sensitivity study.
7. ToN_IoT: duplicate-fingerprint GROUP split because no official boundary or timestamp survives in the file.
8. Direct leakage removals are the target/type and provenance fields listed per dataset.
9. Irrelevant/high-risk identifiers are Edge IP/timestamp/content/session fields and ToN IP/content identity fields; CIC contains no raw IP/flow identifier feature.
10. Only CIC `Time_To_Live` is provisionally independently perturbable. Other listed numerical traffic features are conditionally mutable.
11. Protocol identities, categories, binary flags, labels, provenance and identifiers must remain immutable or be removed.
12. Preserve protocol domains, integer/binary bounds, nonnegativity, counter/byte/packet consistency, timing/rate relations and derived-statistic identities.
13. Recommended sizes: CIC 1,000,000; Edge 1,000,000; ToN full after duplicate policy.
14. ToN_IoT can be used in full. Full CIC and Edge are technically readable but unsuitable for repeated CPU PGD experiments.
15. Serious risks exist: CIC's 53.62% duplicates and extreme imbalance; Edge's absent DNN file, scenario-specific sources and malformed flag-like values; ToN's combined split and topology identifiers.
16. None must be substituted now. Edge requires especially transparent reporting of the actual 23-file construction.
17. FGSM/PGD remain defensible only as constrained feature-space stress tests with masks, projection and relation validation. Unconstrained FGSM/PGD over every scaled column would not be scientifically defensible.

## Artifacts

For each dataset: manifest, profile JSON, feature statistics, duplicates by source, leakage audit and feature-semantics CSV are stored in `results/data_profile/`.

## Frozen Phase 1.5 decision record

The duplicate audit was run only on the materialized `audit_source` DuckDB tables. Its fingerprint uses every predictor column and excludes target, attack-type and provenance fields. A 64-bit DuckDB hash is the deterministic computational group key; the source tables remain available for a direct equality confirmation if a collision is ever suspected.

| Dataset | Rows | Unique X | Duplicate groups / mean / max | Rows in duplicate groups | Cross-label groups / rows | Decision |
|---|---:|---:|---:|---:|---:|---|
| CIC-IoT-2023 | 46,776,700 | 21,056,274 | 1,884,727 / 14.65 / 1,205 | 27,605,153 | 906 / 26,671 | A: remove conflicting fingerprints, deduplicate, then stratify |
| Edge-IIoTset | 20,192,714 | 20,190,092 | 773 / 4.39 / 480 | 3,395 | 0 / 0 | B: duplicate-aware stratified split |
| ToN-IoT | 211,043 | 190,474 | 7,170 / 3.87 / 3,361 | 27,739 | 0 / 0 | A: deduplicate, then stratify |

The CIC label-consistent deduplicated population must exclude the 26,671 rows in the 906 binary-label-conflicting fingerprints. This is reported rather than silently relabelled. ToN becomes 42,040 benign and 148,434 attack rows after deduplication. Edge retains duplicate groups as indivisible groups because they are only 0.0130% of rows. CIC/ToN choose deduplication because repeated vectors would otherwise dominate CPU training and adversarial evaluation.

Options C (official split), D (natural source group) and E (temporal split) are rejected for all primary experiments: no verifiable official boundary exists; source files are scenario/class-confounded; and no trustworthy non-confounded time order is available. The frozen split is 70/15/15 with seed 42. For A, stratify after selecting one representative per label-consistent fingerprint. For B, use a deterministic stratified group assignment with the fingerprint as group and assert no group overlaps partitions.

### Exact model and attack contracts

The exact base features are the `model_numeric`, `model_binary` and `model_categorical` arrays in each versioned dataset YAML. The corresponding feature-semantic CSV is a dependency contract: target, type, provenance, identity/content, checksum/sequence and near-constant removal fields never enter `X`; categorical/binary fields are immutable; numerical derived fields require projection.

- CIC: only `Time_To_Live` is in the initial FGSM/PGD mask, integer-rounded and clipped to the training range. `Protocol Type` and all retained flags are immutable. Header/counter/rate/statistic fields are not independently perturbable; they require a dependency-preserving projection (`Min <= AVG <= Max`, nonnegative counts/sizes, and coherent rate/IAT/statistics).
- Edge: the initial independent mask is empty. `udp.time_delta`, `http.content_length`, `tcp.len`, `mqtt.len`, `mbtcp.len` and `dns.qry.name.len` are a conditional candidate set only after a tested joint projection. Current CSVs are adequate for the scoped binary tabular study after the removals and disclosure; the absent DNN CSV is preferable for a separate standardized reproduction but is not required or downloaded in this phase.
- ToN: the conditional candidate set is `duration`, byte, packet and IP-byte counters listed in its YAML. It needs a joint projection enforcing nonnegative/integer domains and `src_ip_bytes >= src_bytes`, `dst_ip_bytes >= dst_bytes`; categories, ports and labels are not independently changed.

This keeps FGSM/PGD scientifically defensible only as a constrained feature-space robustness stress test. It is not a claim of directly packet-realizable adversarial traffic. No training, attack generation or model evaluation was performed in Phase 1.5.
