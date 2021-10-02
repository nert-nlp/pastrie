#!/usr/bin/env python3
"""
Adapted from STREUSLE, this script fetches information from automatic UD parser output 
and incorporates it into the pastrie.conllulex file. 
This is to correct for problems in the wordforms (e.g. missing token-initial apostrophes) 
and lack of morphological features.
Used for FORM, FEATS, MISC columns only; PASTRIE should be more correct for other columns. 
"""
import sys, re, json, fileinput, glob
from collections import Counter

from helpers import sentences

# requires reddit-supersenses symlink (repo with source files): retok branch
UDDIR='reddit-supersenses/data/conllu_with_id/all' # all 4 languages: english spanish french german

CONLLULEX=sys.argv[1]

# load UD data

ud = {}
udDocs = glob.glob(f'{UDDIR}/*.conllu')
docid = None
for udDoc in udDocs:
    for sent in sentences(udDoc):
        docid = sent.meta_dict.get('new_doc id', docid)
        if '-' not in sent.meta_dict['sent_id'] and '.' not in sent.meta_dict['sent_id']:
            # this sent_id is just within the document. concatenate it to the docid
            sent.meta_dict['sent_id'] = f"{docid}-{int(sent.meta_dict['sent_id']):02}"
        ud[sent.meta_dict['sent_id']] = (udDoc, sent)

FORM = 1
LEMMA = 2
UPOS = 3
XPOS = 4
FEATS = 5
MISC = 9
formChanges = Counter()
featsChanges = Counter()
miscChanges = Counter()
nSentsChanged = nToksChanged = nToksAdded = nFormsChanged = nTagsChanged = nLemmasChanged = nMorphChanged = nDepsChanged = nEDepsChanged = nAutoLemmaFix = nMiscChanged = 0
for sent in sentences(CONLLULEX):
    sentid = sent.meta_dict['sent_id']
    assert sentid.startswith(('english-','spanish-','french-','german-'))
    shortsentid = sentid[sentid.index('-')+1:]
    newudDoc, newudsent = ud[shortsentid]
    if len(sent.tokens)!=len(newudsent.tokens):
        print(f"Attempting to clean up tokenization for sentence {shortsentid}", file=sys.stderr)
        # PASTRIE: a lot of these are due to ">" being encoded as "&gt;" and then parsed as 2 tokens, "&gt" + ";"
        # This was manually corrected. So in the parser output (newudsent), ignore "&gt" tokens if it changes the tokenization
        newudsent.tokens = [t for t in newudsent.tokens if t.word!='&gt']
        if len(sent.tokens)!=len(newudsent.tokens):
            print(f"Number of tokens for sentence {shortsentid} has changed: {len(sent.tokens)}, {len(newudsent.tokens)}", file=sys.stderr)
            assert False
    # ensure the offsets start from 1 and omit tokens deleted above
    for i,t in enumerate(newudsent.tokens, start=1):
        assert int(t.offset),t.offset
        t.offset = str(i)
    sentChanged = False
    oldudtoks = {t.offset: t for t in sent.tokens}
    assert len(oldudtoks)==len(sent.tokens),(shortsentid,len(oldudtoks),len(sent.tokens))
#     if shortsentid=='5d698c8b-4448-0030-f3c6-68b114ed2049-01':
#         assert False,{x: y.word for x,y in oldudtoks.items()}

    # ensure UD sentence metadata lines are present (before STREUSLE-specific metadata lines)
    assert len(newudsent.meta)<len(sent.meta),(newudsent.meta,sent.meta)
    if sent.meta[:len(newudsent.meta)] != newudsent.meta:
        # incorporate new UD metadata
        for entry in newudsent.meta:
            if entry.startswith('# new_doc id = '):
                entry = f"# newdoc id = {sentid[:sentid.rindex('-')]}"  # per https://universaldependencies.org/format.html it should be newdoc, not new_doc
            elif entry.startswith('# sent_id = '):   # offset within doc; ignore
                continue
            print(entry)
        for entry in sent.meta:
            if entry not in newudsent.meta: # STREUSLE-specific (assumes UD lines already in STREUSLE are unchanged in new UD)
                print(entry)
    else:
        print(*sent.meta, sep='\n')

    for i,newudtok in enumerate(newudsent.tokens, start=1):
        tok = oldudtoks.get(str(i))
        oldud = '\t'.join(tok.orig.split('\t')[:10]) if tok else None   # newud may be a new ellipsis node
        newud = '\t'.join(newudtok.orig.split('\t')[:10])
#         if shortsentid=='5d698c8b-4448-0030-f3c6-68b114ed2049-01':
#             assert False,(tok.offset,tok.word,newudtok.offset,newudtok.word,oldud,newud)
        if oldud!=newud and (oldud is None or oldud[oldud.index('\t'):]!=newud[newud.index('\t'):]):   # permit some token renumbering
            if tok:
            
                
            
