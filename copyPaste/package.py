# -*- coding: utf-8 -*-

##      @file           package.py
##      @author         Lars van der Bijl
##      @contact        info@larsvanderbijl.nl
##
##      @desc           Copy and paste method built around the opscript function in houdini.
##----------------------------------------------------------------------------------------

"""
    Simple packaging and archiving method. 

"""

import os
import glob
import tempfile
import shutil
import zipfile
import logging

from lib import zipdir, unzip

import hou

def package():
    """
        First implementation of a packaging class for houdini files and assets.
        the function gets and packages all the OTL's and all in and outputs related to the scene.
        then it will package it as a ZIP file and store it in the home directory.
      
    """
      
    hou.hipFile.save()
    currentHip = hou.expandString(hou.hipFile.name())

    # create a temp directory we are going to fill with crap
    tempFilePath = tempfile.mkdtemp()
      
    otls = os.path.join(tempFilePath, "otls")
    os.mkdir(otls)
    files = os.path.join(tempFilePath, "files")
    os.mkdir(files)
    
    # Get all the external references to the hipfile
    fileOnDisk = hou.fileReferences()

    # loop and do what comes natural.
    for _file in fileOnDisk:

        parm = _file[0]
        filepath = _file[1]
    
        # if its a otl we need to store it.
        if filepath.endswith(".otl"):
    
            shutil.copy(hou.expandString(filepath), otls)
            
        else:
              
            if not os.path.isfile(hou.expandString(filepath)): 
                
                continue
                
            # create a directory in files and save 1 file to that location
            tmpFileName = os.path.basename(hou.expandString(filepath))
            tmpFileDir = os.path.basename(os.path.dirname(hou.expandString(filepath)))
            path = os.path.join(files, tmpFileDir)
              
            if not os.path.isdir(path):
              
                os.mkdir(path)

            shutil.copy(hou.expandString(filepath), os.path.join(path, os.path.basename(hou.expandString(filepath))))

            try:
                      
                if not parm.node().isLocked():
                      
                    parm.set(os.path.join(path.replace(tempFilePath, "$HIP"), tmpFileName))
                      
            except hou.PermissionError: 
                  
                logging.warning("Error hardening parm :" + str(parm.name()) + "on node " +parm.node().path())

    hou.hipFile.save(os.path.join(tempFilePath, os.path.basename(hou.expandString(hou.hipFile.name()))))
    # Load the source hipfile
    hou.hipFile.load(currentHip)
      
    # create a zipfile and package everything. then copy it to the home.
    zipfileLoc = zipdir(tempFilePath)
    shutil.move(zipfileLoc, os.path.join(hou.expandString("~"), "package.zip"))
    shutil.rmtree(tempFilePath)
      

def unpackage():
    """
        Unpacking of a scene file created by the copyPastePackage.package function. this needs to be looked at.
        I don't have windows so I have no idea if it works there.
            
    """

    zipfileLoc = hou.ui.selectFile(title="please select a zipFile created by the package function", pattern="*.zip")
    if not zipfileLoc: 
        
        return
    
    file_ = zipfile.ZipFile(hou.expandString(zipfileLoc), "r")

    isOke = False
    
    for name in file_.namelist():
        
        if name.endswith(".hip") or name.endswith(".hipnc"):
            
            isOke = True
            break
    
    if not isOke: 
        
        return
        
    unpackLoc = hou.expandString(hou.ui.selectFile(title="please select a directory you wish to use to unpack the files to."))
    
    if not unpackLoc or not os.path.isdir(unpackLoc): 
        
        return
      
    unzip(file_, unpackLoc)
    unpackageDir = os.path.dirname(file_.namelist()[0])
    otlsfiles = glob.glob(os.path.join(unpackLoc, unpackageDir, "otls", "*"))
    hipfile = glob.glob(os.path.join(unpackLoc, unpackageDir, "*.hip*"))
        
    if len(hipfile) != 1: 
        
        return
    
    hou.hipFile.load(hipfile[0])
        
    for otl in otlsfiles:

        hou.hda.installFile(otl)