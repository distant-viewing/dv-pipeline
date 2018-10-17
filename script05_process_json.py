# -*- coding: utf-8 -*-
"""Convert dvt json files to semantic csv output.

This callable module is used to convert the jsonl files from the distant
viewing module into csv files. You can select the series and (optionally)
the season and episodes using command line arguments.

Example:
    To process the first 5 episodes from season 2 of Bewitched,
    we would run the following:

        $ python3 script05_process_json.py --series bw --season 2 \
                                           --episode 1 2 3 4 5
"""
import logging
import os
from os.path import join
import pickle
import re
import subprocess

import numpy as np
import pandas as pd

from utils import default_option_parser, get_episodes, get_io_paths, \
                  load_jsonl, norm_array, read_user_properties


class JsonProcessor():
    """Load and process json files.
    """
    def __init__(self, path, fprint):
        self.fprint = fprint
        self.video = "unknown"
        self.sid = 0
        self.last_frame = 0
        self.last_hist = np.zeros((16 * 3,), dtype=np.int64)
        self.data = None
        self.output = dict(frame=[], shots=[], faces=[], yolos=[], meta={})

        self.load(path)

    def _get_character(self, embed):
        embed = norm_array(embed)
        nssim = -1
        nchar = "unknown"

        for key, val in self.fprint.items():
            tsim = np.sum(val * embed)
            if tsim > nssim:
                nssim = tsim
                nchar = key

        return nssim, nchar

    def _add_faces(self, line, frame):

        for face in line['face']:
            score, cname = self._get_character(face['embed'])
            self.output['faces'].append({"video": self.video,
                                         "frame": frame,
                                         "sid": self.sid,
                                         "character": cname,
                                         "top": face['box']['top'],
                                         "bottom": face['box']['bottom'],
                                         "left": face['box']['left'],
                                         "right": face['box']['right'],
                                         "score": score,
                                         "overlap": face['hog_overlap']})

    def _add_frame(self, frame, dval, hval):

        self.output['frame'].append({"video": self.video,
                                     "frame": frame,
                                     "sid": self.sid,
                                     "dval": dval,
                                     "hval": hval})

    def _add_objects(self, line, frame):

        for obj in line['object']:
            self.output['yolos'].append({"video": self.video,
                                         "frame": frame,
                                         "sid": self.sid,
                                         "class": obj['class'],
                                         "top": obj['box']['top'],
                                         "bottom": obj['box']['bottom'],
                                         "left": obj['box']['left'],
                                         "right": obj['box']['right'],
                                         "score": obj['score']})

    def _process_frame(self, line):

        frame = line['frame']
        this_hist = np.array(line['hist']['hsv'])
        hval = np.mean(np.abs(self.last_hist - this_hist))
        self.last_hist = this_hist
        if 'diff' in line:
            dval = line['diff']['decile'][5]
        else:
            dval = 0
        self._add_frame(frame, dval, hval)
        if dval > 12 and hval > 4000:
            if frame - self.last_frame > 12:
                self.output['shots'].append({"video": self.video,
                                             "frame_start": self.last_frame,
                                             "frame_stop": frame - 1,
                                             "sid": self.sid})
                self.last_frame = frame
                print("Finished scene number {0:03d}.".format(self.sid))
                self.sid = self.sid + 1
        if 'object' in line:
            self._add_objects(line, frame)
        if 'face' in line:
            self._add_faces(line, frame)

    def load(self, path):
        """Load json data from file located at 'path'.
        """

        self.data = load_jsonl(path)
        for line in self.data:
            if line['type'] == "video":
                self.video = line['video']
                self.output['meta'] = line
            if line['type'] == "frame":
                self._process_frame(line)

    def get_data(self):
        """Return of a tuple of pandas DataFrame objects.
        """

        video = pd.DataFrame({'video': [self.output['video']],
                              'fps': [self.output['meta']['fps']],
                              'frames': [self.output['meta']['frames']],
                              'width': [self.output['meta']['width']],
                              'height': [self.output['meta']['height']]})
        frame = pd.DataFrame(self.output['frame'])
        shots = pd.DataFrame(self.output['shots'])
        faces = pd.DataFrame(self.output['faces'])
        yolos = pd.DataFrame(self.output['yolos'])

        video = video[["video", "fps", "frames", "width", "height"]]
        frame = frame[["video", "frame", "sid", "dval", "hval"]]
        shots = shots[["video", "frame_start", "frame_stop", "sid"]]
        faces = faces[["video", "frame", "sid", "character", "top", "bottom",
                       "left", "right", "score", "overlap"]]
        yolos = yolos[["video", "frame", "sid", "class", "top", "bottom",
                       "left", "right", "score"]]
        return video, frame, shots, faces, yolos


