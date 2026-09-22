# Adversarial Security Gate for MLOps Pipelines: A Multi-Dataset Evaluation for IoT/IIoT Intrusion Detection

This file is an auxiliary reading and build guide. The authoritative manuscript source is `manuscript_citi2027_anonymous.tex`, using the bundled Springer Computer Science Proceedings `llncs` class and `splncs04` bibliography style.

## Anonymous front matter

- Anonymous Author 1
- Anonymous Author 2
- Anonymous Author 3
- Anonymous Author 4
- Anonymous Author 5
- Anonymous Affiliation 1
- Anonymous Affiliation 2

The anonymous package reserves space for the known total of five authors and two affiliations. The provisional layout maps Authors 1, 3, 4, and 5 to Affiliation 1 and Author 2 to Affiliation 2; it does not encode the real institutional mapping. Names, institutions, emails, ORCID identifiers, cities, and correspondence information are intentionally absent. The final OpenReview form must still be checked in case CITI 2027 requires the author block to be omitted entirely rather than replaced by anonymous placeholders.

## Abstract

Clean-data validation can promote an intrusion-detection model without testing whether operationally influenceable inputs permit evasion. Prior work studies secure machine-learning lifecycles and realistic adversarial evaluation, but provides limited multi-dataset evidence about connecting both to a frozen, auditable promotion rule. We evaluate such a Security Gate using nine multilayer perceptrons trained with three seeds on independently prepared CICIoT2023, Edge-IIoTset, and ToN_IoT populations. Targeted FGSM and PGD attacks use 1%, 3%, and 5% of train-derived feature ranges, dataset-specific attack masks, bounds, and semantic projection. A validation-only policy combines clean attack recall, worst-case adversarial recall, attack success rate, recall degradation, and integrity checks. All nine candidates pass the clean-only rule, whereas the frozen gate blocks four: all three Edge-IIoTset models and one ToN_IoT model. Mean worst-case attack recall is 0.9864 for CICIoT2023, 0.0008 for Edge-IIoTset, and 0.7793 for ToN_IoT. No semantic violations or split-fingerprint overlaps are recorded. Thus, under the evaluated projected feature-space threat model, adversarial evidence changes promotion eligibility that clean evaluation alone would not question; it does not establish packet-level realizability or guarantee deployment security.

## Argument and structure

The manuscript follows the sequence problem, knowledge gap, research question, contribution, method, evidence, interpretation, and limitations. Its sections are Introduction, Related Work, Methodology, Results, Discussion, Threats to Validity, and Conclusions and Future Work. Four original vector figures and six tables are generated directly in LaTeX from verified literature and frozen Phase 5 evidence summarized in `results/final/`. The rendered paper contains 24 bibliographically verified references, of which 19 (79.2%) were published from late 2022 through 2026.

The policy audit establishes that the selection implementation reads only validation artifacts and that the serialized policy digest matches every final decision record. Git history also shows that TEST attack artifacts existed before the final policy record. The manuscript therefore calls the policy validation-derived but does not claim prospective preregistration or chronologically blind TEST generation.

## Reproducible build

From `docs/manuscript_citi2027/`, run:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error manuscript_citi2027_anonymous.tex
bibtex manuscript_citi2027_anonymous
pdflatex -interaction=nonstopmode -halt-on-error manuscript_citi2027_anonymous.tex
pdflatex -interaction=nonstopmode -halt-on-error manuscript_citi2027_anonymous.tex
```

The compiled anonymous PDF is `manuscript_citi2027_anonymous.pdf`.
