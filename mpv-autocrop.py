#!/usr/bin/env python
import os,sys,shutil,re,argparse
from subprocess import Popen,PIPE,STDOUT
from contextlib import contextmanager
import_err_msg="""
This script requires %s
On Debian/Ubuntu:
apt-get install %s
"""
try:
    import numpy as np
except ImportError:
    print import_err_msg%("numpy","python-numpy")
    sys.exit(1)
try:
    from scipy.ndimage import imread
except ImportError:
    print import_err_msg%("scipy","python-scipy")
    sys.exit(1)
try:
    import PIL
except ImportError:
    print import_err_msg%("python imaging library","python-imaging")
    sys.exit(1)

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
def get_screenshots(fname,nshots,mpv_lua_script=default_scan_script,mpv_args=[]):
    """
    invoke mpv with the scan.lua script and image vo and return a numpy array of screenshots
    """
    for func in os.path.expanduser,os.path.abspath:
        mpv_lua_script=func(mpv_lua_script)
    mpv_lua_script_name,ext=os.path.splitext(os.path.basename(mpv_lua_script))
    with tmp_dir() as tmp_dir_path:
        cmd=['mpv']+mpv_args
        cmd+=['--no-config',
              '--no-resume-playback',
              '--no-cache',
              '--hwdec=no',
              '--vo=image:format=pgm:outdir=%s'%tmp_dir_path,
              '--vf-add=dsize',
              '--ao=null',
              '--no-audio',
              '--no-sub',
              '--lua=%s'%(mpv_lua_script),
              '--lua-opts=%s.num_frames=%d'%(mpv_lua_script_name,nshots),
              fname]

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
        shape=[nshots]+list(ims.shape)
        ims.resize(shape,refcheck=False)#add spaces for the other images
        for i in xrange(1,len(fpaths)):
            ims[i]=imread(fpaths[i])
    return ims

def verify_crop(fname,nshots,ims,crop_top,crop_bot,crop_lft,crop_rgt,show_plot=False):
    """
    do another round of screenshots with the crop command this time and verify
    that the correct region is cropped
    """

    ims_crop_ref=ims[:,crop_top:,crop_lft:]
    if crop_bot>0:
        ims_crop_ref=ims_crop_ref[:,:-crop_bot,:]
    if crop_rgt>0:
        ims_crop_ref=ims_crop_ref[:,:,:-crop_rgt]
    nshots,Ny,Nx=ims.shape

    h=Ny-crop_top-crop_bot
    w=Nx-crop_lft-crop_rgt
    x=crop_lft
    y=crop_top

    ims_crop_test=get_screenshots(fname,nshots,mpv_args=['--vf-add=crop=%d:%d:%d:%d'%(w,h,x,y)])

    res=abs(ims_crop_test-ims_crop_ref)
    if res.max()!=0:
        print 'ERROR: mpv didn\'t crop as expected'
        for i,r in enumerate(res):
            print i,'residual=',r.max()
            if show_plot and r.max()>0:
                try:
                    import pylab as pl
                except ImportError:
                    print import_err_msg%("matplotlib","python-matplotlib")
                    sys.exit(1)
                    pl.ion()

                fig=pl.figure(1,dpi=150)
                fig.clf()
                ax=fig.add_subplot(221)
                ax.imshow(ims_crop_ref[i],cmap='gray',interpolation='nearest')
                ax=fig.add_subplot(222)
                ax.imshow(ims_crop_test[i],cmap='gray',interpolation='nearest')
                ax=fig.add_subplot(223)
                ax.imshow(res[i],cmap='gray',interpolation='nearest')
                pl.draw()
                print 'press enter to continue'
                raw_input()
        sys.exit(1)


