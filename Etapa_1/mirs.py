#!/usr/bin/python
import argparse
import re
import pickle
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


def unpickle(rootdir):
    picklefn = '{}/mir.pickle'.format(rootdir)

    with open(picklefn, 'rb') as handle:
        unpickler = pickle.Unpickler(handle)
        validation_str = unpickler.load()
        if DEBUG:
            print(validation_str)
        filelist = unpickler.load()
        r_index = unpickler.load()
        encoding_dic = unpickler.load()

    if DEBUG:
        print(filelist)
        print(encoding_dic)

    print("MIR (My Information Retrieval System) de {}\n"
          "com {} termos e {} documentos\n".format(
              picklefn,
              len(r_index),
              len(filelist)
          ))
    return filelist, r_index, encoding_dic


if __name__ == "__main__":

    args = getArgs()

    if DEBUG:
        print(args)

    filelist, r_index, enconding_dic = unpickle(args.dir)

    tokens = [x for x in r_index.keys()]
    tokens.sort()
    counter = Counter({k: len(r_index[k]) for k in tokens})

    if args.t is not None:

        if args.r is not None:
            counter_filtered = Counter(
                {tok: counter[tok] for tok in counter if args.r.search(tok)}
            )

            total = len(counter)
            matched = len(counter_filtered)
            not_matched = total - matched

            print("Palavras que satisfazem a REGEX \"{}\""
                  .format(args.r.pattern))
            print("Total: {: >7d}"
                  " Regex: {: >7d}"
                  " Não regex: {: >7d}"
                  " Razão: {:.3f}\n"
                  .format(
                      total,
                      matched,
                      not_matched,
                      not_matched/matched)
                  )

        elif args.R is not None:
            counter_filtered = Counter(
                {tok: counter[tok]
                    for tok in counter if not args.R.search(tok)}
            )

            total = len(counter)
            not_matched = len(counter_filtered)
            matched = total - not_matched

            print("Palavras que NÃO satisfazem a REGEX \"{}\""
                  .format(args.R.pattern))
            print("Total: {: >7d}"
                  " Não regex: {: >7d}"
                  " Regex: {: >7d}"
                  " Razão: {:.3f}\n"
                  .format(
                      total,
                      not_matched,
                      matched,
                      matched/not_matched)
                  )

        else:
            counter_filtered = counter
            end_str = ''

        top_tokens = counter_filtered.most_common(args.t)

        print('\tDF\tTermo/Token\tLista de incidência com IDs dos arquivos')

        docs = set()
        for tok, count in top_tokens:
            print('\t{:2d}\t{: <10}\t{}'.format(count, tok, r_index[tok]))
            for i in r_index[tok]:
                docs.add(i)

        if args.r is not None:
            print("Acima estão os {} tokens mais frequentes "
                  "satisfazendo REGEX \"{}\"."
                  .format(len(top_tokens), args.r.pattern))
            print("Presente(s) em {} arquivo(s).\n".format(len(docs)))
        elif args.R is not None:
            print("Acima estão os {} tokens mais frequentes NÃO "
                  "satisfazendo REGEX \"{}\"."
                  .format(len(top_tokens), args.R.pattern))
            print("Presente(s) em {} arquivo(s).\n".format(len(docs)))
        else:
            print("Listados {} tokens, ordenados decrescentemente por freq. de documento(DF)".format(
                len(top_tokens)))

    if args.tokens != [[]]:
        print("Conjugação das listas de incidência dos {} termos seguintes.".format(
            len(args.tokens[0])))

        print('\tDF\tTermo/Token\tLista de incidência com IDs dos arquivos')

        args.tokens[0].sort(reverse=True)
        for tok in args.tokens[0]:
            print('\t{:2d}\t{: <10}\t{}'.format(
                counter[tok], tok, r_index[tok]))

        docs = [
            (i, fn)
            for i, fn in enumerate(filelist)
            if all([
                (i in r_index[tok]) for tok in args.tokens[0]
            ])
        ]

        print("São {} os documentos com os {} termos".format(
            len(docs), len(args.tokens[0])))
        for i, fn in docs:
            print("\t{:2d}\t{}".format(i, fn))
