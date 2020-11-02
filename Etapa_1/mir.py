#!/usr/bin/python
import chardet
import fnmatch
import os
import pickle
import re
import argparse

# DEBUG = True
DEBUG = False

resplit = re.compile(r'[\W\d_\s]+')


def parseArgs():
    parser = argparse.ArgumentParser(
        description='Creates the reverse index for .txt files in a directory')

    parser.add_argument('dir', help='directory to be processed')
    parser.add_argument('-v', action='store_true',
                        help='print verborragic information for debugging purposes')

    parser.add_argument('-@', '--instructions', type=argparse.FileType('r'),
                        help='instruction file to be loaded')
    return parser.parse_args()


def getFileEncoding(file_path):
    """ Get the encoding of file_path using chardet package"""
    with open(file_path, 'rb') as f:
        return chardet.detect(f.read())


def getFileList(rootdir):
    filelist = []
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            if DEBUG:
                print(os.path.join(subdir, file))
            filepath = os.path.join(subdir, file)

            if filepath.endswith(".txt"):
                filelist.append(filepath.replace(rootdir+os.sep, ''))

    filelist.sort(key=lambda x: x.rsplit(os.sep)[-1])

    return filelist


def getTokens(fn, fileID, rootdir, verborragic):
    tokens = set()
    fn_path = os.path.join(rootdir, fn)

    enc = getFileEncoding(fn_path)

    encoding = enc['encoding']
    confidence = float(enc['confidence'])*100

    if verborragic:
        print(
            "{:5} {: <10} {:4.1f} {:6} {}".format(
                fileID,
                str(encoding),
                confidence,
                os.stat(fn_path).st_size,
                fn)
        )

    if confidence < 63:
        myerr = 'replace'
    else:
        myerr = 'strict'

    n_tokens = 0
    with open(fn_path, 'r', encoding=encoding, errors=myerr) as handle:

        words_gen = (
            word.lower()
            for line in handle
            for word in resplit.split(line)
        )

        for token in words_gen:
            n_tokens += 1
            tokens.add(token)

    return tokens, n_tokens, encoding


def buildReverseIndex(files, rootdir, instructions, verborragic):
    r_index = {}  # token : list of fileIDs
    n_tokens = 0
    encoding_dic = {}

    if verborragic:
        print('\nDebugging information:\n')

    for c, fn in enumerate(files):
        tokens, n_tokens_file, enc = getTokens(fn, c, rootdir, verborragic)
        encoding_dic[fn] = enc

        n_tokens += n_tokens_file
        for t in tokens:
            if r_index.get(t) is None:
                r_index[t] = [c]
            else:
                r_index[t].append(c)

    if verborragic:
        print('\n')
    return r_index, n_tokens, encoding_dic


if __name__ == "__main__":

    args = parseArgs()

    # deal with instructions
    instructions = {}
    if args.instructions is not None:
        instructions = dict((line.split()[::-1]
                             for line in args.instructions.readlines()))
        print("Instruções ao indexador tomadas de instruc.lst")
        for fn in instructions:
            print("{} {}".format(instructions[fn], fn))
        print()

    # Get list of txt documents

    print("Lista de arquivos .txt encontrados na "
          "sub-árvore do diretório: {}".format(args.dir))

    ori_filelist = getFileList(args.dir)

    i = 0
    filelist = []
    for fn in ori_filelist:

        wasRemoved = False

        for key in instructions:
            if instructions[key] == '@x':
                if key == fn:
                    print('Arquivo {} excluído da indexação'.format(fn))
                    wasRemoved = True
                elif key in fn:
                    print('Diretório {} excluído da indexação'.format(key))
                    wasRemoved = True
            if wasRemoved:
                break

        if not wasRemoved:
            filelist.append(fn)
            print("{} {}".format(i, fn))
            i += 1

    print("Foram encontrados {} documentos.\n".format(len(filelist)))s
    # Save index

    picklefn = '{}/mir.pickle'.format(args.dir)
    with open(picklefn, 'w+b') as picklefile:
        pickler = pickle.Pickler(picklefile)
        pickler.dump('MIR 1.0')
        pickler.dump(filelist)
        pickler.dump(r_index)
        pickler.dump(encoding_dic)

    # Print statements

    print("Os {} documentos foram processados e produziram um total de "
          "{} tokens, que usaram um vocabulário com {} tokens distintos.\n"
          "Informações salvas em {} para carga via pickle."
          .format(len(filelist), ntokens, len(r_index.keys()), picklefn))
