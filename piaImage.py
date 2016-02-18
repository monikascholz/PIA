# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 15:55:24 2015
image analysis functions for PIA.
@author: monika
"""
import numpy as np
from scipy import ndimage
import matplotlib.pylab as plt


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

def calculateWith2Masks(bgImage, xNewNeuron1,yNewNeuron1,xNewNeuron2,yNewNeuron2,neuronSize,imSize):
    '''calculate a masked quantity for two objects'''
    mask = np.zeros(bgImage.shape, dtype=bool)
    # shade out two boxes
    for (xNewNeuron, yNewNeuron) in zip([xNewNeuron1, xNewNeuron2], [xNewNeuron1]):
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

def cropOutOfBoundsRegions(xC, yC, bgSize, neuronObject, width, height, imSize, shift):
    # --- Deal with shift out of image
    yMin = yC+shift[1]-bgSize
    yMax = yC+shift[1]+bgSize
    xMin = xC+shift[0]-bgSize
    xMax = xC+shift[0]+bgSize
    
    if yMin < 0:
        neuronObject = neuronObject[-yMin:,]
    if yMax > imSize[0]:
        neuronObject = neuronObject[:-yMax+height,]
    if xMin < 0:
        neuronObject = neuronObject[:,-xMin:]
    if xMax > imSize[1]:
        neuronObject = neuronObject[:,:xMax-width]
    return neuronObject
    
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
    bgLevel = calculateWithMask(bgImage, xNewNeuron,yNewNeuron,neuronSize,imSize)
    GreenImage, _,_ = cropImage(Image, xC+shift[0], yC+shift[1], bgSize, imSize)
    
    neuronObject = cropOutOfBoundsRegions(xC, yC, bgSize, neuronObject, width, height, imSize, shift)
    
    if neuronObject.shape[0]<1 or neuronObject.shape[1]<1:
        return bgLevel, newNeuronAverage, xNewNeuron+xMin, yNewNeuron+yMin, neuronArea, 1 , 1, xNewNeuron+xMin+shift[0], yNewNeuron+yMin+shift[1] ,neuronArea,
        
    if GreenImage.shape!= neuronObject.shape:
        print 'tracker out of bounds', GreenImage.shape, neuronObject.shape
        return bgLevel, newNeuronAverage, xNewNeuron+xMin, yNewNeuron+yMin, neuronArea, 1 , 1, xNewNeuron+xMin+shift[0], yNewNeuron+yMin+shift[1] ,neuronArea,
    tmpGreenNeuron = np.ma.masked_array(GreenImage, neuronObject)
    GreenNeuronAverage = np.ma.average(tmpGreenNeuron)
    GreenbgLevel = calculateWithMask(GreenImage, xNewNeuron,yNewNeuron,neuronSize,imSize)
    
    return bgLevel, newNeuronAverage, xNewNeuron+xMin, yNewNeuron+yMin, neuronArea, GreenbgLevel , GreenNeuronAverage, xNewNeuron+xMin+shift[0], yNewNeuron+yMin+shift[1] ,neuronArea,

def dualFluorescence2Neurons(Image, bgSize,neuronSize, threshold, xC, yC, shift, prevLocs):
    """Calculate fluorescene for the two brightest objects."""
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
    # ------ find two objects in the search area
    mask = np.where(bgImage > threshold[0], 1, 0)
    mask = ndimage.binary_opening(mask,structure = np.ones((4,4)))
    mask = ndimage.binary_closing(mask)
        # --- Individually label all connected regions and get their center of mass
    label_im, nb_labels = ndimage.label(mask)
    centroids = ndimage.measurements.center_of_mass(bgImage, label_im, xrange(1,nb_labels+1))
    # --- select brightest object by default (mean brightness)
    meanBrightness = ndimage.measurements.mean(bgImage, label_im, xrange(1,nb_labels+1))
    print nb_labels
#    plt.imshow(label_im)
#    plt.show()
    if nb_labels > 1:
        # if at least two are found, use the brightest ones
        ind = np.argpartition(meanBrightness, -2)[-2:]
        ind =  ind[np.argsort(meanBrightness[ind])]
        yNewNeuron1,xNewNeuron1 = centroids[ind[0]]
        yNewNeuron2,xNewNeuron2 = centroids[ind[1]]
        neuronObject1 = np.where(label_im == ind[0]+1,0,1)
        neuronArea1 = np.sum(neuronObject1)
        neuronObject2 = np.where(label_im == ind[1]+1,0,1)
        neuronArea2 = np.sum(neuronObject2)
        vec1 = np.array([prevLocs[0]-prevLocs[2], prevLocs[1]-prevLocs[3]])
        vec2 = np.array([xNewNeuron2 - xNewNeuron1, yNewNeuron2- yNewNeuron1])
        # P2-P1 = direction from P1 to P2- vec2 from neuron1 to neuron2
        
        # detect neuron identity via angle
        angle1 = np.arccos(np.clip(np.dot(vec1/np.linalg.norm(vec1), vec2/np.linalg.norm(vec2)),-1,1))
        angle2 = np.arccos(np.clip(np.dot(vec1/np.linalg.norm(vec1), -vec2/np.linalg.norm(vec2)),-1,1))
        # switch idenity
        if angle2 > angle1:
            tmp = yNewNeuron2,xNewNeuron2
            yNewNeuron2,xNewNeuron2= yNewNeuron1,xNewNeuron1
            yNewNeuron1,xNewNeuron1 = tmp
            tmp = neuronObject2
            neuronObject2 = neuronObject1
            neuronObject1 = tmp
            
    if nb_labels == 1:
        # if only one object found, assign same values to both
        loc = np.argmax(meanBrightness)
        yNewNeuron1,xNewNeuron1 = centroids[loc]
        xNewNeuron2,yNewNeuron2 = prevLocs[-2]-xMin, prevLocs[-1]-yMin
        neuronObject1 = np.where(label_im ==loc+1,0,1)
        neuronArea1 = np.sum(neuronObject1)
        neuronObject2 = neuronObject1
        neuronArea2 = neuronArea1
        
    elif nb_labels==0:
        # if nothing is found, use bg
        yNewNeuron1,xNewNeuron1 = yNeuron,  xNeuron
        yNewNeuron2,xNewNeuron2 = yNewNeuron1,xNewNeuron1
        loc = -1
        neuronObject1 = np.where(label_im ==loc+1,0,1)
        neuronArea1 = np.sum(neuronObject1)
        neuronObject2 = np.where(label_im == loc+1,0,1)
        neuronArea2 = np.sum(neuronObject2)
    
        # --- Get average of the 2 neurons fluorescence --- 
    tmp_neuron = np.ma.masked_array(bgImage, neuronObject1)
    newNeuronAverage1 = np.ma.average(tmp_neuron[tmp_neuron>threshold[1]])
    
    tmp_neuron = np.ma.masked_array(bgImage, neuronObject2)
    newNeuronAverage2 = np.ma.average(tmp_neuron[tmp_neuron>threshold[1]])

    # --- remove both neuron objetcs from field of view, we assume bg is the same
    
    bgLevel = calculateWith2Masks(bgImage, xNewNeuron1,yNewNeuron1,xNewNeuron2,yNewNeuron2,neuronSize,imSize)
    
    # --- Deal with shift
    GreenImage, _,_ = cropImage(Image, xC+shift[0], yC+shift[1], bgSize, imSize)
    
    neuronObject1 = cropOutOfBoundsRegions(xC, yC, bgSize, neuronObject1, width, height, imSize, shift)
    
    if neuronObject1.shape[0]<1 or neuronObject1.shape[1]<1 or GreenImage.shape != neuronObject1.shape:
        return bgLevel, newNeuronAverage1, xNewNeuron1+xMin, yNewNeuron1+yMin, neuronArea1, \
        1 , 1, xNewNeuron1+xMin+shift[0], yNewNeuron1+yMin+shift[1] ,neuronArea1,\
        bgLevel, newNeuronAverage2, xNewNeuron2+xMin, yNewNeuron2+yMin, neuronArea2, \
        1 , 1, xNewNeuron2+xMin+shift[0], yNewNeuron2+yMin+shift[1] ,neuronArea2,
    else:
        tmpGreenNeuron1 = np.ma.masked_array(GreenImage, neuronObject1)
        GreenNeuronAverage1 = np.ma.average(tmpGreenNeuron1)
    
    neuronObject2 = cropOutOfBoundsRegions(xC, yC, bgSize, neuronObject2, width, height, imSize, shift)
    if neuronObject2.shape[0]<1 or neuronObject2.shape[1]<1 or GreenImage.shape != neuronObject2.shape:
        GreenNeuronAverage2 = 1
        GreenbgLevel = 1
    else:
        tmpGreenNeuron2 = np.ma.masked_array(GreenImage, neuronObject2)
        GreenNeuronAverage2 = np.ma.average(tmpGreenNeuron2)
    
        GreenbgLevel = calculateWith2Masks(bgImage, xNewNeuron1,yNewNeuron1,xNewNeuron2,yNewNeuron2,neuronSize,imSize)
    # for each of the 2 neuron there are red and green components
    return bgLevel, newNeuronAverage1, xNewNeuron1+xMin, yNewNeuron1+yMin, neuronArea1, \
    GreenbgLevel , GreenNeuronAverage1, xNewNeuron1+xMin+shift[0], yNewNeuron1+yMin+shift[1] ,neuronArea1,\
    bgLevel, newNeuronAverage2, xNewNeuron2+xMin, yNewNeuron2+yMin, neuronArea2, \
    GreenbgLevel , GreenNeuronAverage2, xNewNeuron2+xMin+shift[0], yNewNeuron2+yMin+shift[1] ,neuronArea2,\

    
    
def processFluorescence(Image, bgSize,neuronSize, threshold, xC, yC):
    """Calculate fluorescene for the second-brightest object (process)."""
    
    return 0
    
def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n
