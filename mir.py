#!/usr/bin/python
import codecs
import chardet
import fnmatch
import os
import pickle
import re
import argparse
import time

from mirs import unpickle
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

    parser.add_argument('-A', '--auxiliary', action='store_true')
    return parser.parse_args()


def parseInstructions(instrct_list):
    if instrct_list is not None:
        instructions = dict((line.split()[::-1]
                             for line in instrct_list.readlines()))
        print("Instruções ao indexador tomadas de instruc.lst")
        for fn in instructions:
            print("{} {}".format(instructions[fn], fn))
        print()

        return instructions
    return {}


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
    file_path = os.path.join(rootdir, fn)

    encoding = enc['encoding']
    confidence = float(enc['confidence'])*100
    myerr = enc['errors']

    n_tokens = 0
    token_freq = {}
    token_pos = {}

    with open(file_path, 'r', encoding=encoding, errors=myerr) as handle:

        words_gen = (
            word.lower()
            for line in handle
            for word in resplit.split(line)
        )

        for i, token in enumerate(words_gen):
            if token != '':
                if token_freq.get(token) is None:
                    token_freq[token] = 1
                    token_pos[token] = [i]
                else:
                    token_freq[token] += 1
                    token_pos.append(i)

    return token_freq, token_pos


def buildReverseIndex(files, rootdir, encoding_dic, index_name, ind_time):
    r_index = {}  # token : list of (fileID, freq, pos_ini)
    position_list = []

    n_tokens = 0

    for c, fn in enumerate(files):
        enc = encoding_dic[fn]
        token_freq, token_pos = getTokens(fn, rootdir, enc)
        n_tokens += sum(token_freq.values())

        for t in token_freq.keys():
            if r_index.get(t) is None:
                r_index[t] = [(c, token_freq[t], token_pos[t])]
            else:
                r_index[t].append((c, token_freq[t], token_pos[t]))

    # Save position list
    picklefn = '{}/{}p.pickle'.format(args.dir, index_name)
    with open(picklefn, 'w+b') as picklefile:
        pickler = pickle.Pickler(picklefile)
        pickler.dump(position_list)

    # Save index
    picklefn = '{}/{}.pickle'.format(args.dir, index_name)
    with open(picklefn, 'w+b') as picklefile:
        pickler = pickle.Pickler(picklefile)
        pickler.dump('MIR 2.0')
        pickler.dump(files)
        pickler.dump(r_index)
        pickler.dump(encoding_dic)
        pickler.dump(ind_time)

    # Print statements

    print("Os {} documentos foram processados e produziram um total de "
          "{} tokens, que usaram um vocabulário com {} tokens distintos.\n"
          "Informações salvas em {} para carga via pickle."
          .format(len(files), n_tokens, len(r_index.keys()), picklefn))

    return r_index, n_tokens


def buildAuxiliaryIndex(args, current_time):

    old_filelist, old_index, old_encoding_d, _ = unpickle(
        args.dir, out=False)

    old_size = len(old_filelist)

    print(
        "MIR (My Information Retrieval System) de {0}/mir.pickle"
        " com {1} termos e {2} documentos\nForam carregados os nomes de {2} documentos.\n"
        "Lista atual dos arquivos com extensão .txt encontrados pela sub-árvore"
        " do diretório: {0}"
        .format(args.dir, len(old_index), old_size))

    filelist = getFileList(args.dir, {})

    new_size = len(filelist)

    print("Agora foram encontrados {} documentos.".format(new_size))

    # find diferences
    aux_files = []
    rm_files = []
    mod_n = rem_n = new_n = 0
    for fn in filelist:
        if fn in old_filelist:
            file_path = os.path.join(args.dir, fn)
            # Modificado recentemente
            if old_encoding_d[fn]['modificado'] != os.path.getmtime(file_path):
                mod_n += 1
                aux_files.append(fn)
        else:
            aux_files.append(fn)
            new_n += 1

    for fn in old_filelist:
        if not fn in filelist:
            rem_n += 1
            rm_files.append(fn)

    print(
        "De {} para {}, foram acrescentados {} arquivos novos e removidos {}.\n"
        "Permaneceram {} arquivos. Dos quais, {} foram atualizados.\nTemos {} "
        "arquivos atualizados ou novos a serem indexados no índice auxiliar:"
        .format(
            old_size,
            new_size,
            new_n,
            rem_n,
            old_size - rem_n,
            mod_n,
            new_n + mod_n
        ))

    for c, fn in enumerate(aux_files):
        print(c, fn)
    print()
    aux_encoding_dic = getEncodingDict(aux_files, args.dir, {}, args.v)

    r_index, ntokens = buildReverseIndex(
        aux_files, args.dir, aux_encoding_dic, 'mira', current_time)

    with open('{}/mira.rem'.format(args.dir), 'w+') as handle:
        handle.writelines(['@x {}'.format(fn) for fn in rm_files])
        handle.write('\n')
    print("Lista com {} remoções salva em {}/mira.rem".format(rem_n, args.dir))


if __name__ == "__main__":

    start_time = time.time()

    args = parseArgs()

    if args.auxiliary:
        buildAuxiliaryIndex(args, start_time)
    else:
        # deal with instructions
        instructions = parseInstructions(args.instructions)

        # Get list of txt documents

        print("Lista de arquivos .txt encontrados na "
              "sub-árvore do diretório: {}".format(args.dir))

        filelist = getFileList(args.dir, instructions)

        print("Foram encontrados {} documentos.\n".format(len(filelist)))

        # Get encoding dict for all files:

        encoding_dic = getEncodingDict(
            filelist, args.dir, instructions, args.v)

        # Construct index

        r_index, ntokens = buildReverseIndex(
            filelist, args.dir, encoding_dic, 'mir', start_time)
