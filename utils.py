# -*- coding: utf-8 -*-
"""Distant viewing pipeline utilities

General purpose functions for the other modules in this directory.
Modify the file "params.json" to adjust the user-level parameters
that may differ between systems.
"""

import argparse
import datetime
import json
import os
from os.path import join

import numpy as np


def iso8601():
    """Return current time as an string formated according to ISO8601.
    """
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def norm_array(np_array):
    """Normalize columns of a numpy array.

    Args:
        np_array: A numpy array or coercible list.
    Returns:
        A new array with columns normalized by the l2 norm.
    """
    np_array = np.array(np_array)
    np_array = np_array / np.sqrt(np.sum(np_array**2))

    return np_array


def load_jsonl(jpath):
    """Load json line path as list of dictionaries.

    Args:
        jpath: string describing the path to the json file.
    Returns:
        a list of dictionaries corresponding to each line in the file.
    """
    data = []
    with open(jpath) as f:
        for line in f:
            data.append(json.loads(line))
    return data


def default_option_parser(desc):
    """Return a default option parser
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--series', action="store", dest="series",
                        help='name of the series to process data from',
                        required=True)
    parser.add_argument('--season', action="store", dest="season",
                        nargs='+', type=int, default=[],
                        help='season to parse; select multiple seasons '
                             'separated by spaces; leave blank to select '
                             'all seasons')
    parser.add_argument('--episode', action="store", dest="episode",
                        nargs='+', type=int, default=[],
                        help='episode to parse; select multiple episodes '
                             'separated by spaces; leave blank to select '
                             'all episodes')
    return parser


def read_user_properties() -> dict:
    """Read properties json file file user properties.

    Returns:
        dict: Dictionary of the parameter file.
    """
    with open("params.json", "r") as param_file:
        params = json.load(param_file)

    return params


def get_episodes(args):
    """Return list of episode identifiers
    """
    basepath = read_user_properties()['basepath']
    if not os.path.exists(join(basepath, 'input', args.series)):
        raise FileNotFoundError("No video inputs found for series '" +
                                args.series + "'.")

    eps = os.listdir(join(basepath, "input", args.series))
    eps = [x for x in eps if os.path.splitext(x)[1] == ".mp4"]
    eps = [x[:-4] for x in eps if len(x.split("-")) == 3]
    eps = sorted(eps)

    if args.season:
        season_names = ["s{0:02d}".format(x) for x in args.season]
        eps = [ep for ep in eps if ep.split("-")[1] in season_names]

    if args.episode:
        episode_names = ["e{0:02d}".format(x) for x in args.episode]
        eps = [ep for ep in eps if ep.split("-")[2] in episode_names]

    return eps


def get_io_paths(episode):
    """Return input and output paths for episode id
    """
    basepath = read_user_properties()['basepath']
    series = episode.split("-")[0]

    paths = {
        'ifile': join(basepath, "input", series, episode + ".mp4"),
        'ifile_mp3': join(basepath, "input", series, episode + ".mp3"),
        'ifile_srt': join(basepath, "input", series, episode + ".srt"),
        'spath': join(basepath, "stage", series),
        'fpath': join(basepath, "frame", series, episode),
        'opath': join(basepath, "dv-data", series)
    }

    return paths
