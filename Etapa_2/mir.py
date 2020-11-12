#!/usr/bin/python
import codecs
import chardet
import fnmatch
import os
import pickle
import re
import argparse

# DEBUG = True
DEBUG = False

MAXSIZE = 100000
resplit = re.compile(r'[\W\d_\s]+')
mixed_miscoded_espurious = {b'\x81': 1,
                            b'\x8d': 1,
                            b'\x90': 1,
                            b'\x9d': 1,
                            b'\x91': 1}


def mixed_decoder(error: UnicodeDecodeError) -> (str, int):
    global mixed_miscoded_espurious
    """ Trata erros de decodificação Unicode como sendo Windows-1252"""

    bs: bytes = error.object[error.start: error.end]

    if bs in mixed_miscoded_espurious:  # ignored
        return '', error.start + 1
    else:
        return bs.decode("Windows-1252"), error.start + 1
    return bs.decode("Windows-1252", errors='ignore'), error.start + 1


codecs.register_error("mixed", mixed_decoder)


def parseArgs():
    parser = argparse.ArgumentParser(
        description='Creates the reverse index for .txt files in a directory')

    parser.add_argument('dir', help='directory to be processed')
    parser.add_argument('-v', action='store_true',
                        help='print verborragic information for debugging purposes')

    parser.add_argument('-@', '--instructions', type=argparse.FileType('r'),
                        help='instruction file to be loaded')
    return parser.parse_args()


def getFileList(rootdir, instructions):
    ori_filelist = []
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            if DEBUG:
                print(os.path.join(subdir, file))
            filepath = os.path.join(subdir, file)

            if filepath.endswith(".txt"):
                ori_filelist.append(filepath.replace(rootdir+os.sep, ''))

    ori_filelist.sort(key=lambda x: x.rsplit(os.sep)[-1])

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

    return filelist


def getFileEncoding(file_path):
    """ Get the encoding of file_path using chardet package"""

    with open(file_path, 'rb') as f:
        enc = chardet.detect(f.read(MAXSIZE))

        size = os.stat(file_path).st_size

        enc['tamanho'] = size
        enc['modificado'] = os.path.getmtime(file_path)

        if size > MAXSIZE and enc['encoding'] == 'ascii':
            enc['encoding'] = 'UTF-8'
            enc['confidence'] = 0.4
            enc['errors'] = 'mixed'
        elif enc['confidence'] < .63:
            enc['errors'] = 'replace'
        else:
            enc['errors'] = 'strict'

    return enc


def getEncodingDict(filelist, rootdir, instructions, verborragic):
    encoding_dic = {}
    if verborragic:
        print('\nDebugging information:\n')

    for i, fn in enumerate(filelist):
        file_path = os.path.join(rootdir, fn)
        if instructions.get(fn) == '@u':
            encoding_dic[fn] = {
                'encoding': 'utf-8-sig',
                'confidence': 1,
                'error': 'strict',
                'tamanho': os.stat(file_path).st_size,
                'modificado': os.path.getmtime(file_path)
            }
        else:
            encoding_dic[fn] = getFileEncoding(file_path)
        if verborragic:
            encoding = encoding_dic[fn]['encoding']
            confidence = float(encoding_dic[fn]['confidence'])*100

            print(
                "{:5} {: <10} {:4.1f} {:6} {}".format(
                    i,
                    str(encoding),
                    confidence,
                    encoding_dic[fn]['tamanho'],
                    fn)
            )

    if verborragic:
        print('\n')
    return encoding_dic


def getTokens(fn, rootdir, enc):
    tokens = set()
    fn_path = os.path.join(rootdir, fn)

    encoding = enc['encoding']
    confidence = float(enc['confidence'])*100
    myerr = enc['errors']

    n_tokens = 0
    with open(fn_path, 'r', encoding=encoding, errors=myerr) as handle:

        words_gen = (
            word.lower()
            for line in handle
            for word in resplit.split(line)
        )

        for token in words_gen:
            if token != '':
                n_tokens += 1
                tokens.add(token)

    return tokens, n_tokens, encoding


def buildReverseIndex(files, rootdir, encoding_dic, instructions):
    r_index = {}  # token : list of fileIDs
    n_tokens = 0

    for c, fn in enumerate(files):
        enc = encoding_dic[fn]
        tokens, n_tokens_file, enc = getTokens(fn, rootdir, enc)

        n_tokens += n_tokens_file
        for t in tokens:
            if r_index.get(t) is None:
                r_index[t] = [c]
            else:
                r_index[t].append(c)

    return r_index, n_tokens


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

    filelist = getFileList(args.dir, instructions)

    print("Foram encontrados {} documentos.\n".format(len(filelist)))

    # Get encoding dict for all files:

    encoding_dic = getEncodingDict(filelist, args.dir, instructions, args.v)

    # Construct index

    r_index, ntokens = buildReverseIndex(
        filelist, args.dir, encoding_dic, instructions)

    # Save index

    picklefn = '{}/mir.pickle'.format(args.dir)
    with open(picklefn, 'w+b') as picklefile:
        pickler = pickle.Pickler(picklefile)
        pickler.dump('MIR 2.0')
        pickler.dump(filelist)
        pickler.dump(r_index)
        pickler.dump(encoding_dic)

    # Print statements

    print("Os {} documentos foram processados e produziram um total de "
          "{} tokens, que usaram um vocabulário com {} tokens distintos.\n"
          "Informações salvas em {} para carga via pickle."
          .format(len(filelist), ntokens, len(r_index.keys()), picklefn))
