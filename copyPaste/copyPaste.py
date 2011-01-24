# -*- coding: utf-8 -*-

##      @file           copyPaste.py
##      @author         Lars van der Bijl
##      @contact        info@larsvanderbijl.nl
##
##      @desc           Copy and paste method built around the opscript function in houdini.
##----------------------------------------------------------------------------------------
##      Version 0.3:
##      - Added the unpacking button and functions. part of the copyPastePackage class
##
##      Version 0.2: 
##      - Changed the post to pasteBin function to ask for address unless one is given.
##      - Tried to make it as platform independent as possible.
##      - Added copyPastePackage which will package the current scene as best it can.
##
##      Version 0.1: initial version of the package
##----------------------------------------------------------------------------------------
"""
    Functions and classes related to the copy and pasting of node networks using the opscript method.

"""

import os
import re
import time
import urllib

import hou

class CopyPaste(object):
    """
        copy and pasted function.
        this class should be used to write out a selection of nodes and save it to a location.

    """

    def __init__(self):
        
        self._copyFile = hou.expandString(os.path.join("~", "tmpHouWrite.cmd"))
        self._smartPaste = False


    def copy(self):
        """
            Read the selected nodes and do checks to see if there is anything we want to flag to the user.
            then pass the data to the write function.
            
        """
    
        lockedAssets = False

        # Get selected nodes and check if it's a locked asset.
        for node in hou.selectedNodes():
        
            if self.isLocked(node):
        
                lockedAssets = True
                break
            
            # see if the selected node has any children and if so also check them for being locked.
            for childNode in node.allSubChildren():
            
                if self.isLocked(childNode):
        
                    lockedAssets = True
                    break
        
        # If we found a locked assets lets tell the user and we can start doing the writing.
        if lockedAssets:
        
            hou.ui.displayMessage("you have a locked Node in your selection. the file will be saved but the data of that node will be lost.")
        
        
        code = ""
        
        for _node in hou.selectedNodes():
                            
            code += hou.hscript("opscript -r -b " + _node.path())[0]   

        # Nasty Hack we need to do for VopSop. seems that the normal method of writing out the opscript method gives us
        # a problem where the settings will be lost because the vop's inside will automatically override the settings.
        # So we will get the settings for the VopSop and add it to the end just to make sure there being set! Damn SESI

        if self.needVopFix()[0]:

            for _node in self.needVopFix()[1:]:
                
                if not self.isVop(_node.parent()):
                    
                    addCode = hou.hscript("opscript -b " + _node.path())[0]
                    
                    if "opspareds" in addCode:
			
			asCode = "opcf " + _node.parent().path() + "\nopspareds" + addCode.split("opspareds")[1]
			code += asCode
			

        self._write(code, self._copyFile)
    

    def paste(self):
        """
            This is a function to call if you want to invoke a paste of the tmp file.
            It will try to figure out if this is going to be easy or not. normally if it's just for a single user in between
            sessions a normal source will be sufficient but when it comes to different users and locations it gets a little more tricky.
            
        """

        if self.hasGostNodes() or self._smartPaste:

            userInput = hou.ui.displayMessage("Do you want to use Smart Paste?", buttons=('Yes', 'No', 'Cancel'))
            
            if userInput == 2 :
                
                return
            
            if userInput == 0 :
                
                desktop = hou.ui.curDesktop()
                panels = [panel for panel in desktop.paneTabs() if str(panel.type()) == "paneTabType.NetworkEditor"]
                
                if not len(panels) <= 1:

                    selectedLevel = hou.ui.selectNode()
                    
                    if not selectedLevel: 
                        
                        return
                    
                    copyPastePath = hou.node(selectedLevel)
                    
                else:
                
                    copyPastePath = desktop.paneTabOfType(hou.paneTabType.NetworkEditor).pwd()
                
                self.smartPaste(copyPastePath.path())
                
                return
            
        self._paste()
        

    def _paste(self):
        """
            Basic Pasting method.
        
        """
        
        hou.hscript("source " + self._copyFile)
        
        
    def pasteUser(self):
        """
            Request a users home directory's and try to load the cmd file.
        
        """
        
        response = hou.ui.readInput("Please provide the username of the user who's file you'd like to load")[1]
        
        if response:
            
            # Returns the filepath of the users we want to look for. we will check and see if this file is really there.
            pathToFile = os.path.join(os.path.dirname(hou.expandString("~")), response, os.path.split(self._copyFile)[1])

            if os.path.isfile(pathToFile):
                
                self._copyFile = pathToFile
                self.paste()
            
            else:
            
                hou.ui.displayMessage("The given username has no written out commands to load in")

        
    def smartPaste(self, pasteTo):
        """
            The Smart paste is a function that adds some extra options to the copy and paste mechanism.
            it will replace the location of the where you are about to paste it to.
        
        """

        replacement = ""        
        lines = self._read(self._copyFile)

        for line in lines:
                
            if "opcf /" in line:
        
                replacement = line.split()[1]
                break

        linesLocation = [line.replace(replacement, pasteTo) for line in lines]
        lines = linesLocation         
                
        for line in lines: 
            
            hou.hscript(line)
            

    def hasGostNodes(self):
        """
            Check to see if the selected output path is there is the scene.
        
        """
        
        lines = self._read(self._copyFile)

        for line in lines:
                
            if "opcf /" in line:
        
                nodePath = line.split()[1]
                
                if not hou.node(nodePath):
                    
                    return nodePath
                
        return ""


    def needVopFix(self):
        """
            We need to check and see if there are any vop types that we need to fix (grrrrr)
        
        """
        needFix = [False]
        
        for _node in hou.selectedNodes():
            
            if self.isVop(_node): 
                
                needFix[0] = True
                needFix.append(_node)
            
            for __node in _node.allSubChildren():
                
                if self.isVop(__node):
                     
                    needFix[0] = True
                    needFix.append(__node)
        
        return needFix


    @staticmethod
    def isVop(_node):
        """
            check if the given nodes is a vop type node. we need to know this because of a bug in houdini.
        
        """
        
        return (re.match(r".*vop.*", _node.type().name()) != None)
    

    @staticmethod
    def isLocked(node):
        """
            check if the given node is locked.
        
        """
    
        if not hasattr(node, "isHardLocked"): 
        
            return False
        
        if node.isHardLocked(): 
            
            return True
    
    @staticmethod
    def _write(text, _file):
        """
            write the commands to a cmd file.
        
        """
        
        file_ = open(_file, 'w')
        file_.write(text)
        file_.close()


    @staticmethod
    def _read(_file):
        """
            Read the file and give back a list of lines.

        """
        
        file_ = open(_file, 'r')
        lines = file_.readlines()
        file_.close()
        
        return lines



