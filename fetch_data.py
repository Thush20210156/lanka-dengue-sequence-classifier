"""Intentionally refresh a public query snapshot. Never called by the app or training."""
from pathlib import Path
import gzip,hashlib,json,time
import requests
ROOT=Path(__file__).resolve().parent
QUERY='dengue[All Fields] AND "Sri Lanka"[All Fields] AND 9000:12000[SLEN] AND ("1800/01/01"[PDAT] : "2026/11/02"[PDAT])'
BASE='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
def main():
    out=ROOT/'data/raw';out.mkdir(parents=True,exist_ok=True)
    session=requests.Session()
    response=session.get(BASE+'esearch.fcgi',params={'db':'nuccore','term':QUERY,'retmode':'json','retmax':10000,'tool':'local_bioinformatics_coursework'},timeout=90)
    response.raise_for_status();search=response.json();ids=search['esearchresult']['idlist']
    if len(ids)!=int(search['esearchresult']['count']):raise RuntimeError('Query exceeds retrieval limit; paginate rather than silently truncate.')
    if not ids:raise RuntimeError('No records returned; preserve the existing snapshot and inspect the query.')
    manifest={'query':QUERY,'retrieved_date':time.strftime('%Y-%m-%d',time.gmtime()),'query_publication_cutoff':'2026-11-02','count':len(ids),'batches':[]}
    texts=[]
    for start in range(0,len(ids),75):
        target=out/f'batch_{start:04}.gb';time.sleep(.5)
        # Always fetch current IDs. Reusing an old numbered batch after a changed search can mislabel provenance.
        for attempt in range(3):
            try:
                response=session.get(BASE+'efetch.fcgi',params={'db':'nuccore','id':','.join(ids[start:start+75]),'rettype':'gbwithparts','retmode':'text','tool':'local_bioinformatics_coursework'},timeout=120)
                response.raise_for_status()
                if not response.text.startswith('LOCUS'):raise RuntimeError('Unexpected non-GenBank response.')
                payload=response.content;target.write_bytes(payload);texts.append(payload);break
            except (requests.RequestException,RuntimeError):
                if attempt==2:raise
                time.sleep(3)
        manifest['batches'].append({'file':target.name,'sha256':hashlib.sha256(payload).hexdigest()})
        print(target.name,len(payload),flush=True)
    # Replace the committed snapshot only after the entire retrieval has succeeded.
    snapshot=ROOT/'data/genbank_snapshot.gb.gz';temporary=snapshot.with_suffix('.tmp')
    temporary.write_bytes(gzip.compress(b''.join(texts),mtime=0));temporary.replace(snapshot)
    manifest['snapshot_sha256']=hashlib.sha256(snapshot.read_bytes()).hexdigest()
    manifest['download_access']='Public NCBI E-utilities; no login, restricted account or API key required.'
    (out/'search.json').write_text(json.dumps(search,indent=2));(out/'manifest.json').write_text(json.dumps(manifest,indent=2));(ROOT/'data/raw_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Snapshot refreshed. Recompile, retrain, verify, and update the report before using new results.')
if __name__=='__main__':main()
