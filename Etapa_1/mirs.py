import argparse
import re
import pickle
from collections import Counter

# DEBUG = True
DEBUG = False


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

    return filelist, r_index, encoding_dic


if __name__ == "__main__":

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

    args = parser.parse_args()

    if DEBUG:
        print(args)

    filelist, r_index, enconding_dic = unpickle(args.dir)
    # print(picklefn)

    tokens = [x for x in r_index.keys()]
    tokens.sort()
    counter = Counter({k: len(r_index[k]) for k in tokens})

    print(counter.most_common(3))
