#!/usr/bin/python
import sys

if __name__ == "__main__":
    # print(sys.argv)

    if len(sys.argv) < 2:
        print("Usage:\n\tpython mir.py <directory>\nOR\n\t./mir.py <directory>")
        exit(1)

    directory = sys.argv[1]
    print("Dir: {}".format(directory))

    # Construct index

    # print index
