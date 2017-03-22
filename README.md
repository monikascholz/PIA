# PIA
- physiological imaging analyzer -
A graphical interface for tracking and correcting physiological calcium imaging (GCamp).
Integrates automatic and manual inputs to optimize the resulting calcium traces.

## Overview
PIA is designed to load image stacks, and assist in automated and/or manual analysis. The type of image PIA can analyze is either a fluorescently labelled spot (any shape) or a pair of spots that have a constant relative distance to each other. PIA can also deal with ratiometric images, where two fluorescence channels of the same object are shown. Requirements for this type of analysis is listed below.
The PIA output file contains the location of each tracked object (one or two objects), the brightness, the background level around the object and the area of the object.

## Features
PIA has 4 options for detecting fluorescence changes:
1. Tracking a single object over time (eg. traditional GCamp images)
2. Tracking two objects in the same arrangement (rotation and translation are ok)
3. Tracking an object in two colors and showing ratiometric changes
4. Tracking two objects with ratiometric changes.

PIA can also play a series of images at as a movie and load previous PIA data files and allow the user to manually correct/overwrite them.

## Image input

PIA uses matplotlib.image's imread function. Natively, this only supports png images, however, with the help of Pillow, it can also read tif and jpg images. The input images are expected to have a 4-digit timestamp at the end of the filename, eg. img_0001.jpg. 

## File output
The output file specifies four parameters for each object: Fluorescence, associated background, location in the image and area.
Depending on the tracking mode, it returns this for one or two objects in one or two colors.

## Object detection and Tracking
### Parameters
|Parameters     | Description | How to choose a value|
| ------------- |-------------| -------------|
| Background box| Determines the search area around a location where an object is expected. | Should be close to the maximally expected displacement in a frame|
| Neuron box    | This area will be masked for the background calculation and should cover the fluroescent object |Approximately the size of the object and any halo that might appear around it|
| Signal threshold| In percent pixel of the background box, this determines the threshold that separates object and background.| The percentile value of brightness ie. for 95% all pixels with the 5% highest brightness levels are part of the object|
| Dual color shift | Dual color(ratiometric) imaging offset | calculate from shift between images, should be constant for a movie and a microscope|





### Tracking
Tracking assumes that the object does not move extremly far within a frame. The size of the background box determines where the algorithm assumes the object will appear again. The automated tracking algorithm identifies the brightest object in the background box and assumes this is the desired object. The user can also click on or in the vicinity of the object to manually assist tracking. this is particularly useful if the object moved a lot between frames or if the sample was out of frame for a period of time. However, the exact determination of the objects location will still be done by the trackig algorithm, which will find the brightest object in the vicinity of the user's clicked location.