class CopyPasteBin(CopyPaste):
    """
        This is the copyPasteBin class. add-on function for the normal class.
        please feel free to implement your own add-on classes
    
    """
    
    def __init__(self):
        """
            please make sure you set your e-mail address in here. Otherwise it will request you fill in the e-mail address every time.
            
        """
       
        CopyPaste.__init__(self)
        self._email = "com48com@gmail.com"
        self._access = 1
        self._expire = "1D"


    def post(self):
        """
            Main function to send information to Pastebin.
            this uses the normal copy function and then send it to the pastebin.com api. (very useful) 
        
        """
       
        email = self._email
       
        if not email:
                   
            email = hou.ui.readInput("e-mail address to send it to")[1]
            
        if not email: 
        
            return
        
        self.copy()

        fileContent = file(self._copyFile, "r").readlines()

        cTime = time.localtime()

        fileName = "cmdCopy_" + str(cTime.tm_mday) + "-" + str(cTime.tm_mon) \
        + "-" + str(cTime.tm_year) + "_" + str(cTime.tm_hour) + "." + str(cTime.tm_min)
        params = urllib.urlencode({'paste_code': str("".join(fileContent))
                                , 'paste_name': fileName
                                , 'paste_email':email
                                , 'paste_private': self._access
                                , 'paste_expire_date': self._expire})
                                
        fd = urllib.urlopen("http://pastebin.com/api_public.php", params)
        try:
            response = fd.read()
            print response 
        finally:
            fd.close()
        del fd

        hou.ui.displayMessage("The file have been sent.")


    def fetch(self):
        """
            request the user to  fill in a path. this usually be along the line of:
            
            http://pastebin.com/sa41wsde
                       
            we will pass this to our function and it will get the code and put it in our tmp file.
            then run it as a normal Paste.
        
        """
       
        urlPath = hou.ui.readInput("URL to the PasteBin File.")[1]
        if not urlPath: 

            return

        path = urlPath.split("/")[-1]
        url = "http://pastebin.com/raw.php?i=%s" % (path)

        f = urllib.urlopen(url)
        s = f.read()
        f.close()
       
        s = self.unescape(str(s.split("<pre>")[1]).split("</pre>")[0])
        self._write(s, self._copyFile)
        self.paste()


    @staticmethod
    def unescape(s):
        """
            normalize the returning char's we get from post bin.
        
        """

        s = s.replace("&quot;", '"')
        s = s.replace("&apos;", "'")
        s = s.replace("&gt;", ">")
        s = s.replace("&lt;", "<")
        s = s.replace("&amp;", "&")

        return s

