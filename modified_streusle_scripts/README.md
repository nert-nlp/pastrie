These scripts were used to convert PASTRIE's original release format, a sparse form of CONLLULEX, into a more compliant form of CONLLULEX. Usage was like so:

```
python enrich.py
python conllulex2json.py ../corpus.conllulex > ../corpus.json
python govobj.py ../corpus.json > ../corpus.govobj.json
```

We have since removed the legacy format of PASTRIE from the repo. If you want to see it, go back in the repo's history, e.g.: https://github.com/nert-nlp/pastrie/tree/0f6ba1e04f2b232646dfb9178b99d2ef641ddf1a
