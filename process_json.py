# -*- coding: utf-8 -*-

import json
import os
import pickle
import re
import subprocess
import sys

from os.path import join

import numpy as np
import pandas as pd

# input parameters
if sys.platform == "darwin":
    base = "/Users/taylor/local/"
else:
    base = "/home/taylor/data/"

series = "idoj"
season = 5             # None for all
episode_numbers = [8, 9, 10, 11, 12, 13]  # None for all
verbose = True


def ensure_dir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def get_episodes(series, season=None, episode_numbers=None):
    episodes = os.listdir(join(base, "dv", "input", series))
    episodes = [x[:-4] for x in episodes if len(x.split("-")) == 3]
    episodes = sorted(episodes)
    if season is not None:
        season = "s{0:02d}".format(season)
        episodes = [ep for ep in episodes if ep.split("-")[1] == season]
    if episode_numbers is not None:
        en = ["e{0:02d}".format(x) for x in episode_numbers]
        episodes = [ep for ep in episodes if ep.split("-")[2] in en]
    return episodes


class JsonProcessor():

    def __init__(self, path, fprint, verbose=True):
        self.jpath = join(base, "dv", path)
        self.fprint = fprint
        self.verbose = verbose
        self.reset()

    def reset(self):
        self.video = "unknown"
        self.sid = 0
        self.last_frame = 0
        self.last_hist = np.zeros((16 * 3,), dtype=np.int64)
        self.frame = []
        self.shots = []
        self.faces = []
        self.yolos = []

    def _load_json(self):
        self.data = []
        with open(self.jpath) as f:
            for line in f:
                self.data.append(json.loads(line))

    def _get_character(self, embed):
        embed = process_embed(embed)
        nssim = -1
        nchar = "unknown"

        for k, v in self.fprint.items():
            tsim = np.sum(v * embed)
            if tsim > nssim:
                nssim = tsim
                nchar = k

        return nssim, nchar

    def _add_faces(self, line, frame):

        for face in line['face']:
            score, ch = self._get_character(face['embed'])
            self.faces.append({"video": self.video,
                               "frame": frame,
                               "sid": self.sid,
                               "character": ch,
                               "top": face['box']['top'],
                               "bottom": face['box']['bottom'],
                               "left": face['box']['left'],
                               "right": face['box']['right'],
                               "score": score,
                               "overlap": face['hog_overlap']})

    def _add_frame(self, line, frame, dval, hval):

        self.frame.append({"video": self.video,
                           "frame": frame,
                           "sid": self.sid,
                           "dval": dval,
                           "hval": hval})

    def _add_objects(self, line, frame):

        for obj in line['object']:
            self.yolos.append({"video": self.video,
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
        self._add_frame(line, frame, dval, hval)
        if dval > 12 and hval > 4000:
            if frame - self.last_frame > 12:
                self.shots.append({"video": self.video,
                                   "frame_start": self.last_frame,
                                   "frame_stop": frame - 1,
                                   "sid": self.sid})
                self.last_frame = frame
                if self.verbose:
                    print("Finished scene number {0:03d}.".format(self.sid))
                self.sid = self.sid + 1
        if 'object' in line:
            self._add_objects(line, frame)
        if 'face' in line:
            self._add_faces(line, frame)


    def run(self):

        self._load_json()
        for line in self.data:
            if line['type'] == "video":
                self.video = line['video']
                self.meta = line
            if line['type'] == "frame":
                self._process_frame(line)

    def get_data(self):

        video = pd.DataFrame({'video': [self.video],
                              'fps': [self.meta['fps']],
                              'frames': [self.meta['frames']],
                              'width': [self.meta['width']],
                              'height': [self.meta['height']]})
        frame = pd.DataFrame(self.frame)
        shots = pd.DataFrame(self.shots)
        faces = pd.DataFrame(self.faces)
        yolos = pd.DataFrame(self.yolos)

        video = video[["video", "fps", "frames", "width", "height"]]
        frame = frame[["video", "frame", "sid", "dval", "hval"]]
        shots = shots[["video", "frame_start", "frame_stop", "sid"]]
        faces = faces[["video", "frame", "sid", "character", "top", "bottom",
                       "left", "right", "score", "overlap"]]
        yolos = None #yolos[["video", "frame", "sid", "class", "top", "bottom",
                          #  "left", "right", "score"]]
        return video, frame, shots, faces, yolos

    def save_data(self):
        frame, shots, faces, yolo = get_data()
        frame.to_csv(video + "-frame.csv", index=False)
        shots.to_csv(video + "-shots.csv", index=False)
        faces.to_csv(video + "-faces.csv", index=False)
        #/yolos.yolos.to_csv(video + "-yolos.csv", index=False)


def process_embed(embed):
    embed = np.array(embed)
    embed = embed / np.sqrt(np.sum(embed**2))
    return embed


def load_json(jpath):
    data = []
    with open(jpath) as f:
        for line in f:
            data.append(json.loads(line))
    return data


def get_fprint(series):
    if not os.path.exists(series + "fingerprint.pickle"):
        if series == "bw":
            js = load_json(base + "/dv/stage/bw/bw-s02-e02-dvt.jsonl")
            js2 = load_json(base + "/dv/stage/bw/bw-s07-e02-dvt.jsonl")
            fprint = {'larry': process_embed(js[7921]['face'][0]['embed']),
                      'darrin': process_embed(js[8501]['face'][0]['embed']),
                      'sam': process_embed(js[12031]['face'][0]['embed']),
                      'endora': process_embed(js[12201]['face'][0]['embed']),
                      'darrin2': process_embed(js2[21141]['face'][0]['embed'])}
        elif series == "idoj":
            js = load_json(base + "/dv/stage/idoj/idoj-s02-e02-dvt.jsonl")
            fprint = {'tony': process_embed(js[4411]['face'][0]['embed']),
                      'alfred': process_embed(js[15391]['face'][0]['embed']),
                      'jeannie': process_embed(js[6671]['face'][0]['embed']),
                      'roger': process_embed(js[4301]['face'][0]['embed'])}
        elif series == "friends":
            js = load_json(base + "/dv/stage/friends/friends-s02-e03-dvt.jsonl")
            fprint = {'monica': process_embed(js[12081]['face'][0]['embed']),
                      'chandler': process_embed(js[18431]['face'][0]['embed']),
                      'rachel': process_embed(js[15951]['face'][0]['embed']),
                      'ross': process_embed(js[7591]['face'][0]['embed']),
                      'joey': process_embed(js[22151]['face'][0]['embed']),
                      'phoebe': process_embed(js[8831]['face'][0]['embed'])}

        else:
            raise ValueError('No fingerprint found for series "' + series + '"')

        with open(series + "fingerprint.pickle", "wb") as f:
            pickle.dump(fprint, f, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        with open(series + "fingerprint.pickle", "rb") as f:
            fprint = pickle.load(f)

    return fprint


def get_chapter_breaks(series, ep):
    vpath = join(base, "dv", "input", series,  ep + ".mp4")
    assert os.path.exists(vpath)

    vname = os.path.basename(vpath)[:-4]
    p = subprocess.Popen(['ffprobe', vpath],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    msg, err = p.communicate()

    r = re.compile("    Chapter #0:[0-9]")
    z = err.decode("utf-8").split("\n")

    start = []
    end = []
    chapters = [x for x in z if r.match(x)]
    for ch in chapters:
        start.append(float(re.search(" start [0-9]+.[0-9]+", ch).group(0)[7:]))
        end.append(float(re.search(" end [0-9]+.[0-9]+", ch).group(0)[5:]))

    df = pd.DataFrame({'video': vname, 'chapter': range(len(start)),
                       'start': start, 'end': end})
    df = df[['video', 'chapter', 'start', 'end']]

    return df


def time_to_seconds(time):
    hours = int(time[0:2])
    minutes = int(time[3:5])
    seconds = int(time[6:8])
    msec = int(time[9:12])
    return msec/1000 + seconds + minutes * 60 + hours * 60 * 60


def get_subtitles(series, ep):
    cpath = join(base, "input_video", series, "text", ep + ".srt")
    vpath = join(base, "input_video", series, "video", ep + ".mp4")
    vname = os.path.basename(vpath)[:-4]

    if not os.path.exists(cpath):
        assert os.path.exists(vpath)
        subprocess.call(["ffmpeg", "-i", vpath, cpath])

    with open(cpath, 'r') as f:
        x = f.readlines()

    z = []
    nline = []
    for line in x:
        if line == "\n":
            start = time_to_seconds(nline[1][:-1])
            end = time_to_seconds(nline[1][17:])
            text = " ".join(nline[2:]).replace("\n", "")
            text = re.sub("<[^>]+>", " ", text).strip()
            text = re.sub("[ ]+", " ", text)
            z.append({'start': start,
                      'end': end,
                      'text': text})
            nline = []
        else:
            nline.append(line)

    df = pd.DataFrame(z)
    df['video'] = vname
    df = df[['video', 'start', 'end', 'text']]

    return df


if __name__ == "__main__":
    fprint = get_fprint(series)

    episodes = get_episodes(series, season, episode_numbers)
    print(episodes)

    for ep in episodes:
        # process the json file; extract frames, shots, faces, and objects
        jp = JsonProcessor(path=join("stage", series, ep + "-dvt.jsonl"),
                           fprint=fprint, verbose=verbose)
        jp.run()
        video, frame, shots, faces, yolos = jp.get_data()

        # save dvt extracted data in csv files
        odir = join(base, "dv", "stage", series)
        ensure_dir(odir)
        video.to_csv(join(odir, ep + "-video.csv"), index=False)
        frame.to_csv(join(odir, ep + "-frame.csv"), index=False)
        shots.to_csv(join(odir, ep + "-shots.csv"), index=False)
        faces.to_csv(join(odir, ep + "-faces.csv"), index=False)
        #yolos.to_csv(join(odir, ep + "-yolos.csv"), index=False)

        # get chapter breaks from the mp4 file
        chap_breaks = get_chapter_breaks(series, ep)
        chap_breaks.to_csv(join(odir, ep + "-chaps.csv"), index=False)

        # get subtitles as DataFrame and save as csv file
        #stitles = get_subtitles(series, ep)
        #stitles.to_csv(join(odir, ep + "_title.csv"), index=False)

        # echo progress
        if verbose:
            print("finished with {0:s}".format(ep))

