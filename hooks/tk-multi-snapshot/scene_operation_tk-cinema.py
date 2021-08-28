# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import c4d

import tank
from tank import Hook
from tank import TankError


__author__ = "Mykhailo Datsyk"
__contact__ = "https://www.linkedin.com/in/mykhailo-datsyk/"


class SceneOperation(Hook):
    """
    Hook called to perform an operation with the 
    current scene
    """

    def execute(self, operation, file_path, **kwargs):
        """
        Main hook entry point
        
        :operation: String
                    Scene operation to perform
        
        :file_path: String
                    File path to use if the operation
                    requires it (e.g. open)
                    
        :returns:   Depends on operation:
                    'current_path' - Return the current scene
                                     file path as a String
                    all others     - None
        """
        doc = c4d.documents.GetActiveDocument()

        if operation == "current_path":
            # return the current scene path
            return doc[c4d.DOCUMENT_FILEPATH]
        elif operation == "open":
            c4d.documents.LoadFile(file_path)
        elif operation == "save":
            current_project = doc[c4d.DOCUMENT_FILEPATH]

            folder, file = os.path.split(file_path)
            doc.SetDocumentName(file)
            doc.SetDocumentPath(folder)
            c4d.documents.SaveDocument(doc, file_path, c4d.SAVEDOCUMENTFLAGS_NONE, c4d.FORMAT_C4DEXPORT)
