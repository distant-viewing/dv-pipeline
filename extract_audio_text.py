import argparse
import os
import subprocess

def get_audio(series):
  input_files = sorted(os.listdir("./" + series + "/video"))

  with open(os.devnull, 'w') as devnull:
      for f in input_files:
          fout = series + "/audio/" + f[:-4] + ".mp3"
          if os.path.isfile(fout):
              os.remove(fout)
          subprocess.run(["ffmpeg", "-i", series + "/video/" + f, "-ab", "192k", fout],
                         stdout=devnull, stderr=devnull)
          print("Converted {0:s} to {1:s}".format(f, os.path.basename(fout)))


def get_text(series):
  input_files = sorted(os.listdir("./" + series + "/video"))

  with open(os.devnull, 'w') as devnull:
      for f in input_files:
          fout = series + "/text/" + f[:-4] + ".srt"
          if os.path.isfile(fout):
              os.remove(fout)
          subprocess.run(["ffmpeg", "-i", series + "/video/" + f, fout],
                         stdout=devnull, stderr=devnull)

          print("Converted {0:s} to {1:s}".format(f, os.path.basename(fout)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("series")
    parser.add_argument("--audio", help="extract audio mp3 files",
                        action="store_true", default = False)
    parser.add_argument("--text", help="extract text srt files",
                        action="store_true", default = False)
    args = parser.parse_args()

    if args.audio:
        get_audio(args.series)

    if args.text:
        get_text(args.series)



