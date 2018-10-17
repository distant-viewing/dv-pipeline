# -*- coding: utf-8 -*-
"""Convert dvt json files to semantic csv output.

This callable module is used to compute fingerprint files (canonical faces
in the embedding space) for a series.

Example:
    To process the fingerprint file for Bewitched, run the following:

        $ python3 script04_fingerprint.py --series bw
"""
import os
import pickle

from utils import default_option_parser, read_user_properties, load_jsonl, \
                  norm_array


def get_fprint(series):
    """Create of load fingerprint file for a series.
    """
    base = read_user_properties()['basepath']
    fdir = os.path.join(base, "model", "fprint")
    fprint_file = os.path.join(fdir, series + "fingerprint.pickle")

    if not os.path.exists(fprint_file):
        if series == "bw":
            jsl = load_jsonl(base + "/stage/bw/bw-s02-e02-dvt.jsonl")
            js2 = load_jsonl(base + "/stage/bw/bw-s07-e02-dvt.jsonl")
            fprint = {'larry': norm_array(jsl[7921]['face'][0]['embed']),
                      'darrin': norm_array(jsl[8501]['face'][0]['embed']),
                      'sam': norm_array(jsl[12031]['face'][0]['embed']),
                      'endora': norm_array(jsl[12201]['face'][0]['embed']),
                      'darrin2': norm_array(js2[21141]['face'][0]['embed'])}

        elif series == "idoj":
            jsl = load_jsonl(base + "/stage/idoj/idoj-s02-e02-dvt.jsonl")
            fprint = {'tony': norm_array(jsl[4411]['face'][0]['embed']),
                      'alfred': norm_array(jsl[15391]['face'][0]['embed']),
                      'jeannie': norm_array(jsl[6671]['face'][0]['embed']),
                      'roger': norm_array(jsl[4301]['face'][0]['embed'])}

        elif series == "friends":
            jsl = load_jsonl(base + "/stage/friends/friends-s02-e03-dvt.jsonl")
            fprint = {'monica': norm_array(jsl[12081]['face'][0]['embed']),
                      'chandler': norm_array(jsl[18431]['face'][0]['embed']),
                      'rachel': norm_array(jsl[15951]['face'][0]['embed']),
                      'ross': norm_array(jsl[7591]['face'][0]['embed']),
                      'joey': norm_array(jsl[22151]['face'][0]['embed']),
                      'phoebe': norm_array(jsl[8831]['face'][0]['embed'])}

        else:
            raise ValueError('No fingerprint found for "' + series + '"')

        with open(fprint_file, "wb") as fout:
            pickle.dump(fprint, fout, protocol=pickle.HIGHEST_PROTOCOL)

    else:

        with open(fprint_file, "rb") as fin:
            fprint = pickle.load(fin)

    return fprint


def get_args():
    """Run module with the desired options.
    """
    desc = 'Create fingerprint files.'
    parser = default_option_parser(desc)

    return parser.parse_args()


if __name__ == "__main__":
    get_fprint(get_args().series)
