# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 15:55:24 2015
image analysis functions for PIA.
@author: monika
"""
import numpy as np
from scipy import ndimage
#import matplotlib.pylab as plt
def rgb2gray(rgb):

    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b

    return gray
    
def cropImage(Image, xC, yC, bgSize, imSize):
    yMin = max(0,yC-bgSize)
    yMax = min(imSize[0],yC+bgSize)
    xMin = max(0,xC-bgSize)
    xMax = min(imSize[1],xC+bgSize)
    return Image[yMin:yMax, xMin:xMax], xMin, yMin
    
def calculateWithMask(bgImage, xNewNeuron,yNewNeuron,neuronSize,imSize):
    '''calculate a masked quantity'''
    mask = np.zeros(bgImage.shape, dtype=bool)
    # shade out a box
    yMinSRegion = max(0,yNewNeuron-neuronSize)
    yMaxSRegion = min(imSize[0],yNewNeuron+neuronSize)
    xMinSRegion = max(0,xNewNeuron-neuronSize)
    xMaxSRegion = min(imSize[1],xNewNeuron+neuronSize)

    mask[yMinSRegion:yMaxSRegion,xMinSRegion:xMaxSRegion] = True
        
    bgLevel = np.ma.average(np.ma.masked_array(bgImage, mask))
    return bgLevel

def findNeuron(bgImage, threshold, xNeuron,  yNeuron):
    """find bright object in small roi image."""
    mask = np.where(bgImage > threshold[0], 1, 0)
    mask = ndimage.binary_opening(mask,structure = np.ones((2,2)))
    mask = ndimage.binary_closing(mask)
        # --- Individually label all connected regions and get their center of mass
    label_im, nb_labels = ndimage.label(mask)
    centroids = ndimage.measurements.center_of_mass(bgImage, label_im, xrange(1,nb_labels+1))
    # --- select brightest object by default (mean brightness)
    meanBrightness = ndimage.measurements.mean(bgImage, label_im, xrange(1,nb_labels+1))
#        # --- Calculate the distance of each new cms to the old neuron position
#        # --- and select the new neuron position to be the object closest to
#        # --- the old location
#    dist = []
#    for coords in centroids:
#        dist.append((coords[0]-yNeuron)**2 + (coords[1]-xNeuron)**2)
#    if len(dist)==0:
#        yNewNeuron,xNewNeuron = yNeuron,  xNeuron
#    else:
#        loc = np.argmin(dist)
#        yNewNeuron,xNewNeuron = centroids[loc]
    if nb_labels >1:
        loc = np.argmax(meanBrightness)
        yNewNeuron,xNewNeuron = centroids[loc]
    else:
        yNewNeuron,xNewNeuron = yNeuron,  xNeuron
        loc = -1  
    neuronObject = np.where(label_im == loc+1,0,1)
    neuronArea = np.sum(neuronObject)
        # --- Get average of the neuron fluoresence --- 
    tmp_neuron = np.ma.masked_array(bgImage, neuronObject)
    newNeuronAverage = np.ma.average(tmp_neuron[tmp_neuron>threshold[1]])
        
    return yNewNeuron,xNewNeuron, newNeuronAverage,neuronArea,  neuronObject

def fluorescence(Image, bgSize,neuronSize, threshold, xC, yC):
    """Calculate fluorescene in a larger ROI around coordinates xC and yC."""
    imSize = Image.shape
    # deal with RGB images
    if len(imSize) == 3:
        Image = rgb2gray(Image)
     # -- Check if box needs to be cropped as it's ranging beyond the image
    bgImage, xMin, yMin = cropImage(Image, xC, yC, bgSize, imSize)
    # --- Determine position of neuron; might not be centered due to cropping
    height, width = bgImage.shape
    
    xNeuron = xC - xMin
    yNeuron = yC - yMin
    # --- Get number of total pixels in the BG box and determine an intensity
    # --- threshold at which N % of the pixels have less intensity
    threshold = np.percentile(bgImage, [threshold, (100+threshold)/2.])
    yNewNeuron,xNewNeuron, newNeuronAverage, neuronArea,_ = findNeuron(bgImage, threshold, xNeuron,  yNeuron)
    bgLevel = calculateWithMask(bgImage, xNewNeuron,yNewNeuron,neuronSize,imSize)
   
    return bgLevel, newNeuronAverage, xNewNeuron+xMin, yNewNeuron+yMin, neuronArea, 1, 1, 1, 1 ,1
    
    
    
def dualFluorescence(Image, bgSize,neuronSize, threshold, xC, yC, shift):
    """Calculate fluorescene in a larger ROI around coordinates xC and yC."""
    imSize = Image.shape
    # deal with RGB images
    if len(imSize) == 3:
        Image = rgb2gray(Image)
     # -- Check if box needs to be cropped as it's ranging beyond the image
    bgImage, xMin, yMin = cropImage(Image, xC, yC, bgSize, imSize)
    # --- Determine position of neuron; might not be centered due to cropping
    height, width = bgImage.shape
    
    xNeuron = xC - xMin
    yNeuron = yC - yMin
    # --- Get number of total pixels in the BG box and determine an intensity
    # --- threshold at which N % of the pixels have less intensity
    threshold = np.percentile(bgImage, [threshold, (100+threshold)/2.])
    yNewNeuron,xNewNeuron, newNeuronAverage, neuronArea,neuronObject = findNeuron(bgImage, threshold, xNeuron,  yNeuron)
    #threshold = np.sort(bgImage, axis=None)[-int((1-threshold/100.)*height*width)]

    # --- Prepare a mask that shows the position of each individual pixel
    # --- that exceeds the threshold. Clear all objects that are less than
    # --- 2 x 2 pixels and connect all single pixel gaps.
    bgLevel = calculateWithMask(bgImage, xNewNeuron,yNewNeuron,neuronSize,imSize)
    
    # --- Deal with shift
    GreenImage, _,_ = cropImage(Image, xC+shift[0], yC+shift[1], bgSize, imSize)
    
    tmpGreenNeuron = np.ma.masked_array(GreenImage, neuronObject)
    if GreenImage.shape!= neuronObject:
        return bgLevel, newNeuronAverage, xNewNeuron+xMin, yNewNeuron+yMin, neuronArea, 1 , 1, xNewNeuron+xMin+shift[0], yNewNeuron+yMin+shift[1] ,neuronArea,
    
    GreenNeuronAverage = np.ma.average(tmpGreenNeuron)
    GreenbgLevel = calculateWithMask(GreenImage, xNewNeuron,yNewNeuron,neuronSize,imSize)
    
    return bgLevel, newNeuronAverage, xNewNeuron+xMin, yNewNeuron+yMin, neuronArea, GreenbgLevel , GreenNeuronAverage, xNewNeuron+xMin+shift[0], yNewNeuron+yMin+shift[1] ,neuronArea,
    
    
    
def processFluorescence(Image, bgSize,neuronSize, threshold, xC, yC):
    """Calculate fluorescene for the second-brightest object (process)."""
    
    return 0
    
def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n
