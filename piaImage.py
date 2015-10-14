# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 15:55:24 2015
image analysis functions for PIA.
@author: monika
"""
import numpy as np
from scipy import ndimage
import matplotlib.pylab as plt

def fluorescence(Image, bgSize,neuronSize, threshold, xC, yC):
    """Calculate fluorescene in a larger ROI around coordinates xC and yC."""

    imSize = Image.shape
     # -- Check if box needs to be cropped as it's ranging beyond the image
    yMin = max(0,yC-bgSize)
    yMax = min(imSize[0],yC+bgSize)
    xMin = max(0,xC-bgSize)
    xMax = min(imSize[1],xC+bgSize)
    bgImage = Image[yMin:yMax, xMin:xMax]
    # --- Determine position of neuron; might not be centered due to cropping
    height, width = bgImage.shape
    xNeuron = xC - xMin
    yNeuron = yC - yMin
        # --- Get number of total pixels in the BG box and determine an intensity
        # --- threshold at which N % of the pixels have less intensity
    threshold = np.percentile(bgImage, [threshold, (100+threshold)/2.])
    #threshold = np.sort(bgImage, axis=None)[-int((1-threshold/100.)*height*width)]

        # --- Prepare a mask that shows the position of each individual pixel
        # --- that exceeds the threshold. Clear all objects that are less than
        # --- 2 x 2 pixels and connect all single pixel gaps.
    mask = np.where(bgImage > threshold[0], 1, 0)
    #plt.imshow(mask)
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
        
    try:
        neuronObject = np.where(label_im == loc+1,0,1)
            # --- Get average of the neuron fluoresence --- 
        tmp_neuron = np.ma.masked_array(bgImage, neuronObject)
        newNeuronAverage = np.ma.average(tmp_neuron[tmp_neuron>threshold[1]])
        
            # --- Mask the neuron and get the average fluoresence in the 
            # --- BG image box
        mask = np.zeros(bgImage.shape, dtype=bool)
        yMinSRegion = max(0,yNewNeuron-neuronSize)
        yMaxSRegion = min(imSize[0],yNewNeuron+neuronSize)
        xMinSRegion = max(0,xNewNeuron-neuronSize)
        xMaxSRegion = min(imSize[1],xNewNeuron+neuronSize)
        
        mask[yMinSRegion:yMaxSRegion,xMinSRegion:xMaxSRegion] = True
        
        bgLevel = np.ma.average(np.ma.masked_array(bgImage, mask))  
    except IndexError:
        newNeuronAverage = 1
        bgLevel = 1
    return xNewNeuron+xMin, yNewNeuron+yMin, newNeuronAverage, bgLevel
    
def processFluorescence(Image, bgSize,neuronSize, threshold, xC, yC):
    """Calculate fluorescene for the second-brightest object (process)."""
    imSize = Image.shape
     # -- Check if box needs to be cropped as it's ranging beyond the image
    yMin = max(0,yC-bgSize)
    yMax = min(imSize[0],yC+bgSize)
    xMin = max(0,xC-bgSize)
    xMax = min(imSize[1],xC+bgSize)
    bgImage = Image[yMin:yMax, xMin:xMax]
    # --- Determine position of neuron; might not be centered due to cropping
    height, width = bgImage.shape
    xNeuron = xC - xMin
    yNeuron = yC - yMin
        # --- Get number of total pixels in the BG box and determine an intensity
        # --- threshold at which N % of the pixels have less intensity
    threshold = np.sort(bgImage, axis=None)[-int((1-threshold/100.)*height*width)]

        # --- Prepare a mask that shows the position of each individual pixel
        # --- that exceeds the threshold. Clear all objects that are less than
        # --- 2 x 2 pixels and connect all single pixel gaps.
    mask = np.where(bgImage > threshold, 1, 0)
    mask = ndimage.binary_opening(mask,structure = np.ones((2,2)))
    mask = ndimage.binary_closing(mask)
        # --- Individually label all connected regions and get their center of mass
    label_im, nb_labels = ndimage.label(mask)
    centroids = ndimage.measurements.center_of_mass(bgImage, label_im, xrange(1,nb_labels+1))
    # --- select longest object
    snippet = bgImage[ndimage.find_objects(label_im)]
    # find the object with the longest axis - likely the process
    loc = np.max([np.sort(s.shape) for s in snippet])
    meanBrightness = ndimage.measurements.mean(bgImage, label_im, xrange(1,nb_labels+1))
    
    if nb_labels > 1:
        loc = np.argmax(meanBrightness)
        
        yNewNeuron,xNewNeuron = centroids[loc]
    else:
        yNewNeuron,xNewNeuron = yNeuron,  xNeuron
        return xNewNeuron+xMin, yNewNeuron+yMin, 1, 1
        
    
   
    try:
        neuronObject = np.where(label_im == loc+1,0,1)
                
            # --- Get average of the neuron fluoresence --- 
        newNeuronAverage = np.ma.average(np.ma.masked_array(bgImage, neuronObject))
        
            # --- Mask the neuron and get the average fluoresence in the 
            # --- BG image box
        mask = np.zeros(bgImage.shape, dtype=bool)
        yMinSRegion = max(0,yNewNeuron-neuronSize)
        yMaxSRegion = min(imSize[0],yNewNeuron+neuronSize)
        xMinSRegion = max(0,xNewNeuron-neuronSize)
        xMaxSRegion = min(imSize[1],xNewNeuron+neuronSize)
        
        mask[yMinSRegion:yMaxSRegion,xMinSRegion:xMaxSRegion] = True
        
        bgLevel = np.ma.average(np.ma.masked_array(bgImage, mask))  
    except IndexError:
        newNeuronAverage = 1
        bgLevel = 1
    return xNewNeuron+xMin, yNewNeuron+yMin, newNeuronAverage, bgLevel
    
def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n
