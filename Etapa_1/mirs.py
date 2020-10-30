import argparse
import re
import pickle

# DEBUG = True
DEBUG = False

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

    picklefn = '{}/mir.pickle'.format(args.dir)
    # print(picklefn)
    with open(picklefn, 'rb') as handle:
        unpickler = pickle.Unpickler(handle)
        unpickler.load()
        # print(obj)
        filelist = unpickler.load()
        r_index = unpickler.load()
        enconding_dic = unpickler.load()

    print(filelist)
    # print(r_index)
    print(enconding_dic)
