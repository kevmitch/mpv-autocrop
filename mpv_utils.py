import os,sys,shutil
from subprocess import Popen,PIPE,STDOUT
from contextlib import contextmanager
import mpv_utils

def import_err_msg(module=None,package=None):
    assert module and packge
    print """ This script requires %s
    On Debian/Ubuntu:
    apt-get install %s
    """%(module,package)
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    import_err_msg("numpy","python-numpy")
try:
    from scipy.ndimage import imread
except ImportError:
    import_err_msg("scipy","python-scipy")
try:
    import PIL
except ImportError:
    import_err_msg("python imaging library","python-imaging")



@contextmanager
def tmp_dir():
    """
    safe temporary directory context manager
    creates a temporary directory and returns it's path
    to be used in a with statment
    """
    import tempfile
    tmp_dir_path=tempfile.mkdtemp()
    yield tmp_dir_path
    #execute body of with statment
    shutil.rmtree(tmp_dir_path)

@contextmanager
def tmp_file():
    """
    safe temporary file context manager
    creates a temporary file and returns it's path
    to be used in a with statment
    """
    import tempfile
    tmp_fd,tmp_file_path=tempfile.mkstemp(text='true')
    yield tmp_file_path
    #execute body of with statment
    os.close(tmp_fd)
    os.remove(tmp_file_path)

script_dir,this_file=os.path.split(__file__)
default_playlist_script=os.path.join(script_dir,'write_playlist.lua')
def get_playlist_files(mpv_args,mpv_lua_script=default_playlist_script):
    """
    invoke mpv with the write_playlist.lua script and return the playlist as a python list
    """
    for func in os.path.expanduser,os.path.abspath:
        mpv_lua_script=func(mpv_lua_script)
    mpv_lua_script_name,ext=os.path.splitext(os.path.basename(mpv_lua_script))
    with tmp_file() as tmp_path:
        cmd=['mpv']+mpv_args
        cmd+=['--lua=%s'%mpv_lua_script,
              '--lua-opts=%s.out_file=%s'%(mpv_lua_script_name,tmp_path),
              '--vo=null',
              '--ao=null',
              '--no-audio',
              '--no-cache',
              '--no-sub']

        p=Popen(cmd,stdout=PIPE,stderr=STDOUT)
        stdout,stderr=p.communicate()
        rc=p.wait()
        if rc!=0:
            print 'mpv get playlist command exited with non-zero status'
            print 'COMMAND WAS'
            print cmd
            print 'STDOUT/STDERR was'
            print stdout
            sys.exit(1)

        with open(tmp_path,'r') as tmp_object:
            playlist=tmp_object.read().strip('\0')
            if len(playlist)==0:
                playlist=[]
            else:
                playlist=playlist.split('\0')
    return playlist

default_scan_script=os.path.join(script_dir,'scan.lua')
def sample_screenshots(nshots,mpv_lua_script=default_scan_script,mpv_args=[]):
    """
    invoke mpv with the scan.lua script and image vo and return a numpy array of screenshots
    """
    for func in os.path.expanduser,os.path.abspath:
        mpv_lua_script=func(mpv_lua_script)
    mpv_lua_script_name,ext=os.path.splitext(os.path.basename(mpv_lua_script))
    # don't += here since keyword arguments are like static function variables,
    # but the explicit assignment creates a new local instance
    mpv_args=mpv_args+['--no-cache',
                       '--lua=%s'%(mpv_lua_script),
                       '--lua-opts=%s.num_frames=%d'%(mpv_lua_script_name,nshots)]
    return dump_images(mpv_args=mpv_args)

def dump_images(mpv_args=[]):
    """
    invoke mpv with the scan.lua script and image vo and return a numpy array of screenshots
    """
    with tmp_dir() as tmp_dir_path:
        cmd=['mpv']+mpv_args
        cmd+=['--no-config',
              '--no-resume-playback',
              '--vo=image:outdir=%s'%tmp_dir_path,
              '--ao=null',
              '--no-audio']
        print ' '.join(cmd)
        p=Popen(cmd,stdout=PIPE,stderr=STDOUT)
        stdout,stderr=p.communicate()
        rc=p.wait()
        if rc!=0:
            print 'mpv screenshot command exited with non-zero status'
            print 'COMMAND WAS'
            print cmd
            print 'STDOUT/STDERR was'
            print stdout
            sys.exit(1)
        fpaths=[os.path.join(tmp_dir_path,fname) for fname in os.listdir(tmp_dir_path)]

        ims=imread(fpaths[0])
        shape=[len(fpaths)]+list(ims.shape)
        ims.resize(shape,refcheck=False)#add spaces for the other images
        for i in xrange(1,len(fpaths)):
            ims[i]=imread(fpaths[i])
    return ims