def get_chapter_breaks(vpath):
    """Return DataFrame of the chapter breaks.
    """
    assert os.path.exists(vpath)

    vname = os.path.basename(vpath)[:-4]
    psub = subprocess.Popen(['ffprobe', vpath],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    _, err = psub.communicate()

    merr = err.decode("utf-8").split("\n")

    start = []
    end = []
    chapters = [x for x in merr if re.match("    Chapter #0:[0-9]", x)]
    for chap in chapters:
        start.append(float(re.search(" start [0-9]+.[0-9]+",
                                     chap).group(0)[7:]))
        end.append(float(re.search(" end [0-9]+.[0-9]+", chap).group(0)[5:]))

    dframe = pd.DataFrame({'video': vname, 'chapter': range(len(start)),
                           'start': start, 'end': end})
    dframe = dframe[['video', 'chapter', 'start', 'end']]

    return dframe


def _time_to_seconds(time):
    hours = int(time[0:2])
    minutes = int(time[3:5])
    seconds = int(time[6:8])
    msec = int(time[9:12])
    return msec/1000 + seconds + minutes * 60 + hours * 60 * 60


def get_subtitles(episode, cpath):
    """Return DataFrame of the subtitles.
    """

    with open(cpath, 'r') as fin:
        srt_lines = fin.readlines()

    srt_parse = []
    nline = []
    for line in srt_lines:
        if line == "\n":
            start = _time_to_seconds(nline[1][:-1])
            end = _time_to_seconds(nline[1][17:])
            text = " ".join(nline[2:]).replace("\n", "")
            text = re.sub("<[^>]+>", " ", text).strip()
            text = re.sub("[ ]+", " ", text)
            srt_parse.append({'start': start,
                              'end': end,
                              'text': text})
            nline = []
        else:
            nline.append(line)

    dframe = pd.DataFrame(srt_parse)
    dframe['video'] = episode + ".mp4"
    dframe = dframe[['video', 'start', 'end', 'text']]

    return dframe


def get_args():
    """Return the argument parser for this script.
    """
    desc = 'Convert jsonl files into semantic csv files.'
    parser = default_option_parser(desc)
    parser.add_argument('--verbose', dest='verbose', action='store_true')
    parser.add_argument('--breaks', dest='ch_breaks', action='store_true')
    parser.add_argument('--titles', dest='sub_titles', action='store_true')

    return parser.parse_args()


def process_csv_files():
    """Convert all of the selected jsonl files into csv files
    """
    args = get_args()
    fdir = join(read_user_properties()['basepath'], "model", "fprint")

    with open(join(fdir, args.series + "fingerprint.pickle"), "rb") as fin:
        fprint = pickle.load(fin)

    for episode in get_episodes(args):
        paths = get_io_paths(episode)

        # process the json file; extract frames, shots, faces, and objects
        jprc = JsonProcessor(path=join(paths['spath'], episode + "-dvt.jsonl"),
                             fprint=fprint)
        video, frame, shots, faces, yolos = jprc.get_data()

        # save dvt extracted data in csv files
        video.to_csv(join(paths['spath'], episode + "-video.csv"), index=False)
        frame.to_csv(join(paths['spath'], episode + "-frame.csv"), index=False)
        shots.to_csv(join(paths['spath'], episode + "-shots.csv"), index=False)
        faces.to_csv(join(paths['spath'], episode + "-faces.csv"), index=False)
        yolos.to_csv(join(paths['spath'], episode + "-yolos.csv"),
                     index=False)

        # get chapter breaks from the mp4 file
        if args.ch_breaks:
            chaps = get_chapter_breaks(paths['ifile'])
            chaps.to_csv(join(paths['spath'], episode + "-chaps.csv"),
                         index=False)

        # get subtitles as DataFrame and save as csv file
        if args.ch_breaks:
            title = get_subtitles(episode, paths['ifile_srt'])
            title.to_csv(join(paths['spath'], episode + "-title.csv"),
                         index=False)

        # echo progress
        if args.verbose:
            print("Finished with {0:s}".format(episode))


if __name__ == "__main__":
    process_csv_files()
