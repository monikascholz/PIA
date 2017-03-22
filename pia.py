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
from tkMessageBox import showerror
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
        # folders      
        self.imageFolder = tk.StringVar()
        self.dataFile = tk.StringVar()
        self.newFile = tk.StringVar()
        # control variables
        self.startIndex = tk.IntVar()
        self.startIndex.set(0)
        self.currentIndex = tk.IntVar()
        self.currentIndex.set(0)
        self.endIndex = tk.IntVar()
        self.intervalIndex = tk.IntVar()
        self.intervalIndex.set(1000)
        
        self.imageType = tk.StringVar()
        self.imageType.set('tif')
        
        self.playbackSpeed = tk.IntVar()
        self.playbackSpeed.set(5)
        self.skipFrames = tk.IntVar()
        self.skipFrames.set(0)
        self.nextImgOnClick = tk.IntVar()
        self.nextImgOnClick.set(1)
        self.colorMap = tk.StringVar()
        self.colorMap.set('gray')
        
        # alternative tracking options
        # track the process too
        self.mode = tk.StringVar()
        self.mode.set('Single Neuron')
        # dual color
        self.dualX = tk.IntVar()
        self.dualX.set(-10)
        self.dualY = tk.IntVar()
        self.dualY.set(-510)
        # tracking parameters
        self.boxShow = tk.IntVar()
        self.signalThreshold = tk.IntVar()
        self.boxNeuron = tk.IntVar()
        self.boxBG = tk.IntVar()
        
        self.boxShow.set(1)
        self.boxBG.set(200)
        self.boxNeuron.set(50)
        self.signalThreshold.set(95)
        
        # internal data variables/ storage
        self.imageData = []
        self.imSize = (0,0)
        self.data = []
        self.oldData = []
        self.ncols = 21
        # matplotlib variables
        self.imageNames = []
        self.mainImage = None
        self.pause = 0
        self.cidPress = {}
        self.vLine = []
        self.rect = []
        self.canvas = {}
        self.ax = {}
        self.figure = {}
        self.toolbar = {}
        
        self.newAutoRun = False
        self.AutoRunActive = False
        self.ROILocationData = []
        self.ROI = []
        
        columnWidth = 40
        buttonWidth = 10
        textWidth = 15
        entryWidth = 10
        
        ControlFrame = tk.Frame(root)
        ControlFrame.pack(expand = 1,fill=tk.BOTH)#grid(column=0,row=0,columnspan=2,sticky=tk.NSEW )
        #--------------------- display PIA logo  ------------------------
        LogoFrame = tk.Frame(ControlFrame)
        LogoFrame.grid(column=0,row=0,rowspan=5,sticky=tk.NSEW)
        LogoFrame.columnconfigure(0, weight=1)
        LogoFrame.rowconfigure(0, weight=1)
        self.figure['Logo'] = plt.figure('Logo', (1.5,1.5),edgecolor='None',facecolor='None')
        self.canvas['Logo'] = FigureCanvasTkAgg(self.figure['Logo'], master=LogoFrame)
        self.ax['Logo'] = self.figure['Logo'].add_subplot(111)
       
        img=mpimg.imread('PIA.png')
        self.ax['Logo'].imshow(img)
        self.ax['Logo'].set_xticks([])
        self.ax['Logo'].set_yticks([])
        self.ax['Logo'].set_axis_off()
        self.canvas['Logo'].show()
        self.canvas['Logo'].get_tk_widget().grid(column=0,row=0,sticky=tk.NSEW)
       
        #--------------------- Select image and data folders folder  ------------------------
        FolderFrame = tk.Frame(ControlFrame)
        FolderFrame.grid(column=1,row=0, rowspan=3,sticky=tk.NSEW)
        FolderFrame.columnconfigure(0, weight=1)
        FolderFrame.columnconfigure(1, weight=1)
        names = ['Image Folder', 'Data File','New File']
        varnames = [self.imageFolder, self.dataFile, self.newFile]
        actions = [self.selectImageFolder, self.selectDataFile, self.selectNewFile]
        for i in range(3):
            tmpText = tk.StringVar()
            tmpText.set(names[i])
            FolderFrame.rowconfigure(i, weight=1)
            tmpFolderLabel = tk.Label(FolderFrame, textvariable=tmpText,width=textWidth,anchor=tk.W,justify=tk.LEFT)
            tmpFolderLabel.grid(column=0,row=i,sticky=tk.NSEW)
            tmpFolderEntry = tk.Entry(FolderFrame, textvariable=varnames[i],width=columnWidth)
            tmpFolderEntry.grid(column=1,row=i,sticky=tk.NSEW)
            tmpFolderButton = tk.Button(FolderFrame, text = 'Select', fg = 'black', command= actions[i],width=buttonWidth)
            tmpFolderButton.grid(column=2,row=i,sticky=tk.NSEW)

        #--------------------- Control Buttons  ------------------------  
        controlSubFrame1 = tk.Frame(ControlFrame)
        controlSubFrame1.grid(column=2,row=0,rowspan=4,sticky=tk.NSEW)
        controlSubFrame1.columnconfigure(0, weight=1)
        controlSubFrame1.columnconfigure(1, weight=1)
        buttonText = ['Run', 'Pause', 'Reset Data', 'Overwrite Data', 'Write to new file','','Jump To Start','Run Tracker']
        buttonCommands = [self.runControl, self.pauseControl, self.resetControl, self.writeControl, self.writeNewData,None,self.jumpToStart,self.AutoRunControl]
        for i in range(4):
            controlSubFrame1.rowconfigure(i, weight=1)
            runControlButton = tk.Button(controlSubFrame1, text = buttonText[2*i], fg = 'black', command= buttonCommands[2*i],width=buttonWidth)
            runControlButton.grid(column=0,row=i,sticky=tk.NSEW)  
            if i!=2:
                pauseControlButton = tk.Button(controlSubFrame1, text = buttonText[2*i+1], fg = 'black', command= buttonCommands[2*i+1],width=buttonWidth)
                pauseControlButton.grid(column=1,row=i,sticky=tk.NSEW)
      
        #--------------------- Select options ---------------------------------
        optionsFrame = tk.Frame(ControlFrame)
        optionsFrame.grid(column=3,row=0,rowspan=5,sticky=tk.NSEW)
        optionsFrame.columnconfigure(0, weight=1)
        optionsFrame.columnconfigure(1, weight=1)
        
        controlSubFrame1.columnconfigure(0, weight=1)
        controlSubFrame1.columnconfigure(1, weight=1)
            #--------- Start index ---------
        optionsLocations = {'Starting index':[(0,0),self.startIndex, 'entry'],
                            'Current index':[(0,1), self.currentIndex, 'entry'],
                            'Playback Speed':[(0,2),self.playbackSpeed, 'entry'],
                            'Skip Frames' :[(0,3),self.skipFrames, 'entry'],
                            'Next image on click':[(0,5),self.nextImgOnClick, 'check'],
                            'Show Fl/BG boxes':[(2,0),self.boxShow, 'check'],
                            'Neuron box size':[(2,1),self.boxNeuron, 'entry'],
                            'BG box size':[(2,2),self.boxBG, 'entry'],
                            'Signal Th. [%]':[(2,3),self.signalThreshold, 'entry']
                            }
        for key in optionsLocations.keys():
            nCol, nRow= optionsLocations[key][0]
            controlSubFrame1.rowconfigure(nRow, weight=1)
            OptionsText = tk.StringVar()
            OptionsText.set(key)
            OptionsLabel = tk.Label(optionsFrame,textvariable=OptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
            OptionsLabel.grid(column=nCol, row=nRow, sticky=tk.NSEW)
            if optionsLocations[key][2]=='entry':
                startOptionsEntry = tk.Entry(optionsFrame,textvariable=optionsLocations[key][1],justify=tk.CENTER,width=entryWidth)
            elif optionsLocations[key][2]=='check':
                startOptionsEntry = tk.Checkbutton(optionsFrame, variable=optionsLocations[key][1])
            startOptionsEntry.grid(column=nCol+1,row=nRow, sticky=tk.NSEW)
                                  
             #--------- Dual color tracking ---------
        dualOptionsText = tk.StringVar()
        dualOptionsText.set('Track Mode')
        dualOptionsLabel = tk.Label(optionsFrame,textvariable=dualOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        dualOptionsLabel.grid(column=4,row=1, sticky=tk.NSEW)
        dualOptionsCheckbutton = tk.OptionMenu(optionsFrame, self.mode, 'Single Neuron', 'Single Neuron (Ratio)', '2 Neurons', '2 Neurons (Ratio)')
        dualOptionsCheckbutton.config(width=textWidth)
        dualOptionsCheckbutton.grid(column=5,row=1,sticky=tk.NSEW)  

        vecFrame = tk.Frame(optionsFrame)
        vecFrame.grid(row=0, column=4, columnspan=2, sticky=tk.NSEW)
              #--------- Dual color tracking ---------
        dualvecOptionsText = tk.StringVar()
        dualvecOptionsText.set('dual color shift (x,y)')
        dualvecOptionsLabel = tk.Label(vecFrame,textvariable=dualvecOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        dualvecOptionsLabel.grid(column=0,row=0, sticky=tk.NSEW)
        
        dualvecOptionsEntry = tk.Entry(vecFrame,textvariable=self.dualX,justify=tk.CENTER,width=5)
        dualvecOptionsEntry.grid(column=1,row=0, sticky=tk.NSEW)
        dualvecOptionsEntry = tk.Entry(vecFrame,textvariable=self.dualY,justify=tk.CENTER,width=5)
        dualvecOptionsEntry.grid(column=2,row=0, sticky=tk.NSEW) 

            #--------- Image type ---------
        imTypeOptionsText = tk.StringVar()
        imTypeOptionsText.set('Image data type')
        imTypeOptionsLabel = tk.Label(optionsFrame,textvariable=imTypeOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        imTypeOptionsLabel.grid(column=4,row=2, sticky=tk.NSEW)
        imTypeOptionsMenu = tk.OptionMenu(optionsFrame,self.imageType,'tif','png','jpg')
        imTypeOptionsMenu.grid(column=5,row=2, sticky=tk.NSEW)

            #--------- Colormap ---------
        colorMapOptionsText = tk.StringVar()
        colorMapOptionsText.set('Colormap')
        colorMapOptionsLabel = tk.Label(optionsFrame,textvariable=colorMapOptionsText,anchor=tk.E,justify=tk.LEFT,width=textWidth)
        colorMapOptionsLabel.grid(column=4,row=3, sticky=tk.NSEW)
        colorMapOptionsMenu = tk.OptionMenu(optionsFrame,self.colorMap,'gray','blue','green','jet','hot')
        colorMapOptionsMenu.grid(column=5,row=3, sticky=tk.NSEW)   
        
        #------------------------ Main Figure Frame ---------------------------
        
        
        mainFigureFrame = tk.Frame(root)
        mainFigureFrame.pack(fill=tk.BOTH,expand = 1)#.grid(column=0,row=1,columnspan=5,rowspan=1,sticky=tk.NSEW)
        vidFrame = tk.Frame(mainFigureFrame)
        vidFrame.grid(column=0,row=0,rowspan=3,sticky=tk.NSEW )
        vidFrame.columnconfigure(0, weight=1)
        vidFrame.columnconfigure(1, weight=1)
        
        self.figure['Main'] = plt.figure('Main',figsize=(7,7), dpi=100, edgecolor='k',facecolor='w')
        self.canvas['Main'] = FigureCanvasTkAgg(self.figure['Main'], master=vidFrame)
        self.ax['Main'] = self.figure['Main'].add_subplot(111)
        plt.setp(self.ax['Main'].get_xticklabels(), visible=False)
        plt.setp(self.ax['Main'].get_yticklabels(), visible=False)
        plt.tight_layout()
        self.canvas['Main'].show()
        self.canvas['Main'].get_tk_widget().pack(expand=1)
        self.cidPress['Main'] = self.canvas['Main'].mpl_connect('button_press_event', self.onPressMain)
        self.cidPress['Main2'] = self.canvas['Main'].mpl_connect('button_release_event', self.onReleaseMain)
        
        #------------------- Data + Analysed Figure Frame ---------------------
        subFigureFrame = tk.Frame(mainFigureFrame)
        subFigureFrame.grid(column=1,row=1,sticky=tk.NSEW )
        subFigureFrame.columnconfigure(0, weight=1)
        subFigureFrame.columnconfigure(1, weight=1)
        subFigureFrame.rowconfigure(0, weight=1)
        subFigureFrame.rowconfigure(1, weight=1)
        toolbarFrame1 = tk.Frame(mainFigureFrame)
        toolbarFrame1.grid(column=1,row=0,sticky=tk.NSEW)
        toolbarFrame1.columnconfigure(0, weight=1)
        toolbarFrame1.columnconfigure(0, weight=1)
        
        toolbarFrame2 = tk.Frame(mainFigureFrame)
        toolbarFrame2.grid(column=1,row=2,sticky=tk.NSEW)
        toolbarFrame2.columnconfigure(0, weight=1)
           #--------- Data Figure ---------        
        
             #--------- Data Figure ---------        
        self.figure['Data'] = plt.figure('Data',figsize=(9,3.), dpi=100, edgecolor='k',facecolor='w')
        
        self.ax['Data'] = self.figure['Data'].add_subplot(111)
        self.ax['Data'].set_xlabel('time (frames)')
        self.ax['Data'].set_ylabel('Raw Fluorescence')
        
        self.canvas['Data'] = FigureCanvasTkAgg(self.figure['Data'], master=subFigureFrame)
        self.canvas['Data'].show()
        #self.canvas['Data'].get_tk_widget().pack()
        self.toolbar['Data'] = NavigationToolbar2TkAgg(self.canvas['Data'], toolbarFrame1)
        self.toolbar['Data'].update()
        #self.canvas['Data'].get_tk_widget().grid(column=0, row=0,sticky=tk.NSEW)
        self.canvas['Data'].get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        #self.canvas['Data']._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.cidPress['Data'] = self.canvas['Data'].mpl_connect('button_press_event', self.onPressData)
        plt.tight_layout()

             #--------- Analyzed Figure ---------        
        self.figure['Flow'] = plt.figure('Flow',figsize=(9,3.), dpi=100, edgecolor='k',facecolor='w')
        self.ax['Flow'] = self.figure['Flow'].add_subplot(111)
        self.ax['Flow'].set_xlabel('time (frames)')
        self.ax['Flow'].set_ylabel('F/Bg')
        #plt.tight_layout()
        self.canvas['Flow'] = FigureCanvasTkAgg(self.figure['Flow'], master=subFigureFrame)
        self.canvas['Flow'].show()
        self.toolbar['Flow'] = NavigationToolbar2TkAgg( self.canvas['Flow'],toolbarFrame2)
        self.toolbar['Flow'].update()
        self.canvas['Flow']._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        #self.canvas['Flow'].get_tk_widget().grid(row=1, column = 0,sticky=tk.NSEW)
        #self.canvas['Flow'].get_tk_widget().pack()
        #self.cidPress['Flow'] = self.canvas['Flow'].mpl_connect('button_press_event', self.onPressFlow)
        plt.tight_layout()
      
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
        tmp_file = tfd.askdirectory(parent=root, initialdir='/media/monika/Nak/GCAMp Data/MK00014_160613/MK00014_EF1_160613', title='Select image folder')
        if not os.path.isdir:
            showerror(title = "Image directory error", message = "Not an image directory")
        else:
            self.imageFolder.set(tmp_file)
                 #--------- Get all images in folder and sort them --------- 
            tmp = np.array(os.listdir(self.imageFolder.get()))
            tmpNames = {}
            tmpTimes = []
            for item in tmp:
                if item[-3:] == self.imageType.get():
                    time = float(item[:-4].split('_')[-1])#float(item[:-4].split('_')[3])
                    tmpTimes.append(time)
                    tmpNames[time] = item
            if len(tmpNames)==0:
                showerror(title = "Images not found", message = "No images found in folder!")
                return
            self.imageNames = [tmpNames[x] for x in sorted(tmpTimes)]
            self.numOfImages = len(self.imageNames)
            self.status[0] = True
            
                #--------- make a dummy data file with zeros --------- 
            self.fill_dummy_data()
                #--------- Draw main image and set status of main image --------- 
            self.redrawMain()
            self.imSize = self.imageData.shape

        #=====================================================================#
        # Select button for the data file has been pressed
        # Read the provided data file: Time, Fluoresence, None, X, Y
        # Remove previous data plots and redraw new data
        # Save that the data frame is now active
        #=====================================================================#           
    def selectDataFile(self):
             #--------- Get data file from user --------- 
        self.dataFile.set(tfd.askopenfilename(parent=root, initialdir='./', title='Select existing data file'))
        if not os.path.isfile(self.dataFile.get()):
            showerror(title = "File opening error", message = "File does not exist.")
            self.dataFile.set('')  
            return 
        #num_lines = sum(1 for line in open(self.dataFile.get(),'r'))
        
        # the columns are t, bg, f, x, y a for channel 1 and 2 respectively
             #--------- Read data file  --------- 
        self.data = np.loadtxt(self.dataFile.get())
#        with open(self.dataFile.get(),'r') as f:
#            self.data = np.ones((num_lines,self.ncols))
#            self.data[:,0] = np.arange(num_lines)
#            lindex = 0
#            for line in f.readlines():
#                if line[0]=='#':
#                    continue
#                try:
#                    ln = np.array(line.split(),dtype='float')
#                except ValueError:
#                    showerror(title = "File opening error", message = "File is not supported.")
#                    break
#                if len(ln) !=self.ncols:
#                    #tk.Tk.withdraw()
#                    showerror(title = "File opening error", message = "File does not have the correct number of columns.")
#                    break
#                else:
#                    self.data[lindex] = ln
#                lindex+=1
        self.data = self.data.T
        self.oldData = self.data
        
             #--------- Plot fluorescence profile  --------- 
        plt.figure('Data')
        self.ax['Data'].cla()
        self.drawData()
             #--------- Set status of data image ---------         
        self.status[1] = True
        return
        #=====================================================================#
        # Select button for the new data file has been pressed. This avoids overwriting existing data.
        #=====================================================================#  
    def selectNewFile(self):
        self.newFile.set(tfd.asksaveasfilename(parent=root, initialdir='./', title='Select a filename to save to'))
        self.status[2] = True
        return
        
        #=====================================================================#
        # Write new data file. The old one is being overwritten
        #=====================================================================#  
    def writeControl(self):
        np.savetxt(self.dataFile.get(), self.data.T,  delimiter=' ', newline='\n', header='#Frame BG1 F1 X1 Y1 A1 BG2 F2 X2 Y2 A2')
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
            # if data file was previously selected, store this data for reset
            if self.status[1]:
                self.oldData = self.data
                self.data = np.ones((self.ncols,self.numOfImages))
                self.data[0] = np.arange(self.numOfImages)
            else:
                self.data = np.ones((self.ncols,self.numOfImages))
                self.data[0] = np.arange(self.numOfImages)
                self.oldData = self.data
        self.status[1] = True
        #=====================================================================#
        # redraw all plots in main window
        #=====================================================================# 
    def redrawMain(self):
        """draw video frame, data, lines and location rectangle."""
        self.drawMain()
        self.drawData()
        self.drawDataLine()
        #self.updateMain()
        self.drawRect()
        #=====================================================================#
        # An action requires the data to be redrawn
        #=====================================================================#      
            
    def drawData(self):
        # draw raw data and background
        plt.figure('Data')
        self.ax['Data'].cla()
        self.ax['Data'].set_xlabel('time (frames)')
        self.ax['Data'].set_ylabel('Raw Fluorescence')
        self.vLine = []
        #Frame BG1 F1 X1 Y1 A1 BG2 F2 X2 Y2 A2 BG3 F3 X3 Y3 A3 BG4 F4 X4 Y4 A4        
        
        time, redBg1, redFl1, _,_,_, greenBg1, greenFl1, _,_,_,  redBg2, redFl2, _,_,_, greenBg2, greenFl2,_,_,_ = self.data
        if self.mode.get()=='Single Neuron (Ratio)':
            plt.plot(time,redFl1,c=UCred[2],lw=2, label = 'Red F')
            plt.plot(time,redBg1,c=UCorange[0],lw=2, linestyle = '--',label = 'Red Bg')
            plt.plot(time,greenFl1,c=UCgreen[0],lw=2, label = 'Green F')
            plt.plot(time,greenBg1,c=UCgreen[2],lw=2, linestyle = '--',label = 'Green Bg')
            ratio = redFl1/redBg1 - 1
            ratio2 = greenFl1/greenBg1 - 1
            ratio3 = (greenFl1 - greenBg1)/(redFl1 - redBg1)
            
        elif self.mode.get()=='2 Neurons (Ratio)':
            plt.plot(time,redFl1,c=UCred[2],lw=2, label = 'Red F')
            plt.plot(time,redBg1,c=UCorange[0],lw=2, linestyle = '--',label = 'Red Bg')
            plt.plot(time,greenFl1,c=UCgreen[0],lw=2, label = 'Green F')
            plt.plot(time,greenBg1,c=UCgreen[2],lw=2, linestyle = '--',label = 'Green Bg')
            offset = 2*np.max(redFl1)
            plt.plot(time,redFl2+offset,c=UCred[2],lw=2, label = 'Red F 2')
            plt.plot(time,redBg2+offset,c=UCorange[0],lw=2, linestyle = '--',label = 'Red Bg2')
            plt.plot(time,greenFl2+offset,c=UCgreen[0],lw=2, label = 'Green F 2')
            plt.plot(time,greenBg2+offset,c=UCgreen[2],lw=2, linestyle = '--',label = 'Green Bg 2')
           
            ratio3 = (greenFl1 - greenBg1)/(redFl1 - redBg1)
            ratio4 = (greenFl2 - greenBg2)/(redFl2 - redBg2)
            
        elif self.mode.get() == '2 Neurons':
            plt.plot(time,redFl1,c=UCred[2],lw=2, label = 'F1')
            plt.plot(time,redBg1,c=UCorange[0],lw=2, linestyle = '--',label = 'Bg1')
            plt.plot(time,redFl2,c=UCmain,lw=2, label = 'F2')
            plt.plot(time,redBg2,c=UCorange[1],lw=2, linestyle = '--',label = 'Bg2')
            ratio = redFl1/redBg1 - 1
            ratio2 = redFl2/redBg2 - 1
            
        else:
            plt.plot(time,redFl1,c=UCred[2],lw=2, label = 'F')
            plt.plot(time,redBg1,c=UCorange[0],lw=2, linestyle = '--',label = 'Bg')
            ratio = redFl1/redBg1 - 1
            
        #plt.legend(loc = 4, fontsize=10)
        plt.xlim(min(time),max(time))
        # smoothin factor for ratio plot
        n = 10
        self.canvas['Data'].draw()
        self.drawDataLine()
        # draw background subtracted data - (F-Bg)
        plt.figure('Flow')
        self.ax['Flow'].cla()
        self.ax['Flow'].set_xlabel('time (frames)')
        self.ax['Flow'].set_ylabel('F/Bg')
        if self.mode.get()=='Single Neuron (Ratio)':
            plt.plot(time,ratio,c=UCred[0],lw=2, label = 'Channel 1 - Red')
            plt.plot(time,ratio2,c=UCgreen[0],lw=2, label = 'Channel 2 - Green')
            plt.plot(time,ratio3,c=UCblue[0],lw=2, label = '(Green-GreenBg)/(Red-RedBg)')
            plt.plot(time,piaImage.moving_average(ratio, n),c=UCred[2],lw=2)
            plt.plot(time,piaImage.moving_average(ratio2, n),c=UCgreen[2],lw=2)
            plt.plot(time,piaImage.moving_average(ratio3, n),c=UCblue[2],lw=2)
        
        elif self.mode.get()=='2 Neurons (Ratio)':
            plt.plot(time,ratio3+0.5,c=UCblue[0],lw=2, label = '(Green1-GreenBg)/(Red1-RedBg)')
            plt.plot(time,ratio4,c=UCorange[0],lw=2, label = '(Green2-GreenBg)/(Red2-RedBg)')
            plt.plot(time,piaImage.moving_average(ratio3+0.5, n),c=UCblue[2],lw=2)
            plt.plot(time,piaImage.moving_average(ratio4, n),c=UCorange[2],lw=2)
            
        elif self.mode.get() == '2 Neurons':
            plt.plot(time,ratio+0.5,c=UCblue[0],lw=2, label = 'Neuron 1 - Green')
            plt.plot(time,ratio2,c=UCorange[0],lw=2, label = 'Neuron 2 - Green')
            plt.plot(time,piaImage.moving_average(ratio+0.5, n),c=UCblue[2],lw=2)
            plt.plot(time,piaImage.moving_average(ratio2, n),c=UCorange[2],lw=2)
            
        else:
            plt.plot(time,ratio,c=UCblue[0],lw=2, label = 'Channel 1 - GCamp')
            plt.plot(time,piaImage.moving_average(ratio, n),c=UCblue[2],lw=2)
            
        plt.xlim(min(time),max(time))
        #plt.legend(loc=4, fontsize=10)
        self.canvas['Flow'].draw()
        return

        #=====================================================================#
        # If a new data file has been selected write new data there
        #=====================================================================#  
    
    def writeNewData(self):
        '''write new data set without overwriting old data.'''
        headerTxt = '#Frame BG1 F1 X1 Y1 A1 BG2 F2 X2 Y2 A2 BG3 F3 X3 Y3 A3 BG4 F4 X4 Y4 A4'
        if self.status[2] and len(self.data)>0:
            np.savetxt(self.newFile.get(), self.data.T,  delimiter=' ', newline='\n', header=headerTxt)
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

        if self.nextImgOnClick.get() == 1 and not self.newAutoRun and self.currentIndex.get() + 1 + self.skipFrames.get()<self.numOfImages:
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
                if index > self.numOfImages-1:
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
            # use same algorithm as manual to get fluorescence
            self.AutoFluorescenceDetector(_tmpImage, tmp_xC, tmp_yC, i)
        else:
             # read current image
            _tmpImage = mpimg.imread(os.path.join(self.imageFolder.get(),self.imageNames[i]))
            # update coordinates
            trackspeed = 0.2
            tmp_xC, tmp_yC  = self.data[3][i-1]+(self.data[3][i-1]-self.data[3][i-2])*trackspeed, self.data[4][i-1]+(self.data[4][i-1]-self.data[4][i-2])*trackspeed
            self.AutoFluorescenceDetector(_tmpImage, tmp_xC, tmp_yC, i)
        self.drawDataLine()
        self.updateMain()
        self.drawRect()
        self.drawData()
        if len(self.ROI) > 0:
            for item in self.ROI:
                self.ax['Main'].lines.remove(item[0])
                self.ROI = []
        self.currentIndex.set(i+self.skipFrames.get())
        index += 1
        if self.AutoRunActive and self.currentIndex.get()  < self.numOfImages:
            root.after(2, lambda: self.updateAutoRun(index))
        return
        
    def AutoFluorescenceDetector(self, img, xC, yC, index):
        '''Fluorescence analyzer'''
        bgSize = int(np.round(self.boxBG.get()/2.0))
        neuronSize = int(np.round(self.boxNeuron.get()/2.0))
        threshold = self.signalThreshold.get()
        
        if self.mode.get()=='Neuron and Process':
            trackResult = piaImage.processFluorescence(img, bgSize,neuronSize, threshold, xC, yC)
        elif self.mode.get()=='Single Neuron (Ratio)':
            trackResult = piaImage.dualFluorescence(img, bgSize,neuronSize, threshold, xC, yC, [self.dualX.get(),self.dualY.get()])
        elif self.mode.get()=='2 Neurons':
            trackResult = piaImage.singleFluorescence2Neurons(img, bgSize,neuronSize, threshold, xC, yC, [self.dualX.get(),self.dualY.get()], self.data[[3,4,13,14],index-1])
        elif self.mode.get()=='2 Neurons (Ratio)':
            trackResult = piaImage.dualFluorescence2Neurons(img, bgSize,neuronSize, \
                            threshold, xC, yC, [self.dualX.get(),self.dualY.get()], self.data[[3,4,13,14],index-1])
        else:
            trackResult = piaImage.fluorescence(img, bgSize,neuronSize, threshold, xC, yC)
        #-----pad trackResult to size 20----
        trackResult = np.pad(trackResult, (0,20-len(trackResult )), 'constant') 
        # --- Update neuron info in data  ---
        self.oldData[:,index] = self.data[:,index]
        self.data[1::,index] = trackResult

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
        plt.tight_layout()
        self.canvas['Data'].draw()        
        return

        #=====================================================================#
        # Draw two rectangles in the main frame locating signal and BG regions
        #=====================================================================#
    def drawRect(self):
        plt.figure('Main')
        if self.mode.get() =='Single Neuron (Ratio)' or self.mode.get() =='2 Neurons (Ratio)':
            if len(self.rect) > 0:
                for item in self.rect:
                    item.remove()
            self.rect = []
            size = self.boxBG.get()/2.0
            self.rect.append(self.ax['Main'].add_patch(Rectangle((np.round(self.data[3][self.currentIndex.get()]) - size, np.round(self.data[4][self.currentIndex.get()]) - size), 2*size, 2*size, edgecolor=UCblue[2],facecolor='none',alpha=1,lw=2)))
            self.rect.append(self.ax['Main'].add_patch(Rectangle((np.round(self.data[3][self.currentIndex.get()])+self.dualX.get() - size, np.round(self.data[4][self.currentIndex.get()]) +self.dualY.get() - size), 2*size, 2*size, edgecolor=UCblue[2],facecolor='none',alpha=1,lw=2)))
            size = self.boxNeuron.get()/2.0#self.boxBG.get()/2.0
            self.rect.append(self.ax['Main'].add_patch(Rectangle((np.round(self.data[3][self.currentIndex.get()]) - size, np.round(self.data[4][self.currentIndex.get()]) - size), 2*size, 2*size, edgecolor=UCorange[2],facecolor='none',alpha=1,lw=2)))
            self.rect.append(self.ax['Main'].add_patch(Rectangle((np.round(self.data[3][self.currentIndex.get()]) +self.dualX.get()- size, np.round(self.data[4][self.currentIndex.get()]) +self.dualY.get() - size), 2*size, 2*size, edgecolor=UCorange[2],facecolor='none',alpha=1,lw=2)))
            self.canvas['Main'].draw()
        else:
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
             #--------- Update image data ---------             
        self.mainImage.set_data(self.imageData)
        self.canvas['Main'].draw()
        return
        
#    def onPressFlow(self,event):
#        return        

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
        self.updateMain()
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
