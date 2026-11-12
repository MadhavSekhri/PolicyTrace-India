# Ecosystem review and positioning

Review date: 2026-11-12. This is product research, not an assertion of benchmark superiority.

## Primary source ecosystem
- Government of India's Open Government Data portal: https://data.gov.in/ — datasets and APIs published by government entities. It is an authoritative starting point for permitted datasets, not automatic permission to archive everything.
- Published NDSAP implementation guidance: https://data.gov.in/sites/default/files/NDSAP_Implementation_Guidelines_2.2.pdf — emphasizes government publishing workflows and structured open data.

## Where PolicyTrace should fit
Existing official portals focus on discovering/publishing datasets. PolicyTrace's narrow complementary job is to **compare captured document versions with reproducible provenance**: who published a particular source, when observed, what changed and what is only inferred.

## Make it convincing
**5-minute demo:** offline synthetic notice v1/v2, named source, digest, JSON record and readable diff; repeat ingest to show idempotence.
**Production evaluation:** permission-checked public notice, clear distinction between observed/published dates, resilience to missing and changed URLs, reproducible export bundle.
**Hard no:** no official affiliation badge, no 'verified government' claim without independent original-document evidence, no mass crawler until SSRF, robots and terms policies are independently reviewed.

## Competitive risks
Generic web monitors already alert on changes. LLM summaries are easily commoditized. Therefore prioritize a credible evidence model, versioned records, repeatable source attribution and honest uncertainty before adding UI, NLP or alerts.

## Adoption milestones
One independently reproduced import; one outside project consuming exported revisions; public provenance examples with primary source citations, explicit rights and tests. No invented download counts.
