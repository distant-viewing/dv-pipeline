# -*- coding: utf-8 -*-

import contextlib
import datetime
import os
import pathlib
import platform
import re
import shutil
import stat
import subprocess

def iso8601():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def mount_dvd():
    mount_pt = "/mnt/dvd"
    mount_dv = "/dev/sr0"

    os_stat = os.stat(mount_dv)

    if os_stat.st_mode != 25008:
        subprocess.call(['sudo', 'chmod', '660', '/dev/sr0'])

    if os_stat.st_gid != 24:
        subprocess.call(['sudo', 'chgrp', 'cdrom', '/dev/sr0'])

    if not os.path.ismount(mount_pt):
        subprocess.call(['sudo', 'mount', '-t', 'udf', mount_dv, mount_pt])


def get_mount_pt():
    if platform.system() == 'Darwin': 
        mount_pt = [x for x in os.listdir("/Volumes") if x != "Macintosh HD"]
        mount_pt = os.path.join('/Volumes/', mount_pt[0])
    else:
        mount_pt = '/mnt/dvd/VIDEO_TS'

    return mount_pt


def get_chapters():
    mount_pt = get_mount_pt()
    p = subprocess.Popen(['HandBrakeCLI', '-i', mount_pt, '-t', '0',
                          '--min-duration', '240'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    msg, err = p.communicate()

    r = re.compile("\\+ title [0-9]+:")
    z = err.decode("utf-8").split("\n")
    chapters = [x[8:-1] for x in z if r.match(x)]

    return chapters


def extract_from_dvd(chapter, output):
    mount_pt = get_mount_pt()

    cmd = ['HandBrakeCLI', '-i', mount_pt, '-t' + str(chapter),
           '-q', '18', '-s', '1,2,3,4,5,6', '-d', '-o', output]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                         stderr=subprocess.STDOUT)
    p.wait()


def frame_output_loc(series, season, episode):
    fname_out = "{0:s}_s{1:02d}_e{2:02d}.mp4".format(series, season,
                                                     episode)
    if platform.system() == 'Darwin': 
        dir_out = os.path.join("/Users/taylor/local/input_video/", series)
    else:
        dir_out = os.path.join("/media/data/input_video/", series)

    fname_out = os.path.join(dir_out, fname_out)

    if not os.path.exists(dir_out):
        os.makedirs(dir_out)

    return fname_out, os.path.basename(fname_out)


def clean_temp_files():
    with contextlib.suppress(FileNotFoundError):
        os.remove('temp.mp4')

    with contextlib.suppress(FileNotFoundError):
        os.remove('temp2.mp4')


if __name__ == "__main__":
    series = "mtm"
    season = 7
    episode_start = 17
    msg = '[{0:s}] RUNNING FROM --- {1:s}_s{2:02d}_e{3:02d}'
    print(msg.format(iso8601(), series, season, episode_start))

    disk_chapters = get_chapters()
    #disk_chapters = ['1', '2', '3', '4', '5', '6', '7', '8']

    if platform.system() != 'Darwin':
        mount_dvd()

    this_episode = episode_start
    for chapter in disk_chapters:
        # what file are processing now
        clean_temp_files()
        fout, f = frame_output_loc(series, season, this_episode)
        print('[{0:s}] START PROCESSING --- {1:s}'.format(iso8601(), f))

        # process the file
        extract_from_dvd(chapter, 'temp.mp4')
        shutil.copyfile('temp.mp4', fout)

        # report finished, clean up temporary files, increment episodes
        print('[{0:s}] FINISHED PROCESSING --- {1:s}'.format(iso8601(), f))
        clean_temp_files()
        this_episode = this_episode + 1

