"""Compile genuine local public records; never synthesize observations or labels."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,gzip,io,lzma
import pandas as pd
from Bio import SeqIO
from features import FEATURES,describe,clean_sequence
ROOT=Path(__file__).resolve().parent

def label_from_record(record,q):
    # Use explicit source annotation first, then explicit organism/definition wording.
    labels=set()
    for value in q.get('serotype',[]):
        match=re.fullmatch(r'(?:DENV[- ]?)?([1-4])',value.strip(),re.I)
        if match: labels.add('DENV-'+match[1])
    for text in [q.get('organism',[''])[0],record.description]:
        for match in re.finditer(r'dengue(?: virus)?(?: serotype| type)[ -]?([1-4])\b',text,re.I):labels.add('DENV-'+match[1])
    if len(labels)!=1:return None
    return labels.pop()

def main():
    rows=[];audit=[];seen=set();sequences=[]
    sources=[ROOT/'data/genbank_snapshot.gb.xz']
    for f in sources:
        handle=io.StringIO(lzma.decompress(f.read_bytes()).decode()) if f.suffix=='.xz' else f
        for record in SeqIO.parse(handle,'genbank'):
            if record.id in seen:continue
            seen.add(record.id)
            q=next(x.qualifiers for x in record.features if x.type=='source')
            country=q.get('geo_loc_name',q.get('country',['']))[0]
            org=q.get('organism',[''])[0]
            reason=''
            label=label_from_record(record,q)
            if country.split(':')[0].strip()!='Sri Lanka':reason='source country is not Sri Lanka'
            elif 'dengue' not in org.lower():reason='not dengue virus'
            elif not label:reason='no unambiguous explicit serotype annotation'
            try:seq=clean_sequence(str(record.seq))
            except ValueError as exc:
                seq='';reason=reason or str(exc)
            audit.append({'accession':record.id,'included':not bool(reason),'reason':reason,'country':country,'organism':org,'length':len(record)})
            if reason:continue
            date=q.get('collection_date',[''])[0];year=re.search(r'\b(?:19|20)\d{2}\b',date)
            refs=record.annotations.get('references',[])
            pubmed=sorted({r.pubmed_id for r in refs if r.pubmed_id})
            row={'accession':record.id,'country':country,'collection_year':int(year[0]) if year else None,'serotype':label,'length':len(seq),'ambiguous_fraction':sum(c not in 'ACGT' for c in seq)/len(seq),'isolate':q.get('isolate',[''])[0],'study_pubmed':';'.join(pubmed),'sequence_sha256':hashlib.sha256(seq.encode()).hexdigest(),'source_url':f'https://www.ncbi.nlm.nih.gov/nuccore/{record.id}',**describe(seq)}
            rows.append(row);sequences.append((record.id,seq))
    df=pd.DataFrame(rows).sort_values('accession').reset_index(drop=True)
    # Union exact genome duplicates and repeated isolate identifiers. Group remains indivisible.
    parent=list(range(len(df)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(a,b):parent[find(a)]=find(b)
    for col in ['sequence_sha256','isolate']:
        first={}
        for i,v in enumerate(df[col]):
            if not v:continue
            if v in first:union(i,first[v])
            else:first[v]=i
    df['group_id']=[f'G{find(i):04}' for i in range(len(df))]
    assert df.groupby('group_id').serotype.nunique().max()==1,'Conflicting labels within a group require manual curation.'
    # Keep all public source records, but split evaluation by group to avoid exact-match leakage.
    df.to_csv(ROOT/'data/sri_lanka_dengue_features.csv',index=False)
    pd.DataFrame(audit).to_csv(ROOT/'data/record_audit.csv',index=False)
    mapping=dict(sequences)
    with (ROOT/'data/sri_lanka_dengue.fasta').open('w') as out:
        for acc in df.accession:
            out.write(f'>{acc}\n');s=mapping[acc]
            out.write('\n'.join(s[i:i+80] for i in range(0,len(s),80))+'\n')
    with gzip.GzipFile(filename=str(ROOT/'data/sri_lanka_dengue.fasta.gz'),mode='wb',mtime=0) as stream:
        stream.write((ROOT/'data/sri_lanka_dengue.fasta').read_bytes())
    summary={'candidate_records':len(seen),'included_records':len(df),'excluded_records':sum(not r['included'] for r in audit),'exclusion_reasons':dict(Counter(r['reason'] for r in audit if r['reason'])),'class_counts':df.serotype.value_counts().to_dict(),'independent_exact_isolate_groups':df.group_id.nunique(),'duplicate_sequence_records':int(df.sequence_sha256.duplicated().sum()),'duplicate_isolate_records':int(df.isolate[df.isolate!=''].duplicated().sum()),'year_min':int(df.collection_year.min()),'year_max':int(df.collection_year.max()),'missing_years':int(df.collection_year.isna().sum()),'features':FEATURES}
    (ROOT/'data/dataset_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
