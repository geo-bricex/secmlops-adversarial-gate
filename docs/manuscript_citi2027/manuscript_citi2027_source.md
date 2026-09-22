# Adversarial Security Gate for MLOps Pipelines: A Multi-Dataset Evaluation for IoT/IIoT Intrusion Detection

This file is an auxiliary reading and build guide. The authoritative manuscript source is `manuscript_citi2027_anonymous.tex`, using the bundled Springer Computer Science Proceedings `llncs` class and `splncs04` bibliography style.

## Anonymous front matter

- Anonymous Author 1
- Anonymous Affiliation
- Author information withheld for anonymous review

The actual number and identity of authors are intentionally not recorded in the anonymous package. The final OpenReview form must be checked in case CITI 2027 requires the author block to be omitted entirely rather than replaced by anonymous placeholders.

## Abstract

Machine-learning intrusion detection systems can satisfy conventional clean-data criteria while remaining vulnerable to evasion. This paper evaluates an adversarial Security Gate that makes robustness an explicit, auditable condition for model promotion in a machine learning operations pipeline. Nine multilayer perceptrons were trained with three seeds on independently prepared CICIoT2023, Edge-IIoTset, and ToN_IoT populations. Targeted FGSM and PGD attacks were evaluated at 1%, 3%, and 5% of train-derived feature ranges under dataset-specific masks, bounds, and semantic projection. A validation-only policy combined clean attack recall, worst-case adversarial recall, attack success rate, degradation, and integrity checks. All nine models passed the clean-only criterion, whereas the frozen Security Gate blocked four: all three Edge-IIoTset models and one ToN_IoT model. Mean worst-case attack recall was 0.9864 for CICIoT2023, 0.0008 for Edge-IIoTset, and 0.7793 for ToN_IoT. No semantic violations or split-fingerprint overlaps were observed. The results show that, within the evaluated threat model, adversarial validation can materially change promotion decisions that clean metrics alone would accept.

## Argument and structure

The manuscript follows the sequence problem, knowledge gap, research question, contribution, method, evidence, interpretation, and limitations. Its sections are Introduction, Related Work, Methodology, Results, Discussion, Threats to Validity, and Conclusions and Future Work. Four original figures and five tables are generated directly in LaTeX from the frozen Phase 5 evidence summarized in `results/final/`.

## Reproducible build

From `docs/manuscript_citi2027/`, run:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error manuscript_citi2027_anonymous.tex
bibtex manuscript_citi2027_anonymous
pdflatex -interaction=nonstopmode -halt-on-error manuscript_citi2027_anonymous.tex
pdflatex -interaction=nonstopmode -halt-on-error manuscript_citi2027_anonymous.tex
```

The compiled anonymous PDF is `manuscript_citi2027_anonymous.pdf`.
