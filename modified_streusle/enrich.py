from collections import defaultdict

import conllu

from mwerender import render
from tagging import sent_tags


# modified from streusle ----------------------------------------------------------------------
def compute_lexcat(tokNum, smwe, smweGroupToks, ss, lexlemma, poses, rels):
    """
    The lexical category, or LexCat, is the syntactic category of a strong
    lexical expression, which may be a single-word or multiword expression.
    The value of LexCat is determined in part from the UPOS (Universal POS)
    and XPOS (for English, PTB tag), as follows:

    1. If the expression has been annotated as ... the LexCat is ...
        `c    CCONJ
        `j    ADJ
        `r    ADV
        `n    NOUN
        `o    PRON
        `v    VERB
        `d    DISC
        `i    INF
        `a    AUX       (note: the UPOS should usually be AUX)
    2. If the expression has been annotated with a ... supersense, the LexCat is ...
        noun    N
        verb    V
    3. If the expression has been annotated with an adposition supersense or `$:
       a. If XPOS is ... the LexCat is ...
           PRP$     PRON.POSS
           WP$      PRON.POSS
           POS      POSS
           TO       INF.P
          (all `$ tokens should be matched by one of these conditions)
       b. If a multiword expression:
           i. If the last token of the MWE has UPOS of `ADP` or `SCONJ`, LexCat is `P`.
           ii. Otherwise, LexCat is `PP`.
       c. Otherwise, LexCat is `P`.
    4. Other tokens with UPOS of `NOUN`, `VERB`, `ADP`, or XPOS of `POS`, `PRP$`, `WP$`, `TO`: need examination. [N.B. `PART` = `TO` + `POS` + negative markers]
    5. Otherwise, if the UPOS is `PART`, LexCat is `ADV` (negative markers).
    6. Other strong MWEs need examination. Some special cases are handled.
    7. Otherwise, the LexCat is the same as the UPOS.

    The script that performs automatic assignment should have an option to suffix any default (non-human) annotations with `@` and any problematic cases with `!`.
    """
    upos, xpos = poses[tokNum - 1]
    # custom for PASTRIE
    if ss == "??" and upos in ["ADP"] and xpos in ["IN"]:
        return "P"

    if smwe != "_" and not smwe.endswith(":1"):
        # non-initial token in MWE
        return "_"

    # Rule 1
    lc = {
        "`a": "AUX",
        "`c": "CCONJ",
        "`d": "DISC",
        "`i": "INF",
        "`j": "ADJ",
        "`n": "N",
        "`o": "PRON",
        "`r": "ADV",
        "`v": "V",
    }.get(ss)
    if lc is not None:
        return lc

    # Rule 3
    if ss == "`$" or ss == "??" or ss.startswith("p.") or upos == "ADP":
        lc = {
            "PRP$": "PRON.POSS",
            "WP$": "PRON.POSS",
            "POS": "POSS",
            "TO": "INF.P",
        }.get(xpos)
        if lc is not None:
            return lc
        assert ss != "`$"
        if smwe != "_":
            if poses[smweGroupToks[-1] - 1][0] in ("ADP", "SCONJ"):
                return "P"
            return "PP"
        return "P"
    # End rule 3

    # Rule 2
    # Extension to rule 2 made for PASTRIE
    if upos == "AUX":
        return "AUX"
    if upos in ["NOUN", "PROPN"]:
        return "N"
    if upos == "VERB" or xpos[0:2] == "VB":
        return "V"

    if upos == "PART":
        if lexlemma == "to":
            return "INF"
        return "ADV"
    if smwe != "_":
        if upos == "DET":
            if lexlemma in (
                "a lot",
                "a couple",
                "a few",
                "a little",
                "a bit",
                "a number",
                "a bunch",
            ):
                return "DET"
            elif lexlemma in (
                "no one",
                "every one",
                "every thing",
                "each other",
                "some place",
            ):
                return "PRON"
        if upos == "AUX":
            if lexlemma in ("might as well",):
                return "AUX"

        head, rel = rels[tokNum - 1]
        if head in smweGroupToks:
            return compute_lexcat(head, "_", smweGroupToks, ss, lexlemma, poses, rels)
        else:
            assert upos != "X"  # X is used for goeswith (also 'sub <advmod par').
            # In those cases the head should be in the MWE.
        # return "!@"
    return upos


