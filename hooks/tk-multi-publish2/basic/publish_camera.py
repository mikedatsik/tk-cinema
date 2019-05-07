# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import fnmatch
import os

import c4d

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class CinemaCameraPublishPlugin(HookBaseClass):
    """
    Publish2 plugin for publishing cinema cameras to abc files.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_camera.py"

    """

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        return """
        <p>This plugin handles publishing of cameras from cinema.
        A publish template is required to define the destination of the output
        file. The FBXExport command is used to create the camera.
        </p>
        """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """
        # inherit the settings from the base publish plugin
        base_settings = super(CinemaCameraPublishPlugin, self).settings or {}

        # settings specific to this class
        cinema_camera_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published camera. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            },
            "Cameras": {
                "type": "list",
                "default": ["camera*"],
                "description": "Glob-style list of camera names to publish. "
                               "Example: ['camMain', 'camAux*']."
            }
        }

        # update the base settings
        base_settings.update(cinema_camera_publish_settings)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["cinema.*", "file.cinema"]
        """
        return ["cinema.session.camera"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here. Returns a
        dictionary with the following booleans:

            - accepted: Indicates if the plugin is interested in this value at
                all. Required.
            - enabled: If True, the plugin will be enabled in the UI, otherwise
                it will be disabled. Optional, True by default.
            - visible: If True, the plugin will be visible in the UI, otherwise
                it will be hidden. Optional, True by default.
            - checked: If True, the plugin will be checked in the UI, otherwise
                it will be unchecked. Optional, True by default.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: dictionary with boolean keys accepted, required and enabled
        """

        publisher = self.parent
        template_name = settings["Publish Template"].value

        # validate the camera name first
        cam_name = item.properties.get("camera_name")
        cam_shape = item.properties.get("camera_shape")

        if cam_name and cam_shape:
            if not self._cam_name_matches_settings(cam_name, settings):
                self.logger.debug(
                    "Camera name %s does not match any of the configured "
                    "patterns for camera names to publish. Not accepting "
                    "session camera item." % (cam_name,)
                )
                return {"accepted": False}
        else:
            self.logger.debug(
                "Camera name or shape was set on the item properties. Not "
                "accepting session camera item."
            )
            return {"accepted": False}

        # ensure a camera file template is available on the parent item
        work_template = item.parent.properties.get("work_template")
        if not work_template:
            self.logger.debug(
                "A work template is required for the session item in order to "
                "publish a camera. Not accepting session camera item."
            )
            return {"accepted": False}

        # ensure the publish template is defined and valid and that we also have
        publish_template = publisher.get_template_by_name(template_name)
        if publish_template:
            item.properties["publish_template"] = publish_template
            # because a publish template is configured, disable context change.
            # This is a temporary measure until the publisher handles context
            # switching natively.
            item.context_change_allowed = False
        else:
            self.logger.debug(
                "The valid publish template could not be determined for the "
                "session camera item. Not accepting the item."
            )
            return {"accepted": False}

        # all good!
        return {
            "accepted": True,
            "checked": True
        }

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish. Returns a
        boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """

        path = _session_path()
        doc = c4d.documents.GetActiveDocument()

        # ---- ensure the session has been saved

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Cinema session has not been saved."
            self.logger.error(
                error_msg,
                extra=_get_save_as_action()
            )
            raise Exception(error_msg)

        # get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)

        cam_name = item.properties["camera_name"]

        # check that the camera still exists in the file
        if not doc.SearchObject(cam_name):
            error_msg = (
                "Validation failed because the collected camera (%s) is no "
                "longer in the scene. You can uncheck this plugin or create "
                "a camera with this name to export to avoid this error." %
                (cam_name,)
            )
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # get the configured work file template
        work_template = item.parent.properties.get("work_template")
        publish_template = item.properties.get("publish_template")

        # get the current scene path and extract fields from it using the work
        # template:
        work_fields = work_template.get_fields(path)

        # include the camera name in the fields
        work_fields["camera_name"] = cam_name

        # ensure the fields work for the publish template
        missing_keys = publish_template.missing_keys(work_fields)
        if missing_keys:
            error_msg = "Work file '%s' missing keys required for the " \
                        "publish template: %s" % (path, missing_keys)
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # create the publish path by applying the fields. store it in the item's
        # properties. This is the path we'll create and then publish in the base
        # publish plugin. Also set the publish_path to be explicit.
        publish_path = publish_template.apply_fields(work_fields)
        item.properties["path"] = publish_path
        item.properties["publish_path"] = publish_path

        # use the work file's version number when publishing
        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]

        # run the base class validation
        return super(CinemaCameraPublishPlugin, self).validate(settings, item)

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        # keep track of everything currently selected. we will restore at the
        # end of the publish method

        # the camera to publish
        cam_shape = item.properties["camera_shape"]

        # get the path to create and publish
        publish_path = item.properties["publish_path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)

        doc = c4d.documents.GetActiveDocument()
        tdoc = c4d.documents.IsolateObjects(doc, [cam_shape])

        plug = c4d.plugins.FindPlugin(1028082, c4d.PLUGINTYPE_SCENESAVER)

        op = {}
        plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, op)
        abcExport = op["imexporter"]

        abcExport[c4d.ABCEXPORT_SELECTION_ONLY] = False
        abcExport[c4d.ABCEXPORT_PARTICLES] = True
        abcExport[c4d.ABCEXPORT_FRAME_START] = doc.GetLoopMinTime().GetFrame(doc.GetFps())
        abcExport[c4d.ABCEXPORT_FRAME_END] = doc.GetLoopMaxTime().GetFrame(doc.GetFps())

        if c4d.documents.SaveDocument(tdoc, publish_path, c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST, 1028082):
            self.logger.debug("Run export command.")
        else:
            self.logger.error("Failed to export camera.")

        # Now that the path has been generated, hand it off to the
        super(CinemaCameraPublishPlugin, self).publish(settings, item)


    def _cam_name_matches_settings(self, cam_name, settings):
        """
        Returns True if the supplied camera name matches any of the configured
        camera name patterns.
        """

        # loop through each pattern specified and see if the supplied camera
        # name matches the pattern
        cam_patterns = settings["Cameras"].value

        # if no patterns specified, then no constraints on camera name
        if not cam_patterns:
            return True

        for camera_pattern in cam_patterns:
            if fnmatch.fnmatch(cam_name, camera_pattern):
                return True

        return False

