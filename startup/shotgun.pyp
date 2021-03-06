# :coding: utf-8
# :copyright: Copyright (c) 2019 Room 8 Studio

import os
import sys
import c4d
import signal
import hashlib

import sgtk

import tank


# Need to find better Solution with dinamic menu
menu_prebuild = [   ['File Save...', '1825592'],
                    ['File Open...', '1760964'],
                    ['Snapshot...', '2436236'],
                    ['Jump to Shotgun', '2701393'],
                    ['Jump to File System', '2158662'],
                    ['Jump to Screening Room in RV', '2188709'],
                    ['Jump to Screening Room Web Player', '2419038'],
                    ['Open Log Folder', '3271712'],
                    ['Scene Breakdown...', '1506973'],
                    ['Load...', '3279052'],
                    ['Reload and Restart', '5919542'],
                    ['Work Area Info...', '2574358'],
                    ['Shotgun Panel...', '2399777'],
                    ['Publish...', '3378887'],
                    ['Sync Frame Range with Shotgun', '3366874'],
                    ['Snapshot History...', '3313077'],
                    ]

logger = sgtk.LogManager.get_logger(__name__)

logger.debug("Launching toolkit in classic mode.")
env_engine = os.environ.get("SGTK_ENGINE")
env_context = os.environ.get("SGTK_CONTEXT")
context = sgtk.context.deserialize(env_context)

try:
    engine = sgtk.platform.start_engine(env_engine, context.sgtk, context)
except:
    engine = tank.platform.engine.current_engine()



def get_plugins():
    out = []
    for item in engine.commands.items():
        tmp = [item]
        m = hashlib.md5()
        m.update(item[0].encode('utf-8'))
        plug_id = str(int(m.hexdigest(), 16))[0:7]
        tmp.append(plug_id)
        out.append(tmp)
    return out


class callbackPlugin(c4d.plugins.CommandData):
    def __init__(self, callback, *args, **kwargs):
        '''Instantiate the asset options.'''
        super(callbackPlugin, self).__init__(*args, **kwargs)
        self.callback = callback

    def _jump_to_sg(self):
        """
        Jump to shotgun, launch web browser
        """
        from sgtk.platform.qt import QtGui, QtCore

        url = engine.context.shotgun_url
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _jump_to_fs(self):
        """
        Jump from context to FS
        """
        # launch one window for each location on disk
        paths = engine.context.filesystem_locations
        for disk_location in paths:

            # get the setting
            system = sys.platform

            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)
            if exit_code != 0:
                engine.logger.error("Failed to launch '%s'!", cmd)

    def Execute(self, doc):
        '''Open dialog when executed.'''
        # self.callback.__call__()
        for item in engine.commands.items():
            if self.callback in item[0]:
                item[1].get('callback').__call__()

        if self.callback == 'Jump to File System':
            self._jump_to_fs()
        elif self.callback == 'Jump to Shotgun':
            self._jump_to_sg()

        return True


class SceneChangeEvent(c4d.plugins.MessageData):
    def __init__(self):
        self.document = c4d.documents.GetActiveDocument()[c4d.DOCUMENT_FILEPATH]

    def CoreMessage(self, id, bc):
        if id == c4d.EVMSG_CHANGE:
            new_document = c4d.documents.GetActiveDocument()[c4d.DOCUMENT_FILEPATH]
            if new_document != self.document:
                if "Untitled " not in new_document:
                    self.document = new_document
                    try:
                        ctx = engine.get_document_context(self.document)
                        engine.change_context(ctx)
                    except tank.TankError as e:
                        logger.exception("Could not execute tank_from_path('%s')" % self.document)
        return True


def EnhanceMainMenu():
    mainMenu = c4d.gui.GetMenuResource("M_EDITOR")
    menu = c4d.BaseContainer()
    menu.InsData(c4d.MENURESOURCE_SUBTITLE, "Shotgun")

    submenu = c4d.BaseContainer()
    submenu.InsData(c4d.MENURESOURCE_SUBTITLE, "{}".format(engine.context))

    registred_commands = get_plugins()
    for item in registred_commands:
        m_type = item[0][1].get('properties').get('type', 'default')
        if 'context_menu' in m_type:
            submenu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(item[-1]))
        else:
            menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(item[-1]))

    menu.InsData(c4d.MENURESOURCE_SUBMENU, submenu)
    mainMenu.InsData(c4d.MENURESOURCE_STRING, menu)


def PluginMessage(id, data):
    if id==c4d.C4DPL_BUILDMENU:
        EnhanceMainMenu()
    if id==c4d.C4DPL_ENDPROGRAM:
        # Close Cinema Solution after PySide executes
        os.kill(os.getpid(), signal.SIGTERM)

def register_plugins():

    c4d.plugins.RegisterMessagePlugin(id=15151510, str="", info=0, dat=SceneChangeEvent())

    for item in engine.import_module("tk_cinema").constant_apps.menu_prebuild:
        if not "separator" in item[-1]:
            c4d.plugins.RegisterCommandPlugin(
                id=int(item[-2]),
                str=item[0],
                info=c4d.PLUGINFLAG_HIDEPLUGINMENU,
                help='',
                icon=None,
                dat=callbackPlugin(callback=item[0])
            )

if __name__ == '__main__':
    register_plugins()
