import os
import sys

import sgtk
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation


__author__ = "Mykhailo Datsyk"
__contact__ = "https://www.linkedin.com/in/mykhailo-datsyk/"


class CinemaLauncher(SoftwareLauncher):
    """
    Handles launching Cinema executables. Automatically starts up
    a tk-cinema engine with the current context in the new session
    of Cinema.
    """

    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and products. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place
    COMPONENT_REGEX_LOOKUP = {"version": r"R\d\d|\d\d\d\d|\d\d\d\d\.\d"}

    EXECUTABLE_TEMPLATES = {
        "darwin": [
            "/Applications/MAXON/Cinema 4D {version}/CINEMA 4D.app",
            "$CINEMA_BIN_DIR/CINEMA 4D.app",
        ],
        "win32": [
            "C:/Program Files/MAXON/Cinema 4D {version}/CINEMA 4D.exe",
            "C:/Program Files/MAXON Cinema 4D {version}/CINEMA 4D.exe",
            "$CINEMA_BIN_DIR/CINEMA 4D.exe",
        ],
    }

    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return "20"

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch Cinema in that will automatically
        load Toolkit and the tk-cinema engine when Cinema starts.

        :param str exec_path: Path to Cinema executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on
                                 launch.
        :returns: :class:`LaunchInformation` instance
        """

        required_env = {}

        # Run the engine's userSetup.py file when Cinema starts up
        # by appending it to the env PYTHONPATH.
        startup_path = os.path.join(self.disk_location, "startup")

        sgtk.util.append_path_to_env_var("g_additionalModulePath", startup_path)
        required_env["g_additionalModulePath"] = os.environ["g_additionalModulePath"]

        if "R23" in exec_path:
            # Get Qt Site - when launching from Shotgun Desktop this should
            # point to the installs lib/site-packages directory.
            try:
                from sgtk.platform.qt import QtCore

                qt_site = os.path.dirname(os.path.dirname(QtCore.__file__))
                sgtk.util.append_path_to_env_var("PYTHONPATH", qt_site)
            except ImportError:
                pass

        sgtk.util.append_path_to_env_var(
            "PYTHONPATH", os.path.join(startup_path, "libs")
        )
        required_env["PYTHONPATH"] = os.environ["PYTHONPATH"]
        required_env["C4DPYTHONPATH37"] = os.environ["PYTHONPATH"]  # R23
        required_env["C4DPYTHONPATH39"] = os.environ["PYTHONPATH"]  # R24-2023.1
        required_env["C4DPYTHONPATH310"] = os.environ["PYTHONPATH"]  # 2023.2

        # Prepare the launch environment with variables required by the
        # classic bootstrap approach.
        self.logger.debug("Preparing Cinema Launch via Toolkit Classic methodology ...")
        required_env["SGTK_ENGINE"] = self.engine_name
        required_env["SGTK_CONTEXT"] = sgtk.context.serialize(self.context)

        if file_to_open:
            # Add the file name to open to the launch environment
            required_env["SGTK_FILE_TO_OPEN"] = file_to_open

        return LaunchInformation(exec_path, args, required_env)

    ###########################################################################
    # private methods

    def _icon_from_engine(self):
        """
        Use the default engine icon as cinema does not supply
        an icon in their software directory structure.

        :returns: Full path to application icon as a string or None.
        """

        # the engine icon
        engine_icon = os.path.join(self.disk_location, "icon_256.png")
        return engine_icon

    def scan_software(self):
        """
        Scan the filesystem for cinema executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """
        self.logger.debug("Scanning for Cinema executables...")

        supported_sw_versions = []
        for sw_version in self._find_software():
            (supported, reason) = self._is_supported(sw_version)
            if supported:
                supported_sw_versions.append(sw_version)
            else:
                self.logger.debug(
                    "SoftwareVersion %s is not supported: %s" % (sw_version, reason)
                )

        return supported_sw_versions

    def _find_software(self):
        """
        Find executables in the default install locations.
        """

        # all the executable templates for the current OS
        executable_templates = self.EXECUTABLE_TEMPLATES.get(sys.platform, [])

        # all the discovered executables
        sw_versions = []

        for executable_template in executable_templates:
            executable_template = os.path.expanduser(executable_template)
            executable_template = os.path.expandvars(executable_template)

            self.logger.debug("Processing template %s", executable_template)

            executable_matches = self._glob_and_match(
                executable_template, self.COMPONENT_REGEX_LOOKUP
            )

            # Extract all products from that executable.
            for executable_path, key_dict in executable_matches:
                # extract the matched keys form the key_dict.
                # in the case of version we return something different than
                # an empty string because there are cases were the installation
                # directories do not include version number information.
                executable_version = key_dict.get("version", " ").lstrip("R")

                sw_versions.append(
                    SoftwareVersion(
                        executable_version,
                        "Cinema",
                        executable_path,
                        self._icon_from_engine(),
                    )
                )

        return sw_versions
