# Lanka Dengue Sequence Classifier
## Serotype classification from public Sri Lankan viral genomes using regularized QDA
MSc in Artificial Intelligence | Machine Learning Assignment
Prepared for: Thushini Abeysuriya
Student ID, module and lecturer: complete before submission
Date: 2 November 2026
Repository: https://github.com/Thush20210156/lanka-dengue-sequence-classifier

## Abstract
This project compiles publicly available dengue genome records whose source geographic location is Sri Lanka and investigates whether simple sequence-composition descriptors can distinguish the four annotated dengue serotypes. A reproducible curation pipeline retains 383 of 410 candidate GenBank records. Fifteen dinucleotide frequencies are extracted without using accession names, geographic metadata or collection dates as predictors. The selected algorithm is regularized Quadratic Discriminant Analysis (QDA), a classical method outside the supplied lecture list. Exact genome duplicates and identical isolate identifiers are grouped before partitioning. Training-only cross-validation selects covariance regularization; a frozen test set is used for final evaluation. The model correctly classifies all 77 held-out genomes, while a majority-class baseline achieves 50.65% accuracy. A supplementary later-year test obtains 99.25% accuracy but includes only three serotypes. Permutation importance and partial dependence are used to inspect model behavior. A Streamlit interface and Azure deployment automation support demonstration. These findings concern annotation recovery in a selected public dataset, not clinical diagnosis or universal serotyping accuracy.

## Contribution and local-data scope
The dataset is generated computationally by compiling real public records and extracting descriptors. Biological observations and labels are not simulated. The source researchers collected and sequenced the samples; this project does not claim new laboratory collection. Local provenance is established from source-country fields, not merely a Sri Lankan application name. This follows the guideline's option to collect or compile a dataset; if the lecturer requires personally collected primary samples, secondary-data compilation should be confirmed separately.


<!-- PAGEBREAK -->

# 1. Problem definition and local relevance
Dengue surveillance involves distinguishing genetically different serotypes. A compact sequence-classification exercise provides a useful bioinformatics problem for studying how biological information can be represented numerically and evaluated with an unfamiliar machine-learning method. The research question is: how well can regularized QDA recover the annotated serotype of public Sri Lankan near-complete dengue genomes using only dinucleotide composition?

The proposed application is a teaching and research exploration tool. A student or researcher can inspect a known dengue genome, compare its composition-based prediction with its reference annotation and examine model explanations. The app assumes the input is already dengue. It does not identify dengue among arbitrary organisms, predict an outbreak, infer disease severity or support treatment decisions. Established sequence alignment and validated laboratory typing remain outside this prototype's scope.

Published research documents dengue genome surveillance in Colombo and strain characterization in Sri Lanka [2,3]. These studies motivate the local setting; the provenance of each included observation is its own GenBank accession and source annotation. No partnership with a laboratory or health authority is claimed.

# 2. Public dataset compilation
GenBank is a public annotated sequence repository, and NCBI provides programmatic access through E-utilities [1]. A query snapshot dated 2 November 2026 retrieves dengue-associated records mentioning Sri Lanka, with lengths 9,000-12,000 bases and publication dates no later than the snapshot date. The exact query is preserved in data/raw_manifest.json. This deliberately broad candidate search is followed by stricter source-record filtering.

The candidate set contains 410 accessioned records. Inclusion requires the source country, before any colon, to equal Sri Lanka; a dengue organism annotation; exactly one explicit serotype annotation; length 10,000-12,000 bases; and at most 1% ambiguous bases. Serotype comes from an explicit source qualifier or explicit dengue type/serotype wording in the organism or definition. It is never inferred from an isolate identifier or from the descriptors that the classifier will later use.

Twenty-seven candidates are excluded: 11 exceed the ambiguity limit, five are unrelated viruses, one is too short, nine lack an unambiguous explicit serotype, and one has Germany as its source country. These are first-applicable exclusion reasons, rather than counts of every possible failed rule. The audit CSV retains the decision for every candidate. This filtering matters: a country name in a paper reference can match a text search without establishing local sample origin.


