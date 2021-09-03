from collections import defaultdict

import conllu

from streusle.lexcatter import compute_lexcat
from streusle.mwerender import render
from streusle.tagging import sent_tags
# misc --------------------------------------------------------------------------------

def get_conllulex_tokenlists(conllulex_path):
    fields = tuple(list(conllu.parser.DEFAULT_FIELDS)
                   + ['smwe',     # 10
                      'lexcat',   # 11
                      'lexlemma', # 12
                      'ss',       # 13
                      'ss2',      # 14
                      'wmwe',     # 15
                      'wcat',     # 16
                      'wlemma',   # 17
                      'lextag'])  # 18

    with open(conllulex_path, 'r', encoding='utf-8') as f:
        return conllu.parse(f.read(), fields=fields)


special_labels = ['`i','`d','`c','`$','??']


def read_mwes(sentence):
    """Returns two dicts mapping from smwe/wmwe ID to token IDs"""
    smwes = defaultdict(list)
    wmwes = defaultdict(list)

    for t in sentence:
        if t['smwe'] != '_':
            smwe_id, _ = t['smwe'].split(':')
            smwes[smwe_id].append(t['id'])
        if t['wmwe'] != '_':
            wmwe_id, _ = t['wmwe'].split(':')
            wmwes[wmwe_id].append(t['id'])
    return smwes, wmwes


# modifications --------------------------------------------------------------------------------
def add_lextag(sentences):
    for sentence in sentences:
        smwes, wmwes = read_mwes(sentence)
        tags = sent_tags(
            len(sentence),
            sentence,
            list(smwes.values()),
            list(wmwes.values())
        )
        for i, (t, tag) in enumerate(zip(sentence, tags)):
            if tag not in ["I_", "i_"]:
                tag += "-" + t['lexcat']
                if t['ss'] != '_':
                    tag += "-" + t['ss']
                if t['ss2'] not in ['_', t['ss']]:
                    tag += "|" + t['ss2']
            sentence[i]['lextag'] = tag


def add_lexcat(sentences):
    for sentence in sentences:
        smwes, _ = read_mwes(sentence)
        poses = [(t['upos'], t['xpos']) for t in sentence]
        deps = [(t['head'], t['deprel']) for t in sentence]
        for t in sentence:
            smwe_tok_ids = '_' if ':' not in t['smwe'] else smwes[t['smwe'].split(":")[0]]
            t['lexcat'] = compute_lexcat(
                t['id'],
                t['smwe'],
                smwe_tok_ids,
                t['ss'],
                t['lexlemma'],
                poses,
                deps
            )


def add_lexlemma(sentences):
    for sentence in sentences:
        for t in sentence:
            if t['smwe'] == '_' and t['wmwe'] == '_':
                t['lexlemma'] = t['lemma']


def prefix_prepositional_supersenses(sentences):
    for sentence in sentences:
        for t in sentence:
            if t['ss'] != '_' and t['ss'] not in special_labels:
                t['ss'] = 'p.' + t['ss']
            if t['ss2'] != '_' and t['ss2'] not in special_labels:
                t['ss2'] = 'p.' + t['ss2']

def add_mwe_metadatum(sentences):
    for sentence in sentences:
        smwes, wmwes = read_mwes(sentence)
        if 'mwe' not in sentence.metadata:
            sentence.metadata['mwe'] = render(
                [t['form'] for t in sentence],
                [tok_ids for tok_ids in smwes.values()],
                [tok_ids for tok_ids in wmwes.values()],
                {}  # ??
            )


def main():
    sentences = get_conllulex_tokenlists('corpus.conllulex')

    add_mwe_metadatum(sentences)
    add_lexlemma(sentences)
    prefix_prepositional_supersenses(sentences)
    add_lexcat(sentences)
    add_lextag(sentences)

    with open('corpus_enriched.conllulex', 'w') as f:
        f.write("\n".join(s.serialize() for s in sentences))


if __name__ == '__main__':
    main()
