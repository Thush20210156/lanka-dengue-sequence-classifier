"""Check provenance, feature extraction, leakage boundaries, metrics and real app submissions."""
import gzip,json,hashlib
from io import StringIO
from Bio import SeqIO
import numpy as np,pandas as pd,joblib
from sklearn.metrics import accuracy_score,f1_score
from streamlit.testing.v1 import AppTest
from features import FEATURES,describe,clean_sequence
from train import ROOT,LABELS

def main():
    df=pd.read_csv(ROOT/'data/sri_lanka_dengue_features.csv').set_index('accession');meta=json.loads((ROOT/'results/metrics.json').read_text());s=json.loads((ROOT/'results/split_accessions.json').read_text())
    sets=[set(s[k]) for k in ['train','validation','test']]
    assert not(sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2]);assert set.union(*sets)==set(df.index)
    for a,b in [(0,1),(0,2),(1,2)]:
        for col in ['group_id','sequence_sha256']:
            assert not set(df.loc[list(sets[a]),col])&set(df.loc[list(sets[b]),col])
    assert len(df)==383 and df.country.str.split(':').str[0].eq('Sri Lanka').all()
    assert set(df.serotype)==set(LABELS)
    text=gzip.decompress((ROOT/'data/sri_lanka_dengue.fasta.gz').read_bytes()).decode();seqs={r.id:str(r.seq) for r in SeqIO.parse(StringIO(text),'fasta')}
    for acc,seq in seqs.items():
        assert hashlib.sha256(seq.encode()).hexdigest()==df.loc[acc,'sequence_sha256']
        assert np.allclose(list(describe(seq).values()),df.loc[acc,FEATURES].astype(float).values)
        assert describe('>header can contain any label\n'+seq)==describe(seq)
    for bad in ['ACGT','>one\nAAAA\n>two\nCCCC','Z'*10500,'N'*10500]:
        try:clean_sequence(bad)
        except ValueError:pass
        else:raise AssertionError('Invalid input accepted')
    predictions=pd.read_csv(ROOT/'results/test_predictions.csv').set_index('accession').loc[s['test']]
    model=joblib.load(ROOT/'results/model.joblib');actual=df.loc[s['test'],'serotype'];p=model.predict(df.loc[s['test'],FEATURES])
    assert np.array_equal(p,predictions.predicted.to_numpy())
    assert accuracy_score(actual,p)==meta['test']['accuracy']
    assert f1_score(actual,p,average='macro',labels=LABELS)==meta['test']['macro_f1']
    probs=model.predict_proba(df.loc[s['test'],FEATURES]);assert np.allclose(probs,predictions[['prob_'+c for c in model.classes_]])
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run();assert not app.exception,app.exception
    for label in LABELS:
        example=df.loc[s['test']].query('serotype == @label').index[0]
        app.selectbox[0].select(example).run();app.button[0].click().run();assert not app.exception,app.exception;assert len(app.metric)==1
    app.radio[0].set_value('Paste a known dengue genome').run();app.text_area[0].set_value('ACGT').run();app.button[0].click().run();assert len(app.error)==1
    app.text_area[0].set_value(next(iter(seqs.values()))).run();app.button[0].click().run();assert not app.exception and len(app.metric)==1
    print('PASS: 383 local records, sequence hashes/descriptors, label-free FASTA headers, disjoint accession/group/hash splits, invalid input rejection, saved metrics/probabilities, four serotype examples and pasted-sequence UI.')
if __name__=='__main__':main()
