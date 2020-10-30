#!/usr/bin/python
import chardet
import sys
import fnmatch
import os
import pickle
import re
import argparse

# DEBUG = True
DEBUG = False


def GetFileEncoding(file_path):
    """ Get the encoding of file_path using chardet package"""
    with open(file_path, 'rb') as f:
        return chardet.detect(f.read())


def get_filelist(rootdir):
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


def get_tokens(fn, fileID, rootdir, verborragic):
    tokens = set()
    fn_path = os.path.join(rootdir, fn)

    enc = GetFileEncoding(fn_path)

    encoding = enc['encoding']
    confidence = float(enc['confidence'])*100

    if verborragic:
        print(
            "{:5} {: <10} {:4.1f} {:6} {}".format(
                fileID,
                str(encoding),
                confidence,
                os.stat(fn_path).st_size,
                fn))
        # print("For file {}:\n{}".format(file, enc))

    if confidence < 63:
        myerr = 'replace'
    else:
        myerr = 'strict'

    n_tokens = 0
    with open(fn_path, 'r', encoding=encoding, errors=myerr) as handle:
        for line in handle:
            line_tokens = re.sub(r'([^\w\s]|\d|_)', ' ', line).split()
            n_tokens += len(line_tokens)
            for tok in line_tokens:
                tokens.add(tok.lower())
    return tokens, n_tokens, encoding


def build_reverse_index(files, rootdir, verborragic):
    r_index = {}  # token : list of files
    n_tokens = 0
    encoding_dic = {}

    if verborragic:
        print('\nDebugging information:\n')

    for c, fn in enumerate(files):
        tokens, n_tokens_file, enc = get_tokens(fn, c, rootdir, verborragic)
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
    if DEBUG:
        print(sys.argv)

    parser = argparse.ArgumentParser(
        description='Creates the reverse index for .txt files in a directory')

    parser.add_argument('dir', help='directory to be processed')
    parser.add_argument('-v', action='store_true',
                        help='print verborragic information for debugging purposes')
    args = parser.parse_args()

    if DEBUG:
        print(args)
        print("Dir: {}".format(args.dir))

    # list all txt documents

    filelist = get_filelist(args.dir)
    for c, fn in enumerate(filelist):
        print("{} {}".format(c, fn))

    print("Foram encontrados {} documentos.".format(len(filelist)))

    # Construct index

    r_index, ntokens, encoding_dic = build_reverse_index(
        filelist, args.dir, args.v)

    # Save index

    picklefn = '{}/mir.pickle'.format(args.dir)
    with open(picklefn, 'w+b') as picklefile:
        pickler = pickle.Pickler(picklefile)
        pickler.dump('MIR 1.0')
        pickler.dump(filelist)
        pickler.dump(r_index)
        pickler.dump(encoding_dic)

    print("Os {} documentos foram processados e produziram um total de "
          "{} tokens, que usaram um vocabulário com {} tokens distintos.\n"
          "Informações salvas em {} para carga via pickle."
          .format(len(filelist), ntokens, len(r_index.keys()), picklefn))