<!-- PAGEBREAK -->

# 3. Dataset structure and preprocessing
| Target class | Included genomes | Share |
| --- | --- | --- |
| DENV-1 | 51 | 13.3% |
| DENV-2 | 216 | 56.4% |
| DENV-3 | 90 | 23.5% |
| DENV-4 | 26 | 6.8% |
| Total | 383 | 100.0% |

Known collection years span 1978-2025; three included records lack a collection year. Missing dates are retained because dates are audit metadata rather than model predictors. They are omitted from the supplementary temporal check. Records are not claimed to represent current national serotype prevalence: public sequencing is a selected sample of outbreaks, studies and submission practices.

Each row includes accession.version, country, collection year, serotype, sequence length, ambiguity fraction, isolate ID, available PubMed references, a sequence SHA-256 and a source-record URL. These fields support provenance and auditing. Only the fifteen di_* descriptors enter the predictor. Neither metadata nor the target column enters the feature matrix.

For a sequence s, the frequency of dinucleotide ab is its count among adjacent unambiguous A/C/G/T pairs divided by the total number of such pairs. Overlapping pairs are counted. Pairs containing ambiguity are ignored. RNA U is converted to T; spacing and a single FASTA header are removed. The model expects a positive-sense near-complete dengue genome. Reverse-complemented sequences and short fragments are not part of the supported input definition.

There are sixteen possible dinucleotides, but their frequencies sum to one. TT is omitted to remove exact compositional dependence, leaving AA, AC, AG, AT, CA, CC, CG, CT, GA, GC, GG, GT, TA, TC and TG. This does not eliminate correlation among the remaining frequencies.

Five records repeat an exact sequence. Records sharing either an exact sequence hash or an identical non-empty isolate identifier are joined into 378 groups. All records remain in the curated dataset, but each group is kept intact across evaluation partitions. This prevents direct exact-match leakage. It is not phylogenetic clustering and does not guarantee that related strains are independent.

A Pipeline applies a training-fitted variance filter, StandardScaler and QDA. The filter and scaler are refitted inside each cross-validation fold. No feature imputation or categorical encoding is required. Label-free feature extraction is deterministic and contains no fitted parameters.


<!-- PAGEBREAK -->

# 4. Selection of a new machine-learning algorithm
QDA is chosen because it is a classical, non-deep-learning classifier that estimates class-specific means and covariances. Unlike a linear decision surface, separate covariance matrices allow a curved boundary. Its model size and computation are modest for fifteen tabular descriptors. QDA is outside the student's supplied list of taught methods; this should be checked against any additional lecture material before final submission.

For class k, QDA uses the score:

delta_k(x) = -0.5 log|Sigma_k| - 0.5 (x-mu_k)^T Sigma_k^-1 (x-mu_k) + log(pi_k).

Here mu_k is the class mean, Sigma_k is its covariance and pi_k is its estimated prior. The class with the highest score is selected. Normalizing class likelihoods gives model probabilities, which are not separately calibrated in this study [4,5].

Logistic regression models conditional class probabilities rather than estimating a class-specific Gaussian density. Trees partition inputs with rules, while k-NN votes among nearby examples. SVM uses a margin-based objective, and the listed boosting methods combine multiple weak learners. QDA offers a different statistical assumption and learning mechanism; the project does not claim that it is superior to all of those algorithms.

Covariance regularization is necessary because the smallest training class has only twelve genomes and descriptors are correlated. In standardized space, scikit-learn's reg_param shrinks within-class variance components toward an identity contribution. Candidate values are 0.05, 0.10, 0.25, 0.50, 0.75 and 1.00. Positive regularization stabilizes estimation. Collinearity warnings are recorded rather than hidden; they remain a reason for caution about the underlying Gaussian model.

