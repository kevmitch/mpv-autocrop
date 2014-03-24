mpv-autocrop
============
autocropping scripts for [mpv](https://github.com/mpv-player/mpv)


The main script is mpv-autocrop.py. It uses calls mpv with the lua scripts to search the arguments for valid playlist items and then automatically compute the appropriate --vf=crop command for each one. Finally it calls mpv with the the computed crop commands. Unparsed arguments are passed on to mpv.


dependencies
============
In order to run this program you need
* python-numpy
* python-scipy
* python imaging library
* mpv with lua scripting enabled
* python-matplotlib (for the --show-plot functionality)

examples
========
To play a file with its dark borders cut out, simply run

    $ mpv_autocrop.py file.mkv 
    
Adjust the tolerance for what is considered "black" as a fraction between 0 (no luma) and 1 (max luma)

    $ mpv_autocrop.py --tol 0.1 file.mkv
    
Any arguments not recognized by the script are passed on to mpv

    $ mpv_autocrop.py file.mkv --start=10:00 --vo=opengl-hq
    
You can get some diagnostic plotting with

    $ mpv_autocrop.py --show-plot file.mkv
        
And you can verify that mpv crops exactly as expected

    $ mpv_autocrop.py --verify file.mkv

