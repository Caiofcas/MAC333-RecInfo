#!/usr/bin/python
import chardet
import sys
import fnmatch
import os
import pickle

# DEBUG = True
DEBUG = False

# CODE FROM ALAIR ----------------------


def GetFileEncoding(file_path):
    """ Get the encoding of file_path using chardet package"""
    with open(file_path, ’rb’) as f:
        return chardet.detect(f.read())

# END ----------------------------------


def find_txt_files(path):
    filelist = []

    for file in os.listdir(path):
        file_path = path+'/'+file

        if os.path.isdir(file_path):
            filelist += find_txt_files(file_path)

        elif fnmatch.fnmatch(file, '*.txt'):
            filelist.append(file_path)
    return filelist


def get_filelist(path):
    files = find_txt_files(path)
    files.sort(key=lambda x: x.rsplit('/')[-1])
    for i in range(len(files)):
        files[i] = (i, files[i])
    return files


def build_reverse_index(files):
    r_index = {}  # token : list of files
    for c, fn in files:
        tokens = get_tokens(fn)
        for t in tokens:
            if r_index.get(t) is None:
                r_index[t] = [c]
            else:
                r_index[t].append(c)
    return r_index


def get_tokens(file):
    tokens = set()
    enc = GetFileEncoding(file)
    # encoding = enc[’encoding’]
    confidence = float(enc[’confidence’])*100
    print('% 5d % -10s % 4.1f % % % s' % (ifile, encoding, confidence, ListaDeArquivos[ifile])
    if confidence < 63:
        myerr='replace'
    else:
        myerr='strict'
    with open(ListaDeArquivos[ifile], 'r', encoding=encoding, errors=myerr) as filehand:
        pass
    return tokens


if __name__ == "__main__":
    if DEBUG:
        print(sys.argv)

    if len(sys.argv) < 2:
        print("Usage:\n\tpython mir.py <directory>\nOR\n\t./mir.py <directory>")
        exit(1)

    directory=sys.argv[1]
    if DEBUG:
        print("Dir: {}".format(directory))

    # list all txt documents

    filelist=get_filelist(directory)
    for c, fn in filelist:
        print("{} {}".format(c, fn))

    print("Foram encontrados {} documentos.".format(len(filelist)))

    # Construct index

    r_index=build_reverse_index(filelist)
    ntokens=0
    print("Os {} documentos foram processados e produziram um total de "
          "{} tokens, que usaram um vocabulário com {} tokens distintos.\n"
          "Informações salva em {}/mir.pickle para carga via pickle."
          .format(len(filelist), ntokens, len(r_index.keys()), directory))
    # print index
