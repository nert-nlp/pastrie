#!/usr/bin/env python3
"""
Looks up raw source text in the reddit-supersenses repo and incorporates it 
into the pastrie.conllulex file.
This is a bit complicated as sentence boundaries are not entirely consistent.
"""

import sys, fileinput
from modified_streusle_scripts.helpers import sentences

LANGS = ['english', 'french', 'german', 'spanish']

def clean(ln):
    return ln.strip().replace('&gt;','>').replace('&lt;','<').replace('&amp;','&')

# Load raw sentences. They don't have IDs, so index them in a tokenization-invariant way by removing spaces

nospaces2raw = {}

nospaces2next = {}  # for oversegmented cases, map to the next one

SEGMENT_THESE = ['---', 'Really?', 'really??', 'What?', 'Soybeanexplosion sir!', 'are you serious?']


nosp_prev = None
for lg in LANGS:
    for ln in fileinput.input(f'reddit-supersenses/data/raw/{lg}.txt'): # reddit-supersenses is a symlink to the repo with sources
        nosp = clean(ln).replace(' ','')
        if nosp in nospaces2raw:
            assert nospaces2raw[nosp] == clean(ln),(nosp,ln)
        
        raw = clean(ln)
        # split off initial prefixes that recur as separate sentences
        for s in SEGMENT_THESE:
            if raw.startswith(s):
                snosp = s.replace(' ','')
                nospaces2raw[snosp] = s
                nospaces2raw[nosp[len(snosp):]] = raw[len(s):].strip()
                if nosp_prev:
                    nospaces2next[nosp_prev] = snosp
                    nospaces2next[snosp] = nosp[len(snosp):]
#                     if s=='Soybeanexplosion sir!':
#                         assert False,('@@@', snosp,nosp[len(snosp):])
                nosp_prev = nosp[len(snosp):]
                break
        else:   # nothing to split off
            nospaces2raw[nosp] = clean(ln)
            if nosp_prev:
#                 if nosp_prev.startswith('Andwhatdowesay'):
#                     assert False,('@#@', nosp_prev, nosp)
                nospaces2next[nosp_prev] = nosp
            nosp_prev = nosp

for sent in sentences('pastrie.conllulex'):
    sentid, = [m.split(' = ',1)[1] for m in sent.meta if m.startswith('# sent_id = ')]
    nosp = ''.join(tok.word for tok in sent.tokens)
    assert ' ' not in nosp,(sentid,nosp,len(sent.tokens))
    if nosp not in nospaces2raw:
        # Check whether raw sentence is undersegmented
        prefixmatches = [k for k in nospaces2raw if k.startswith(nosp)]
        if prefixmatches:
            # split the raw string into 2 sentences
            if len(prefixmatches)>1:
                assert False,(nosp,prefixmatches)
            nospfull, = prefixmatches
            nNonspace = 0
            rawfull = nospaces2raw[nospfull]
            i = 0
            while i < len(rawfull):
                if rawfull[i]!=' ':
                    nNonspace += 1
                    if nNonspace==len(nosp):
                        break
                i += 1
            raw, raw2 = rawfull[:i+1], rawfull[i+1:].strip()
            nosp2 = nospfull[len(nosp):]
            nospaces2raw[nosp2] = raw2
            if 'Andwhatdowesayto' in nospfull:
                print('$$$', (nospfull,nosp,nosp2,nospaces2raw[nospfull]), file=sys.stderr)
            assert nospfull in nospaces2next
            nospaces2next[nosp2] = nospaces2next[nospfull]
            nospaces2next[nosp] = nosp2
        else:   # Check whether raw sentence is oversegmented
            prefixmatches = [k for k in nospaces2raw if nosp.startswith(k)]
            if len(prefixmatches)!=1:
                assert False,(sentid,nosp,prefixmatches)
            
            prefix, = prefixmatches
            nNonspace = 0
            if prefix not in nospaces2next:
                assert False,(sentid,nosp,prefix)
            nospnext = nospaces2next[prefix]
            nospcombined = prefix+nospnext
            raw = nospaces2raw[prefix] + ' ' + nospaces2raw[nospnext]  # assume there's a space?
            if len(nospcombined)<len(nosp):
                nospnext = nospaces2next[nospnext]
                nospcombined += nospnext
                raw += ' ' + nospaces2raw[nospnext]
            assert nospcombined==nosp,(sentid,nosp,prefix,nospnext,raw)
            print(sentid, nosp, raw, file=sys.stderr)
        
    else:
        raw = nospaces2raw[nosp]
    for entry in sent.meta:
        if entry.startswith('# text = '):
            assert raw.replace(' ','')==nosp,(nosp,raw)
            print('# text =', raw)
        else:
            print(entry)
    for tok in sent.tokens:
        print(tok.orig)
    print()
    prev_nosp = nosp
