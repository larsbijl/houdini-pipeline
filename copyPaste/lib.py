# -*- coding: utf-8 -*-

##      @file           lib.py
##      @author         Lars van der Bijl
##      @contact        info@larsvanderbijl.nl
##
##      @desc           Copy and paste method built around the opscript function in houdini.
##----------------------------------------------------------------------------------------

"""
    Functions and classes related to the copy and pasting of node networks using the opscript method and
    a crude method of packaging houdini scene for archiving or transport.

"""

import os
import zipfile

def zipdir(dirPath=None, zipFilePath=None, includeDirInZip=True):
    """
        function to zip up a directory structure and returns the location of the new Zip file.
    
    """

    if not zipFilePath:
        
        zipFilePath = dirPath + ".zip"
        
    if not os.path.isdir(dirPath):
        
        raise OSError("dirPath argument must point to a directory. '%s' does not." % dirPath)
    
    parentDir, dirToZip = os.path.split(dirPath)
    
    def trimPath(path):
        """
            Trims and returns the path of where the archive should go.
        
        """
        
        archivePath = path.replace(parentDir, "", 1)
        
        if parentDir:
            
            archivePath = archivePath.replace(os.path.sep, "", 1)
            
        if not includeDirInZip:
            
            archivePath = archivePath.replace(dirToZip + os.path.sep, "", 1)
            
        return os.path.normcase(archivePath)

    outFile = zipfile.ZipFile(zipFilePath, "w", compression=zipfile.ZIP_DEFLATED)
    
    for (archiveDirPath, dirNames, fileNames) in os.walk(dirPath):
        
        for fileName in fileNames:
            
            filePath = os.path.join(archiveDirPath, fileName)
            outFile.write(filePath, trimPath(filePath))

        if not fileNames and not dirNames:
            
            zipInfo = zipfile.ZipInfo(trimPath(archiveDirPath) + os.path.sep)
            outFile.writestr(zipInfo, "")
            
    outFile.close()
    
    return zipFilePath


def unzip(zip_, path=""):
    """
        Unzip a given zipfile object to a directory. if path is left empty it will unpack to where it was packaged. 
    
    """
     
    for each in zip_.namelist():
        
        if not each.endswith('/') and not each.endswith('\\'):
            
            root, name = os.path.split(each)
            directory = os.path.join(path, root)
                
            if not os.path.isdir(directory):
                
                os.makedirs(directory)
                
        file(os.path.join(directory, name), 'wb').write(zip_.read(each))