The algorithm is suitable for an MSc investigation because its assumptions, fitting process and failure modes can be explained explicitly. Its convenience does not justify a clinical claim or replace a comparison with established sequence-based typing. Such a comparison would be a useful extension.


<!-- PAGEBREAK -->

# 5. Model training and selection
| Partition | DENV-1 | DENV-2 | DENV-3 | DENV-4 | Total |
| --- | --- | --- | --- | --- | --- |
| Training | 33 | 132 | 52 | 12 | 229 |
| Validation | 10 | 45 | 16 | 6 | 77 |
| Test | 8 | 39 | 22 | 8 | 77 |

The first fold of a shuffled five-fold StratifiedGroupKFold split, seed 42, is reserved for testing. The first fold of a four-fold group-aware split of development data, seed 43, becomes validation. Remaining observations form training. Group stratification approximates class balance while keeping groups intact, so the fractions are approximately 60/20/20 rather than exact class-proportional counts. There are 226 training groups, 76 validation groups and 76 test groups.

Three-fold StratifiedGroupKFold cross-validation, seed 44, is performed within the 229 training rows. Mean macro-F1 is used for selection because it gives each serotype equal weight despite class imbalance. Every candidate uses identical folds and independently fitted preprocessing. The selected pipeline is checked on the separate validation set, then refitted on training plus validation (306 genomes). The test partition is evaluated after that selection is fixed; no threshold or parameter is revised from its results.

| Regularization | Mean training CV macro-F1 | Fold SD |
| --- | --- | --- |
| 0.05 | 0.9954 | 0.0064 |
| 0.10 | 0.9954 | 0.0064 |
| 0.25 | 0.9954 | 0.0064 |
| 0.50 | 0.9954 | 0.0064 |
| 0.75 | 0.9954 | 0.0064 |
| 1.00 | 0.9954 | 0.0064 |

All six candidates tie at mean CV macro-F1 0.9954. GridSearchCV selects the first listed value, reg_param 0.05; this is a deterministic tie-break, not evidence that 0.05 is uniquely best. Validation accuracy and macro-F1 are both 1.0 before the development refit. The fold SD is variability across these three folds, not an inferential confidence interval. A majority-class DummyClassifier provides a minimal benchmark; a single shuffled-training-label control is an additional diagnostic, not a statistical significance test.


<!-- PAGEBREAK -->

# 6. Final evaluation
| Metric | QDA | Majority baseline | Shuffled-label control |
| --- | --- | --- | --- |
| Accuracy | 1.0000 | 0.5065 | 0.4026 |
| Balanced Accuracy | 1.0000 | 0.2500 | 0.2236 |
| Macro F1 | 1.0000 | 0.1681 | 0.1857 |
| Weighted F1 | 1.0000 | 0.3406 | 0.3426 |
| Macro Ovr Auc | 1.0000 | 0.5000 | 0.2833 |

Accuracy measures overall correctness; balanced accuracy averages class recall. Macro-F1 averages the per-class precision-recall harmonic mean equally across serotypes, while weighted F1 uses observed class support. Macro one-vs-rest ROC-AUC averages four binary ranking assessments. Class prediction uses the greatest probability, with no test-driven threshold tuning.

All 77 held-out predictions match their annotated labels: 8 DENV-1, 39 DENV-2, 22 DENV-3 and 8 DENV-4. The majority baseline predicts DENV-2 for every observation, explaining its 39/77 accuracy and much poorer macro-F1. When the same model structure is fitted to a fixed shuffled development-label assignment, macro-F1 falls to 0.1857. This is consistent with learning a sequence-label relationship, but one negative-control run cannot rule out every form of confounding or leakage.

![Held-out confusion matrix](results/confusion_matrix.png)

The perfect score is reported because it occurred in the fixed experiment; it has not been manufactured, rounded up from errors or selected from repeated test splits. Serotype-level sequence differences can be relatively strong compared with within-serotype variation. However, historical cohort composition and related outbreak genomes may also make this task easier than independent surveillance deployment.

