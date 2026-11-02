# Lanka Dengue Sequence Classifier

Classify a known dengue genome as **DENV-1, DENV-2, DENV-3 or DENV-4** using regularized Quadratic Discriminant Analysis (QDA).

**[Open the live application](https://lanka-dengue-demo.politecliff-7391470b.centralindia.azurecontainerapps.io/)**

Hosted on Azure Container Apps in Central India. The first visit after inactivity may take longer while the app starts.

## Features

- Select a public held-out example or paste a near-complete dengue genome.
- View the predicted serotype and model probabilities.
- Explore local sensitivity explanations, permutation importance and partial dependence.
- Inspect dataset provenance and evaluation results.

## Dataset and method

The dataset contains **383 public GenBank genomes with Sri Lankan source metadata**: 51 DENV-1, 216 DENV-2, 90 DENV-3 and 26 DENV-4.

The model uses 15 dinucleotide frequencies. Accession names, collection dates, location metadata and labels are excluded from the predictors. Exact duplicate genomes and identical isolate identifiers remain in the same evaluation partition.

The original researchers collected and sequenced the samples; this project compiles their public records and derives features. See [dataset attribution and curation](data/README.md) and the [record audit](data/record_audit.csv).

## Results

The split contains 229 training, 77 validation and 77 test genomes. Model selection uses group-aware cross-validation on the training set.

| Held-out metric | QDA | Majority baseline |
| --- | ---: | ---: |
| Accuracy | 1.0000 | 0.5065 |
| Macro-F1 | 1.0000 | 0.1681 |

These results describe a small, selected public dataset. Related outbreak strains may cross partitions, and each of DENV-1 and DENV-4 has only eight test examples. The perfect score does not establish perfect future performance. See the [report](docs/Sri_Lankan_Dengue_Report.pdf) for the temporal check, negative control and limitations.

## Run locally

Use Python 3.11 or 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python train.py
python verify.py
python -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501). On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

To rebuild the feature table from the archived public records, run `python compile_dataset.py` before training.

## Project files

| Path | Purpose |
| --- | --- |
| `features.py` | Sequence validation and descriptor extraction |
| `compile_dataset.py` | Dataset curation from the archived GenBank snapshot |
| `train.py` | Model selection, evaluation and explainability |
| `app.py` | Streamlit interface |
| `verify.py` | Data, split, prediction and frontend checks |
| `data/` | Dataset, source snapshot and attribution |
| `results/` | Trained model, metrics and plots |
| `docs/` | Report, deployment guide and demonstration script |

## Deployment

The live app runs on **Azure Container Apps**, with its image stored in **Azure Container Registry**. The [Azure image workflow](.github/workflows/azure-image.yml) builds and pushes images using passwordless authentication. The [verification workflow](.github/workflows/ci.yml) checks dataset reconstruction, training, the frontend and the Docker container.

See the [deployment guide](docs/AZURE_GUIDE.md) for setup details. Student-subscription region and build restrictions can vary.

## Intended use

This is a research and teaching prototype for already-known, positive-sense dengue genomes of 10,000–12,000 bases. Model probabilities are uncalibrated. It is not a diagnostic or disease-severity tool; use public sequences rather than private patient records.
