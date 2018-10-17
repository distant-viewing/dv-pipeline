# -*- coding: utf-8 -*-

import os
from os.path import join

import dvt

import tensorflow as tf

from keras import backend as K
from keras.backend.tensorflow_backend import set_session
from keras.applications.vgg19 import preprocess_input

# make sure keras does not take all of the available GPU
# when running on the server
config = tf.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.1
set_session(tf.Session(config=config))

# input parameters
base = "/home/taylor/data"
series = "bw"
season = 7            # None for all
episode_numbers = [2] # None for all
verbose = True 
png_flag = True


def ensure_dir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def get_processor():
    vp = dvt.video.VideoProcessor()
    vp.load_annotator(dvt.frame.DiffFrameAnnotator())
    vp.load_annotator(dvt.frame.HistogramFrameAnnotator())
    vp.load_annotator(dvt.frame.TerminateFrameAnnotator())
    vp.load_annotator(dvt.frame.PngFrameAnnotator(output_dir="/"))
    return vp


def process_video(vp, vpath, jpath, ipath):
    ensure_dir(ipath)

    vp.pipeline['png'].output_dir = ipath
    vp.pipeline['diff'].clear()
    vp.setup_input(video_path=vpath, output_path=jpath)
    vp.process(verbose=verbose)


def get_episodes(series, season=None, episode_numbers=None):
    episodes = os.listdir(join(base, "input_video", series, "video"))
    episodes = [x[:-4] for x in episodes if len(x.split("_")) == 3]
    episodes = sorted(episodes)
    if season is not None:
        season = "s{0:02d}".format(season)
        episodes = [ep for ep in episodes if ep.split("_")[1] == season]
    if episode_numbers is not None:
        en = ["e{0:02d}".format(x) for x in episode_numbers]
        episodes = [ep for ep in episodes if ep.split("_")[2] in en]
    return episodes


if __name__ == "__main__":

    episodes = get_episodes(series, season, episode_numbers)

    for ep in episodes:
        vp = get_processor()
        vpath = join(base, "input_video", series, "video", ep + ".mp4")
        jpath = "temp.jsonl"
        ipath = join(base, "dv_data", "frames", series, ep)

        print("Starting video  {0:s}".format(ep))
        process_video(vp, vpath, jpath, ipath)
        print("Done with video {0:s}".format(ep))

        K.clear_session() # garbage collect for GPU memory