An approximate 95% Wilson interval for 77/77 correct is 0.9525-1.0000 under independent Bernoulli sampling assumptions. Those assumptions are imperfect for related viral records, so this interval is descriptive rather than a guarantee. The 2,000-resample group bootstrap gives F1 [1,1] because all observed predictions are correct; that degenerate result does not imply zero uncertainty about future errors.


<!-- PAGEBREAK -->

# 7. Robustness and the limits of the result
![One-vs-rest ROC curves](results/roc.png)

A supplementary temporal check retains the selected regularization, fits on genomes collected through 2018 and evaluates later genomes from 2019 onward. Exact/isolate groups appearing in the early period are excluded from the later test. Three records with missing years are omitted. The early set contains 246 rows and the later set 133. One later prediction is wrong: accuracy is 132/133 (0.9925) and macro-F1 over the represented classes is 0.9875.

This temporal check supports the idea that the primary result is not solely a consequence of an exact duplicate split. It does not establish four-class future performance: later data contain 18 DENV-1, 48 DENV-2 and 67 DENV-3 genomes, and no DENV-4. It is supplementary and reuses the available public sample rather than providing a prospectively collected external cohort. It was not used to tune the final model.

The strongest next evaluation would reserve independent sequencing studies, isolates and sequence-homology clusters before any model selection. That analysis is not completed here. Full-genome alignment, homology clustering and comparison with a validated serotyping pipeline would be more informative than treating perfect classification on a small public sample as operational readiness.


<!-- PAGEBREAK -->

# 8. Explainability and interpretation
Permutation feature importance is the main XAI method. After final model selection, each held-out descriptor is shuffled thirty times with seed 45; importance is the mean decrease in macro-F1. The test set is used here only for post-hoc explanation, and the results are not used to select features or refit another model [6].

| Descriptor | Mean macro-F1 reduction | Shuffle SD |
| --- | --- | --- |
| di_CC | 0.00352 | 0.00431 |
| di_GG | 0.00323 | 0.00424 |
| di_AG | 0.00293 | 0.00415 |
| di_GA | 0.00264 | 0.00403 |
| di_AA | 0.00205 | 0.00372 |
| di_GC | 0.00205 | 0.00372 |
| di_TC | 0.00176 | 0.00352 |
| di_CG | 0.00147 | 0.00328 |
| di_CA | 0.00120 | 0.00305 |
| di_TA | 0.00029 | 0.00158 |
| di_AC | 0.00000 | 0.00000 |
| di_AT | 0.00000 | 0.00000 |
| di_CT | 0.00000 | 0.00000 |
| di_GT | 0.00000 | 0.00000 |
| di_TG | 0.00000 | 0.00000 |

![Permutation importance](results/importance.png)

## 8.1. Reading the importance results
CC, GG and AG have the largest mean reductions in this experiment, but their effects are small (about 0.0035, 0.0032 and 0.0029 macro-F1). Their shuffle SDs are comparable to or larger than the means. The ranking is consequently weak evidence for a stable biological hierarchy. Zero decrease for a descriptor means that this perturbation did not change measured test F1 here; it does not prove the feature is irrelevant.

A supplementary joint permutation moves all fifteen descriptors together between held-out rows, preserving each row's composition while breaking its association with the label. Across thirty repeats the mean macro-F1 reduction is 0.7472 (shuffle SD 0.0579). This supports reliance on the descriptor set jointly; it cannot identify a unique causal dinucleotide. The model appears to distinguish serotypes from combined composition patterns rather than depending on a single score. This is plausible for sequence-based annotation, but no specific molecular mechanism is established. Composition features are correlated, and information may be redundant. In addition, a ceiling classification score hides probability changes until the predicted class changes. Independent shuffling can create compositions not observed in real genomes, further limiting biological interpretation.



