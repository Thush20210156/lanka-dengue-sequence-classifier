"""Public-sequence demonstration frontend. No submitted sequence is written to disk."""
from pathlib import Path
import gzip,json
import joblib,numpy as np,pandas as pd
import streamlit as st
from Bio import SeqIO
from io import StringIO
from features import FEATURES,describe
ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Lanka Dengue Sequence Explorer',page_icon='🧬',layout='wide')
st.markdown('<style>.block-container{max-width:1150px;padding-top:2rem} h1{color:#12465b}</style>',unsafe_allow_html=True)
st.caption('SRI LANKAN BIOINFORMATICS • PUBLIC GENBANK DATA')
st.title('Lanka Dengue Sequence Explorer')
st.write('Explore dengue serotype classification from near-complete viral genome composition.')
st.info('Research and teaching prototype. This model assumes the input is already a dengue genome; it cannot diagnose dengue, assess severity, detect another pathogen or replace a validated typing assay.')
@st.cache_resource
def resources():
    return joblib.load(ROOT/'results/model.joblib'),json.loads((ROOT/'results/metrics.json').read_text())
@st.cache_data
def genomes():
    text=gzip.decompress((ROOT/'data/sri_lanka_dengue.fasta.gz').read_bytes()).decode()
    return {r.id:str(r.seq) for r in SeqIO.parse(StringIO(text),'fasta')}
model,meta=resources();df=pd.read_csv(ROOT/'data/sri_lanka_dengue_features.csv');seqs=genomes()
splits=json.loads((ROOT/'results/split_accessions.json').read_text());examples=df[df.accession.isin(splits['test'])].sort_values(['serotype','accession'])
tab1,tab2,tab3=st.tabs(['Predict a sequence','Evaluation and explanations','Data provenance'])
with tab1:
    mode=st.radio('Input source',['Public held-out example','Paste a known dengue genome'],horizontal=True)
    if mode=='Public held-out example':
        accession=st.selectbox('Accession.version (known label shown for comparison)',examples.accession.tolist(),format_func=lambda a:f"{a} | recorded {df.set_index('accession').loc[a,'serotype']}")
        sequence=seqs[accession]
        st.caption(f'{len(sequence):,} bases | Sri Lankan source metadata | labels and accession are excluded from model input')
    else:
        sequence=st.text_area('One FASTA record or plain sequence',height=160,placeholder='Paste a public positive-sense dengue RNA genome (10,000-12,000 bases). U is converted to T.')
        st.caption('Use a public viral sequence. Do not paste patient identifiers or private biological records. Input is processed in this app session and is not saved by the application.')
    if st.button('Classify and explain',type='primary'):
        try:
            values=describe(sequence);X=pd.DataFrame([values],columns=FEATURES);probs=model.predict_proba(X)[0];ranking=np.argsort(probs)[::-1];pred=model.classes_[ranking[0]]
            st.subheader(f'Predicted serotype: {pred}')
            st.metric('Model probability (not calibrated)',f'{probs[ranking[0]]:.1%}')
            st.bar_chart(pd.DataFrame({'serotype':model.classes_,'probability':probs}).set_index('serotype'))
            st.caption('All four classes are known dengue serotypes. High probability is not proof that the input belongs to dengue or that the result is correct.')
            dev=df[df.accession.isin(splits['train']+splits['validation'])][FEATURES]
            outside=[f for f in FEATURES if not dev[f].min()<=values[f]<=dev[f].max()]
            if outside:st.warning('Some descriptor values fall outside the development range: '+', '.join(outside)+'. This is only a simple range flag, not a validated out-of-distribution detector.')
            with st.expander('Sequence-derived descriptors',expanded=False):st.dataframe(X.T.rename(columns={0:'frequency'}))
            # Sequential replacement decomposition. Explicitly not SHAP or causal effects.
            reference=dev.median().to_frame().T;ci=list(model.classes_).index(pred);base=float(model.predict_proba(reference)[0,ci]);last=base;effects=[]
            for f in FEATURES:
                reference[f]=values[f];current=float(model.predict_proba(reference)[0,ci]);effects.append(current-last);last=current
            assert np.isclose(base+sum(effects),probs[ci])
            st.subheader('Local sensitivity: changes from a reference')
            st.write(f'The development-median reference gives {base:.1%} probability for {pred}. Bars replace descriptors in the displayed order. They sum to the final probability minus the reference.')
            st.bar_chart(pd.DataFrame({'descriptor':FEATURES,'probability change':effects}).set_index('descriptor'))
            st.caption('This is an order-dependent reference-replacement path, not SHAP. Frequencies are correlated and constrained, so intermediate combinations may not describe a real genome. The bars do not establish causal biology.')
        except ValueError as exc:st.error(str(exc))
with tab2:
    st.subheader('Frozen held-out evaluation')
    st.dataframe(pd.DataFrame({'QDA':meta['test'],'Majority baseline':meta['baseline_test'],'Shuffled-label control':meta['negative_control_test']}))
    st.write('77 test genomes; exact duplicate genomes and identical isolate IDs never cross training, validation and test partitions. Related outbreak strains can still cross partitions. Perfect test scores do not establish perfect generalization.')
    c1,c2=st.columns(2)
    with c1:st.image(str(ROOT/'results/confusion_matrix.png'))
    with c2:st.image(str(ROOT/'results/roc.png'))
    st.subheader('Global permutation feature importance')
    st.image(str(ROOT/'results/importance.png'))
    st.caption('Mean macro-F1 decrease across 30 shuffles; bars show shuffle SD. Small individual effects can reflect redundancy and the ceiling score. Correlated composition features make shuffled combinations difficult to interpret.')
    st.image(str(ROOT/'results/pdp.png'))
    st.caption('PDP averages a DENV-1 model response across development rows. It is not causal, and substituted descriptor combinations may be unrealistic.')
    st.write('Supplementary later-year check: train through 2018, test from 2019. Accuracy 99.25%; three observed serotypes only. No post-2018 DENV-4 records are available in this snapshot.')
with tab3:
    st.subheader('A compiled local dataset, not synthetic observations')
    st.write('383 public GenBank genomes with source country Sri Lanka; 51 DENV-1, 216 DENV-2, 90 DENV-3 and 26 DENV-4. The source studies collected the biological samples; this project compiles records and derives 15 dinucleotide frequencies.')
    st.dataframe(df[['accession','country','collection_year','serotype','source_url']],hide_index=True)
    st.download_button('Download curated feature dataset',data=(ROOT/'data/sri_lanka_dengue_features.csv').read_bytes(),file_name='sri_lanka_dengue_features.csv',mime='text/csv')
    st.markdown('[Source repository](https://github.com/Thush20210156/lanka-dengue-sequence-classifier) · [GenBank overview and usage](https://www.ncbi.nlm.nih.gov/genbank/)')
    st.caption('No restricted database was used. See data/README.md and the record audit for provenance, filters and source attribution.')