# misc --------------------------------------------------------------------------------


def get_conllulex_tokenlists(conllulex_path):
    fields = tuple(
        list(conllu.parser.DEFAULT_FIELDS)
        + [
            "smwe",  # 10
            "lexcat",  # 11
            "lexlemma",  # 12
            "ss",  # 13
            "ss2",  # 14
            "wmwe",  # 15
            "wcat",  # 16
            "wlemma",  # 17
            "lextag",
        ]
    )  # 18

    with open(conllulex_path, "r", encoding="utf-8") as f:
        return conllu.parse(f.read(), fields=fields)


special_labels = ["`i", "`d", "`c", "`$", "??"]


def read_mwes(sentence):
    """Returns two dicts mapping from smwe/wmwe ID to token IDs"""
    smwes = defaultdict(list)
    wmwes = defaultdict(list)

    for t in sentence:
        if t["smwe"] != "_":
            smwe_id, _ = t["smwe"].split(":")
            smwes[smwe_id].append(t["id"])
        if t["wmwe"] != "_":
            wmwe_id, _ = t["wmwe"].split(":")
            wmwes[wmwe_id].append(t["id"])
    return smwes, wmwes


def get_token(sentence, tid):
    try:
        return [t for t in sentence if str(tid) == str(t['id'])][0]
    except IndexError:
        raise Exception(f"Token with ID {tid} not found in {sentence.metadata['sent_id']}")


# modifications --------------------------------------------------------------------------------
def add_lextag(sentences):
    for sentence in sentences:
        smwes, wmwes = read_mwes(sentence)
        tags = sent_tags(
            len(sentence), sentence, list(smwes.values()), list(wmwes.values())
        )
        for i, (t, tag) in enumerate(zip(sentence, tags)):
            if tag not in ["I_", "i_"]:
                tag += "-" + t["lexcat"]
                if t["ss"] != "_":
                    tag += "-" + t["ss"]
                if t["ss2"] not in ["_", t["ss"]]:
                    tag += "|" + t["ss2"]
            sentence[i]["lextag"] = tag


def add_wlemma(sentences):
    for sentence in sentences:
        _, wmwes = read_mwes(sentence)

        for t in sentence:
            wmwe_tok_ids = ([] if ":" not in t["wmwe"] else wmwes[t["wmwe"].split(":")[0]])
            if len(wmwe_tok_ids) > 0 and str(wmwe_tok_ids[0]) == str(t['id']):
                t['wlemma'] = " ".join([get_token(sentence, tid)['lemma'] for tid in wmwe_tok_ids])


def add_lexcat(sentences):
    for sentence in sentences:
        smwes, _ = read_mwes(sentence)
        poses = [(t["upos"], t["xpos"]) for t in sentence]
        deps = [(t["head"], t["deprel"]) for t in sentence]
        for t in sentence:
            smwe_tok_ids = (
                "_" if ":" not in t["smwe"] else smwes[t["smwe"].split(":")[0]]
            )
            t["lexcat"] = compute_lexcat(
                t["id"], t["smwe"], smwe_tok_ids, t["ss"], t["lexlemma"], poses, deps
            )
            # Check if we had a shorthand anno
            if t['ss'][0] == '`':
                # If it was for `i, force SCONJ+CC pos tags
                if t['ss'] == "`i" and t['form'] == 'for':
                    t['upos'] = "SCONJ"
                    t['xpos'] = "CC"

                if not (t['ss'] == "`$" and t['ss2'] == "`$"):
                    # wipe away the supersense columns
                    t['ss'] = '_'
                    t['ss2'] = '_'