# 9. Partial dependence and frontend explanations
Partial dependence for the two highest-ranked descriptors shows the average predicted DENV-1 probability while varying a descriptor over development-set backgrounds [7]. Both curves are essentially flat near 0.1405 on a probability scale of zero to one. Minute numerical variation is not a substantive directional effect. This supports the caution that changing one descriptor alone offers little insight into an already well-separated, redundant feature representation. Its substituted compositions may be unrealistic because frequencies share a common denominator, so the curves are not causal biological effects.

![DENV-1 partial dependence](results/pdp.png)

The frontend adds a local sensitivity path. Starting from development-feature medians, it replaces each descriptor with the selected genome's value in a fixed order and plots successive changes in that predicted serotype's probability. The changes sum to the final probability minus the reference probability. This is explicitly an order-dependent reference-replacement explanation, not SHAP. The reference and intermediate feature combinations need not represent actual genomes.

Users can select a public held-out example or paste one public near-complete dengue genome. The application derives frequencies internally, displays the predicted serotype, an uncalibrated probability distribution, local sensitivity bars and global evaluation figures. Input checks reject short, invalid or overly ambiguous sequences. A development-range warning is a simple flag, not a validated detector for unknown organisms or out-of-distribution inputs. No private sequence upload is needed to demonstrate the system.

The source code separates deterministic descriptor extraction, curation, training/evaluation and the interface. Verification covers all 383 sequence hashes and extracted feature vectors, FASTA-header independence, disjoint accession/group/hash splits, recomputed metrics and probabilities, invalid inputs and frontend predictions across all four serotypes.


<!-- PAGEBREAK -->

# 10. Critical discussion and ethical data use
This is a small, selected collection of publicly submitted viral genomes. DENV-2 dominates, while DENV-4 has only 26 rows and eight held-out examples. The distribution reflects sequencing and submission choices, not a representative survey of Sri Lanka. Serotype, collection year, outbreak lineage and laboratory protocol may be confounded. No demographic fairness analysis is possible from the chosen viral-only predictors; relevant bias concerns are strain, geography, time and study coverage.

Grouping prevents exact duplicate leakage but not homology leakage. Closely related sequences may occur across splits. Retained duplicate records also give repeated genomes extra weight within a partition. A future study should compare deduplicated and sequence-clustered evaluations and include independent source studies. The temporal check reduces one type of temporal mixing but cannot cover later DENV-4 performance.

QDA assumes approximately Gaussian within-class descriptor distributions. Dinucleotide frequencies are bounded and compositional, so that assumption is imperfect. Collinearity warnings occur for the small classes even after omitting TT. Positive regularization prevents unstable unregularized covariance estimation from being used, but does not make the assumptions true. The limited hyperparameter grid and single primary partition also leave model-selection uncertainty.

Reference labels are public annotations, not a new independent laboratory gold standard. Excluding missing or ambiguous serotype labels improves label clarity but may introduce selection bias. These labels can be audited through accessions and references. Performance is annotation recovery among known dengue genomes and must not be described as diagnostic sensitivity or specificity for dengue infection.

All source records used here are publicly downloadable without restricted access. No GISAID records, controlled human-genomic dataset or patient-level clinical table is used. Original sequence generation and sample collection are attributed to the original submitters. No new human-subject recruitment or consent claim is made. Public availability is not presented as a universal CC0 license; NCBI's usage statement notes possible submitter rights [1].

Potential value is educational exploration and a transparent local-data ML workflow. Potential harm is overtrust: an arbitrary input can receive a confident serotype because the model must choose among four known classes. The interface explains this closed-set assumption and avoids clinical recommendations. Production use would require external validation, calibrated uncertainty, rejection behavior and comparison with validated reference methods.


<!-- PAGEBREAK -->

# 11. Deployment, repository and submission status
The repository is https://github.com/Thush20210156/lanka-dengue-sequence-classifier . Its commits document the actual compilation, modelling, interface and packaging work with their real timestamps. The supplied source archive includes the same dataset, scripts and results. A dedicated report and deployment guide explain how to reproduce the project from a fresh environment.

