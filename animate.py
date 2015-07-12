import csv
import glob
import math
import os
import shutil
import subprocess
import tempfile


def animate(args):
    gridfile = path(args.dir, ext='txt')
    bgfile = image_path(args.dir, 'background.png')
    audiopath = path(args.dir, ext='wav')
    videopath = path(args.dir, ext='mp4')
    frames = Frames(args.fps, bgfile)
    fps = args.fps
    with open(gridfile, 'r') as grid:
        gridreader = csv.reader(grid, delimiter='\t')
        # The first line puts the following lines in the context of a larger
        # video; we just want the onset from it so that we can make all of the
        # following onsets and offsets relative to 0.
        context = gridreader.next()
        start = int(context[2])
        for row in gridreader:
            # Elan inserts a column we don't care about.
            obj, _, onset, offset, dur, action = row
            onset, offset = int(onset) - start, int(offset) - start
            first = onset == 0
            imagespath = image_path(args.dir, os.path.join(obj, action))
            images = Images.for_path(imagespath)
            frames.assign_images(images, onset, offset, first)
    composite_dir = tempfile.mkdtemp(prefix='composite_', dir=args.dir)
    frames.composite(composite_dir)
    make_video(composite_dir, audiopath, videopath)
    if not args.stills:
        shutil.rmtree(composite_dir)


def make_video(composite_dir, audiopath, videopath):
    # ffmpeg -r 25 -f image2 -i IMAGE_GLOB -i WAV -vcodec libx264 -crf 25  OUT
    image_glob = os.path.join(composite_dir, '%05d.jpg')
    subprocess.call(
        ['ffmpeg',
         '-loglevel', 'warning',
         '-y',
         '-r', '25', 
         '-f', 'image2',
         '-i', image_glob,
         '-i', audiopath,
         '-pix_fmt', 'yuvj420p',
         '-vcodec', 'libx264',
         '-crf', '25',
         '-ac', '2',
         videopath])


def path(dirname, filename=None, ext=None):
    dirname = os.path.normpath(dirname)
    if filename is None:
        filename = dirname
    if ext is not None:
        filename = filename + '.' + ext
    return os.path.join(dirname, filename)


def image_path(dirname, filename):
    return path(dirname, os.path.join("images", filename))


class Frames(object):

    def __init__(self, fps, bgpath):
        self.frame_len = 1000.0 / fps
        self.bgpath = bgpath
        self.frames = []

    def assign_images(self, images, onset, offset, first=False):
        subset = self.find_frames(onset, offset, first)
        k = float(len(images)) / len(subset)
        for i, frame in enumerate(subset):
            img_index = int(math.floor(i * k))
            frame.add_image(images.path_for_index(img_index))

    def find_frames(self, onset, offset, first):
        subset = []
        onset_frame = self.round_to_frame(onset) + 1
        offset_frame = self.round_to_frame(offset)
        if first:
            onset_frame -= 1
        for i in range(onset_frame, offset_frame + 1):
            subset.append(self.get_frame(i))
        return subset

    def composite(self, outdir):
        for i, frame in enumerate(self.frames):
            outpath = os.path.join(outdir, "%05d.jpg" % i)
            frame.composite(outpath)

    def get_frame(self, n):
        num_frames = len(self.frames)
        if num_frames < n + 1:
            for i in range(num_frames, n + 1):
                self.frames.append(Frame(self.bgpath))
        return self.frames[n]

    def round_to_frame(self, time):
        return int(math.ceil(time / self.frame_len))


class Frame(object):

    def __init__(self, bgpath):
        self.images = [bgpath]

    def add_image(self, path):
        self.images.append(path)

    def composite(self, outpath):
        cmd = (['gm', 'convert'] + self.images + ['-flatten', outpath])
        subprocess.call(cmd)


class Images(object):
    cache = {}

    @staticmethod
    def for_path(dirpath):
        if dirpath not in Images.cache:
            Images.cache[dirpath] = Images(dirpath)
        return Images.cache[dirpath]

    def __init__(self, dirpath):
        self.paths = list(glob.iglob(os.path.join(dirpath, '*.png')))

    def __len__(self):
        return len(self.paths)

    def path_for_index(self, i):
        return self.paths[i]
