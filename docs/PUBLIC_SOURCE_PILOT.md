# Export source evidence for India's National Critical Mineral Mission

This pilot starts with two Press Information Bureau releases. The [January 29, 2025 Cabinet release](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2097308&lang=2&reg=48) records the approval. The [July 29, 2025 PIB release](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2149747&lang=2&reg=48) gives a later account of the proposed expenditure and expected investment. Treat the releases as separate sources. They have separate URLs, and the July release is a follow-up rather than a revision of the January page.

1. Open each source in your browser and save the relevant text locally as UTF-8 files named `ncmm-approval.txt` and `ncmm-follow-up.txt`. Keep publication dates in your research notes. Use a fresh database for the pilot.
2. From an installed copy of PolicyTrace India, run the following in Bash. Quote the URLs so the shell passes the full query string.

```bash
policytrace ingest --db ncmm-pilot.sqlite3 --source-url 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2097308&lang=2&reg=48' --publisher 'Press Information Bureau' --title 'National Critical Mineral Mission approval' --file ncmm-approval.txt
policytrace ingest --db ncmm-pilot.sqlite3 --source-url 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2149747&lang=2&reg=48' --publisher 'Press Information Bureau' --title 'National Critical Mineral Mission follow-up' --file ncmm-follow-up.txt
policytrace verify --db ncmm-pilot.sqlite3
policytrace export --db ncmm-pilot.sqlite3 > ncmm-evidence.jsonl
```

3. Check for two JSONL records with distinct source URLs and digests. Keep the evidence file alongside your notes. Link each claim to the corresponding release. Keep the proposed public expenditure and expected investment as separate figures, and check separate records if your analysis needs actual spending or implementation.
4. If you later capture different text at the **same** source URL, ingest it again and use `policytrace history` to find the revision IDs before running `policytrace diff`.

The export defaults to metadata only. The checksum verifies the bytes stored in your local database. PolicyTrace records the time you ingested the text, so use the publication date from PIB for your policy timeline.