The serving architecture is a browser connecting by HTTPS to Azure Container Apps, which forwards requests to Streamlit on port 8501. Azure Container Registry stores the Docker image. A user-assigned managed identity receives registry pull permission, avoiding a stored registry password. The deployment script creates a Consumption environment and limits the demonstration to zero minimum and one maximum replica. Registry storage, builds and logs can consume student credits even when the app has no active replica [8-10].

The Dockerfile installs pinned Python dependencies and trains offline from the committed feature dataset in the serving environment. This avoids relying on a model serialized under an unrelated Python environment. The GitHub workflow reproduces training, runs the app/data checks, builds the image and checks its health endpoint. These checks passed in run 41455582237 on 2 November 2026 after pinning compatible transitive dependencies. This provides a clean Linux build check, not evidence of Azure hosting. The Azure script saves the real hostname and resource names after deployment and checks the live health endpoint. A successful health response must be followed by manual frontend checks.

Azure execution remains the student's next step, as requested: run the automation in the student's own signed-in subscription. No Azure deployment URL or completed cloud recording is claimed in this report. Add the actual URL, deployment date, ready revision and successful browser-prediction evidence after running the guide. A local walkthrough and a CI build do not substitute for live Azure evidence.

# 12. Conclusion
A genuinely local secondary dataset was compiled from 383 public Sri Lankan dengue genome records, with transparent inclusion decisions and reproducible sequence descriptors. Regularized QDA achieved perfect classification on the fixed small test partition and strong, but incomplete, later-year results. These findings justify further investigation rather than a claim of general-purpose serotyping readiness. The contribution is a clear end-to-end workflow: public local records, classical ML, leakage checks, explainability, a working interface and reviewable deployment automation.


<!-- PAGEBREAK -->

# References
[1] NCBI. GenBank overview, public access, E-utilities and data usage statement. https://www.ncbi.nlm.nih.gov/genbank/ . Individual accession.version links and available PubMed IDs are included in the curated dataset; retain these source-study attributions.
[2] Genomic Surveillance of Recent Dengue Outbreaks in Colombo, Sri Lanka. Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC10384240/
[3] Identifying the strains of dengue circulating in the western province of Sri Lanka during 2019-2022. Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC11251588/
[4] scikit-learn. Linear and Quadratic Discriminant Analysis. https://scikit-learn.org/stable/modules/lda_qda.html
[5] scikit-learn. QuadraticDiscriminantAnalysis API reference. https://scikit-learn.org/stable/modules/generated/sklearn.discriminant_analysis.QuadraticDiscriminantAnalysis.html
[6] scikit-learn. Permutation feature importance. https://scikit-learn.org/stable/modules/permutation_importance.html
[7] scikit-learn. Partial dependence and individual conditional expectation. https://scikit-learn.org/stable/modules/partial_dependence.html
[8] Microsoft Azure. Azure for Students. https://azure.microsoft.com/en-us/free/students/
[9] Microsoft Learn. Azure Container Apps quickstart. https://learn.microsoft.com/en-us/azure/container-apps/get-started
[10] Microsoft Learn. Managed-identity image pull. https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull
Sources and public-record snapshot checked 2 November 2026. The application uses scikit-learn 1.5.1; current online documentation may describe a later version.

# Reproduction and completion checklist
Install requirements.txt, run python compile_dataset.py from the committed snapshot if rebuilding the table, then python train.py, python verify.py and streamlit run app.py. Docker trains from the committed CSV without contacting NCBI. Preserve data/raw_manifest.json, data/record_audit.csv and results/split_accessions.json.

Before submission, complete student/course details, review the analysis and follow institutional assistance-disclosure rules. Run the Azure automation, verify the public URL and add real deployment evidence. Record the final 3-5 minute demonstration showing the interface, explanations, source repository and deployed service. Upload the reviewed PDF, source ZIP or repository link, dataset/attribution and actual video to Moodle.
