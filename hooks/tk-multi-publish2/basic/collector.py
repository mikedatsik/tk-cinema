# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import glob
import os
import c4d
import sgtk


__author__ = "Mykhailo Datsyk"
__contact__ = "https://www.linkedin.com/in/mykhailo-datsyk/"


HookBaseClass = sgtk.get_hook_baseclass()

def get_all_objects(op, filter, output):
    while op:
        if filter(op):
            output.append(op)
        get_all_objects(op.GetDown(), filter, output)
        op = op.GetNext()
    return output


class CinemaSessionCollector(HookBaseClass):
    """
    Collector that operates on the cinema session. Should inherit from the
    basic collector hook.
    """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this collector expects to receive
        through the settings parameter in the process_current_session and
        process_file methods.

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

        # grab any base class settings
        collector_settings = super(CinemaSessionCollector, self).settings or {}

        # settings specific to this collector
        cinema_session_settings = {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for artist work files. Should "
                               "correspond to a template defined in "
                               "templates.yml. If configured, is made available"
                               "to publish plugins via the collected item's "
                               "properties. ",
            },
        }

        # update the base settings with these settings
        collector_settings.update(cinema_session_settings)

        return collector_settings

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Cinema and parents a subtree of
        items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        """
        # create an item representing the current cinema session
        doc = c4d.documents.GetActiveDocument()
        item = self.collect_current_cinema_session(settings, parent_item)
        project_root = doc.GetDocumentPath()

        self.collect_playblasts(item, project_root)
        self.collect_alembic_caches(item, project_root)
        self._collect_session_cameras(item)
        self.collect_rendered_images(item)

    def collect_current_cinema_session(self, settings, parent_item):
        """
        Creates an item that represents the current cinema session.

        :param parent_item: Parent Item instance

        :returns: Item of type cinema.session
        """

        publisher = self.parent

        # get the path to the current file
        doc = c4d.documents.GetActiveDocument()

        project_path = doc.GetDocumentPath()
        project_name = doc.GetDocumentName()
        path = os.path.join(project_path, project_name)

        # determine the display name for the item
        if project_path:
            file_info = publisher.util.get_file_path_components(path)
            display_name = file_info["filename"]
        else:
            display_name = "Untitled_01"

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            "cinema.session",
            "Cinema Session",
            display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "cinema.png"
        )
        session_item.set_icon_from_path(icon_path)

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:

            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value)

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template
            session_item.properties["publish_type"] = "Cinema Project File"
            self.logger.debug("Work template defined for Cinema collection.")

        self.logger.info("Collected current Cinema scene")

        return session_item

    def _collect_session_cameras(self, parent_item):
        """
        Creates items for each camera to be exported.

        :param parent_item:
        :return:
        """

        # get the icon path to display for camera items
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "camera.png"
        )

        doc = c4d.documents.GetActiveDocument()
        cameras = get_all_objects(doc.GetFirstObject(), lambda x: x.CheckType(5103), [])
        
        for camera in cameras:
            if camera.GetType() == 5103:
                # try to determine the camera display name
                camera_name = camera.GetName()

                cam_item = parent_item.create_item(
                    "cinema.session.camera",
                    "Camera",
                    camera_name
                )

                cam_item.set_icon_from_path(icon_path)

                # store the camera name so that any attached plugin knows which
                # camera this item represents!
                cam_item.properties["camera_name"] = camera_name
                cam_item.properties["camera_shape"] = camera
                cam_item.properties["publish_type"] = "Camera"

                self.logger.debug("Collected cemera:" + camera_name)

    def collect_playblasts(self, parent_item, project_root):
        """
        Creates items for quicktime playblasts.

        Looks for a 'project_root' property on the parent item, and if such
        exists, look for movie files in a 'movies' subfolder.

        :param parent_item: Parent Item instance
        :param str project_root: The maya project root to search for playblasts
        """

        # ensure the movies dir exists
        movies_dir = os.path.join(project_root, "movies")
        if not os.path.exists(movies_dir):
            return

        self.logger.info(
            "Processing movies folder: %s" % (movies_dir,),
            extra={
                "action_show_folder": {
                    "path": movies_dir
                }
            }
        )

        # look for movie files in the movies folder
        for filename in os.listdir(movies_dir):

            # do some early pre-processing to ensure the file is of the right
            # type. use the base class item info method to see what the item
            # type would be.
            item_info = self._get_item_info(filename)
            if item_info["item_type"] != "file.video":
                continue

            movie_path = os.path.join(movies_dir, filename)

            # allow the base class to collect and create the item. it knows how
            # to handle movie files
            item = super(CinemaSessionCollector, self)._collect_file(
                parent_item,
                movie_path
            )

            # the item has been created. update the display name to include
            # the an indication of what it is and why it was collected
            item.name = "%s (%s)" % (item.name, "playblast")

    def collect_alembic_caches(self, parent_item, project_root):
        """
        Creates items for alembic caches

        Looks for a 'project_root' property on the parent item, and if such
        exists, look for alembic caches in a 'cache/alembic' subfolder.

        :param parent_item: Parent Item instance
        :param str project_root: The maya project root to search for alembics
        """

        # ensure the alembic cache dir exists
        cache_dir = os.path.join(project_root, "cache", "alembic")
        if not os.path.exists(cache_dir):
            return

        self.logger.info(
            "Processing alembic cache folder: %s" % (cache_dir,),
            extra={
                "action_show_folder": {
                    "path": cache_dir
                }
            }
        )

        # look for alembic files in the cache folder
        for filename in os.listdir(cache_dir):
            cache_path = os.path.join(cache_dir, filename)

            # do some early pre-processing to ensure the file is of the right
            # type. use the base class item info method to see what the item
            # type would be.
            item_info = self._get_item_info(filename)
            if item_info["item_type"] != "file.alembic":
                continue

            # allow the base class to collect and create the item. it knows how
            # to handle alembic files
            super(CinemaSessionCollector, self)._collect_file(
                parent_item,
                cache_path
            )

    def collect_rendered_images(self, parent_item):
        """
        Creates items for any rendered images that can be identified by
        render layers in the file.
        :param parent_item: Parent Item instance
        :return:
        """

        # iterate over defined render layers and query the render settings for
        # information about a potential render

        doc = c4d.documents.GetActiveDocument()

        active_data = doc.GetActiveRenderData()
        active_video_post = active_data.GetFirstVideoPost()

        if active_data.GetName() == 'shotgun_render' and active_video_post.GetName() == 'Octane Renderer':
            takedata = doc.GetTakeData()
            main = takedata.GetMainTake()
            talelist = [main]
            talelist = talelist + main.GetChildren()

            work_template = parent_item.properties.get("work_template")
            work_fields = work_template.get_fields(doc[c4d.DOCUMENT_FILEPATH])

            for take in talelist:
                renderData = take.GetRenderData(takedata)
                if renderData:
                    renderer = renderData.GetFirstVideoPost()
                    renderpath = renderer[c4d.SET_PASSES_SAVEPATH]
                    rpd = {'_doc': doc, '_rData': renderData, '_rBc': renderData.GetData(), '_frame': 0}
                    fpath = c4d.modules.tokensystem.FilenameConvertTokens(renderpath, rpd)
                    fpath = os.path.dirname(fpath)
                    if renderer[c4d.SET_PASSES_MULTILAYER]:
                        fpath = os.path.dirname(fpath)
                
                joined_path = os.path.abspath(
                                os.path.join(
                                    doc.GetDocumentPath(), fpath.replace('$take', take.GetName())
                                    ))
                if os.path.exists(joined_path):
                    for layer in os.listdir(joined_path):
                        rendered_paths = glob.glob(
                            os.path.join(joined_path, layer, '*.exr'))

                        self.logger.info("Processing render take_layer: %s_%s" % (take.GetName(), layer))

                        if rendered_paths:
                            item = super(CinemaSessionCollector, self)._collect_file(
                                parent_item,
                                rendered_paths[0],
                                frame_sequence=True
                            )
                            render_name = "Take_Layer: %s_%s" % (take.GetName(), layer)
                            item.properties["publish_version"] = work_fields["version"]
                            item.properties["publish_name"] = render_name
                            item.name = render_name