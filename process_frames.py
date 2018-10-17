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
config.gpu_options.per_process_gpu_memory_fraction = 0.5
set_session(tf.Session(config=config))

# input parameters
base = "/home/taylor/data"
series = ""
season = [5]     # None for all
episode_numbers = [7, 8, 9, 10, 11, 12, 13] # None for all
verbose = False
png_flag = False

def ensure_dir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def create_model_h5():
    if not os.path.exists("../models"):
        raise NameError('You are not running this from the correct location.')

    if not os.path.exists("../models/vgg19_fc2.h5"):
        from keras.applications.vgg19 import VGG19
        from keras.models import Model
        vgg19_full = VGG19(weights='imagenet')
        vgg_fc2 = Model(inputs=vgg19_full.input,
                        outputs=vgg19_full.get_layer('fc2').output)
        vgg_fc2.save("../models/vgg19_fc2.h5")


def get_processor():
    km = dvt.frame.KerasFrameAnnotator(model_path="../models/vgg19_fc2.h5",
                                       preprocessor=preprocess_input)

    vp = dvt.video.VideoProcessor()
    vp.load_annotator(dvt.frame.DiffFrameAnnotator())
    vp.load_annotator(dvt.frame.HistogramFrameAnnotator())
    vp.load_annotator(dvt.frame.TerminateFrameAnnotator())
    #vp.load_annotator(dvt.frame.ObjectCocoFrameAnnotator())
    vp.load_annotator(dvt.frame.FaceFrameAnnotator())
    if png_flag:
        vp.load_annotator(dvt.frame.PngFrameAnnotator(output_dir="/"))
    #vp.load_annotator(km)
    return vp


def process_video(vp, vpath, jpath, ipath):
    ensure_dir(ipath)

    if png_flag:
        vp.pipeline['png'].output_dir = ipath
    vp.pipeline['diff'].clear()
    vp.setup_input(video_path=vpath, output_path=jpath)
    vp.process(verbose=verbose)


def get_episodes(series, season=None, episode_numbers=None):
    episodes = os.listdir(join(base, "input_video", series, "video"))
    episodes = [x[:-4] for x in episodes if len(x.split("_")) == 3]
    episodes = sorted(episodes)
    if season is not None:
        season = ["s{0:02d}".format(x) for x in season]
        episodes = [ep for ep in episodes if ep.split("_")[1] in season]
    if episode_numbers is not None:
        en = ["e{0:02d}".format(x) for x in episode_numbers]
        episodes = [ep for ep in episodes if ep.split("_")[2] in en]
    return episodes


if __name__ == "__main__":

    create_model_h5()
    episodes = get_episodes(series, season, episode_numbers)
    print(episodes)

    for ep in episodes:
        vp = get_processor()
        vpath = join(base, "input_video", series, "video", ep + ".mp4")
        jpath = join(base, "dv_data", "json", series, ep + ".jsonl")
        ipath = join(base, "dv_data", "frames", series, ep)

        print("Starting video  {0:s}".format(ep))
        process_video(vp, vpath, jpath, ipath)
        print("Done with video {0:s}".format(ep))

        K.clear_session() # garbage collect for GPU memory

