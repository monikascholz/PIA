# PIA
- physiological imaging analyzer -
An interface for tracking and correcting physiological calcium imaging (GCamp).
Integrates automatic and manual inputs to optimize the resulting calcium traces.

## Overview
PIA is designed to load image stacks, and assist in automated and/or manual analysis. The type of image PIA can analyze is either a fluorescently labelled spot (any shape) or a pair of spots that have a constant relative distance to each other. PIA can also deal with ratiometric images, where two fluorescence channels of the same object are shown. Requirements for this type of analysis is listed below.
The PIA output file contains the location of each tracked object (one or two objects), the brightness, the background level around the object and the area of the object.

## Tracking



