# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import c4d

import sgtk
from sgtk import TankError

HookBaseClass = sgtk.get_hook_baseclass()


__author__ = "Mykhailo Datsyk"
__contact__ = "https://www.linkedin.com/in/mykhailo-datsyk/"

class FrameOperation(HookBaseClass):
    """
    Hook called to perform a frame operation with the
    current scene
    """

    def get_frame_range(self, **kwargs):
        """
        get_frame_range will return a tuple of (in_frame, out_frame)
        :returns: Returns the frame range in the form (in_frame, out_frame)
        :rtype: tuple[int, int]
        """

        doc = c4d.documents.GetActiveDocument()
        fps = doc[c4d.DOCUMENT_FPS]
        return (
            doc[c4d.DOCUMENT_MINTIME].GetFrame(fps),
            doc[c4d.DOCUMENT_MAXTIME].GetFrame(fps)
        )

    def set_frame_range(self, in_frame=None, out_frame=None, **kwargs):
        """
        set_frame_range will set the frame range using `in_frame` and `out_frame`
        :param int in_frame: in_frame for the current context
            (e.g. the current shot, current asset etc)
        :param int out_frame: out_frame for the current context
            (e.g. the current shot, current asset etc)
        """

        doc = c4d.documents.GetActiveDocument()
        fps = doc[c4d.DOCUMENT_FPS]
        head_in_frame = kwargs.get('head_in_frame')
        tail_out_frame = kwargs.get('tail_out_frame')

        if head_in_frame:
            # Set Handles if exists
            doc[c4d.DOCUMENT_MINTIME] = c4d.BaseTime(head_in_frame, fps)
        else:
            doc[c4d.DOCUMENT_MINTIME] = c4d.BaseTime(in_frame, fps)

        if tail_out_frame:
            # Set Handles if exists
            doc[c4d.DOCUMENT_MAXTIME] = c4d.BaseTime(tail_out_frame, fps)
        else:
            doc[c4d.DOCUMENT_MAXTIME] = c4d.BaseTime(out_frame, fps)

        # Set Project Preview MIN/MAX Time
        doc[c4d.DOCUMENT_LOOPMINTIME] = c4d.BaseTime(in_frame, fps)
        doc[c4d.DOCUMENT_LOOPMAXTIME] = c4d.BaseTime(out_frame, fps)

        doc[c4d.DOCUMENT_LOOPMINTIME] = c4d.BaseTime(in_frame, fps)
        return True
