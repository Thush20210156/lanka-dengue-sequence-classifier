# Public Sri Lankan dengue sequence dataset
This dataset is compiled from public NCBI GenBank records with a source geographic location of Sri Lanka. It is not simulated data and is not a new wet-laboratory collection.

Snapshot date: 2 November 2026. Exact query and download hashes: raw_manifest.json.
Candidate records: 410. Included: 383. Excluded: 27 (see record_audit.csv).
Classes: DENV-1 51; DENV-2 216; DENV-3 90; DENV-4 26.
Collection years with known metadata: 1978-2025; three records lack a year.

Files:
- genbank_snapshot.gb.gz: public source records, compressed, including excluded candidates for audit.
- sri_lanka_dengue.fasta.gz: only included near-complete viral sequences; accession headers only.
- sri_lanka_dengue_features.csv: provenance metadata, target and 15 dinucleotide frequencies.
- dataset_summary.json: quality-filter counts and class sizes.
- record_audit.csv: inclusion decision and first applicable exclusion reason for every candidate.
- raw_manifest.json: query, retrieval date and source batch hashes.

Eligibility: source country exactly Sri Lanka before any colon; dengue organism; one explicit serotype from source serotype annotation or explicit dengue type/serotype wording; length 10,000-12,000 bases; no more than 1% ambiguous bases. No serotype is inferred from feature values or from an isolate name. Broad text-search false positives are removed using source metadata.

The identifier, country, year, isolate, source URL, length, ambiguity and publication fields are audit fields, NOT model predictors. Only columns di_AA through di_TG in features.FEATURES enter the pipeline. TT frequency is omitted because the 16 frequencies sum to one. Valid adjacent A/C/G/T pairs form the denominator; pairs containing ambiguity are ignored.

Five exact duplicate-sequence records exist. These and repeated identical isolate IDs are linked into 378 indivisible evaluation groups. Records remain in the dataset, but no such group crosses a split. These groups do not imply phylogenetic independence: near-identical/homologous strains may cross partitions.

Attribution: NCBI GenBank and the original record submitters. Each included row links its accession.version to the source record and includes available PubMed IDs. Preserve these references and acknowledge the original sequence-generating studies; this project's contribution is compilation, descriptor extraction and analysis.

NCBI states that it places no restrictions on use/distribution of GenBank data, while noting possible submitter intellectual-property claims: https://www.ncbi.nlm.nih.gov/genbank/ . This is public access, not a claim that every record has a CC0/CC BY license. No GISAID account, login-only dataset, API key or controlled human dataset was used. Only viral sequence descriptors and public isolate metadata are included; no patient-level clinical table, age, exact home location or treatment data is collected.

Local context examples (not claims that every record comes from these papers):
- Genomic Surveillance of Recent Dengue Outbreaks in Colombo, Sri Lanka: https://pmc.ncbi.nlm.nih.gov/articles/PMC10384240/
- Identifying the strains of dengue circulating in the western province of Sri Lanka during 2019-2022: https://pmc.ncbi.nlm.nih.gov/articles/PMC11251588/
Use the per-record references to establish the provenance of any particular accession.
