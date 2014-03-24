mpv-autocrop
============
autocropping scripts for mpv


This script uses mpv to search its arguments for valid playlist items and
automatically computes the appropriate --vf=crop command for each one. These
are then amalgamated with any unparsed arguments and used to finally execute
mpv.

Dependencies
============
In order to run this program you need
* python-numpy
* python-scipy
* python imaging library
* mpv with lua scripting enabled
* python-matplotlib (for the --show-plot functionality)

Usage
=====
    usage: usage: mpv-autocrop.py [-h] [--nshots NSHOTS] [--tol TOL] [--pad PAD] [--show-plot] [--ignore-pixels IGNORE_PIXELS] [MPV_ARGS]

Optional arguments
==================

    -h, --help            
show this help message and exit

    --nshots NSHOTS, -n NSHOTS
number of screenshots from which to estimate the crop parameters

    --tol TOL, -t TOL     
the maximum brightness of pixels discarded by cropping (1.0 is maximum brightness)

    --pad PAD, -d PAD     
additional pixels to add to each side of the cropped image

    --show-plot, -p
enable diagnostic plotting/visualisation (requires matplotlib)

    --ignore-pixels IGNORE_PIXELS, -i IGNORE_PIXELS
number of pixels on the outter edge of the image to ignore