def _session_path():
    """
    Return the path to the current session
    :return:
    """
    doc = c4d.documents.GetActiveDocument()

    project_path = doc.GetDocumentPath()
    project_name = doc.GetDocumentName()
    path = os.path.join(project_path, project_name)

    if isinstance(path, unicode):
        path = path.encode("utf-8")

    return path

def _save_session(path):
    """
    Save the current session to the supplied path.
    """

    # Ensure that the folder is created when saving
    folder = os.path.dirname(path)
    ensure_folder_exists(folder)

    doc = c4d.documents.GetActiveDocument()
    c4d.documents.SaveDocument(doc, str(path), c4d.SAVEDOCUMENTFLAGS_NONE, c4d.FORMAT_C4DEXPORT)
    c4d.documents.LoadFile(path)


# TODO: method duplicated in all the cinema hooks
def _get_save_as_action():
    """
    Simple helper for returning a log action dict for saving the session
    """

    engine = sgtk.platform.current_engine()

    callback = _save_as

    # if workfiles2 is configured, use that for file save
    if "tk-multi-workfiles2" in engine.apps:
        app = engine.apps["tk-multi-workfiles2"]
        if hasattr(app, "show_file_save_dlg"):
            callback = app.show_file_save_dlg

    return {
        "action_button": {
            "label": "Save As...",
            "tooltip": "Save the current session",
            "callback": callback,
        }
    }


def _save_as():
    doc = c4d.documents.GetActiveDocument()
    path = c4d.storage.SaveDialog(c4d.FILESELECTTYPE_SCENES)
    if path:
        c4d.documents.SaveDocument(doc, str(path), c4d.SAVEDOCUMENTFLAGS_NONE, c4d.FORMAT_C4DEXPOR)
