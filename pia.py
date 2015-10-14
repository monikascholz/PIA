# -*- coding: utf-8 -*-
"""

    An interface for tracking and correcting physiological calcium imaging.
    Integrates automatic and manual inputs to optimize the resulting calcium traces.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details; 
    see http://www.gnu.org/licenses.
    
    Authors: B.J. Scholz and M. Scholz
"""

import matplotlib as mpl
mpl.use('TkAgg')
import numpy as np
import matplotlib.pylab as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,  NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
import Tkinter as tk
import os
import tkFileDialog as tfd
import matplotlib.image as mpimg
# load image analysis module
import piaImage

#=============================================================================#
#                           Define UC colors
#=============================================================================#
UCyellow = ['#FFA319','#FFB547','#CC8214']
UCorange = ['#C16622','#D49464','#874718']
UCred    = ['#8F3931','#B1746F','#642822']
UCgreen  = ['#8A9045','#ADB17D','#616530','#58593F','#8A8B79','#3E3E23']
UCblue   = ['#155F83','#5B8FA8','#0F425C']
UCviolet = ['#350E20','#725663']
UCgray   = ['#767676','#D6D6CE']
UCmain   = '#800000'

#=============================================================================#
#                     Define available colormaps
#=============================================================================#
cMaps = {'gray': mpl.cm.gray,
         'jet': mpl.cm.jet,
         'hot': mpl.cm.hot,
         'blue': mpl.cm.Blues_r,
         'green': mpl.cm.Greens_r}

