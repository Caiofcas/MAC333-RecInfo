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
    parser.add_argument('-o', '--order', type=int, default=0,
                        help='Order to be used when displaying results')
    parser.add_argument('-r', type=re.compile,
                        help='Print tokens that match the regex passed')
    parser.add_argument('-R', type=re.compile,
                        help='Print tokens that DON\'T match the regex passed')
    parser.add_argument('tokens', action="append", nargs='*',
                        help='directory to be processed')

    return parser.parse_args()


def getIndex(l: list, v):
    for i, item in enumerate(l):
        if item[0] == v:
            return i

    return -1


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


def removeDeletedFiles(filelist, r_index, rootdir):

    with open('{}/mira.rem'.format(args.dir), 'r') as handle:
        rm_files = [line.split()[-1] for line in handle.readlines()]

    rm_ind = [filelist.index(x) for x in rm_files]

    # Code to remove files in "mira.rem" from filelist, but this
    # has behaviour incompatible with examples

    # new_filelist = [fn for fn in filelist if not fn in rm_files]
    # mapping = {filelist.index(fn): new_filelist.index(fn)
    #            for fn in new_filelist}

    # for tok in r_index:
    #     l = r_index[tok]
    #     l = [(mapping[file_c], count)
    #          for (file_c, count) in l if not file_c in rm_ind]
    #     r_index[tok] = l

    for tok in r_index:
        l = r_index[tok]
        l = [(file_c, count, ini)
             for (file_c, count, ini) in l if not file_c in rm_ind]
        r_index[tok] = l

    return filelist, r_index, len(rm_ind)


def combineIndexes(main_fl, main_rind, aux_fl, aux_rind):
    filelist = main_fl
    mapping = {}
    for c, fn in enumerate(aux_fl):
        if fn in main_fl:
            mapping[c] = main_fl.index(fn)
        else:
            mapping[c] = len(main_fl)
            main_fl.append(fn)

    r_index = main_rind
    for tok, aux_val in aux_rind.items():

        # convert to new indexes
        aux_val = [(mapping[c], token_freq, ini)
                   for c, token_freq, ini in aux_val]

        main_val = r_index.get(tok)

        if main_val is not None:
            for c, freq, ini in aux_val:
                i = getIndex(main_val, c)
                if i >= 0:
                    main_val[i] = (c, freq, ini)
                else:
                    main_val.append((c, freq, ini))
        else:
            main_val = aux_val
        r_index[tok] = main_val

    return filelist, r_index


def loadCombinedIndex(args):
    hasAux = os.path.isfile(os.path.join(args.dir, 'mira.pickle'))
    hasRem = os.path.isfile(os.path.join(args.dir, 'mira.rem'))

    printStartMsg(args.dir, hasAux, hasRem)

    filelist, r_index, _, _ = unpickle(args.dir)

    if hasRem:
        filelist, r_index, removed_count = removeDeletedFiles(
            filelist, r_index, args.dir)

    if hasAux:
        aux_filelist, aux_index, _, _ = unpickle(args.dir, ind_name='mira')

        removed_count += len([x for x in filelist if x in aux_filelist])

        filelist, r_index = combineIndexes(
            filelist, r_index, aux_filelist, aux_index)

    print('Arquivos caducados ou removidos: {}'.format(removed_count))
    print('Indice conjugado com {} termos e {} documentos'.format(
        len(r_index), len(filelist)))

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


def sortDocuments(mode, documents, tokens):

    print("São {} os documentos com os {} termos"
          .format(len(documents), len(tokens)))
    if mode == 0:
        for i, fn in documents:
            print("\t{:2d}\t{}".format(i, fn))
    else:
        print('Ordenação {} não implementada ainda'.format(mode))


if __name__ == "__main__":

    args = getArgs()

    if args.dir[-1] == '/':
        args.dir = args.dir[:-1]

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

        tokens = []
        for tok in args.tokens[0]:
            ind = r_index.get(tok)
            if ind is not None:
                print('\t{:2d}\t{: <10}\t{}'.format(
                    counter[tok], tok, [x[0] for x in r_index[tok]]))
                tokens.append(tok)
            else:
                print('\tToken {} não encontrado.'.format(tok))

        docs = []
        for i, fn in enumerate(filelist):
            if all([
                any([
                    i == c
                    for c, _, _ in r_index[tok]])
                for tok in tokens
            ]):
                docs.append((i, fn))

        sortDocuments(args.order, docs, tokens)
