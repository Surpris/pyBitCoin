#-*- coding: utf-8 -*-

from keras.models import Sequential, Model
from keras.callbacks import CSVLogger, ModelCheckpoint, EarlyStopping
from sklearn.model_selection import train_test_split

import copy
import datetime
import glob
import numpy as np
import os
import pandas as pd
import pickle
from . import drawfigfunc as dff
import matplotlib.pyplot as plt

from PIL import Image

def grouping_dataset(filelist, labelData, nbr_of_grp, 
                     shuffle=True, seed=None):
    """
    Separate datasets into 'nbr_of_grp' groups.
    """
    if shuffle is True:
        if seed is not None and isinstance(seed, int):
            np.random.seed(seed)
        ind = np.random.permutation(np.arange(0, len(filelist))).astype("int32")
    else:
        ind = np.arange(0, len(filelist)).astype("int32")
    groups_X = []
    groups_Y = []
    grp_size = len(filelist) // nbr_of_grp
    for ii in range(nbr_of_grp-1):
        ind_ii = ind[ii*grp_size:(ii+1)*grp_size]
        groups_X.append(filelist[ind_ii])
        groups_Y.append(labelData[ind_ii])
    ind_ii = ind[(ii+1)*grp_size:]
    groups_X.append(filelist[ind_ii])
    groups_Y.append(labelData[ind_ii])
    return groups_X, groups_Y

def load_images_from_filelist(filelist, channel=1):
    img1 = np.array(Image.open(filelist[0]))[:,:,0]
    imglist_shape = (len(filelist), img1.shape[0], img1.shape[1], channel)
    imglist = np.zeros(imglist_shape)
    for ii in range(len(filelist)):
        img = Image.open(filelist[ii])
        if channel == 1:
            buff = np.array(img)[:,:,0][: ,:, None]
        elif channel == 3:
            buff = np.array(img)
        else:
            raise ValueError("channel must be 1 or 3.")
        imglist[ii] = buff.copy()
    imglist = imglist.astype("float") / 255.0
    return imglist

def create_model():
    pass

def train_with_groups(model, groups_Xpath_train, groups_y_train, 
                      X_test, y_test, channel=1, 
                      epochs=80, useCsvLogger=False, useModelCheckPoint=False):
    """
    Train a model with groups of datasets.
    """
    callbacks = []
    callbacks.append(EarlyStopping(monitor='val_loss', patience=2))
    # if useCsvLogger: # TODO: modify so that logging is for each group.
    #     callbacks.append(CSVLogger(basepath + "ML/history.csv"))
    # if useModelCheckPoint:
    #     callbacks.append(ModelCheckpoint(filepath=basepath+"ML/model_ep/ep{epoch:02d}.h5"))
        
    hists = []
    scores = []
    for ii in range(len(groups_Xpath_train)):
        X = load_images_from_filelist(groups_Xpath_train[ii], channel)
        y = groups_y_train[ii]
        hist = model.fit(X, y, batch_size=100, epochs=epochs,
                         validation_split=0.1, callbacks=callbacks, verbose=0)
        score = model.evaluate(X_test, y_test, verbose=0)
        print('Group {0}: loss={1:.4f}, accuracy={2:.4f}'.format(ii, score[0], score[1]))
        hists.append(hist)
        scores.append(score)
    return hists, scores

def plot_probability(model, testdata):
    """
    Plot predicted probability
    """
    ### Calculate probability
    if isinstance(model, Sequential):
        probs = model.predict_proba(testdata, verbose=0).T
    elif isinstance(model, Model):
        probs = model.predict(testdata, verbose=0).T
    else:
        raise TypeError()
    labels = ["high", "lose", "low"]

    ### Make histograms of each probability
    xbins = np.arange(0, 1.0, 0.05)
    hists = np.zeros((3, len(xbins)))
    for ii in range(len(probs)):
        hists[ii, :-1], _ = np.histogram(probs[ii], bins=xbins)
        hists[ii] /= hists[ii].sum()
    
    ### Plot probability of each dataset
    dff.makefig(18, 5)
    for ii in range(len(probs)):
        plt.subplot(1,3,ii + 1)
        plt.plot(probs[ii], linewidth=1.2)
        dff.arrangefig(xlabel="Time index", ylabel="Probability", title="Probability of {}".format(labels[ii]))
        plt.ylim(0, 1)
    plt.tight_layout()

    ### Plot histogram
    dff.makefig(18, 5)
    dxbins = np.diff(xbins)[0]
    for ii in range(len(hists)):
        plt.subplot(1,3,ii + 1)
        plt.bar(xbins, hists[ii], width=0.8*dxbins, color="g")
        dff.arrangefig(ylabel="Frequency")
        ax2 = plt.gca().twinx()
        ax2.plot(xbins, 1.0 - np.cumsum(hists[ii]), "r-", linewidth=1.5)
        dff.arrangefig(xlabel="Probability", ylabel="Accumulation", title="Hist of {}".format(labels[ii]))
        plt.ylim(0, 1)
    #     plt.yscale("log")
    plt.tight_layout()
    
    return

def calc_accuracy_above_threshold(model, X, y, threshold=0.5, verbose=0):
    """
    Calculate accuracy of model for the datasets
    where the predicted probability is above 'threshold'.
    """
    
    ### Extract the datasets with the predicted probability above 'threshold'
    if isinstance(model, Sequential):
        probs = model.predict_proba(X, verbose=0).T
    elif isinstance(model, Model):
        probs = model.predict(X, verbose=0).T
    else:
        raise TypeError()
    inds = np.zeros(probs.shape, dtype=bool)
    for ii in range(0, probs.shape[0]):
        inds[ii] = probs[ii] >= threshold
    ind_sum = inds.sum(axis=0) > 0
    
    ### Evaluate the datasets
    if inds.sum() == 0:
        score = [0, 0]
    else:
        score = model.evaluate(X[ind_sum], y[ind_sum], verbose=0)
    if verbose > 0:
        print("<# of events over threshold>")
        print("[high, lose, low]:", inds.sum(axis=1), ",total:", ind_sum.sum())
        print('loss=', score[0])
        print('accuracy=', score[1])
    return score