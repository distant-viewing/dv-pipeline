# -*- coding: utf-8 -*-
"""Run distant viewing toolkit over video files

This callable module is used to run the distant viewing toolkit over
a set of raw mp4 files. You can select the series and (optionally)
the season and episodes using command line arguments. Other arguments
determine the specific annotators that will be run.

Example:
    To process the first 5 episodes from season 2 of Bewitched,
    we would run the following:

        $ python3 run_dvt.py --series bw --season 2 --episode 1 2 3 4 5

Section breaks are created by resuming unindented text. Section breaks
are also implicitly created anytime a new section starts.
"""

import os
from os.path import join

from utils import default_option_parser, get_episodes, get_io_paths


def setup_tensorflow():
    """Help
    """
    import tensorflow as tf
    from keras.backend.tensorflow_backend import set_session

    config = tf.ConfigProto()
    config.gpu_options.per_process_gpu_memory_fraction = 0.5
    set_session(tf.Session(config=config))


def get_processor(args):
    """Help
    """
    import dvt

    vproc = dvt.video.VideoProcessor()
    vproc.load_annotator(dvt.frame.DiffFrameAnnotator())
    vproc.load_annotator(dvt.frame.HistogramFrameAnnotator())
    vproc.load_annotator(dvt.frame.TerminateFrameAnnotator())
    #vproc.load_annotator(dvt.frame.ObjectCocoFrameAnnotator())
    vproc.load_annotator(dvt.frame.FaceFrameAnnotator())
    if args.png_flag:
        vproc.load_annotator(dvt.frame.PngFrameAnnotator(output_dir="/"))
    return vproc


def process_video(vproc, video_file, json_file, frame_path, args):
    """Help
    """

    # make sure staging area has been created
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    # if creating frames, make sure output directory exists
    if args.png_flag:
        os.makedirs(frame_path, exist_ok=True)
        vproc.pipeline['png'].output_dir = frame_path

    # clear the pipeline and setup metadata
    vproc.pipeline['diff'].clear()
    vproc.setup_input(video_path=video_file, output_path=json_file)

    # run the pipeline
    vproc.process(verbose=args.verbose)


def get_args():
    """Help
    """
    desc = 'Run distant viewing toolkit on raw mp4 files.'
    parser = default_option_parser(desc)
    parser.add_argument('--frames', dest='png_flag', action='store_true')
    parser.add_argument('--verbose', dest='verbose', action='store_true')

    return parser.parse_args()


def run_pipeline():
    """Help
    """
    args = get_args()

    from keras import backend as K

    for episode in get_episodes(args):
        vproc = get_processor(args)

        paths = get_io_paths(episode)

        video_file = paths['ifile']
        json_file = join(paths['spath'], episode + "-dvt.jsonl")
        frame_path = paths['fpath']

        process_video(vproc, video_file, json_file, frame_path, args)

        K.clear_session()   # garbage collect for GPU memory


if __name__ == "__main__":
    run_pipeline()

