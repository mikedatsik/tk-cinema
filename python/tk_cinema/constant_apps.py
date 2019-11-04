# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

# Menu Id"s generated with simple function
# def get_plugins():
#     out = []
#     for item in engine.commands.items():
#         tmp = [item]
#         m = hashlib.md5()
#         m.update(item[0])
#         plug_id = str(int(m.hexdigest(), 16))[0:7]
#         tmp.append(plug_id)
#         out.append(tmp)
#     return out

menu_prebuild = [   
                    ["Separator", "0", "separator"],
                    ["Jump to Shotgun", "2701393", "submenu"], 
                    ["Jump to File System", "2158662", "submenu"],
                    ["Jump to Screening Room in RV", "2188709", "submenu"],
                    ["Jump to Screening Room Web Player", "2419038", "submenu"],
                    ["Reload and Restart", "5919542", "submenu"],
                    ["Open Log Folder", "3271712", "submenu"],
                    ["Work Area Info...", "2574358", "submenu"],
                    ["File Open...", "1760964", "main"],
                    ["Snapshot...", "2436236", "main"],
                    ["File Save...", "1825592", "main"],
                    ["Publish...", "3378887", "main"],
                    ["Load...", "3279052", "main"],
                    ["Separator", "0", "separator"],
                    ["Scene Breakdown...", "1506973", "main"],
                    ["Shotgun Panel...", "2399777", "main"],
                    ["Snapshot History...", "3313077", "main"],
                    ["Sync Frame Range with Shotgun", "3366874", "main"],
                    ["Separator", "0", "separator"],
                ]