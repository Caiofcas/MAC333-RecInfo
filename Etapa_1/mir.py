#!/usr/bin/python
import sys
import fnmatch
import os

# DEBUG = True
DEBUG = False


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


if __name__ == "__main__":
    if DEBUG:
        print(sys.argv)

    if len(sys.argv) < 2:
        print("Usage:\n\tpython mir.py <directory>\nOR\n\t./mir.py <directory>")
        exit(1)

    directory = sys.argv[1]
    if DEBUG:
        print("Dir: {}".format(directory))

    # list all txt documents

    filelist = get_filelist(directory)
    for c, fn in filelist:
        print("{} {}".format(c, fn))

    print("Foram encontrados {} documentos.".format(len(filelist)))

    # Construct index

    # print index
