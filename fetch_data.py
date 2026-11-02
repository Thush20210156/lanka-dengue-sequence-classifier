"""Download a dated NCBI query snapshot. Re-run intentionally; never during app startup."""
from pathlib import Path
import requests,json,time,hashlib,gzip
ROOT=Path(__file__).resolve().parent
QUERY='dengue[All Fields] AND "Sri Lanka"[All Fields] AND 9000:12000[SLEN] AND ("1800/01/01"[PDAT] : "2026/11/02"[PDAT])'
BASE='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
def main():
 out=ROOT/'data/raw';out.mkdir(parents=True,exist_ok=True)
 session=requests.Session();r=session.get(BASE+'esearch.fcgi',params={'db':'nuccore','term':QUERY,'retmode':'json','retmax':10000,'tool':'local_bioinformatics_coursework'},timeout=90);r.raise_for_status();search=r.json();ids=search['esearchresult']['idlist'];assert len(ids)==int(search['esearchresult']['count'])
 (out/'search.json').write_text(json.dumps(search,indent=2));manifest={'query':QUERY,'retrieved_date':'2026-11-02','count':len(ids),'batches':[]}
 print('Records:',len(ids),flush=True)
 for start in range(0,len(ids),75):
  time.sleep(.5);target=out/f'batch_{start:04}.gb'
  if not target.exists():
   for attempt in range(3):
    try:
     resp=session.get(BASE+'efetch.fcgi',params={'db':'nuccore','id':','.join(ids[start:start+75]),'rettype':'gbwithparts','retmode':'text','tool':'local_bioinformatics_coursework'},timeout=120);resp.raise_for_status();assert resp.text.startswith('LOCUS');target.write_text(resp.text);break
    except Exception:
     if attempt==2:raise
     time.sleep(3)
  manifest['batches'].append({'file':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()});print(target.name,target.stat().st_size,flush=True)
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
 with gzip.GzipFile(filename=str(ROOT/'data/genbank_snapshot.gb.gz'),mode='wb',mtime=0) as stream:
  for batch in manifest['batches']:stream.write((out/batch['file']).read_bytes())
 manifest['snapshot_sha256']=hashlib.sha256((ROOT/'data/genbank_snapshot.gb.gz').read_bytes()).hexdigest()
 manifest['download_access']='Public NCBI E-utilities; no login required.'
 (ROOT/'data/raw_manifest.json').write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
