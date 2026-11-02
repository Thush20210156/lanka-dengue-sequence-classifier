# Lanka Dengue Sequence Classifier

A reproducible MSc machine-learning project using public dengue genomes collected in Sri Lanka. It classifies an already-known dengue genome into DENV-1, DENV-2, DENV-3 or DENV-4 with regularized Quadratic Discriminant Analysis (QDA).

## Run locally
Use Python 3.11 (recommended) or the locally tested Python 3.12.7.
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python train.py
python verify.py
streamlit run app.py
```
Open http://localhost:8501. On Windows, use `.venv\Scripts\Activate.ps1` for local PowerShell activation; the Azure scripts require Bash/WSL.

## What is included
- 383 real public Sri Lankan dengue genome records, not simulated observations.
- Four serotypes: DENV-1 51, DENV-2 216, DENV-3 90, DENV-4 26.
- A dated GenBank snapshot, accession-level provenance and an exclusion audit.
- Fifteen sequence-derived dinucleotide frequencies. All metadata and target labels are excluded from prediction.
- Exact-genome/isolate group separation; training-only cross-validation; frozen validation/test results.
- Permutation feature importance, partial dependence and a clearly labelled local sensitivity path.
- Streamlit frontend accepting one public near-complete viral sequence or a held-out example.
- Azure deployment and cleanup scripts, a beginner guide, report and video materials under docs/.

## Results and their limits
The current split has 229 training, 77 validation and 77 test genomes. Three-fold group-aware training CV selects reg_param=0.05, then a frozen model is refitted on training+validation. The held-out test accuracy and macro-F1 are 1.0; the majority baseline accuracy is 0.5065 and macro-F1 is 0.1681. A shuffled-training-label control yields macro-F1 0.1857. A supplementary train-through-2018/test-from-2019 check gives accuracy 0.9925 but contains no DENV-4 test samples.

Perfect scores do not establish perfect deployment performance. Only eight test genomes are available for each of DENV-1 and DENV-4. Related outbreak strains can cross partitions; no phylogenetic/homology clustering was performed. QDA uses imperfect Gaussian assumptions and can report collinear variables; positive regularization stabilizes covariance estimation. See the report for limitations and uncertainty.

## Rebuild the compiled dataset
The original public snapshot is committed as data/genbank_snapshot.gb.gz. Run `python compile_dataset.py` to recreate features and audit. It uses local raw batches when present, otherwise the compressed snapshot. Run `python fetch_data.py` only if intentionally refreshing the public search; database updates can change counts or annotations. Preserve the supplied snapshot for the submitted experiment. The app never downloads records at startup.

## Azure deployment
Follow docs/AZURE_GUIDE.md for student sign-in, subscription/credit checks and CLI setup, then run:
```bash
bash scripts/deploy_azure.sh
```
The default cloud-build route needs no local Docker. If student ACR Tasks are unsupported, start Docker Desktop and run `BUILD_MODE=docker bash scripts/deploy_azure.sh`. Both routes create resources that can consume credits. The script saves non-secret resource names and URL in deployment-state.json. It does not claim deployment until the live health check succeeds; test the frontend manually afterward. Cleanup is interactive: `bash scripts/cleanup_azure.sh` after marking.

## Verification
`python verify.py` checks all 383 sequence hashes and descriptors, disjoint accession/group/hash splits, recalculated metrics and probabilities, invalid input handling and frontend submissions for all four serotypes plus pasted sequence input. GitHub Actions reproduces training, runs those checks, builds the image and tests its health endpoint. Check the actual Actions run before claiming container verification.

## Data access and attribution
Source: public NCBI GenBank records whose source location is Sri Lanka. No GISAID, login-only sequence data or controlled patient dataset is used. Original sequence generation belongs to the source researchers. This project compiles and analyses public records; it does not claim new sample collection. See data/README.md, source_url and study_pubmed columns. Public access is not a blanket assertion that each submitter's data have a CC0 license.

## Scope
The application assumes a near-complete, positive-sense dengue genome represented with A/C/G/T (U is converted to T). It is an annotation demonstration, not a dengue detector, diagnostic, severity predictor, clinical assay or phylogenetic typing replacement. Do not upload private biological or patient records.

## Submission
Review the report, fill in your student/course details, follow your institution's assistance-disclosure rules, and understand/reproduce the analysis. Run deployment in your own Azure account, add the real URL/date and evidence, and record the 3-5 minute demonstration. The guide and script do not substitute for a successful live deployment or a real video recording.
