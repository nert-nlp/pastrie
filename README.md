# PASTRIE
[![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

Official release of the corpus described in the paper:

Michael Kranzlein, Emma Manning, Siyao Peng, Shira Wein, Aryaman Arora, and Nathan Schneider (2020).
**PASTRIE: A Corpus of Prepositions Annotated with Supersense Tags in Reddit International English** [[link](https://www.aclweb.org/anthology/2020.law-1.10/)].
_Proceedings of the 14th Linguistic Annotation Workshop_.

---

## Overview
PASTRIE is a corpus of English data from Reddit annotated with preposition supersenses from the [SNACS inventory](https://arxiv.org/abs/1704.02134).

While the data in PASTRIE is in English, it was produced by presumed speakers of four L1s:
- English
- French
- German
- Spanish

For details on how L1s were identified, see section 3.1 of [Rabinovich et al. (2018)](https://www.aclweb.org/anthology/Q18-1024.pdf).

### Annotation Example
Below is an example sentence from the corpus, where annotation targets are bolded and preposition supersenses are annotated with the notation SceneRole↝Function. Together, a scene role and function are known as a [construal](https://www.aclweb.org/anthology/S17-1022.pdf).

![](annotation_example.svg)

---

## Data Formats
PASTRIE is released in the following formats. We expect that most projects will be best served by one of the JSON formats.

- [`.conllulex`](https://github.com/nert-nlp/streusle/blob/master/CONLLULEX.md): the 19-column CoNLL-U-Lex format originally used for [STREUSLE](https://github.com/nert-nlp/streusle).
- [`.json`](https://github.com/nert-nlp/streusle/blob/master/CONLLULEX.md#remarks): a JSON representation of the CoNLL-U-Lex that does not require a CoNLL-U-Lex parser.
- [`.govobj.json`](https://github.com/nert-nlp/streusle/blob/master/govobj.py): an extended version of the JSON representation that contains information about each preposition's syntactic parent and object.

PASTRIE mostly follows [STREUSLE](https://github.com/nert-nlp/streusle) with respect to the data format and SNACS annotation practice. Primary differences in the annotations are:
- Lemmas, part-of-speech tags, and syntactic dependencies aim to follow the UD standard in both cases. They are gold in STREUSLE, versus automatic with some manual corrections in PASTRIE.
  * The PASTRIE `text` field for each sentence is tokenized, whereas in STREUSLE/most UD corpora it is the raw source text.
  * PASTRIE does not group together base+clitic combinations, whereas STREUSLE does (_multiword tokens_—where a single orthographic word contains multiple syntactic words).
  * PASTRIE lacks morphological features and enhanced dependencies.
- Multiword expression annotations in PASTRIE are limited to expressions containing a preposition. Depending on the syntactic head, the expression may or may not have a SNACS supersense.
  * Verbal multiword expressions in PASTRIE are not subtyped in the lexcat; they all have a lexcat of `V`.
- Noun and verb expressions in PASTRIE do not have supersense labels.

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg
