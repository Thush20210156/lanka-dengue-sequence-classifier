"""Deterministic descriptor extraction from public dengue RNA sequences (DNA alphabet)."""
from itertools import product
import re
import numpy as np
KMER_NAMES=[''.join(p) for p in product('ACGT',repeat=2)]
# Frequencies sum to one, so omit TT to remove exact linear dependence.
FEATURES=[f'di_{k}' for k in KMER_NAMES if k!='TT']
MIN_LENGTH=10000
MAX_LENGTH=12000
MAX_AMBIGUITY=.01

def clean_sequence(text):
    lines=text.strip().splitlines()
    headers=[line for line in lines if line.startswith('>')]
    if len(headers)>1:raise ValueError('Submit one genome at a time, not multiple FASTA records.')
    seq=''.join(line.strip() for line in lines if not line.startswith('>')).upper()
    seq=re.sub(r'\s+','',seq).replace('U','T')
    if set(seq)-set('ACGTRYSWKMBDHVN'):raise ValueError('Sequence contains invalid nucleotide symbols.')
    if not MIN_LENGTH<=len(seq)<=MAX_LENGTH:raise ValueError(f'Expected a near-complete genome of {MIN_LENGTH}-{MAX_LENGTH} bases.')
    ambiguity=sum(c not in 'ACGT' for c in seq)/len(seq)
    if ambiguity>MAX_AMBIGUITY:raise ValueError('More than 1% of bases are ambiguous.')
    return seq

def describe(seq):
    seq=clean_sequence(seq)
    counts={k:0 for k in KMER_NAMES}
    for i in range(len(seq)-1):
        pair=seq[i:i+2]
        if pair in counts:counts[pair]+=1
    total=sum(counts.values())
    if not total:raise ValueError('No unambiguous adjacent nucleotide pairs.')
    return {f'di_{k}':counts[k]/total for k in KMER_NAMES if k!='TT'}
