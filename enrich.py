
annolexcatmap = {'`c':'CCONJ','`j':'ADJ','`r':'ADV','`n':'NOUN','`o':'PRON','`v':'VERB','`d':'DISC','`i':'INF','`a':'AUX'}
xposlexcatmap = {'PRP$':'PRON.POSS','WP$':'PRON.POSS','POS':'POSS','TO':'INF.P'}
special_labels = ['`i','`d','`c','`$','??']

def compute_lexcat(inputfile,outputfile):
    """
    Given a conllulex file, populates the lexcat
    The rules are taken from: https://github.com/nert-nlp/streusle/blob/master/lexcatter.py

    Uses the 'p.' prefix to identify an adposition supersense. Script does not check for noun / verb supersenses for the time being.

    :param filename: the conllulex filename
    :return: Nada
    """
    assert inputfile != outputfile

    with open (outputfile,'w') as fo:
        with open (inputfile,'r') as fi:

            lines = fi.readlines()
            c = 0
            while c < len(lines):
                cache = []
                if lines[c].strip() != '' and not lines[c].startswith('#'):
                    l = lines[c].split('\t')

                    # Now start the rule sequences
                    if l[13].lower() in annolexcatmap.keys():
                        l[11] = annolexcatmap[l[13]]

                        # e.g `i with a TO Xpos is INF.P!
                        if l[4] in xposlexcatmap.keys():
                            l[11] = xposlexcatmap[l[4]]

                        c += 1
                    elif l[13].lower().startswith('p.') or l[13].lower() == '`$': # adposition supersense
                        if l[10] != '_': # SMWE
                            print(l)
                            c += 1
                            cache = []
                            while lines[c].strip().split('\t')[10] != '_':
                                cache.append(lines[c].strip() + '\n')
                                c += 1 # get the last MWE token location
                            if lines[c - 1].strip().split('\t')[3] in ['ADP','SCONJ']: l[11] = 'P'
                            else: l[11] = 'PP'

                        elif l[4] in xposlexcatmap.keys():
                            l[11] = xposlexcatmap[l[4]]
                            c += 1
                        else:
                            l[11] = 'P'
                            c += 1
                    elif l[3] in ['PART']:
                        l[11] = 'ADV'
                        c += 1
                    else:
                        l[11] = l[3]
                        #if l[11] == 'NOUN': l[11] = 'N'
                        #if l[11] == 'VERB': l[11] = 'V'
                        c += 1

                    fo.write('\t'.join(l))
                    for cach in cache:
                        fo.write(cach)

                else:
                    fo.write(lines[c].strip() + '\n')
                    c += 1



def add_lemmas_prefix_supersense(filename):
    """
    Adds lemmas and prefixes supersenses with p. (except the special list of backtick tags)
    :param filename: the input filename
    :return: Nada
    """
    with open(filename.replace('.conllulex', '.enriched.conllulex'), 'w') as fo:
        with open(filename,'r') as fi:
            for line in fi.readlines():
                if line.strip() != '' and not line.startswith('#'):
                    l = line.strip().split('\t')
                    if l[10] == '_' and l[15] == '_': #not strong nor weak mwe
                        l[12] = l[2]
                    if l[13] != '_' and l[13] not in special_labels: l[13] = 'p.' + l[13]
                    if l[14] != '_' and l[14] not in special_labels: l[14] = 'p.' + l[14]
                    fo.write('\t'.join(l) + '\n')
                else:
                    fo.write(line.strip() + '\n')

def add_lextag(inputfile,outputfile):

    """
    Adds the LEXTAG. Only considers strong and continuous MWEs since there seem to be no weak MWE annotations nor any discontinuous ones (not confirmed!) in the PASTRIE data
    """

    assert inputfile != outputfile

    with open(outputfile, 'w') as fo:
        with open(inputfile, 'r') as fi:

            lines = fi.readlines()
            c = 0
            while c < len(lines):
                if lines[c].strip() != '' and not lines[c].startswith('#'):
                    l = lines[c].strip().split('\t')
                    if l[10] == '_' and l[15] == '_': # not an smwe nor wmwe
                        if l[13] == '_':
                            l[18] = 'O' + '-' + l[11]
                        elif l[13] != '_' and l[14] == l[13]:
                            l[18] = 'O' + '-' + l[11] + '-' + l[13]
                        elif l[13] != '_' and l[14] != l[13]:
                            l[18] = 'O' + '-' + l[11] + '-' + l[13] + '|' + l[14]
                    elif l[10] != '_': # strong mwe only

                        if (c != 0 and not lines[c - 1].startswith('#') and lines[c - 1].strip().split('\t')[10] == '_') or c == 0: # B token

                            if l[13] == '_':
                                l[18] = 'B' + '-' + l[11]
                            elif l[13] != '_' and l[14] == l[13]:
                                l[18] = 'B' + '-' + l[11] + '-' + l[13]
                            elif l[13] != '_' and l[14] != l[13]:
                                l[18] = 'B' + '-' + l[11] + '-' + l[13] + '|' + l[14]
                        else: # I token
                            l[18] = 'I_'


                    fo.write('\t'.join(l) + '\n')

                else:
                    fo.write(lines[c].strip() +  '\n')

                c += 1


inputfile = 'corpus.conllulex'
outputfile = 'corpus.enriched.conllulex'
outputfile2 = 'corpus.enriched2.conllulex'
outputfile3 = 'corpus.enriched3.conllulex'

add_lemmas_prefix_supersense(inputfile)
compute_lexcat(outputfile,outputfile2)
add_lextag(outputfile2,outputfile3)