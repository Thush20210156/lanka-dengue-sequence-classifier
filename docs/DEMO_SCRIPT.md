# Assessment demo: about 4 minutes 45 seconds
Use this as a speaking guide and adapt it to your own understanding. Record the actual application, not just these pages. The final Azure section must be recorded after running deployment successfully. The existing local screenshots do not prove Azure deployment.

## 0:00-0:30 | Problem and scope
Screen: live app title and public Azure URL (after deployment).
Say: "My project is Lanka Dengue Sequence Classifier. It explores whether simple sequence-composition features can recover the annotated serotype of dengue genomes collected in Sri Lanka. The intended context is bioinformatics teaching and research. The application assumes the sequence is already dengue; it is not a diagnostic test or a disease-severity predictor."

## 0:30-1:10 | Genuine local dataset and provenance
Screen: Data provenance tab, then data/record_audit.csv in GitHub.
Say: "I compiled public GenBank records with Sri Lanka in the source-country field. This is real secondary data, not synthetic observations or a new laboratory collection. The query returned 410 candidates, and explicit source and quality rules retained 383. The four classes contain 51, 216, 90 and 26 genomes respectively. Every row links an accession to its source record. No restricted database or patient-level clinical table is used. Labels are explicit source serotypes, while the model sees only fifteen dinucleotide frequencies."

## 1:10-1:50 | Algorithm and experiment
Screen: train.py pipeline and results/split_accessions.json.
Say: "The new algorithm is regularized Quadratic Discriminant Analysis. It estimates class-specific means and covariances, so it differs from logistic regression, nearest-neighbor voting and tree-based models. It is not deep learning. Exact duplicate genomes and identical isolate identifiers are grouped before splitting. There are 229 training, 77 validation and 77 test rows. Three-fold group-aware cross-validation selects using macro-F1. All six regularization values tie, so the first value, 0.05, is chosen. Preprocessing is fitted inside folds, and metadata is excluded from prediction."

## 1:50-2:30 | Live prediction
Screen actions: in Predict a sequence choose a DENV-1 example, click Classify and explain. Choose a DENV-3 example, click again. Briefly show paste-input mode and the validation message for a short input such as ACGT.
Say: "Here the app extracts descriptors from a public held-out genome. The known label is displayed only for comparison and is not passed to the classifier. The prediction shows a serotype and an uncalibrated model probability. This second example shows another class. Input checks reject a short sequence. A confident prediction does not establish that an unfamiliar sequence is dengue, because this is a closed-set four-class model."

## 2:30-3:10 | Evaluation and XAI
Screen: evaluation table, confusion matrix and importance chart.
Say: "All 77 held-out labels were recovered, compared with 50.65 percent accuracy for the majority baseline. A shuffled-label control gave macro-F1 about 0.186. The later-year check gave 99.25 percent accuracy, but it has no DENV-4 examples. Perfect scores here do not establish perfect future performance. Permutation importance measures the macro-F1 decrease after shuffling a feature. CC, GG and AG have the largest mean effects, but the effects are tiny and variable. Correlated composition features and a ceiling score limit individual explanations. The local bars are an order-dependent reference-replacement path, not SHAP or causal effects."

<!-- PAGEBREAK -->

## 3:10-3:45 | GitHub and reproducibility
Screen: repository README, data files, commit history, Actions workflow run.
Say: "The repository includes the original public snapshot, curated dataset, preprocessing, training, evaluation, explanations and frontend. The commits show the actual implementation stages. The automated workflow trains, checks sequence hashes and leakage boundaries, tests frontend predictions, then builds and health-checks the container. The dependency issue found on the first clean run was fixed and the rerun passed. A green CI result verifies the build; it does not itself prove an Azure deployment."

## 3:45-4:20 | Actual Azure deployment
Screen: Azure Container App Overview with ready revision and hostname; switch to the public app and make a prediction.
Say ONLY after successful deployment: "This instance runs in my Azure student subscription. Container Registry stores the image, and a managed identity allows image pulls. Container Apps exposes Streamlit over HTTPS on target port 8501. The minimum replica count is zero and maximum is one. Registry, build and log usage can still consume student credits. The deployment script checks the live health endpoint, and this browser prediction verifies the frontend."
Do not show sign-in, one-time codes, tokens, email or billing details. If not yet deployed, complete it before recording this section; do not narrate the local app as Azure-hosted.

## 4:20-4:45 | Limitations and close
Screen: report discussion and app.
Say: "The main limitations are selected public records, small rare-serotype samples, imperfect Gaussian assumptions and related strains crossing partitions despite exact-duplicate grouping. Future work should use sequence-clustered and independent-study testing, validated reference typing and calibrated uncertainty. My submission includes the report, repository, dataset provenance and this demonstration."

## Record and review
On macOS press Shift+Command+5, select a recording region, choose a microphone in Options, and record. Stop from the menu bar. On Windows use an installed recorder such as OBS and select screen/window capture plus microphone. Test audio first. Increase editor text size, hide notifications, and rehearse using the actual app. Allow pauses for buttons and tabs; keep the finished recording between 3 and 5 minutes. Save MP4 where supported, check Moodle's upload limit and watch the whole file before submission. Suggested name: StudentID_LankaDengue_Demo.mp4.

A local walkthrough can be used for rehearsal, but the final video should show your real Azure deployment and your own explanation. No completed Azure video is claimed by this script.

## Optional longer deployment tutorial
For a separate 10-15 minute learning video, follow AZURE_GUIDE.md in order: student login off-camera; subscription and cost explanation without sensitive details; local setup; Azure CLI login; run deploy_azure.sh; pause while building; explain registry, identity, environment and port; show the live result; demonstrate cleanup only after saving evidence and after the marking window. Do not include the entire deployment wait inside the 3-5 minute assessment video.