def get_crop_cmd(fname,nshots=11,tol=0.02,pad=0,ignore_pixels=0,show_plot=False,verify=True):
    """
    compute the appropriate crop command for a given file
    """
    ims=get_screenshots(fname,nshots)

    nshots,Ny,Nx=ims.shape
    imax=float(np.iinfo(ims.dtype).max)
    ymx=ims.transpose((1,0,2)).reshape((Ny,-1)).max(axis=-1)/imax
    xmx=ims.transpose((2,1,0)).reshape((Nx,-1)).max(axis=-1)/imax

    # determine the cropping region where pixels average to greater than tol
    ygood=ymx>=tol
    xgood=xmx>=tol
    print ymx[:10],tol

    if ygood.size>0:
        crop_top=np.flatnonzero(ygood[ignore_pixels:]      )[0]
        if crop_top>0: crop_top+=ignore_pixels
        crop_bot=np.flatnonzero(ygood[::-1][ignore_pixels:])[0]
        if crop_bot>0: crop_bot+=ignore_pixels
    else:
        print 'WARNING: Seems to be nothing here to crop from'
        crop_top=crop_bot=0

    if xgood.size>0:
        crop_lft=np.flatnonzero(xgood[ignore_pixels:]     )[0]
        if crop_lft>0: crop_lft+=ignore_pixels
        crop_rgt=np.flatnonzero(xgood[::-1][ignore_pixels:])[0]
        if crop_rgt>0: crop_rgt+=ignore_pixels
    else:
        print 'WARNING: Seems to be nothing here to crop from'
        crop_lft=crop_rgt=0

    crop_top=max(0,crop_top-pad)
    crop_bot=max(0,crop_bot-pad)
    crop_rgt=max(0,crop_rgt-pad)
    crop_lft=max(0,crop_lft-pad)
    # these should be even to get exact results
    # (probably b/c of chroma subsampling)
    crop_top=np.floor(crop_top/2)*2
    crop_lft=np.floor(crop_lft/2)*2
    crop_bot=np.floor(crop_bot/2)*2
    crop_rgt=np.floor(crop_rgt/2)*2

    h=Ny-crop_top-crop_bot
    w=Nx-crop_lft-crop_rgt
    x=crop_lft
    y=crop_top

    print fname
    print 'crop_top=',crop_top
    print 'crop_bot=',crop_bot
    print 'crop_lft=',crop_lft
    print 'crop_rgt=',crop_rgt
    if show_plot:
        """visually check the crop detection"""
        try:
            import pylab as pl
        except ImportError:
            print import_err_msg%("matplotlib","python-matplotlib")
            sys.exit(1)
        pl.ion()

        fig=pl.figure(1,dpi=150)
        fig.clf()
        ax=fig.add_subplot(111)
        ax.imshow(ims.max(axis=0),cmap='gray',interpolation='nearest')
        ax.hlines((crop_top-0.5,Ny-crop_bot-0.5),-0.5,Nx-0.5,color='g')
        ax.vlines((crop_lft-0.5,Nx-crop_rgt-0.5),-0.5,Ny-0.5,color='g')

        fig=pl.figure(2)
        fig.clf()
        axs=map(lambda i:fig.add_subplot(2,2,i),xrange(1,5))

        ii=np.arange(ymx[:Ny/2].size)
        axs[0].plot(ymx[:Ny/2],-ii,'.r')
        axs[0].hlines(-(crop_top-0.5),0,1)
        axs[0].set_xlim(0,1)
        axs[0].set_ylim((-ii).min(),(-ii).max())

        ii=np.arange(ymx[Ny/2:].size)
        axs[1].plot(ymx[Ny/2:],ii[::-1],'.r')
        axs[1].hlines(crop_bot-0.5,0,1)
        axs[1].set_xlim(0,1)
        axs[1].set_ylim(ii.min(),ii.max())

        ii=np.arange(xmx[:Nx/2].size)
        axs[2].plot(ii,xmx[:Nx/2],'.b')
        axs[2].vlines(crop_lft-0.5,0,1)
        axs[2].set_ylim(0,1)
        axs[2].set_xlim(ii.min(),ii.max())

        ii=np.arange(xmx[Nx/2:].size)
        axs[3].plot(-ii[::-1],xmx[Nx/2:],'.b')
        axs[3].vlines(-(crop_rgt-0.5),0,1)
        axs[3].set_ylim(0,1)
        axs[3].set_xlim((-ii).min(),(-ii).max())

        pl.draw()
        print 'press enter to continue'
        raw_input()

    if crop_top>0 or crop_bot>0 or crop_lft>0 or crop_rgt>0:
        if verify: verify_crop(fname,nshots,ims,crop_top,crop_bot,crop_lft,crop_rgt,show_plot=show_plot)
        return ['--hwdec=no','--vf=crop=%d:%d:%d:%d'%(w,h,x,y)]
    else:
        return []

def main(mpv_args=[],**kwargs):
    # use mpv itself to figure out which arguments are playable items
    playlist_files=get_playlist_files(mpv_args)
    assert len(playlist_files)>0,"need at least one playable, but file found none"
    # remove those from the args list
    mpv_args=[arg for arg in mpv_args if arg not in playlist_files]
    # add them back with appropriate crop commands
    for playlist_file in playlist_files:
        mpv_args+=['--{']+get_crop_cmd(playlist_file,**kwargs)+[playlist_file,'--}']
    return ['mpv']+mpv_args

if __name__ == "__main__":
    cmd=sys.argv[0]
    parser = argparse.ArgumentParser(description="This script uses mpv to search its arguments for valid playlist items and automatically computes the appropriate --vf=crop command for each one. These are then amalgamated with any unparsed arguments and used to finally execute mpv.")
    parser.add_argument('--nshots','-n',type=int,default=11,help="number of screenshots from which to estimate the crop parameters")
    parser.add_argument('--tol','-t',type=float,default=0.1,help="the maximum brightness of pixels discarded by cropping (1.0 is full brightness)")
    parser.add_argument('--pad','-d',type=int,default=0,help="additional pixels to add to each side of the cropped image")
    parser.add_argument('--show-plot','-p',action='store_true',help="enable diagnostic plotting/visualisation (requires matplotlib)")
    parser.add_argument('--ignore-pixels','-i',type=int,default=0,help="number of pixels on the outter edge of the image to ignore")
    parser.usage=parser.format_usage().strip()+' [MPV_ARGS]'
    options,mpv_args=parser.parse_known_args(sys.argv[1:])
    options=vars(options)
    options['mpv_args']=mpv_args

    cmd=main(**options)
    print cmd
    os.execvp(cmd[0],cmd)