#                 if tok.ud_pos=='ADJ' and newudtok.ud_pos=='VERB':
#                     print(f'ADJ/VERB issue: need to revert to VERB in {newudDoc}: {tok.word}', file=sys.stderr)

                oldudparts = oldud.split('\t')
                newudparts = oldudparts[:]  # update specific fields below

                if tok.word!=newudtok.word:
                    if tok.word=='>':   # keep "old" form
                        newudparts[FORM] = tok.word
                    else:
                        nFormsChanged += 1
                        newudparts[FORM] = newudtok.word
                        formChanges[(oldudparts[FORM],newudparts[FORM])] += 1
                        print(oldud,newud, sep='\n', file=sys.stderr)
                        if (oldudparts[FORM],newudparts[FORM])==('&',';'):
                            assert False,shortsentid
                if tok.morph!=newudtok.morph:
                    nMorphChanged += 1
                    newudparts[FEATS] = newudtok.morph
                    print(oldud,newud, sep='\n', file=sys.stderr)
                    assert oldudparts[FEATS]=='_' or oldudparts[FEATS] in newudparts[FEATS],(oldudparts[FEATS],newudparts[FEATS],shortsentid)
                    featsChanges[(oldudparts[FEATS],newudparts[FEATS])] += 1
                if tok.misc!=newudtok.misc:
                    nMiscChanged += 1
                    newudparts[MISC] = newudtok.misc
                    assert oldudparts[MISC]=='_',(oldudparts[MISC],newudparts[MISC])
                    miscChanges[(oldudparts[MISC],newudparts[MISC])] += 1
                    print(oldud,newud, sep='\n', file=sys.stderr)
                
#                 if shortsentid=='5d698c8b-4448-0030-f3c6-68b114ed2049-01':
#                         assert False,('_____',tok.offset,tok.word,newudtok.offset,newudtok.word,oldudparts,newudparts)
                
                if newudparts != oldudparts:
                    assert newudparts[0]==oldudparts[0] # offset is correct in oldudparts
                    nToksChanged += 1
                    sentChanged = True
                    newud = '\t'.join(newudparts)
                else:   # no change to the token, but offsets may be incorrect in the newud, so use oldud
                    newud = oldud
                    
                # count but don't actually change the other things
                if tok.ud_pos!=newudtok.ud_pos or tok.ptb_pos!=newudtok.ptb_pos:
                    nTagsChanged += 1
                    #print(oldud,newud, sep='\n', file=sys.stderr)
                elif tok.head!=newudtok.head or tok.deprel!=newudtok.deprel:
                    #print(oldud,newud, sep='\n', file=sys.stderr)
                    nDepsChanged += 1
                elif tok.lemma!=newudtok.lemma:
                    #print(oldud,newud, sep='\n', file=sys.stderr)
                    nLemmasChanged += 1
#                 elif tok.morph!=newudtok.morph:
#                     nMorphChanged += 1
                elif tok.edeps!=newudtok.edeps:
                    nEDepsChanged += 1
#                 elif tok.misc!=newudtok.misc:
#                     nMiscChanged += 1
#                 else:
#                     print(oldud, newud, sep='\n', file=sys.stderr)
#                     assert False,'Unexpected change in UD (see last 2 data lines above)'
            else:
                print(oldud,newud, sep='\n', file=sys.stderr)
                assert False,shortsentid
                nToksAdded += 1
        else:   # no change to the token, but offsets may be incorrect in the newud, so use oldud
            newud = oldud

        if tok:
            streusle = tok.orig.split('\t')[10:]
            # old_strong_lemma = streusle[2]
#             if old_strong_lemma!='_' and tok.lemma!=newudtok.lemma and old_strong_lemma==tok.lemma:
#                 streusle[2] = newudtok.lemma
#                 nAutoLemmaFix += 1
        else:
            streusle = '_'*9

        streusle = '\t'.join(streusle)
        print(f'{newud}\t{streusle}')
        # NOTE: lemmas updated in column 3 need to be manually fixed in the STREUSLE columns
        # These will be caught by running conllulex2json.py
    if sentChanged:
        nSentsChanged += 1
    print()

print('FORM changes:', formChanges, file=sys.stderr)
print('FEATS changes:', featsChanges, file=sys.stderr)
print('MISC changes:', miscChanges, file=sys.stderr)
print(f'{nToksAdded} new tokens', file=sys.stderr)
print(f'Changes implemented in {nToksChanged} tokens ({nSentsChanged} sentences): {nFormsChanged} wordforms + {nMorphChanged} morph features + {nMiscChanged} misc features', file=sys.stderr)
print(f'Differences ignored: {nTagsChanged} tags + {nDepsChanged} additional deps + {nLemmasChanged} additional lemmas + {nEDepsChanged} additional enhanced deps)', file=sys.stderr)
#print(f'{nAutoLemmaFix} STREUSLE single-word lemmas were automatically fixed, but multiword lemmas may need to be fixed manually', file=sys.stderr)
