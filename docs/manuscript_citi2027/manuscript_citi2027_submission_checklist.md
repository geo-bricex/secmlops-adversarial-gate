# CITI 2027 Anonymous Submission Checklist

## Manuscript package

- [x] English research manuscript uses the official Springer Computer Science Proceedings `llncs` class and `splncs04` bibliography style applicable to CCIS.
- [x] The rendered PDF is 15 pages, including figures, tables, and references; the stated limit is 12–15 pages.
- [x] Title, abstract, research question, contributions, evidence, limitations, and conclusions are mutually aligned.
- [x] Four figures and six tables are cited in order in the body.
- [x] The PDF opens successfully and has no unresolved citations or references.
- [x] All reported experimental results trace to reconciled Phase 5 artifacts.
- [x] No Phase 2–5 experiment, policy, threshold, sample, model, or conclusion was modified.

## Anonymous review

- [x] Front matter reserves exactly five anonymous authors and two anonymous affiliations using Springer `\inst{}` and `\and` commands.
- [x] The provisional layout assigns Authors 1, 3, 4, and 5 to Affiliation 1 and Author 2 to Affiliation 2 solely to reserve space; it does not assert the real mapping.
- [x] No real names, institutions, cities, emails, ORCID identifiers, acknowledgements, personal paths, or identity-revealing repository links occur in the manuscript or PDF metadata.
- [x] PDF metadata exposes the TeX producer only; it has no Author, Subject, or Keywords field containing identity data.
- [x] Scientific self-citations, if later required, must remain in the third person.
- [ ] Confirm the final CITI 2027 OpenReview form's exact anonymous-front-matter rule. The public OpenReview page was not readable reliably enough to determine whether placeholders or complete author-block removal is required. If removal is required, derive the submission variant by suppressing `\\author` and `\\institute`; keep this internal placeholder version unchanged.
- [ ] Insert the real author count and camera-ready author metadata only after acceptance and outside the anonymous submission package.

## Evidence and literature

- [x] Reference records were checked against publisher, conference, DOI, OpenReview, or arXiv records.
- [x] Foundational FGSM and PGD sources and original dataset papers are retained rather than replaced by secondary citations.
- [x] Goodfellow et al. link to the original arXiv record and Madry et al. link to the ICLR OpenReview record; both URLs render in the Springer bibliography.
- [x] Recent references are reported transparently as 19/24 (79.2%, late 2022–2026); each added source supports a substantive methodological, governance, validity, or comparative claim.
- [x] No Q1 quartile claim is made in the manuscript, so no unverified quartile label is presented.
- [x] The literature matrix supports the bounded knowledge-gap statement.
- [x] Claims, references, and visuals have separate audit files in `results/final/`.
- [x] Phase 4 evidence confirms validation-only selector inputs and one matching policy digest across all nine decisions.
- [x] The chronology limitation is explicit: TEST attack artifacts predate the final policy record, so no prospective-preregistration claim is made.

## Final manual actions (not performed automatically)

- [ ] Reconfirm the call text and deadline immediately before upload.
- [ ] Inspect the PDF in the OpenReview preview and confirm its page count remains 15.
- [ ] Complete the form's conflict, subject-area, keyword, licence, and author declarations truthfully.
- [ ] Do not upload supplementary material unless the current call explicitly permits it.
- [ ] Do not submit automatically; submission remains an author-controlled action.