def add_lexlemma(sentences):
    for sentence in sentences:
        for t in sentence:
            # don't touch smwe tokens
            if t['smwe'] != '_':
                pass
            # otherwise, copy
            else:
                t["lexlemma"] = t["lemma"]


def prefix_prepositional_supersenses(sentences):
    for sentence in sentences:
        for t in sentence:
            if t["ss"] != "_" and t["ss"] not in special_labels:
                t["ss"] = "p." + t["ss"]
            if t["ss2"] != "_" and t["ss2"] not in special_labels:
                t["ss2"] = "p." + t["ss2"]


def add_mwe_metadatum(sentences):
    for sentence in sentences:
        smwes, wmwes = read_mwes(sentence)
        if "mwe" not in sentence.metadata:
            sentence.metadata["mwe"] = render(
                [t["form"] for t in sentence],
                [tok_ids for tok_ids in smwes.values()],
                [tok_ids for tok_ids in wmwes.values()],
                {},  # ??
            )


def dedupe_question_marks(sentences):
    for sentence in sentences:
        for t in sentence:
            if t['ss'] == "??" and t['ss2'] == "??""":
                t['ss2'] = "_"


def make_compount_prts_smwes(sentences):
    """
    If a token has the deprel compound:prt and it's not in a SMWE, make a SMWE out of it and its head
    """
    for sentence in sentences:
        smwes, wmwes = read_mwes(sentence)
        next_mwe_id = len(smwes) + len(wmwes) + 1

        for i, t in enumerate(sentence):
            #if t['deprel'] == 'compound:prt' and t['ss'] == '_' and (t['smwe'] != '_' or t['wmwe'] != '_'):
            #    print(sentence.metadata['sent_id'])
            #    print("@!", t)
            if t['deprel'] == 'compound:prt' and t['ss'] == '_' and t['smwe'] == '_' and t['wmwe'] == '_':
                #print(sentence.metadata['sent_id'])
                head = get_token(sentence, t['head'])

                # Skip if compound:prt is to the left of head--this is a parse error
                if not int(head['id']) < int(t['id']):
                    continue

                # Assign SMWE
                head['smwe'] = f"{next_mwe_id}:1"
                t['smwe'] = f"{next_mwe_id}:2"

                # Fix lexlemma
                t['lexlemma'] = '_'
                head['lexlemma'] = f"{head['lemma']} {t['lemma']}"

                next_mwe_id += 1


def renumber_mwes(sentences):
    for sentence in sentences:
        smwes, wmwes = read_mwes(sentence)
        mwes = (
                [(mwe_id, toknums, 'strong') for mwe_id, toknums in smwes.items()]
                + [(mwe_id, toknums, 'weak') for mwe_id, toknums in wmwes.items()]
        )
        # Sort by first token number first, and strength second (to break toknum ties)
        mwes = sorted(mwes, key=lambda x: (float(x[1][0]), 0 if x[2] == 'strong' else 1))
        for new_id, (_, toknums, strength) in enumerate(mwes, start=1):
            # also sort toknums just in case
            for mwe_token_count, toknum in enumerate(sorted(toknums), start=1):
                tok = get_token(sentence, toknum)
                tok['smwe' if strength == 'strong' else 'wmwe'] = f"{new_id}:{mwe_token_count}"


def main():
    sentences = get_conllulex_tokenlists("../corpus_raw.conllulex")

    dedupe_question_marks(sentences)
    make_compount_prts_smwes(sentences)
    add_mwe_metadatum(sentences)
    add_lexlemma(sentences)
    add_wlemma(sentences)
    prefix_prepositional_supersenses(sentences)
    add_lexcat(sentences)
    add_lextag(sentences)
    renumber_mwes(sentences)

    ignored = []

    sentences = [s for s in sentences if s.metadata["sent_id"] not in ignored]
    with open("../corpus.conllulex", "w") as f:
        f.write("".join(s.serialize() for s in sentences))


if __name__ == "__main__":
    main()
