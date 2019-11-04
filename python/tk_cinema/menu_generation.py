# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Menu handling for Cinema

"""

import tank
import sys
import os
import unicodedata
import traceback

from tank.platform.qt import QtGui, QtCore

import c4d


__author__ = "Mykhailo Datsyk"
__contact__ = "https://www.linkedin.com/in/mykhailo-datsyk/"


class MenuGenerator(object):
    """
    Menu generation functionality for Cinema
    """

    def __init__(self, engine, menu_name):
        self._engine = engine
        self._menu_name = menu_name

    def create_menu(self, *args):
        mainMenu = c4d.gui.GetMenuResource("M_EDITOR")

        for index, x in enumerate(mainMenu):
            if x[1][c4d.MENURESOURCE_SUBTITLE] == self._menu_name:
                mainMenu.RemoveIndex(index)
        
        menu = c4d.BaseContainer()
        menu.InsData(c4d.MENURESOURCE_SUBTITLE, self._menu_name)
        
        submenu = c4d.BaseContainer()
        submenu.InsData(c4d.MENURESOURCE_SUBTITLE, "{}".format(self._engine.context))
        
        submenu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(2701393))
        submenu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(2158662))
        submenu.InsData(c4d.MENURESOURCE_SEPERATOR, True)
        submenu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(2188709))
        submenu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(2419038))
        submenu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(3271712))
        submenu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(2574358))
        menu.InsData(c4d.MENURESOURCE_SUBMENU, submenu)

        menu.InsData(c4d.MENURESOURCE_SEPERATOR, True)
        menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(1760964))

        menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(2436236))
        menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(1825592))
        menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(3378887))

        menu.InsData(c4d.MENURESOURCE_SEPERATOR, True)
        menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(3279052))
        menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(1506973))
        menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(3313077))
        menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(2399777))
        menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_{}".format(3366874))
        
        mainMenu.InsData(c4d.MENURESOURCE_STRING, menu)

        c4d.gui.UpdateMenus()