#=============================================================================#
#                     Define tk window class
#         ----------------------------------------------------------
#
#=============================================================================#         
class Window():
    #=========================================================================#
    #          Define frame layout and initialize everything
    #=========================================================================#
    def __init__(self,root):
        root.title( "PIA - physiological imaging analyzer" )
        self.status = [False, # Image Folder selected
                       False, # Data File selected
                       False, # Argument File selected
                       False] # Video plaback on
                       
        self.imageFolder = tk.StringVar()
        self.dataFile = tk.StringVar()
        self.newFile = tk.StringVar()
        
        self.startIndex = tk.IntVar()
        self.startIndex.set(0)
        self.currentIndex = tk.IntVar()
        self.currentIndex.set(0)
        self.endIndex = tk.IntVar()
        self.intervalIndex = tk.IntVar()
        self.intervalIndex.set(1000)
        
        self.imageType = tk.StringVar()
        self.imageType.set('tif')
        self.imageData = []
        self.imSize = (0,0)
        self.rotate = tk.IntVar()
        self.rotate.set(0)
        
        self.playbackSpeed = tk.IntVar()
        self.playbackSpeed.set(5)
        self.skipFrames = tk.IntVar()
        self.skipFrames.set(0)
        
        self.process = tk.IntVar()
        

        self.process.set(0)
       
        
        self.boxShow = tk.IntVar()
        self.signalThreshold = tk.IntVar()
        self.boxNeuron = tk.IntVar()
        self.boxBG = tk.IntVar()
        
        self.boxShow.set(1)
        self.boxBG.set(150)
        self.boxNeuron.set(50)
        self.signalThreshold.set(93)
        
        self.data = []
        self.oldData = []
        self.imageNames = []
        self.mainImage = None
        self.pause = 0
        self.cidPress = {}
        self.vLine = []
        self.rect = []
        
        self.colorMap = tk.StringVar()
        self.colorMap.set('gray')
        
        self.newAutoRun = False
        self.AutoRunActive = False
        self.ROILocationData = []
        self.ROI = []
        self.TrackerData = []
        
        self.nextImgOnClick = tk.IntVar()
        self.nextImgOnClick.set(1)
        
        columnWidth = 45
        buttonWidth = 10
        textWidth = 15
        entryWidth = 10
        
        #--------------------- Select an image folder  ------------------------
        imageFolderFrame = tk.Frame(root)
        imageFolderFrame.grid(column=0,row=0,sticky=tk.NW)        
        imageFolderText = tk.StringVar()
        imageFolderText.set('Image Folder')
        imageFolderLabel = tk.Label(imageFolderFrame, textvariable=imageFolderText,width=textWidth,anchor=tk.W,justify=tk.LEFT)
        imageFolderLabel.pack(side=tk.LEFT)
        imageFolderEntry = tk.Entry(imageFolderFrame, textvariable=self.imageFolder,width=columnWidth)
        imageFolderEntry.pack(side=tk.LEFT)
        imageFolderButton = tk.Button(imageFolderFrame, text = 'Select', fg = 'black', command= self.selectImageFolder,width=buttonWidth)
        imageFolderButton.pack(side=tk.LEFT)

        #--------------------- Select a data file -----------------------------
        dataFileFrame = tk.Frame(root)
        dataFileFrame.grid(column=0,row=1,sticky=tk.NW)        
        dataFileText = tk.StringVar()
        dataFileText.set('Data File')
        dataFileLabel = tk.Label(dataFileFrame, textvariable=dataFileText,width=textWidth,anchor=tk.W,justify=tk.LEFT)
        dataFileLabel.pack(side=tk.LEFT)
        dataFileEntry = tk.Entry(dataFileFrame, textvariable=self.dataFile,width=columnWidth)
        dataFileEntry.pack(side=tk.LEFT)
        dataFileButton = tk.Button(dataFileFrame, text = 'Select', fg = 'black', command= self.selectDataFile,width=buttonWidth)
        dataFileButton.pack(side=tk.LEFT)

        #--------------------- Select a new data file ------------------------
        newFileFrame = tk.Frame(root)
        newFileFrame.grid(column=0,row=2,sticky=tk.NW)        
        newFileText = tk.StringVar()
        newFileText.set('New File')
        newFileLabel = tk.Label(newFileFrame, textvariable=newFileText,width=textWidth,anchor=tk.W,justify=tk.LEFT)
        newFileLabel.pack(side=tk.LEFT)
        newFileEntry = tk.Entry(newFileFrame, textvariable=self.newFile,width=columnWidth)
        newFileEntry.pack(side=tk.LEFT)
        newFileButton = tk.Button(newFileFrame, text = 'Select', fg = 'black', command= self.selectNewFile,width=buttonWidth)
        newFileButton.pack(side=tk.LEFT)

        
        #--------------------- Control Buttons  ------------------------  
        controlSubFrame1 = tk.Frame(root)
        controlSubFrame1.grid(column=1,row=0,sticky=tk.N)    
        runControlButton = tk.Button(controlSubFrame1, text = 'Run', fg = 'black', command= self.runControl,width=buttonWidth)
        runControlButton.pack(side=tk.LEFT)    
        pauseControlButton = tk.Button(controlSubFrame1, text = 'Pause', fg = 'black', command= self.pauseControl,width=buttonWidth)
        pauseControlButton.pack(side=tk.LEFT)  
        
        controlSubFrame2 = tk.Frame(root)
        controlSubFrame2.grid(column=1,row=1,sticky=tk.N)    
        resetControlButton = tk.Button(controlSubFrame2, text = 'Reset Data', fg = 'black', command= self.resetControl,width=buttonWidth)
        resetControlButton.pack(side=tk.LEFT)  
        writeControlButton = tk.Button(controlSubFrame2, text = 'Write Data', fg = 'black', command= self.writeControl,width=buttonWidth)
        writeControlButton.pack(side=tk.LEFT)     
        
        controlSubFrame3 = tk.Frame(root)
        controlSubFrame3.grid(column=1,row=2,sticky=tk.N)    
        AutoRunControlButton = tk.Button(controlSubFrame3, text = 'Run Tracker', fg = 'black', command= self.AutoRunControl,width=buttonWidth)
        AutoRunControlButton.pack(side=tk.LEFT)       
        writeControlButton = tk.Button(controlSubFrame3, text = 'Write New Data', fg = 'black', command= self.writeNewData,width=buttonWidth)
        writeControlButton.pack(side=tk.LEFT) 
        
        controlSubFrame4 = tk.Frame(root)
        controlSubFrame4.grid(column=1,row=3,sticky=tk.N)
            
        jumpToStartButton = tk.Button(controlSubFrame4, text = 'Jump To Start', fg = 'black', command= self.jumpToStart,width=buttonWidth)
        jumpToStartButton.pack(side=tk.LEFT)     
         
        #--------------------- Select options ---------------------------------
        optionsFrame = tk.Frame(root)
        optionsFrame.grid(column=2,row=0,rowspan=4,sticky=tk.N)
        
            #--------- Start index ---------
        startOptionsText = tk.StringVar()
        startOptionsText.set('Starting index')
        startOptionsLabel = tk.Label(optionsFrame,textvariable=startOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        startOptionsLabel.grid(column=0, row=0)
        startOptionsEntry = tk.Entry(optionsFrame,textvariable=self.startIndex,justify=tk.CENTER,width=entryWidth)
        startOptionsEntry.grid(column=1,row=0)

            #--------- End index ---------
        endOptionsText = tk.StringVar()
        endOptionsText.set('Current index')
        endOptionsLabel = tk.Label(optionsFrame,textvariable=endOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        endOptionsLabel.grid(column=0, row=1)
        endOptionsEntry = tk.Entry(optionsFrame,textvariable=self.currentIndex,justify=tk.CENTER,width=entryWidth)
        endOptionsEntry.grid(column=1,row=1)
 
             #--------- Playback Speed ---------
        playbackOptionsText = tk.StringVar()
        playbackOptionsText.set('Playback Speed')
        playbackOptionsLabel = tk.Label(optionsFrame,textvariable=playbackOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        playbackOptionsLabel.grid(column=0,row=2)
        playbackOptionsEntry = tk.Entry(optionsFrame,textvariable=self.playbackSpeed,justify=tk.CENTER,width=entryWidth)
        playbackOptionsEntry.grid(column=1,row=2)    

        skipFramesOptionsText = tk.StringVar()
        skipFramesOptionsText.set('Skip Frames')
        skipFramesOptionsLabel = tk.Label(optionsFrame,textvariable=skipFramesOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        skipFramesOptionsLabel.grid(column=0,row=3)
        skipFramesOptionsEntry = tk.Entry(optionsFrame,textvariable=self.skipFrames,justify=tk.CENTER,width=entryWidth)
        skipFramesOptionsEntry.grid(column=1,row=3)  
        
             #--------- Rotate ---------
        rotateOptionsText = tk.StringVar()
        rotateOptionsText.set('Rotate image')
        rotateOptionsLabel = tk.Label(optionsFrame,textvariable=rotateOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        rotateOptionsLabel.grid(column=2,row=0)
        rotateOptionsCheckbutton = tk.Checkbutton(optionsFrame, variable=self.rotate)
        rotateOptionsCheckbutton.grid(column=3,row=0)   

            #--------- Image type ---------
        imTypeOptionsText = tk.StringVar()
        imTypeOptionsText.set('Image data type')
        imTypeOptionsLabel = tk.Label(optionsFrame,textvariable=imTypeOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        imTypeOptionsLabel.grid(column=4,row=0)
        imTypeOptionsMenu = tk.OptionMenu(optionsFrame,self.imageType,'tif','png','jpg')
        imTypeOptionsMenu.grid(column=5,row=0,sticky="ew")

            #--------- Colormap ---------
        colorMapOptionsText = tk.StringVar()
        colorMapOptionsText.set('Colormap')
        colorMapOptionsLabel = tk.Label(optionsFrame,textvariable=colorMapOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        colorMapOptionsLabel.grid(column=6,row=0)
        colorMapOptionsMenu = tk.OptionMenu(optionsFrame,self.colorMap,'gray','blue','green','jet','hot')
        colorMapOptionsMenu.grid(column=7,row=0, sticky="ew")   
        
             #--------- track processes Image ---------
        processOptionsText = tk.StringVar()
        processOptionsText.set('Track process')
        processOptionsLabel = tk.Label(optionsFrame,textvariable=processOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        processOptionsLabel.grid(column=2,row=1)
        processOptionsCheckbutton = tk.Checkbutton(optionsFrame, variable=self.process)
        processOptionsCheckbutton.grid(column=3,row=1)           

        
        
             #--------- Rectangle info ---------
        boxOptionsText = tk.StringVar()
        boxOptionsText.set('Show signal/BG boxes')
        boxOptionsLabel = tk.Label(optionsFrame,textvariable=boxOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        boxOptionsLabel.grid(column=2,row=2)
        boxOptionsCheckbutton = tk.Checkbutton(optionsFrame, variable=self.boxShow)
        boxOptionsCheckbutton.grid(column=3,row=2)           

        boxNeuronOptionsText = tk.StringVar()
        boxNeuronOptionsText.set('Neuron box size')
        boxNeuronOptionsLabel = tk.Label(optionsFrame,textvariable=boxNeuronOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        boxNeuronOptionsLabel.grid(column=4,row=2)
        boxNeuronOptionsEntry = tk.Entry(optionsFrame,textvariable=self.boxNeuron,justify=tk.CENTER,width=entryWidth)
        boxNeuronOptionsEntry.grid(column=5,row=2)           

        boxBGOptionsText = tk.StringVar()
        boxBGOptionsText.set('BG box size')
        boxBGOptionsLabel = tk.Label(optionsFrame,textvariable=boxBGOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        boxBGOptionsLabel.grid(column=6,row=2)
        boxBGOptionsEntry = tk.Entry(optionsFrame,textvariable=self.boxBG,justify=tk.CENTER,width=entryWidth)
        boxBGOptionsEntry.grid(column=7,row=2)    

        signalThresholdOptionsText = tk.StringVar()
        signalThresholdOptionsText.set(r'Signal Th. [%]')
        signalThresholdOptionsLabel = tk.Label(optionsFrame,textvariable=signalThresholdOptionsText,anchor=tk.E,justify=tk.RIGHT,width=textWidth)
        signalThresholdOptionsLabel.grid(column=4,row=3)
        signalThresholdOptionsEntry = tk.Entry(optionsFrame,textvariable=self.signalThreshold,justify=tk.CENTER,width=entryWidth)
        signalThresholdOptionsEntry.grid(column=5,row=3)    

           #--------- Next Image On Click ---------
        nextOnClickText = tk.StringVar()
        nextOnClickText.set('Next image on click')
        nextOnClickLabel = tk.Label(optionsFrame,textvariable=nextOnClickText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        nextOnClickLabel.grid(column=2,row=3)
        nextOnClickCheckbutton = tk.Checkbutton(optionsFrame, variable=self.nextImgOnClick)
        nextOnClickCheckbutton.grid(column=3,row=3)  
     
        
        #------------------------ Main Figure Frame ---------------------------
        self.canvas = {}
        self.ax = {}
        self.figure = {}
        self.toolbar = {}
        
        mainFigureFrame = tk.Frame(root)
        mainFigureFrame.grid(column=0,row=5,columnspan=2,sticky=tk.NSEW )
        self.figure['Main'] = plt.figure('Main',figsize=(7,7), dpi=100, edgecolor='k',facecolor='w')
        self.canvas['Main'] = FigureCanvasTkAgg(self.figure['Main'], master=mainFigureFrame)
        self.ax['Main'] = self.figure['Main'].add_subplot(111)
        plt.setp(self.ax['Main'].get_xticklabels(), visible=False)
        plt.setp(self.ax['Main'].get_yticklabels(), visible=False)
        plt.tight_layout()
        self.canvas['Main'].show()
        self.canvas['Main'].get_tk_widget().pack()
        self.cidPress['Main'] = self.canvas['Main'].mpl_connect('button_press_event', self.onPressMain)
        self.cidPress['Main2'] = self.canvas['Main'].mpl_connect('button_release_event', self.onReleaseMain)
        
        #------------------- Data + Analysed Figure Frame ---------------------
        subFigureFrame = tk.Frame(root)
        subFigureFrame.grid(column=2,row=5,sticky=tk.NSEW )
        toolbarFrame1 = tk.Frame(root)
        toolbarFrame1.grid(column=2,row=4,sticky=tk.S )
        toolbarFrame2 = tk.Frame(root)
        toolbarFrame2.grid(column=2,row=6,sticky=tk.S )
           #--------- Data Figure ---------        
        
             #--------- Data Figure ---------        
        self.figure['Data'] = plt.figure('Data',figsize=(7,3.45), dpi=100, edgecolor='k',facecolor='w')
        self.ax['Data'] = self.figure['Data'].add_subplot(111)
        #plt.tight_layout()
        self.canvas['Data'] = FigureCanvasTkAgg(self.figure['Data'], master=subFigureFrame)
        self.canvas['Data'].show()
        #self.canvas['Data'].get_tk_widget().pack()
        self.toolbar['Data'] = NavigationToolbar2TkAgg(self.canvas['Data'], toolbarFrame1 )
        self.toolbar['Data'].update()
        self.canvas['Data']._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        #self.canvas['Data'].get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.cidPress['Data'] = self.canvas['Data'].mpl_connect('button_press_event', self.onPressData)
        #plt.tight_layout()

             #--------- Analyzed Figure ---------        
        self.figure['Flow'] = plt.figure('Flow',figsize=(7,3.45), dpi=100, edgecolor='k',facecolor='w')
        self.ax['Flow'] = self.figure['Flow'].add_subplot(111)
        #plt.tight_layout()
        self.canvas['Flow'] = FigureCanvasTkAgg(self.figure['Flow'], master=subFigureFrame)
        self.toolbar['Flow'] = NavigationToolbar2TkAgg( self.canvas['Flow'],toolbarFrame2 )
        self.toolbar['Flow'].update()
        #self.canvas['Flow']._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas['Flow'].get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas['Flow'].show()
        #self.canvas['Flow'].get_tk_widget().pack()
        self.cidPress['Flow'] = self.canvas['Flow'].mpl_connect('button_press_event', self.onPressFlow)
        #plt.tight_layout()
      
    #=========================================================================#
    #             Define button and click functions
    #=========================================================================#        
        
        #=====================================================================#
        # Select button for the image folder has been pressed.
        # Get all images from folder and sort them by image number
        # Get total number of images present (in case data file is longer than
        #  the number of available images)
        # Draw the first image and save that the main image frame is now active
        #=====================================================================#   
    def selectImageFolder(self):
             #--------- Get directory from the user ---------         
        self.imageFolder.set(tfd.askdirectory(parent=root, initialdir='/home/monika/Copy/workspace spyder/PIA_old/HSN GCaMP', title='Select image folder'))
        
             #--------- Get all images in folder and sort them --------- 
        tmp = np.array(os.listdir(self.imageFolder.get()))
        tmpNames = {}
        tmpTimes = []
        for item in tmp:
            if item[-3:] == self.imageType.get():
                time = float(item[:-4].split('_')[3])
                tmpTimes.append(time)
                tmpNames[time] = item
        self.imageNames = [tmpNames[x] for x in sorted(tmpTimes)]
        self.numOfImages = len(self.imageNames)
        self.status[0] = True
            #--------- make a dummy data file with zeros --------- 
        self.fill_dummy_data()
            #--------- Draw main image and set status of main image --------- 
        self.drawMain()
        self.imSize = self.imageData.shape
        self.drawData()
        self.drawDataLine()
        self.updateMain()
        self.drawRect()
        return

        #=====================================================================#
        # Select button for the data file has been pressed
        # Read the provided data file: Time, Fluoresence, None, X, Y
        # Remove previous data plots and redraw new data
        # Save that the data frame is now active
        #=====================================================================#           
    def selectDataFile(self):
             #--------- Get data file from user --------- 
        self.dataFile.set(tfd.askopenfilename(parent=root, initialdir='./', title='Select existing data file'))

             #--------- Read data file  --------- 
        with open(self.dataFile.get(),'r') as f:
            tmpX = []
            tmpY = []
            tmpSF = []
            tmpBF = []
            tmpT = []
            for line in f.readlines():
                ln = np.array(line.split(),dtype='float')
                tmpT.append(ln[0])
                tmpBF.append(ln[1])
                tmpSF.append(ln[2])
                tmpX.append(ln[3])
                tmpY.append(ln[4])
        self.data = np.array([tmpT,tmpBF,tmpSF,tmpX,tmpY])
        self.oldData = np.array([tmpT,tmpBF,tmpSF,tmpX,tmpY])
        
             #--------- Plot fluorescence profile  --------- 
        plt.figure('Data')
        self.ax['Data'].cla()
        self.drawData()
#        self.vLine = []
#        plt.plot(self.data[0],self.data[2],c=UCblue[2],lw=2)
#        plt.plot(self.data[0],self.data[1],c=UCgreen[4],lw=2)
#        plt.xlim(min(self.data[0]),max(self.data[0]))
#        self.canvas['Data'].draw()
        
             #--------- Set status of data image ---------         
        self.status[1] = True
        return
        #=====================================================================#
        # Select button for the new data file has been pressed. This avoids overwriting existing data.
        #=====================================================================#  
    def selectNewFile(self):
             #--------- Get argument file from user  --------- 
        self.newFile.set(tfd.asksaveasfilename(parent=root, initialdir='./', title='Select argument file'))
        self.status[2] = True
             #--------- If we have data, create and show empty data  --------- 
        return
        
        #=====================================================================#
        # Write new data file. The old one is being overwritten
        #=====================================================================#  
    def writeControl(self):
        with open(self.dataFile.get(),'w') as f:
            for i in range(len(self.data[0])):
                f.write('%f %f %f %f %f\n'%(self.data[0][i],self.data[1][i],self.data[2][i],self.data[3][i],self.data[4][i]))
        return

        #=====================================================================#
        # Reset all changes made to the data or reset to zeros
        #=====================================================================#          
    def resetControl(self):
        self.data = np.copy(self.oldData)
        self.drawData()
        return
        #=====================================================================#
        # create dummy data 
        #=====================================================================#  
    def fill_dummy_data(self):
        """empty data set."""
        if self.status[0]:
            tmpEntries = np.ones(self.numOfImages)
            tmpT = np.arange(self.numOfImages)
            # if data file was previously selected, store this data for reset
            if self.status[1]:
                self.oldData = self.data
                self.data = np.array([tmpT,tmpEntries,tmpEntries,tmpEntries,tmpEntries])
            else:
                self.data = np.array([tmpT,tmpEntries,tmpEntries,tmpEntries,tmpEntries])
                self.oldData = self.data
        self.status[1] = True
            
        #=====================================================================#
        # An action requires the data to be redrawn
        #=====================================================================#      
            
    def drawData(self):
        # draw raw data and background
        plt.figure('Data')
        self.ax['Data'].cla()
        self.vLine = []
        plt.plot(self.oldData[0],self.oldData[2],c=UCblue[2],lw=1,ls='dotted')
        plt.plot(self.data[0],self.data[2],c=UCblue[2],lw=2)
        plt.plot(self.oldData[0],self.oldData[1],c=UCgreen[4],lw=1,ls='dotted')
        plt.plot(self.data[0],self.data[1],c=UCgreen[4],lw=2)
        plt.xlim(min(self.data[0]),max(self.data[0]))
        self.canvas['Data'].draw()
        self.drawDataLine()
        # draw background subtracted data - (F-Bg)
        plt.figure('Flow')
        self.ax['Flow'].cla()
        bg = self.data[1]+1
        fl = self.data[2]
        ratio = fl/bg -1
        plt.plot(self.data[0],ratio,c=UCgreen[4],lw=2)
        n = 10
        plt.plot(self.data[0][:-n+1],piaImage.moving_average(ratio, n),c=UCgreen[2],lw=2)
        plt.xlim(min(self.data[0]),max(self.data[0]))
        self.canvas['Flow'].draw()
        return

        #=====================================================================#
        # If a new data file has been selected write new data there
        #=====================================================================#  
    
    def writeNewData(self):
        '''write new data set without overwriting old data.'''
        if self.status[2] and len(self.data)>0:
            with open(self.newFile.get(),'w') as f:
                for i in range(len(self.data[0])):
                    f.write('%f %f %f %f %f\n'%(self.data[0][i],self.data[1][i],self.data[2][i],self.data[3][i],self.data[4][i]))
        return
        #=====================================================================#
        # If active the user may draw another flow rectangular
        #=====================================================================#  
    def AutoRunControl(self):
        if not self.newAutoRun:
            self.newAutoRun = True
        return

    def jumpToStart(self):
        self.currentIndex.set(self.startIndex.get())
        if self.status[0]:
                 #--------- Update line position and main image ---------
            self.drawDataLine()
            self.updateMain()
            self.drawRect()
        return
        
        #=====================================================================#
        # The user has clicked on the main image frame
        # If he previously specified that he wants to define a new flow
        # region he can drag a rectangle acros the desired region
        #=====================================================================#      
    def onPressMain(self,event):
        if self.AutoRunActive:
            self.AutoRunActive = False
            return
        if self.newAutoRun:
#            print self.ROI
            self.ROI = []
            self.ROILocationData = [event.xdata,event.ydata]
            
        else:
            self.data[3][self.currentIndex.get()] = event.xdata
            self.data[4][self.currentIndex.get()] = event.ydata
            self.drawRect()
            self.getFluoresence()
            self.drawData()

        if self.nextImgOnClick.get() == 1 and not self.newAutoRun:
            self.currentIndex.set(self.currentIndex.get() + 1 + self.skipFrames.get())
                 #--------- Increment current index  --------- 
            if self.currentIndex.get() >= self.numOfImages-1:
                self.currentIndex.set(self.startIndex.get())
                 #--------- Update line position and main image ---------
            self.drawDataLine()
            self.updateMain()
            self.drawRect()
        return

        #=====================================================================#
        # The user has release the mouse button on the main image frame
        # If he previously specified that he wants to start the tracker,
        # click on the image to start the tracker.
        #=====================================================================#    
    def onReleaseMain(self,event):
        if self.newAutoRun:
            #self.ROILocationData = [event.xdata,event.ydata]
            self. drawRegionOfInterest()
            self.canvas['Main'].draw()
            self.AutoRunActive = True
            if self.AutoRunActive:
                index = 0
                self.updateAutoRun(index)
                if index >= self.numOfImages-1:
                    self.AutoRunActive = False
            self.newAutoRun = False
        return
        
        #=====================================================================#
        # Determine new neuron location and get signal and bg fluoresence
        #=====================================================================# 
    def getFluoresence(self):
            # ---- Get analysis box size and central position ----
        index = self.currentIndex.get()
        xC = int(np.round(self.data[3][self.currentIndex.get()]))
        yC = int(np.round(self.data[4][self.currentIndex.get()]))
        _tmpImg = self.imageData
        self.AutoFluorescenceDetector(_tmpImg, xC, yC, index)
        return   

        #=====================================================================#
        # An action requires the flow region to be drawn
        #=====================================================================#  
    def drawRegionOfInterest(self):
        plt.figure('Main')
        self.ROI = []
        self.ROI.append(self.ax['Main'].plot(np.round(self.ROILocationData[0]), np.round(self.ROILocationData[1]), 'o', color=UCorange[0]))
        #add_patch(Rectangle((np.round(self.flowRegionData[0][0]), np.round(self.flowRegionData[0][1])), self.flowRegionData[1][0]-self.flowRegionData[0][0], self.flowRegionData[1][1]-self.flowRegionData[0][1], edgecolor=UCgreen[4],facecolor='none',alpha=1,lw=2)))
        self.canvas['Main'].draw()        
        return

        #=====================================================================#
        # Update the autotracker results (or create if not run before)
        #=====================================================================#          
    def updateAutoRun(self, index):
        
        i = self.currentIndex.get()
        if index ==0:
            # read current image
            _tmpImage = mpimg.imread(os.path.join(self.imageFolder.get(),self.imageNames[i]))
            # update coordinates
            tmp_xC, tmp_yC = self.ROILocationData
            # use same algoruthm as manual to get fluorescence
            self.AutoFluorescenceDetector(_tmpImage, tmp_xC, tmp_yC, i)
            #self.ax['Main'].plot(self.data[3][0], self.data[4][0], 'o', color= UCmain)
        else:
             # read current image
            _tmpImage = mpimg.imread(os.path.join(self.imageFolder.get(),self.imageNames[i]))
            # update coordinates
            tmp_xC, tmp_yC  = self.data[3][i-1]+(self.data[3][i-1]-self.data[3][i-2])*0.1, self.data[4][i-1]++(self.data[4][i-1]-self.data[4][i-2])*0.1
            
            #xC, yC = np.average(self.data[3][max(0,i-3):i]),  np.average(self.data[4][max(0,i-3):i])
            # use same algoruthm as manual to get fluorescence
            self.AutoFluorescenceDetector(_tmpImage, tmp_xC, tmp_yC, i)
            #self.
            #self.ax['Main'].plot(self.data[3][i], self.data[4][i], 'o', color= UCmain)
        
        self.drawDataLine()
        self.updateMain()
        self.drawRect()
        self.drawData()
        if len(self.ROI) > 0:
            for item in self.ROI:
                print self.ax['Main'].lines, item
                self.ax['Main'].lines.remove(item[0])
                self.ROI = []
        self.currentIndex.set(i+1)
        index += 1
        if self.AutoRunActive and index <= self.numOfImages-1:
            root.after(2, lambda: self.updateAutoRun(index))
        return
        
    def AutoFluorescenceDetector(self, img, xC, yC, index):
        '''Fluorescence analyzer'''
        bgSize = int(np.round(self.boxBG.get()/2.0))
        neuronSize = int(np.round(self.boxNeuron.get()/2.0))
        threshold = self.signalThreshold.get()
        if self.process.get():
            print self.process
            xNew,yNew,Signal, BgLevel = piaImage.processFluorescence(img, bgSize,neuronSize, threshold, xC, yC)
        else:
            xNew,yNew,Signal, BgLevel = piaImage.fluorescence(img, bgSize,neuronSize, threshold, xC, yC)
    
         # --- Update neuron info in data  ---
        self.oldData[:,index] = self.data[:,index] 
        self.data[3][index] = xNew#Neuron+xMin
        self.data[4][index] = yNew#Neuron+yMin
        self.data[2][index] = Signal#newNeuronAverage
        self.data[1][index] = BgLevel#bgLevel
             
        return   
        
        
        #=====================================================================#
        # The user has clicked on the data image frame
        # Get click position and set the position tracker line to these coords
        # Update the current and start index used for video playback
        # Redraw the main image with updated start index
        #=====================================================================#  
    def onPressData(self,event):
        if self.toolbar['Data'].mode!='':
            print("You clicked on something, but toolbar is in mode {:s}.".format(self.toolbar['Data'].mode))
            return
        # ------------stop an autorun -------------
        if self.AutoRunActive:
            self.AutoRunActive = False
            
             #--------- Get new image index from click --------- 
        if self.status[0] and self.status[1]:
            if not event.inaxes:
                self.startIndex.set(0)
                self.currentIndex.set(0)    
            elif int(np.round(event.xdata)) > self.numOfImages-1:
                self.startIndex.set(self.numOfImages-1)
                self.currentIndex.set(self.numOfImages-1)   
            else:
                self.startIndex.set(int(np.round(event.xdata)))
                self.currentIndex.set(int(np.round(event.xdata)))

             #--------- Update position indicator and main image ---------     
            self.drawDataLine()
            self.drawMain()
            self.drawRect()
            
                

        #=====================================================================#
        # Draw a vertical line at the current index position in the data image
        #=====================================================================#  
    def drawDataLine(self):
             #--------- Update position indicator --------- 
        plt.figure('Data')
        if len(self.vLine) > 0:
            for item in self.vLine:
                item.remove()
        self.vLine = []
        self.vLine.append(plt.axvline(self.currentIndex.get(),ls='dashed',c='k'))
        self.canvas['Data'].draw()        
        return

        #=====================================================================#
        # Draw two rectangles in the main frame locating signal and BG regions
        #=====================================================================#
    def drawRect(self):
        plt.figure('Main')
        if len(self.rect) > 0:
            for item in self.rect:
                item.remove()
        self.rect = []
        size = self.boxBG.get()/2.0
        self.rect.append(self.ax['Main'].add_patch(Rectangle((np.round(self.data[3][self.currentIndex.get()]) - size, np.round(self.data[4][self.currentIndex.get()]) - size), 2*size, 2*size, edgecolor=UCblue[2],facecolor='none',alpha=1,lw=2)))
        size = self.boxNeuron.get()/2.0#self.boxBG.get()/2.0
        self.rect.append(self.ax['Main'].add_patch(Rectangle((np.round(self.data[3][self.currentIndex.get()]) - size, np.round(self.data[4][self.currentIndex.get()]) - size), 2*size, 2*size, edgecolor=UCorange[2],facecolor='none',alpha=1,lw=2)))
        self.canvas['Main'].draw()
        return
        
        #=====================================================================#
        # Get new image data. Delete old image and plot a new one. This is
        # necessary when the aspect ratio is being changed, i.e. after cropping
        # Do not use this function for video playback as it is significantly
        # slower than just changing the data of the image
        #=====================================================================#          
    def drawMain(self):
             #--------- Load image with current index --------- 
        self.imageData = mpimg.imread(os.path.join(self.imageFolder.get(),self.imageNames[self.currentIndex.get()]))
        if self.rotate.get() == 1:
            self.imageData = self.imageData.transpose()
        
             #--------- Delete old image and plot new ---------             
        plt.figure('Main')
        self.ax['Main'].cla()
        self.rect = []
        self.flowRegion = []
        self.mainImage = plt.imshow(self.imageData,cmap=cMaps[self.colorMap.get()])
        self.ax['Main'].set_aspect('equal', 'datalim')
        plt.setp(self.ax['Main'].get_xticklabels(), visible=False)
        plt.setp(self.ax['Main'].get_yticklabels(), visible=False)
        self.canvas['Main'].draw()
        self.ax['Main'].autoscale(False)
        return
        
        #=====================================================================#
        # Get new image data and update the image within the main frame.
        # The axis are not being updated. This speeds up the render process.
        #=====================================================================#          
    def updateMain(self):
             #--------- Load image with current index --------- 
        self.imageData = mpimg.imread(os.path.join(self.imageFolder.get(),self.imageNames[self.currentIndex.get()]))
        if self.rotate.get() == 1:
            self.imageData = self.imageData.transpose()
        
             #--------- Update image data ---------             
        self.mainImage.set_data(self.imageData)
        self.canvas['Main'].draw()
        return
        
    def onPressFlow(self,event):
        return        

        #=====================================================================#
        # Video playback controls. Clicking on run requests the execution of
        # newFrame within the next iteration of the mainloop. But no sooner
        # than the time specified within the after function (in ms)
        #=====================================================================#    
    def runControl(self):
                 #--------- Start video plaback  --------- 
        if self.status[0] and not self.status[3]:
            self._job_id = root.after(int(1000.0/float(self.playbackSpeed.get())), lambda: self.newFrame())
            self.status[3] = True
        return

        #=====================================================================#
        # Video playback controls. Clicking on pause prevents newFrame to
        # execute on the next iteration of mainloop as the job is deleted
        #=====================================================================#            
    def pauseControl(self):
             #--------- If video is playing stop it --------- 
        if self.status[3]:
            root.after_cancel(self._job_id)
            self._job_id = None
            self.status[3] = False
        return

        #=====================================================================#
        # Video playback controls. Invoked as soon as run has been pressed
        # until pause is being pressed.
        # The position tracker in the data frame is updated as well as the
        # data in the main image.
        # The current index is incremented and newFrame is requested to be
        # executed upon the next iteration of the mainloop.
        #=====================================================================#  
    def newFrame(self):
             #--------- Update line position and main image ---------
        self.drawDataLine()
        self.drawMain()
        self.drawRect()
        
        self.currentIndex.set(self.currentIndex.get() + 1 + self.skipFrames.get())
             #--------- Increment current index  --------- 
        if self.currentIndex.get() >= self.numOfImages-1:
            self.currentIndex.set(self.startIndex.get())
            
             #--------- Execute newFrame upon new mainloop iteration --------- 
        self._job_id = root.after(int(1.0/float(self.playbackSpeed.get())*1000), lambda: self.newFrame())       
        return

        
if __name__ == "__main__":
    root = tk.Tk()
    window = Window(root)
    root.mainloop()
