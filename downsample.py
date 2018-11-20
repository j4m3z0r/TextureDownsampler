#!/usr/bin/env python

'''
Simple script to downsample images to a more manageable size. Intended for use
with Blender, which becomes unwieldy if you don't have enough memory to store
all your textures in uncompressed format.

I recommend you use this by keeping a directory for your original textures, and
using this script to generate a new directory of images that have been
downsampled. This way you can use a symlink to switch between them.

This has all sorts of horrid implications for your workflow (you probably still
need a ridiculously capacious computer to do work on the original textures),
but it's probably slightly better than not having it.

At present it will only support JPEG and PNG textures. Any files that are not
named either *.png or *.jpg will just be copied from the source directory to
the target.

Images larger than MAX_RES in either dimension will be resized so that the
larger dimension is equal to MAX_RES, with the other dimension scaled
proportionally. Images smaller than or equal to MAX_RES will just be copied
directly (meaning that images that are already small enough are not
re-compressed)

JPEGs are written out at 100% compression, so there is a chance that the output
file will be larger on disk than the input. This is because we are optimizing
for RAM usage and don't want to unnecessarily sacrifice quality.
'''

import sys, os.path
from PIL import Image
from glob import glob
from shutil import copyfile

MAX_RES = 2048

class NoResizeNeeded(Exception) :
    pass

def resize(inFile) :
    img = Image.open(inFile)
    maxDimension = max(img.width, img.height)
    if maxDimension <= MAX_RES :
        raise NoResizeNeeded()

    ratio = float(maxDimension) / MAX_RES
    width = int(img.width / ratio)
    height = int(img.height / ratio)

    # FIXME: this should be done by converting from gamma space to linear,
    # resizing there and then transforming back to gamma space. Unfortunately
    # Pillow's support for this is a bit hit and miss so we just call the
    # resize() method directly.

    # We use Lanczos for resize since it generally performs better for
    # downsampling than Bicubic.
    resized = img.resize((width, height), Image.LANCZOS)
    return resized


def main(inDir, outDir) :
    if not os.path.isdir(outDir) :
        os.mkdir(outDir)

    allFiles = glob(os.path.join(inDir, '*'))

    imgFiles = []
    otherFiles = []

    extensions = set(['.png', '.jpg', '.jpeg'])
    for f in allFiles :
        basename, ext = os.path.splitext(f)
        if ext.lower() in extensions :
            imgFiles.append(f)
        else :
            otherFiles.append(f)

    # First copy over all the non image files
    for f in otherFiles :
        outPath = os.path.join(outDir, os.path.basename(f))
        print >> sys.stderr, 'Copying %s to %s' % (f, outPath)
        copyfile(f, outPath)

    for f in imgFiles :
        outPath = os.path.join(outDir, os.path.basename(f))
        print >> sys.stderr, 'Processing %s to %s' % (f, outPath)
        basename, ext = os.path.splitext(f)

        try :
            resized = resize(f)
        except NoResizeNeeded :
            copyfile(f, outPath)
            continue

        if ext.lower() in ('.jpeg', '.jpg') :
            resized.save(outPath, quality=100)
        else :
            copyfile(f, outPath)

if __name__ == '__main__' :
    if len(sys.argv) != 3 :
        print >> sys.stderr, "Usage: %s <input directory> <output directory>" % sys.argv[0]
        sys.exit(-1)

    main(*tuple(sys.argv[1:]))

