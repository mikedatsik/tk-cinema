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
import tempfile
import uuid

import tank
from tank import Hook
from tank.platform.qt import QtCore, QtGui


__author__ = "Mykhailo Datsyk"
__contact__ = "https://www.linkedin.com/in/mykhailo-datsyk/"


class ThumbnailHook(Hook):
    """
    Hook that can be used to provide a pre-defined thumbnail for the app
    """

    def execute(self, **kwargs):
        """
        Main hook entry point
        :returns:       String
                        Hook should return a file path pointing to the location
                        of a thumbnail file on disk that will be used.
                        If the hook returns None then the screenshot
                        functionality will be enabled in the UI.
        """
        engine = self.parent.engine
        engine_name = engine.name

        # depending on engine:
        if engine_name == "tk-cinema":
            return self._extract_cinema_thumbnail()

        # default implementation does nothing
        return None

    def _extract_cinema_thumbnail(self):
        """
        Render a thumbnail for the current window in Cinema

        :returns:   The path to the thumbnail on disk
        """
        thumb = QtGui.QPixmap.grabWindow(QtGui.QApplication.desktop().winId())

        if thumb:
            # save the thumbnail
            temp_dir = tempfile.gettempdir()
            temp_filename = "sgtk_thumb_%s.jpg" % uuid.uuid4().hex
            jpg_thumb_path = os.path.join(temp_dir, temp_filename)
            thumb.save(jpg_thumb_path)

        return jpg_thumb_path
