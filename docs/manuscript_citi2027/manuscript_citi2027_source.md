# Adversarial Security Gate for MLOps Pipelines: A Multi-Dataset Evaluation for IoT/IIoT Intrusion Detection

This file is an auxiliary reading and build guide. The authoritative manuscript source is `manuscript_citi2027_anonymous.tex`, using the bundled Springer Computer Science Proceedings `llncs` class and `splncs04` bibliography style.

## Anonymous front matter

- Anonymous Author 1
- Anonymous Affiliation
- Author information withheld for anonymous review

The actual number and identity of authors are intentionally not recorded in the anonymous package. The final OpenReview form must be checked in case CITI 2027 requires the author block to be omitted entirely rather than replaced by anonymous placeholders.

## Abstract

Clean-data validation can promote an intrusion-detection model without testing whether operationally influenceable inputs permit evasion. Prior work studies secure machine-learning lifecycles and realistic adversarial evaluation, but provides limited multi-dataset evidence about connecting both to a frozen, auditable promotion rule. We evaluate such a Security Gate using nine multilayer perceptrons trained with three seeds on independently prepared CICIoT2023, Edge-IIoTset, and ToN_IoT populations. Targeted FGSM and PGD attacks use 1%, 3%, and 5% of train-derived feature ranges, dataset-specific attack masks, bounds, and semantic projection. A validation-only policy combines clean attack recall, worst-case adversarial recall, attack success rate, recall degradation, and integrity checks. All nine candidates pass the clean-only rule, whereas the frozen gate blocks four: all three Edge-IIoTset models and one ToN_IoT model. Mean worst-case attack recall is 0.9864 for CICIoT2023, 0.0008 for Edge-IIoTset, and 0.7793 for ToN_IoT. No semantic violations or split-fingerprint overlaps are recorded. Thus, under the evaluated projected feature-space threat model, adversarial evidence changes promotion eligibility that clean evaluation alone would not question; it does not establish packet-level realizability or guarantee deployment security.

## Argument and structure

The manuscript follows the sequence problem, knowledge gap, research question, contribution, method, evidence, interpretation, and limitations. Its sections are Introduction, Related Work, Methodology, Results, Discussion, Threats to Validity, and Conclusions and Future Work. Four original vector figures and six tables are generated directly in LaTeX from verified literature and frozen Phase 5 evidence summarized in `results/final/`. The rendered paper contains 24 bibliographically verified references, of which 19 (79.2%) were published from late 2022 through 2026.

## Reproducible build

From `docs/manuscript_citi2027/`, run:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error manuscript_citi2027_anonymous.tex
bibtex manuscript_citi2027_anonymous
pdflatex -interaction=nonstopmode -halt-on-error manuscript_citi2027_anonymous.tex
pdflatex -interaction=nonstopmode -halt-on-error manuscript_citi2027_anonymous.tex
```

The compiled anonymous PDF is `manuscript_citi2027_anonymous.pdf`.
