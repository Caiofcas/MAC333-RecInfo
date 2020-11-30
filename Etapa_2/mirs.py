#!/usr/bin/python
import argparse
import re
import pickle
import os
from collections import Counter

# DEBUG = True
DEBUG = False


def getArgs():
    parser = argparse.ArgumentParser(
        description="Searchs <dir>'s Information Retrieval system.")

    parser.add_argument('dir', help='directory to be processed')
    parser.add_argument('-t', type=int,
                        help='Print the <t> most common tokens')
    parser.add_argument('-r', type=re.compile,
                        help='Print tokens that match the regex passed')
    parser.add_argument('-R', type=re.compile,
                        help='Print tokens that DON\'T match the regex passed')
    parser.add_argument('tokens', action="append", nargs='*',
                        help='directory to be processed')

    return parser.parse_args()


def unpickle(rootdir, out=True, ind_name='mir'):
    picklefn = '{}/{}.pickle'.format(rootdir, ind_name)

    with open(picklefn, 'rb') as handle:
        unpickler = pickle.Unpickler(handle)
        validation_str = unpickler.load()
        if DEBUG:
            print(validation_str)
        filelist = unpickler.load()
        r_index = unpickler.load()
        encoding_dic = unpickler.load()
        index_time = unpickler.load()

    if DEBUG:
        print(filelist)
        print(encoding_dic)

    if out:
        print("MIR (My Information Retrieval System) de {}\n"
              "com {} termos e {} documentos".format(
                  picklefn,
                  len(r_index),
                  len(filelist)
              ))
    return filelist, r_index, encoding_dic, index_time


def printEndMsg(args, top_tokens: int, docs_size: int):
    if args.r is not None:
        end_msg = "Acima estão os {} tokens mais ".format(top_tokens)
        end_msg += "frequentes satisfazendo REGEX "
        end_msg += "\"{}\". ".format(args.r.pattern)
        end_msg += "Presente(s) em {} arquivo(s).".format(docs_size)
    elif args.R is not None:
        end_msg = "Acima estão os {} tokens mais ".format(top_tokens)
        end_msg += "frequentes NÃO satisfazendo REGEX "
        end_msg += "\"{}\". ".format(args.R.pattern)
        end_msg += "Presente(s) em {} arquivo(s).".format(docs_size)
    else:
        end_msg = "Listados {} tokens, ".format(top_tokens)
        end_msg += "ordenados decrescentemente por freq. de documento(DF)."

    print(end_msg)


def printStartMsg(rootdir, aux, rem):
    if rem:
        print("Instruções de exclusão ao indexador tomadas de "
              "{}/mira.rem".format(rootdir))
    if aux:
        print("MIR (My Information Retrieval System) de atualização"
              " dinâmica ('{0}/mir.pickle', "
              "'{0}/mira.pickle')".format(rootdir))


def loadCombinedIndex(args):
    hasAux = os.path.isfile(os.path.join(args.dir, 'mira.pickle'))
    hasRem = os.path.isfile(os.path.join(args.dir, 'mira.rem'))

    printStartMsg(args.dir, hasAux, hasRem)
    filelist, r_index, _, _ = unpickle(args.dir)

    if hasAux:
        aux_filelist, aux_index, _, _ = unpickle(args.dir, ind_name='mira')
    if hasRem:
        with open('{}/mira.rem'.format(args.dir), 'r') as handle:
            rm_files = [line.split()[-1] for line in handle.readlines()]

    # Combine

    return filelist, r_index


def filterTokens(args, counter: Counter, out: bool = True):

    if args.r is not None:
        counter_filtered = Counter({
            tok: counter[tok]
            for tok in counter
            if args.r.search(tok)
        })

        total = len(counter)
        matched = len(counter_filtered)
        not_matched = total - matched

        if out:
            print("Palavras que satisfazem a REGEX \"{}\"\n"
                  "Total: {: >7d} Regex: {: >7d} "
                  "Não regex: {: >7d} Razão: {:.3f}\n"
                  .format(
                      args.r.pattern,
                      total, matched,
                      not_matched, not_matched/matched
                  ))
    elif args.R is not None:
        counter_filtered = Counter({
            tok: counter[tok]
            for tok in counter
            if not args.R.search(tok)
        })

        total = len(counter)
        not_matched = len(counter_filtered)
        matched = total - not_matched

        if out:
            print("Palavras que NÃO satisfazem a REGEX \"{}\"\n"
                  "Total: {: >7d} Não regex: {: >7d} "
                  "Regex: {: >7d} Razão: {:.3f}\n"
                  .format(
                      args.R.pattern,
                      total, not_matched,
                      matched, matched/not_matched
                  ))
    else:
        counter_filtered = counter

    return counter_filtered


if __name__ == "__main__":

    args = getArgs()

    if DEBUG:
        print(args)

    filelist, r_index = loadCombinedIndex(args)

    tokens = [x for x in r_index.keys()]
    tokens.sort()
    counter = Counter({k: len(r_index[k]) for k in tokens})

    if args.t is not None:

        counter_filtered = filterTokens(args, counter)
        top_tokens = counter_filtered.most_common(args.t)

        print('\tDF\tTermo/Token\tLista de incidência com IDs dos arquivos')

        docs = set()
        for tok, count in top_tokens:
            print('\t{:2d}\t{: <10}\t{}'.format(
                count, tok, [x[0] for x in r_index[tok]]))
            for i in r_index[tok]:
                docs.add(i)

        printEndMsg(args, len(top_tokens), len(docs))

    if args.tokens != [[]]:
        print("\nConjugação das listas de incidência dos {} termos seguintes."
              .format(len(args.tokens[0])))

        print('\tDF\tTermo/Token\tLista de incidência com IDs dos arquivos')

        args.tokens[0].sort(reverse=True)

        for tok in args.tokens[0]:
            ind = r_index.get(tok)
            if ind is not None:
                print('\t{:2d}\t{: <10}\t{}'.format(
                    counter[tok], tok, [x[0] for x in r_index[tok]]))
            else:
                print('\tToken {} não encontrado.'.format(tok))

        docs = [
            (i, fn)
            for i, fn in enumerate(filelist)
            if all((
                (i in r_index[tok]) for tok in args.tokens[0]
            ))
        ]

        print("São {} os documentos com os {} termos"
              .format(len(docs), len(args.tokens[0])))

        for i, fn in docs:
            print("\t{:2d}\t{}".format(i, fn))
