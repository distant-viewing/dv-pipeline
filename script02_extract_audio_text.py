# -*- coding: utf-8 -*-
"""Extract audio and video files.

This callable module is used to extract mp3 and srt files from the raw
input video files. You can select the series and (optionally) the season
and episodes using command line arguments. You must also turn on the flags
for text and/or audio extraction (neither are run by default).

Example:
    To process the first 5 episodes from season 2 of Bewitched,
    we would run the following:

        $ python3 script02_extract_audio_text.py --series bw \
                                                 --season 2 \
                                                 --episode 1 2 3 4 5 \
                                                 --audio --text --verbose

Note: you must run this file in the docker image.
"""
import os
import subprocess

from utils import default_option_parser, get_episodes, get_io_paths


def get_audio(episode, verbose=True):
    """For a given episode, extract a mp3 audio file.

    Args:
        episode: String describing the episode to parse
        verbose: Boolean value. Should progress be printed to the console.
    Returns:
        None
    """
    paths = get_io_paths(episode)
    ifile = paths['ifile']
    ofile = paths['ifile_mp3']

    with open(os.devnull, 'w') as devnull:
        if os.path.isfile(ofile):
            os.remove(ofile)
        subprocess.run(["ffmpeg", "-i", ifile, "-ab", "192k", ofile],
                       stdout=devnull, stderr=devnull)
        if verbose:
            print("Converted {0:s} to {1:s}".format(os.path.basename(ifile),
                                                    os.path.basename(ofile)))


def get_text(episode, verbose):
    """For a given episode, extract a mp3 audio file.

    Args:
        episode: String describing the episode to parse
        verbose: Boolean value. Should progress be printed to the console.
    Returns:
        None
    """
    paths = get_io_paths(episode)
    ifile = paths['ifile']
    ofile = paths['ifile_srt']

    with open(os.devnull, 'w') as devnull:
        if os.path.isfile(ofile):
            os.remove(ofile)
        subprocess.run(["ffmpeg", "-i", ifile, "-ab", "192k", ofile],
                       stdout=devnull, stderr=devnull)
        if verbose:
            print("Converted {0:s} to {1:s}".format(os.path.basename(ifile),
                                                    os.path.basename(ofile)))


def get_args():
    """Return the argument parser for this script.
    """
    desc = 'Extract mp3 and srt files.'
    parser = default_option_parser(desc)
    parser.add_argument('--audio', dest='audio', action='store_true')
    parser.add_argument('--text', dest='text', action='store_true')
    parser.add_argument('--verbose', dest='verbose', action='store_true')

    return parser.parse_args()


def run_text_audio_convert():
    """Run the module with the selected user arguments.
    """
    args = get_args()

    for episode in get_episodes(args):

        if args.audio:
            get_audio(episode, args.verbose)

        if args.text:
            get_text(episode, args.verbose)


if __name__ == "__main__":
    run_text_audio_convert()
