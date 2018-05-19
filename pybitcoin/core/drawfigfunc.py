# -*- coding: utf-8 -*-
# Self-made plotting class
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d import Axes3D

class Arrow3D(FancyArrowPatch):
    """
        3D arrowオブジェクトクラス。
        pyplot.ax.add_artist()に引数として入れれば描画される。
    """
    def __init__(self, xs, ys, zs, *args, **kwargs):
        FancyArrowPatch.__init__(self, (0,0), (0,0), *args, **kwargs)
        self._verts3d = xs, ys, zs

    def draw(self, renderer):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, renderer.M)
        self.set_positions((xs[0],ys[0]),(xs[1],ys[1]))
        FancyArrowPatch.draw(self, renderer)
import os

def makefig(w=6, h=5, dpi=100, fignum=None):
    if fignum is None:
        fig = plt.figure(figsize=(w, h), dpi=dpi)
    else:
        fig = plt.figure(fignum, figsize=(w, h), dpi=dpi)
    return fig

def arrangefig(xlabel=None, ylabel=None, title=None, ticks_fontsize=14, label_fontsize=14, grid=True, linewidth=0.75):
    if xlabel is not None:
        plt.xlabel(xlabel, fontsize=label_fontsize)
    if ylabel is not None:
        plt.ylabel(ylabel, fontsize=label_fontsize)
    if title is not None:
        plt.title(title, fontsize=label_fontsize)
    plt.xticks(fontsize=ticks_fontsize)
    plt.yticks(fontsize=ticks_fontsize)
    if grid is True:
        plt.grid(which='major', axis='x', linewidth=linewidth,
                 linestyle='-', color='0.75')
        plt.grid(which='major', axis='y', linewidth=linewidth,
                 linestyle='-', color='0.75')
        ax = plt.gca()
        ax.set_axisbelow(True)

def save(filepath, bbox_inches="tight", pad_inches=0.0, overwrite=True, dpi=100):
    save_count = 0
    _filepath = filepath + ""
    if overwrite == False:
        while(os.path.exists(filepath)):
            _ext = _filepath.split('.')[-1]
            save_count += 1
            _filepath = _filepath.replace('.'+_ext, '_save_{0:04d}.{1}'.format(save_count, _ext))
    plt.savefig(_filepath, bbox_inches=bbox_inches, pad_inches=pad_inches, dpi=dpi)

def Plot(x, y, ptype='plot', **kwargs):
    _color='r' if kwargs.get('color') is None else kwargs.get('color')
    if ptype is 'plot':
        if kwargs.get('marker') is not None:
            _marker = kwargs.get('marker')
            plt.plot(x, y, color=_color, marker=_marker)
        else:
            ls = 'solid' if kwargs.get('linestyle') is None else kwargs.get('linestyle')
            plt.plot(x, y, color=_color, ls=ls)
    else:
        if ptype is 'bar':
            aligns = ['edge', 'center']
            align = aligns[1] if kwargs.get('align') is None else kwargs.get('align')
            if align not in aligns:
                raise ValueError('align must be "{0}" or "{1}"'.format(aligns[0], aligns[1]))
            width=np.min(np.diff(x))*0.8 if kwargs.get('width') is None else kwargs.get('width')
            plt.bar(x, y, color=_color, width=width)

    _xlim = kwargs.get('xlim')
    _ylim = kwargs.get('ylim')
    if _xlim is not None: plt.xlim(_xlim[0], _xlim[1])
    if _ylim is not None: plt.ylim(_ylim[0], _ylim[1])

    linewidth=0.75 if kwargs.get('linewidth') is None else kwargs.get('linewidth')
    plt.grid(which='major', axis='x', linewidth=linewidth,
             linestyle='-', color='0.75')
    plt.grid(which='major', axis='y', linewidth=linewidth,
             linestyle='-', color='0.75')

    ticks_fontsize = 15 if kwargs.get('ticks_fontsize') is None else kwargs.get('ticks_fontsize')
    plt.xticks(fontsize=ticks_fontsize)
    plt.yticks(fontsize=ticks_fontsize)

    _xlog=False if kwargs.get('xlog') is None else kwargs.get('xlog')
    if _xlog is True:
        plt.xscale('log')
    _ylog=False if kwargs.get('ylog') is None else kwargs.get('ylog')
    if _ylog is True:
        plt.yscale('log')
    else:
        _sci=False if kwargs.get('sci') is None else kwargs.get('sci')
        if _sci is True:
            plt.ticklabel_format(style='sci',axis='y',scilimits=(0,0))

    label_fontsize = 15 if kwargs.get('label_fontsize') is None else kwargs.get('label_fontsize')
    if kwargs.get('xlabel') is not None:
        plt.xlabel(kwargs.get('xlabel'), fontsize=label_fontsize)
    if kwargs.get('ylabel') is not None:
        plt.ylabel(kwargs.get('ylabel'), fontsize=label_fontsize)
    if kwargs.get('title') is not None:
        plt.title(kwargs.get('title'), fontsize=label_fontsize)

def Imagesc(X, **kwargs):
    cmap=kwargs.get('cmap'); norm=kwargs.get('norm')
    interpolation=kwargs.get('interpolation'); alpha=kwargs.get('alpha')
    vmin=kwargs.get('vmin');vmax=kwargs.get('vmax')
    extent=kwargs.get('extent'); shape=kwargs.get('shape')
    filternorm=1 if kwargs.get('filternorm') is None else kwargs.get('filternorm')
    filterrad=4.0 if kwargs.get('filterrad') is None else kwargs.get('filterrad')
    imlim=kwargs.get('imlim'); resample=kwargs.get('resample')
    url=kwargs.get('url'); hold=kwargs.get('hold'); data=kwargs.get('data')

    plt.imshow(X, cmap, norm, 'auto', interpolation, alpha,
               vmin, vmax, 'lower', extent, shape, filternorm,
               filterrad, imlim, resample, url, hold, data)

    xlim = kwargs.get('xlim')
    ylim = kwargs.get('ylim')
    if xlim is not None: plt.xlim(xlim[0], xlim[1])
    if ylim is not None: plt.ylim(ylim[0], ylim[1])

    ticks_fontsize = 15 if kwargs.get('ticks_fontsize') is None else kwargs.get('ticks_fontsize')
    plt.xticks(fontsize=ticks_fontsize)
    plt.yticks(fontsize=ticks_fontsize)

    label_fontsize = 15 if kwargs.get('label_fontsize') is None else kwargs.get('label_fontsize')
    if kwargs.get('xlabel') is not None:
        plt.xlabel(kwargs.get('xlabel'), fontsize=label_fontsize)
    if kwargs.get('ylabel') is not None:
        plt.ylabel(kwargs.get('ylabel'), fontsize=label_fontsize)
    if kwargs.get('title') is not None:
        plt.title(kwargs.get('title'), fontsize=label_fontsize)
