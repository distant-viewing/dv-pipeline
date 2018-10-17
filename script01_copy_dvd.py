# -*- coding: utf-8 -*-
"""Copy files from a DVD device to a local location.

This script is not called on the server, and so it does
not directly put the files in the correct location. The
mp4 files must be manually put into the correct location
when uploading via sftp.
"""
import os
import re
import shutil
import subprocess

from utils import iso8601, default_option_parser


def get_mount_pt():
    """Return location of the mounted DVD drive.

    The name of the device, on macOS, depends on the DVD itself and so we need
    to look this up.
    """
    mount_pt = [x for x in os.listdir("/Volumes") if x != "Macintosh HD"]
    mount_pt = os.path.join('/Volumes/', mount_pt[0])

    return mount_pt


def get_chapters():
    """Return a list of chapters on the DVD over 240 seconds.

    Some DVDs have very short filler chapters that are not actual episodes.
    Skip these. Runs HandBrakeCLI to find the chapters and lengths.
    """
    mount_pt = get_mount_pt()
    subp = subprocess.Popen(['HandBrakeCLI', '-i', mount_pt, '-t', '0',
                             '--min-duration', '240'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    _, err = subp.communicate()

    derr = err.decode("utf-8").split("\n")
    chapters = [x[8:-1] for x in derr if re.match("\\+ title [0-9]+:", x)]

    return chapters


def extract_from_dvd(chapter, output):
    """Download chapter by number

    Args:
        chapter: integer describing the chapter of interest.
        output: name of the output file.

    Returns:
        name of the output file, if successful.
    """
    mount_pt = get_mount_pt()

    cmd = ['HandBrakeCLI', '-i', mount_pt, '-t' + str(chapter),
           '-q', '18', '-s', '1,2,3,4,5,6', '-d', '-o', output]
    subp = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)
    subp.wait()

    return output


def frame_output_loc(series, season, episode):
    """Return name of the output based on series, season, and episode.

    Args:
        series: string describing the series.
        season: integer giving the season number.
        episode: integer giving the episode number.
    Returns:
        tuple containing two strings, the filename and name of the directory.
    """
    fname_out = "{0:s}-s{1:02d}-e{2:02d}.mp4".format(series, season,
                                                     episode)
    dir_out = os.path.join("/Users/taylor/local/input_video/", series)
    fname_out = os.path.join(dir_out, fname_out)

    if not os.path.exists(dir_out):
        os.makedirs(dir_out)

    return fname_out, os.path.basename(fname_out)


def _clean_temp_files():
    """Remove temporary files if they exist.
    """
    if os.path.exists("temp.mp4"):
        os.remove('temp.mp4')

    if os.path.exists("temp2.mp4"):
        os.remove('temp2.mp4')


def get_args():
    """Return the argument parser for this script.
    """
    desc = 'Extract mp4 files from DVD.'
    parser = default_option_parser(desc)
    parser.add_argument('--start', dest='episode_start', type=int, default=1)
    parser.add_argument('--verbose', dest='verbose', action='store_true')

    return parser.parse_args()


def copy_dvd():
    """Run the module with the selected user arguments.
    """
    args = get_args()

    msg = '[{0:s}] RUNNING FROM --- {1:s}_s{2:02d}_e{3:02d}'
    print(msg.format(iso8601(), args.series, args.season, args.episode_start))
    disk_chapters = get_chapters()

    this_episode = args.episode_start
    for chapter in disk_chapters:
        # what file are processing now
        _clean_temp_files()
        fout, fname = frame_output_loc(args.series, args.season, this_episode)
        print('[{0:s}] START PROCESSING --- {1:s}'.format(iso8601(), fname))

        # process the file
        extract_from_dvd(chapter, 'temp.mp4')
        shutil.copyfile('temp.mp4', fout)

        # report finished, clean up temporary files, increment episodes
        print('[{0:s}] FINISHED PROCESSING --- {1:s}'.format(iso8601(), fname))
        _clean_temp_files()
        this_episode = this_episode + 1


if __name__ == "__main__":
    copy_dvd()
